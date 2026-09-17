package com.star.watch;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.pm.PackageManager;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * Coleta somente sensores físicos presentes no relógio enquanto o usuário deixa
 * o modo SENSORES ligado. Não cria valores sintéticos e não roda em background
 * depois que a Activity é destruída.
 */
final class WatchSensorBridge implements SensorEventListener, LocationListener {
    interface TelemetrySink { void send(JSONArray samples); }

    private final Activity activity;
    private final SensorManager sensors;
    private final LocationManager location;
    private final TelemetrySink sink;
    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
    private final Object lock = new Object();
    private final Map<String, JSONObject> latest = new LinkedHashMap<>();
    private volatile boolean active = false;

    WatchSensorBridge(Activity activity, TelemetrySink sink) {
        this.activity = activity;
        this.sink = sink;
        this.sensors = (SensorManager) activity.getSystemService(Context.SENSOR_SERVICE);
        this.location = (LocationManager) activity.getSystemService(Context.LOCATION_SERVICE);
        scheduler.scheduleAtFixedRate(this::flush, 3, 5, TimeUnit.SECONDS);
    }

    boolean isActive() { return active; }

    void start() {
        if (active) return;
        active = true;
        register(Sensor.TYPE_ACCELEROMETER);
        register(Sensor.TYPE_GYROSCOPE);
        register(Sensor.TYPE_ROTATION_VECTOR);
        register(Sensor.TYPE_HEART_RATE);
        register(Sensor.TYPE_STEP_COUNTER);
        register(Sensor.TYPE_PROXIMITY);
        startLocation();
    }

    void stop() {
        active = false;
        if (sensors != null) sensors.unregisterListener(this);
        if (location != null) {
            try { location.removeUpdates(this); } catch (SecurityException ignored) { }
        }
        synchronized (lock) { latest.clear(); }
    }

    void close() {
        stop();
        scheduler.shutdownNow();
    }

    private boolean granted(String permission) {
        return activity.checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED;
    }

    private void register(int type) {
        if (sensors == null) return;
        if (type == Sensor.TYPE_HEART_RATE && !granted(Manifest.permission.BODY_SENSORS)) return;
        if (type == Sensor.TYPE_STEP_COUNTER
                && Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q
                && !granted(Manifest.permission.ACTIVITY_RECOGNITION)) return;
        Sensor sensor = sensors.getDefaultSensor(type);
        if (sensor == null) return;
        try {
            sensors.registerListener(this, sensor, SensorManager.SENSOR_DELAY_NORMAL);
        } catch (SecurityException ignored) {
            // Permissão/hardware indisponível significa ausência de observação,
            // nunca valor sintético nem queda da Activity.
        }
    }

    private void startLocation() {
        if (location == null) return;
        if (!granted(Manifest.permission.ACCESS_FINE_LOCATION)
                && !granted(Manifest.permission.ACCESS_COARSE_LOCATION)) return;
        try {
            if (location.isProviderEnabled(LocationManager.GPS_PROVIDER))
                location.requestLocationUpdates(LocationManager.GPS_PROVIDER, 5000L, 2f, this);
            if (location.isProviderEnabled(LocationManager.NETWORK_PROVIDER))
                location.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 10000L, 5f, this);
        } catch (IllegalArgumentException | SecurityException ignored) { }
    }

    private void put(String kind, JSONObject sample) {
        if (!active) return;
        try {
            sample.put("kind", kind);
            sample.put("timestamp", System.currentTimeMillis());
            synchronized (lock) { latest.put(kind, sample); }
        } catch (Exception ignored) { }
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (!active || event == null || event.sensor == null) return;
        try {
            JSONObject value = new JSONObject();
            switch (event.sensor.getType()) {
                case Sensor.TYPE_ACCELEROMETER:
                    value.put("x", event.values[0]); value.put("y", event.values[1]); value.put("z", event.values[2]);
                    value.put("unit", "m/s^2"); put("accelerometer", value); break;
                case Sensor.TYPE_GYROSCOPE:
                    value.put("x", event.values[0]); value.put("y", event.values[1]); value.put("z", event.values[2]);
                    value.put("unit", "rad/s"); put("gyroscope", value); break;
                case Sensor.TYPE_ROTATION_VECTOR:
                    value.put("x", event.values.length > 0 ? event.values[0] : 0);
                    value.put("y", event.values.length > 1 ? event.values[1] : 0);
                    value.put("z", event.values.length > 2 ? event.values[2] : 0);
                    value.put("unit", "unitless"); put("rotation_vector", value); break;
                case Sensor.TYPE_HEART_RATE:
                    if (event.values.length > 0 && event.values[0] > 0) {
                        value.put("bpm", event.values[0]); value.put("accuracy", event.accuracy); put("heart_rate", value);
                    }
                    break;
                case Sensor.TYPE_STEP_COUNTER:
                    if (event.values.length > 0 && event.values[0] >= 0) {
                        value.put("steps", (long) event.values[0]); put("steps", value);
                    }
                    break;
                case Sensor.TYPE_PROXIMITY:
                    if (event.values.length > 0 && event.values[0] >= 0) {
                        value.put("centimeters", event.values[0]); value.put("method", "android-proximity"); put("proximity", value);
                    }
                    break;
                default: break;
            }
        } catch (Exception ignored) { }
    }

    @Override
    public void onLocationChanged(Location item) {
        if (!active || item == null) return;
        try {
            JSONObject value = new JSONObject();
            value.put("kind", "location"); value.put("timestamp", item.getTime());
            value.put("latitude", item.getLatitude()); value.put("longitude", item.getLongitude());
            value.put("accuracy_m", item.hasAccuracy() ? item.getAccuracy() : 9999.0);
            synchronized (lock) { latest.put("location", value); }
        } catch (Exception ignored) { }
    }

    @Override public void onStatusChanged(String provider, int status, Bundle extras) { }
    @Override public void onProviderEnabled(String provider) { }
    @Override public void onProviderDisabled(String provider) { }
    @Override public void onAccuracyChanged(Sensor sensor, int accuracy) { }

    private void flush() {
        if (!active) return;
        JSONArray batch = new JSONArray();
        synchronized (lock) {
            for (JSONObject sample : latest.values()) batch.put(sample);
            latest.clear();
        }
        if (batch.length() > 0) sink.send(batch);
    }
}
