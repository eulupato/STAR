package com.star.watch;

import android.content.Context;
import android.content.SharedPreferences;
import android.provider.Settings;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.widget.TextView;
import android.widget.ViewFlipper;

import org.json.JSONObject;

import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Navegação horizontal do STAR Watch sem duplicar estado cognitivo.
 *
 * Página 0 = experiência principal existente.
 * Página 1 = AGORA. Ao entrar, pede "status agora" ao mesmo STAR Core. Se o Core
 * estiver offline/desconectado, hora/data locais continuam disponíveis no relógio.
 */
public class NowSwipeView extends ViewFlipper {
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private float downX;
    private float downY;
    private boolean intercepting;

    public NowSwipeView(Context context) {
        super(context);
        init();
    }

    public NowSwipeView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    private void init() {
        setMeasureAllChildren(true);
    }

    private float threshold() {
        return 52f * getResources().getDisplayMetrics().density;
    }

    @Override
    public boolean onInterceptTouchEvent(MotionEvent event) {
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                downX = event.getX();
                downY = event.getY();
                intercepting = false;
                break;
            case MotionEvent.ACTION_MOVE:
                float dx = event.getX() - downX;
                float dy = event.getY() - downY;
                if (Math.abs(dx) > threshold() && Math.abs(dx) > Math.abs(dy) * 1.2f) {
                    intercepting = true;
                    return true;
                }
                break;
            default:
                break;
        }
        return false;
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (event.getActionMasked() == MotionEvent.ACTION_UP || event.getActionMasked() == MotionEvent.ACTION_CANCEL) {
            float dx = event.getX() - downX;
            float dy = event.getY() - downY;
            if (intercepting || (Math.abs(dx) > threshold() && Math.abs(dx) > Math.abs(dy) * 1.2f)) {
                if (dx < 0 && getDisplayedChild() == 0) {
                    setDisplayedChild(1);
                    refreshNow();
                } else if (dx > 0 && getDisplayedChild() == 1) {
                    setDisplayedChild(0);
                }
                intercepting = false;
                return true;
            }
        }
        return true;
    }

    private void refreshNow() {
        TextView nowText = findViewById(R.id.nowTimeText);
        TextView status = findViewById(R.id.nowStatusText);
        if (nowText != null) {
            String value = new SimpleDateFormat("HH:mm\nEEE, dd/MM/yyyy", Locale.getDefault()).format(new Date());
            nowText.setText(value);
        }
        if (status == null) return;

        SharedPreferences preferences = getContext().getSharedPreferences("star_watch", Context.MODE_PRIVATE);
        String base = normalizeServer(preferences.getString("server", ""));
        String token = preferences.getString("token", "");
        if (base.isEmpty() || token.isEmpty()) {
            status.setText("🔒 Core desconectado\nHora e data continuam locais.");
            return;
        }
        status.setText("⭐ Consultando STAR Core...");
        executor.execute(() -> {
            String value;
            try {
                value = fetchCoreNow(base, token);
            } catch (Exception exception) {
                value = "● Sem conexão com o Core\n" + exception.getClass().getSimpleName();
            }
            final String finalValue = value;
            post(() -> {
                TextView target = findViewById(R.id.nowStatusText);
                if (target != null && getDisplayedChild() == 1) target.setText(finalValue);
            });
        });
    }

    private String fetchCoreNow(String base, String token) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(base + "/v1/text").openConnection();
        connection.setRequestMethod("POST");
        connection.setConnectTimeout(5000);
        connection.setReadTimeout(15000);
        connection.setDoOutput(true);
        connection.setRequestProperty("Accept", "application/json");
        connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
        connection.setRequestProperty("Authorization", "Bearer " + token);
        connection.setRequestProperty("X-STAR-Device", deviceId());
        connection.setRequestProperty("X-STAR-Client-Form", "watch");
        byte[] body = new JSONObject().put("text", "status agora").toString().getBytes(StandardCharsets.UTF_8);
        try (OutputStream output = connection.getOutputStream()) {
            output.write(body);
        }
        int code = connection.getResponseCode();
        InputStream stream = code >= 200 && code < 300 ? connection.getInputStream() : connection.getErrorStream();
        String raw = new String(readAll(stream), StandardCharsets.UTF_8);
        if (code < 200 || code >= 300) throw new IllegalStateException("HTTP " + code);
        return new JSONObject(raw).optString("response", "Sem status.");
    }

    private String deviceId() {
        String value = Settings.Secure.getString(getContext().getContentResolver(), Settings.Secure.ANDROID_ID);
        return value == null || value.trim().isEmpty() ? "star-watch" : "watch-" + value;
    }

    private static String normalizeServer(String value) {
        String result = value == null ? "" : value.trim();
        while (result.endsWith("/")) result = result.substring(0, result.length() - 1);
        return result;
    }

    private static byte[] readAll(InputStream input) throws Exception {
        if (input == null) return new byte[0];
        try (InputStream stream = input; java.io.ByteArrayOutputStream output = new java.io.ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096];
            int read;
            while ((read = stream.read(buffer)) >= 0) output.write(buffer, 0, read);
            return output.toByteArray();
        }
    }

    @Override
    protected void onDetachedFromWindow() {
        executor.shutdownNow();
        super.onDetachedFromWindow();
    }
}
