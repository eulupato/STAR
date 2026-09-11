package com.star.watch;

import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;

final class WatchAudioRecorder {
    private static final int CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO;
    private static final int AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT;
    private static final int[] SAMPLE_RATES = new int[]{16000, 22050, 44100};

    private final AudioRecord audioRecord;
    private final int sampleRate;
    private final int bufferSize;
    private final File pcmFile;
    private final File wavFile;

    private volatile boolean recording;
    private volatile Exception captureError;
    private Thread captureThread;

    private WatchAudioRecorder(AudioRecord audioRecord, int sampleRate, int bufferSize, File cacheDir) {
        this.audioRecord = audioRecord;
        this.sampleRate = sampleRate;
        this.bufferSize = bufferSize;
        this.pcmFile = new File(cacheDir, "star_watch_audio.pcm");
        this.wavFile = new File(cacheDir, "star_watch_audio.wav");
    }

    static WatchAudioRecorder create(File cacheDir) throws IOException {
        int[] sources = new int[]{MediaRecorder.AudioSource.VOICE_RECOGNITION, MediaRecorder.AudioSource.MIC};
        for (int source : sources) {
            for (int rate : SAMPLE_RATES) {
                int minimum = AudioRecord.getMinBufferSize(rate, CHANNEL_CONFIG, AUDIO_FORMAT);
                if (minimum <= 0) continue;
                int buffer = Math.max(minimum * 2, 4096);
                AudioRecord candidate = null;
                try {
                    candidate = new AudioRecord(source, rate, CHANNEL_CONFIG, AUDIO_FORMAT, buffer);
                    if (candidate.getState() == AudioRecord.STATE_INITIALIZED) {
                        return new WatchAudioRecorder(candidate, rate, buffer, cacheDir);
                    }
                } catch (Exception ignored) {
                    // Tenta a próxima combinação de fonte/sample rate.
                }
                if (candidate != null) candidate.release();
            }
        }
        throw new IOException("Nenhuma configuração PCM de microfone foi aceita pelo relógio.");
    }

    void start() throws IOException {
        if (recording) return;
        captureError = null;
        if (pcmFile.exists() && !pcmFile.delete()) throw new IOException("Não consegui limpar a gravação PCM anterior.");
        if (wavFile.exists() && !wavFile.delete()) throw new IOException("Não consegui limpar a gravação WAV anterior.");

        audioRecord.startRecording();
        if (audioRecord.getRecordingState() != AudioRecord.RECORDSTATE_RECORDING) {
            audioRecord.release();
            throw new IOException("O microfone não entrou em estado de gravação.");
        }

        recording = true;
        captureThread = new Thread(this::captureLoop, "STAR-Watch-Audio");
        captureThread.start();
    }

    private void captureLoop() {
        byte[] buffer = new byte[bufferSize];
        try (FileOutputStream output = new FileOutputStream(pcmFile)) {
            while (recording) {
                int count = audioRecord.read(buffer, 0, buffer.length);
                if (count > 0) {
                    output.write(buffer, 0, count);
                } else if (!recording) {
                    break;
                } else if (count == AudioRecord.ERROR_INVALID_OPERATION
                        || count == AudioRecord.ERROR_BAD_VALUE
                        || count == AudioRecord.ERROR_DEAD_OBJECT) {
                    throw new IOException("Falha de captura do microfone: " + count);
                }
            }
            output.flush();
        } catch (Exception exception) {
            captureError = exception;
        }
    }

    File stopAndGetFile() throws Exception {
        if (!recording) throw new IllegalStateException("A gravação não está ativa.");
        recording = false;
        try {
            audioRecord.stop();
        } catch (IllegalStateException ignored) {
        }

        Thread thread = captureThread;
        if (thread != null) thread.join(1500);
        audioRecord.release();

        if (captureError != null) throw captureError;
        if (!pcmFile.exists() || pcmFile.length() < sampleRate / 2L) {
            throw new IOException("A gravação ficou curta demais. Fale por um pouco mais de tempo.");
        }

        writeWav(pcmFile, wavFile, sampleRate, 1, 16);
        if (!pcmFile.delete()) pcmFile.deleteOnExit();
        return wavFile;
    }

    void cancel() {
        recording = false;
        try {
            if (audioRecord.getRecordingState() == AudioRecord.RECORDSTATE_RECORDING) audioRecord.stop();
        } catch (Exception ignored) {
        }
        try {
            audioRecord.release();
        } catch (Exception ignored) {
        }
    }

    int getSampleRate() { return sampleRate; }

    private static void writeWav(File pcm, File wav, int sampleRate, int channels, int bitsPerSample) throws IOException {
        long pcmSize = pcm.length();
        long dataSize = pcmSize + 36;
        long byteRate = (long) sampleRate * channels * bitsPerSample / 8;

        try (FileOutputStream output = new FileOutputStream(wav); FileInputStream input = new FileInputStream(pcm)) {
            output.write(new byte[]{'R', 'I', 'F', 'F'});
            writeLittleEndian(output, dataSize, 4);
            output.write(new byte[]{'W', 'A', 'V', 'E'});
            output.write(new byte[]{'f', 'm', 't', ' '});
            writeLittleEndian(output, 16, 4);
            writeLittleEndian(output, 1, 2);
            writeLittleEndian(output, channels, 2);
            writeLittleEndian(output, sampleRate, 4);
            writeLittleEndian(output, byteRate, 4);
            writeLittleEndian(output, channels * bitsPerSample / 8, 2);
            writeLittleEndian(output, bitsPerSample, 2);
            output.write(new byte[]{'d', 'a', 't', 'a'});
            writeLittleEndian(output, pcmSize, 4);
            byte[] buffer = new byte[8192];
            int count;
            while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
        }
    }

    private static void writeLittleEndian(FileOutputStream output, long value, int byteCount) throws IOException {
        for (int index = 0; index < byteCount; index++) output.write((int) (value >> (8 * index)) & 0xff);
    }
}
