package com.star.watch;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.media.MediaRecorder;
import android.os.Build;
import android.os.Bundle;
import android.provider.MediaStore;
import android.provider.Settings;
import android.speech.tts.TextToSpeech;
import android.util.DisplayMetrics;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class MainActivity extends Activity {
    private static final int REQUEST_AUDIO = 1001;
    private static final int REQUEST_CAMERA = 1002;
    private static final int REQUEST_CAPTURE_IMAGE = 2001;

    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final ScheduledExecutorService syncExecutor = Executors.newSingleThreadScheduledExecutor();

    private EditText serverInput;
    private EditText pairCodeInput;
    private EditText messageInput;
    private TextView statusText;
    private TextView responseText;
    private Button pairButton;
    private Button sendButton;
    private Button voiceButton;
    private Button cameraButton;

    private SharedPreferences preferences;
    private MediaRecorder recorder;
    private File audioFile;
    private boolean recording = false;
    private TextToSpeech tts;
    private volatile String runtimeRevision = "";
    private volatile boolean spokenRepliesEnabled = true;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        preferences = getSharedPreferences("star_watch", Context.MODE_PRIVATE);
        serverInput = findViewById(R.id.serverInput);
        pairCodeInput = findViewById(R.id.pairCodeInput);
        messageInput = findViewById(R.id.messageInput);
        statusText = findViewById(R.id.statusText);
        responseText = findViewById(R.id.responseText);
        pairButton = findViewById(R.id.pairButton);
        sendButton = findViewById(R.id.sendButton);
        voiceButton = findViewById(R.id.voiceButton);
        cameraButton = findViewById(R.id.cameraButton);

        serverInput.setText(preferences.getString("server", ""));
        updateStatus();

        pairButton.setOnClickListener(v -> pair());
        sendButton.setOnClickListener(v -> sendText());
        voiceButton.setOnClickListener(v -> toggleRecording());
        cameraButton.setOnClickListener(v -> openCamera());

        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(new Locale("pt", "BR"));
            }
        });

        if (!token().isEmpty() && !storedServer().isEmpty()) {
            executor.execute(this::refreshRuntimeSafe);
        }
        syncExecutor.scheduleAtFixedRate(this::syncOnce, 10, 30, TimeUnit.SECONDS);
    }

    private String deviceId() {
        String value = Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID);
        return value == null || value.trim().isEmpty() ? "star-watch" : "watch-" + value;
    }

    private String normalizeServer(String value) {
        String result = value == null ? "" : value.trim();
        while (result.endsWith("/")) {
            result = result.substring(0, result.length() - 1);
        }
        return result;
    }

    private String serverBase() {
        return normalizeServer(serverInput.getText().toString());
    }

    private String storedServer() {
        return normalizeServer(preferences.getString("server", ""));
    }

    private String token() {
        return preferences.getString("token", "");
    }

    private void updateStatus() {
        if (token().isEmpty()) {
            statusText.setText("● DESCONECTADO");
        } else {
            statusText.setText("● PAREADO");
        }
    }

    private void setBusy(String text) {
        statusText.setText(text);
    }

    private void showResponse(String text) {
        responseText.setText(text == null ? "" : text);
    }

    private void showError(Exception exception) {
        runOnUiThread(() -> {
            statusText.setText("● ERRO");
            responseText.setText(exception.getClass().getSimpleName() + ": " + exception.getMessage());
        });
    }

    private void pair() {
        String base = serverBase();
        String code = pairCodeInput.getText().toString().trim();
        if (!base.startsWith("http://") && !base.startsWith("https://")) {
            showResponse("Informe o endereço exibido pelo PC, incluindo http:// e a porta.");
            return;
        }
        if (code.length() != 6) {
            showResponse("Informe o código de pareamento de 6 dígitos exibido pelo PC.");
            return;
        }

        setBusy("● PAREANDO...");
        DisplayMetrics metrics = getResources().getDisplayMetrics();
        executor.execute(() -> {
            try {
                JSONObject body = new JSONObject();
                body.put("pairing_code", code);
                body.put("device_id", deviceId());
                body.put("name", "STAR Watch Android");

                JSONArray capabilities = new JSONArray();
                capabilities.put("microphone");
                capabilities.put("camera");
                capabilities.put("display");
                capabilities.put("speaker");
                body.put("capabilities", capabilities);

                JSONObject metadata = new JSONObject();
                metadata.put("platform", "android");
                metadata.put("form_factor", "watch");
                metadata.put("os_version", Build.VERSION.RELEASE);
                metadata.put("app_version", BuildConfig.VERSION_NAME);
                metadata.put("screen_width", metrics.widthPixels);
                metadata.put("screen_height", metrics.heightPixels);
                body.put("metadata", metadata);

                JSONObject response = postJson(base + "/v1/pair", body, false);
                String newToken = response.getString("token");
                preferences.edit()
                        .putString("server", base)
                        .putString("token", newToken)
                        .apply();

                JSONObject runtime = response.optJSONObject("runtime");
                if (runtime != null) {
                    applyRuntime(runtime);
                }

                runOnUiThread(() -> {
                    serverInput.setText(base);
                    statusText.setText("● ONLINE");
                    responseText.setText("STAR Watch pareado com o Core.");
                    pairCodeInput.setText("");
                });
            } catch (Exception exception) {
                showError(exception);
            }
        });
    }

    private void sendText() {
        String text = messageInput.getText().toString().trim();
        if (text.isEmpty()) {
            return;
        }
        if (token().isEmpty()) {
            showResponse("Pareie o relógio com a STAR primeiro.");
            return;
        }
        String base = serverBase();
        setBusy("● STAR PENSANDO NO PC...");
        executor.execute(() -> {
            try {
                JSONObject body = new JSONObject();
                body.put("text", text);
                JSONObject response = postJson(base + "/v1/text", body, true);
                String answer = response.optString("response", "Sem resposta.");
                runOnUiThread(() -> {
                    statusText.setText("● ONLINE");
                    responseText.setText(answer);
                    messageInput.setText("");
                    speak(answer);
                });
            } catch (Exception exception) {
                showError(exception);
            }
        });
    }

    private void toggleRecording() {
        if (recording) {
            stopRecordingAndUpload();
            return;
        }
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, REQUEST_AUDIO);
            return;
        }
        startRecording();
    }

    private void startRecording() {
        if (token().isEmpty()) {
            showResponse("Pareie o relógio com a STAR primeiro.");
            return;
        }
        try {
            audioFile = new File(getCacheDir(), "star_watch_audio.m4a");
            recorder = new MediaRecorder();
            recorder.setAudioSource(MediaRecorder.AudioSource.MIC);
            recorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
            recorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);
            recorder.setAudioEncodingBitRate(96000);
            recorder.setAudioSamplingRate(44100);
            recorder.setOutputFile(audioFile.getAbsolutePath());
            recorder.prepare();
            recorder.start();
            recording = true;
            voiceButton.setText("■ " + runtimeLabel("stop_and_send", "ENVIAR ÁUDIO"));
            statusText.setText("● OUVINDO...");
        } catch (Exception exception) {
            releaseRecorder();
            showResponse("Não consegui iniciar o microfone: " + exception.getMessage());
        }
    }

    private void stopRecordingAndUpload() {
        try {
            recorder.stop();
        } catch (Exception exception) {
            releaseRecorder();
            recording = false;
            voiceButton.setText("🎙 " + runtimeLabel("speak", "FALAR"));
            showResponse("A gravação ficou curta demais. Tente novamente.");
            return;
        }
        releaseRecorder();
        recording = false;
        voiceButton.setText("🎙 " + runtimeLabel("speak", "FALAR"));
        statusText.setText("● TRANSCRIBINDO NO PC...");
        String base = serverBase();

        executor.execute(() -> {
            try {
                byte[] data = readFile(audioFile);
                JSONObject response = postBytes(base + "/v1/audio", data, "audio/mp4");
                String transcript = response.optString("transcript", "");
                String answer = response.optString("response", "Sem resposta.");
                runOnUiThread(() -> {
                    statusText.setText("● ONLINE");
                    responseText.setText("Você: " + transcript + "\n\nSTAR: " + answer);
                    speak(answer);
                });
            } catch (Exception exception) {
                showError(exception);
            }
        });
    }

    private void releaseRecorder() {
        if (recorder != null) {
            try {
                recorder.release();
            } catch (Exception ignored) {
            }
            recorder = null;
        }
    }

    private void openCamera() {
        if (token().isEmpty()) {
            showResponse("Pareie o relógio com a STAR primeiro.");
            return;
        }
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.CAMERA}, REQUEST_CAMERA);
            return;
        }
        Intent intent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
        if (intent.resolveActivity(getPackageManager()) == null) {
            showResponse("Nenhum aplicativo de câmera disponível neste relógio.");
            return;
        }
        startActivityForResult(intent, REQUEST_CAPTURE_IMAGE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQUEST_CAPTURE_IMAGE || resultCode != RESULT_OK || data == null) {
            return;
        }
        Object raw = data.getExtras() == null ? null : data.getExtras().get("data");
        if (!(raw instanceof Bitmap)) {
            showResponse("A câmera não retornou uma imagem compatível.");
            return;
        }
        Bitmap bitmap = (Bitmap) raw;
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        bitmap.compress(Bitmap.CompressFormat.JPEG, 90, output);
        byte[] image = output.toByteArray();
        statusText.setText("● ENVIANDO IMAGEM...");
        String base = serverBase();

        executor.execute(() -> {
            try {
                JSONObject response = postBytes(base + "/v1/image", image, "image/jpeg");
                String message = response.optString("message", "Imagem recebida.");
                runOnUiThread(() -> {
                    statusText.setText("● ONLINE");
                    responseText.setText(message);
                });
            } catch (Exception exception) {
                showError(exception);
            }
        });
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        boolean granted = grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED;
        if (!granted) {
            showResponse("Permissão negada.");
            return;
        }
        if (requestCode == REQUEST_AUDIO) {
            startRecording();
        } else if (requestCode == REQUEST_CAMERA) {
            openCamera();
        }
    }

    private String runtimeLabel(String key, String fallback) {
        Object value = pairButton.getTag(R.id.pairButton);
        if (value instanceof JSONObject) {
            return ((JSONObject) value).optString(key, fallback);
        }
        return fallback;
    }

    private void applyRuntime(JSONObject runtime) {
        runtimeRevision = runtime.optString("revision", runtimeRevision);
        JSONObject labels = runtime.optJSONObject("labels");
        JSONObject features = runtime.optJSONObject("features");
        if (labels == null) {
            labels = new JSONObject();
        }
        if (features == null) {
            features = new JSONObject();
        }
        final JSONObject finalLabels = labels;
        final JSONObject finalFeatures = features;
        spokenRepliesEnabled = finalFeatures.optBoolean("spoken_reply", true);

        runOnUiThread(() -> {
            pairButton.setTag(R.id.pairButton, finalLabels);
            pairButton.setText(finalLabels.optString("pair", "PAREAR"));
            sendButton.setText("💬 " + finalLabels.optString("send", "ENVIAR"));
            voiceButton.setText(recording
                    ? "■ " + finalLabels.optString("stop_and_send", "ENVIAR ÁUDIO")
                    : "🎙 " + finalLabels.optString("speak", "FALAR"));
            cameraButton.setText("📷 " + finalLabels.optString("camera", "MOSTRAR À STAR"));
            sendButton.setVisibility(finalFeatures.optBoolean("text", true) ? View.VISIBLE : View.GONE);
            voiceButton.setVisibility(finalFeatures.optBoolean("voice_input", true) ? View.VISIBLE : View.GONE);
            cameraButton.setVisibility(finalFeatures.optBoolean("camera_transport", true) ? View.VISIBLE : View.GONE);
        });
    }

    private void refreshRuntimeSafe() {
        try {
            String base = storedServer();
            if (base.isEmpty() || token().isEmpty()) {
                return;
            }
            applyRuntime(getJson(base + "/v1/runtime"));
        } catch (Exception ignored) {
        }
    }

    private void syncOnce() {
        String base = storedServer();
        if (base.isEmpty() || token().isEmpty()) {
            return;
        }
        try {
            JSONObject heartbeat = postJson(base + "/v1/heartbeat", new JSONObject(), true);
            if (heartbeat.optBoolean("runtime_changed", false)) {
                applyRuntime(getJson(base + "/v1/runtime"));
            } else {
                runOnUiThread(() -> statusText.setText("● ONLINE"));
            }
        } catch (Exception exception) {
            runOnUiThread(() -> statusText.setText("● SEM CONEXÃO"));
        }
    }

    private void speak(String text) {
        if (!spokenRepliesEnabled || text == null || text.trim().isEmpty() || tts == null) {
            return;
        }
        tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "star-reply");
    }

    private JSONObject postJson(String url, JSONObject body, boolean authenticated) throws Exception {
        byte[] bytes = body.toString().getBytes(StandardCharsets.UTF_8);
        return request(url, "POST", bytes, "application/json; charset=utf-8", authenticated);
    }

    private JSONObject postBytes(String url, byte[] body, String contentType) throws Exception {
        return request(url, "POST", body, contentType, true);
    }

    private JSONObject getJson(String url) throws Exception {
        return request(url, "GET", null, null, true);
    }

    private JSONObject request(
            String endpoint,
            String method,
            byte[] body,
            String contentType,
            boolean authenticated
    ) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(endpoint).openConnection();
        connection.setRequestMethod(method);
        connection.setConnectTimeout(10000);
        connection.setReadTimeout(120000);
        connection.setRequestProperty("Accept", "application/json");
        if (contentType != null) {
            connection.setRequestProperty("Content-Type", contentType);
        }
        if (authenticated) {
            connection.setRequestProperty("Authorization", "Bearer " + token());
            connection.setRequestProperty("X-STAR-Device", deviceId());
            if (!runtimeRevision.isEmpty()) {
                connection.setRequestProperty("X-STAR-Runtime", runtimeRevision);
            }
        }
        if (body != null) {
            connection.setDoOutput(true);
            try (OutputStream output = connection.getOutputStream()) {
                output.write(body);
            }
        }

        int status = connection.getResponseCode();
        InputStream input = status >= 200 && status < 300
                ? connection.getInputStream()
                : connection.getErrorStream();
        String text = readStream(input);
        connection.disconnect();

        JSONObject result = text.isEmpty() ? new JSONObject() : new JSONObject(text);
        if (status < 200 || status >= 300) {
            throw new IllegalStateException(
                    result.optString("detail", result.optString("error", "HTTP " + status))
            );
        }
        return result;
    }

    private static byte[] readFile(File file) throws Exception {
        try (FileInputStream input = new FileInputStream(file);
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = input.read(buffer)) != -1) {
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }

    private static String readStream(InputStream input) throws Exception {
        if (input == null) {
            return "";
        }
        try (InputStream source = input;
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = source.read(buffer)) != -1) {
                output.write(buffer, 0, count);
            }
            return new String(output.toByteArray(), StandardCharsets.UTF_8);
        }
    }

    @Override
    protected void onDestroy() {
        releaseRecorder();
        executor.shutdownNow();
        syncExecutor.shutdownNow();
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }
        super.onDestroy();
    }
}
