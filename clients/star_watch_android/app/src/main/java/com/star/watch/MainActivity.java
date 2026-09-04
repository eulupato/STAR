package com.star.watch;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.media.MediaRecorder;
import android.os.Bundle;
import android.provider.MediaStore;
import android.provider.Settings;
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
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private static final int REQUEST_AUDIO = 1001;
    private static final int REQUEST_CAMERA = 1002;
    private static final int REQUEST_CAPTURE_IMAGE = 2001;

    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    private EditText serverInput;
    private EditText pairCodeInput;
    private EditText messageInput;
    private TextView statusText;
    private TextView responseText;
    private Button voiceButton;

    private SharedPreferences preferences;
    private MediaRecorder recorder;
    private File audioFile;
    private boolean recording = false;

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
        voiceButton = findViewById(R.id.voiceButton);

        serverInput.setText(preferences.getString("server", ""));
        updateStatus();

        findViewById(R.id.pairButton).setOnClickListener(v -> pair());
        findViewById(R.id.sendButton).setOnClickListener(v -> sendText());
        voiceButton.setOnClickListener(v -> toggleRecording());
        findViewById(R.id.cameraButton).setOnClickListener(v -> openCamera());
    }

    private String deviceId() {
        String value = Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID);
        return value == null || value.trim().isEmpty() ? "star-watch" : "watch-" + value;
    }

    private String serverBase() {
        String value = serverInput.getText().toString().trim();
        while (value.endsWith("/")) {
            value = value.substring(0, value.length() - 1);
        }
        return value;
    }

    private String token() {
        return preferences.getString("token", "");
    }

    private void updateStatus() {
        String token = token();
        if (token.isEmpty()) {
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

                JSONObject response = postJson(base + "/v1/pair", body, false);
                String newToken = response.getString("token");
                preferences.edit()
                        .putString("server", base)
                        .putString("token", newToken)
                        .apply();
                runOnUiThread(() -> {
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

        setBusy("● STAR PENSANDO NO PC...");
        executor.execute(() -> {
            try {
                JSONObject body = new JSONObject();
                body.put("text", text);
                JSONObject response = postJson(serverBase() + "/v1/text", body, true);
                String answer = response.optString("response", "Sem resposta.");
                runOnUiThread(() -> {
                    statusText.setText("● ONLINE");
                    responseText.setText(answer);
                    messageInput.setText("");
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
            voiceButton.setText("■ ENVIAR ÁUDIO");
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
            voiceButton.setText("🎙 FALAR");
            showResponse("A gravação ficou curta demais. Tente novamente.");
            return;
        }
        releaseRecorder();
        recording = false;
        voiceButton.setText("🎙 FALAR");
        statusText.setText("● TRANSCRIBINDO NO PC...");

        executor.execute(() -> {
            try {
                byte[] data = readFile(audioFile);
                JSONObject response = postBytes(
                        serverBase() + "/v1/audio",
                        data,
                        "audio/mp4"
                );
                String transcript = response.optString("transcript", "");
                String answer = response.optString("response", "Sem resposta.");
                runOnUiThread(() -> {
                    statusText.setText("● ONLINE");
                    responseText.setText("Você: " + transcript + "\n\nSTAR: " + answer);
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

        executor.execute(() -> {
            try {
                JSONObject response = postBytes(
                        serverBase() + "/v1/image",
                        image,
                        "image/jpeg"
                );
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

    private JSONObject postJson(String url, JSONObject body, boolean authenticated) throws Exception {
        byte[] bytes = body.toString().getBytes(StandardCharsets.UTF_8);
        return request(url, bytes, "application/json; charset=utf-8", authenticated);
    }

    private JSONObject postBytes(String url, byte[] body, String contentType) throws Exception {
        return request(url, body, contentType, true);
    }

    private JSONObject request(String endpoint, byte[] body, String contentType, boolean authenticated) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(endpoint).openConnection();
        connection.setRequestMethod("POST");
        connection.setConnectTimeout(10000);
        connection.setReadTimeout(120000);
        connection.setDoOutput(true);
        connection.setRequestProperty("Content-Type", contentType);
        connection.setRequestProperty("Accept", "application/json");
        if (authenticated) {
            connection.setRequestProperty("Authorization", "Bearer " + token());
            connection.setRequestProperty("X-STAR-Device", deviceId());
        }

        try (OutputStream output = connection.getOutputStream()) {
            output.write(body);
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
        super.onDestroy();
    }
}
