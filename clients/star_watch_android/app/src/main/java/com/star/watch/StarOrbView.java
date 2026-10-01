package com.star.watch;

import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.util.AttributeSet;
import android.view.View;
import android.view.animation.LinearInterpolator;

import org.json.JSONObject;

import java.util.Arrays;

/**
 * "Cosmic Crystal" orb: N great circles projected in perspective, mirroring gui/visual3d.py.
 * Line width and alpha scale with depth z; segments are painted back-to-front.
 */
public class StarOrbView extends View {
    private static final int FILAMENTS = 7;
    private static final int SAMPLES = 48;
    private static final float FOV = 300f;
    private static final float CAMERA = 3.2f;

    private final Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint glowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint haloPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final float[] segs = new float[FILAMENTS * SAMPLES * 5]; // z, ax, ay, bx, by
    private final Integer[] order = new Integer[FILAMENTS * SAMPLES];

    private ValueAnimator animator;
    private float time = 0f;
    private long lastFrameNanos = 0L;

    private int bgColor = Color.parseColor("#05030D");
    private int coreColor = Color.parseColor("#57388F");
    private int primary = Color.parseColor("#7E58B3");
    private int secondary = Color.parseColor("#3A2467");
    private int glow = Color.parseColor("#C49EE0");
    private float speed = 0.35f, pulse = 0.03f, wobble = 0.04f;
    private String state = "neutral";

    public StarOrbView(Context context) { this(context, null); }

    public StarOrbView(Context context, AttributeSet attrs) {
        super(context, attrs);
        linePaint.setStyle(Paint.Style.STROKE);
        linePaint.setStrokeCap(Paint.Cap.ROUND);
        glowPaint.setStyle(Paint.Style.STROKE);
        glowPaint.setStrokeCap(Paint.Cap.ROUND);
        for (int i = 0; i < order.length; i++) order[i] = i;
    }

    /** Accepts neutral/idle, listening, thinking, speaking, error (same tokens as gui/theme.py). */
    public void setState(String newState) {
        String value = newState == null ? "neutral" : newState;
        if (value.equals(state)) return;
        state = value;
        switch (value) {
            case "listening": setPalette("#638CBF", "#555F9F", "#B5AFD3"); setMotion(0.55f, 0.06f, 0.07f); break;
            case "thinking": setPalette("#A192C6", "#7E58B3", "#C49EE0"); setMotion(0.95f, 0.04f, 0.10f); break;
            case "speaking": setPalette("#E6B8E0", "#A192C6", "#E6DCEA"); setMotion(0.70f, 0.09f, 0.08f); break;
            case "error": setPalette("#FF7C87", "#7E58B3", "#FFD36E"); setMotion(0.25f, 0.02f, 0.02f); break;
            default: setPalette("#7E58B3", "#3A2467", "#C49EE0"); setMotion(0.35f, 0.03f, 0.04f); break;
        }
        invalidate();
    }

    /** Applies runtime theme keys (background, primary, accent) when the state is neutral. */
    public void applyTheme(JSONObject theme) {
        if (theme == null) return;
        bgColor = parse(theme.optString("background", null), bgColor);
        if ("neutral".equals(state) || "idle".equals(state)) {
            primary = parse(theme.optString("primary", null), primary);
            secondary = parse(theme.optString("border", null), secondary);
            glow = parse(theme.optString("accent", null), glow);
        }
        invalidate();
    }

    private void setPalette(String p, String s, String g) {
        primary = Color.parseColor(p); secondary = Color.parseColor(s); glow = Color.parseColor(g);
    }

    private void setMotion(float sp, float pu, float wo) { speed = sp; pulse = pu; wobble = wo; }

    private static int parse(String hex, int fallback) {
        if (hex == null || hex.isEmpty()) return fallback;
        try { return Color.parseColor(hex); } catch (IllegalArgumentException ignored) { return fallback; }
    }

    @Override
    protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        if (animator == null) {
            animator = ValueAnimator.ofFloat(0f, 1f);
            animator.setDuration(1000L);
            animator.setRepeatCount(ValueAnimator.INFINITE);
            animator.setInterpolator(new LinearInterpolator());
            animator.addUpdateListener(a -> {
                long now = System.nanoTime();
                if (lastFrameNanos != 0L) time += Math.min(0.1f, (now - lastFrameNanos) / 1e9f);
                lastFrameNanos = now;
                invalidate();
            });
        }
        lastFrameNanos = 0L;
        animator.start();
    }

    @Override
    protected void onDetachedFromWindow() {
        if (animator != null) animator.cancel();
        super.onDetachedFromWindow();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float w = getWidth(), h = getHeight();
        if (w <= 0 || h <= 0) return;
        canvas.drawColor(bgColor);
        float cx = w / 2f, cy = h / 2f;
        float radius = Math.min(w, h) * 0.36f * (1f + pulse * (float) Math.sin(time * 2.4f));
        float scale = radius * CAMERA / FOV;

        haloPaint.setShader(new RadialGradient(cx, cy, radius * 1.45f,
                new int[]{withAlpha(glow, 0.22f), withAlpha(primary, 0.10f), withAlpha(bgColor, 0f)},
                new float[]{0.15f, 0.6f, 1f}, Shader.TileMode.CLAMP));
        canvas.drawCircle(cx, cy, radius * 1.45f, haloPaint);
        haloPaint.setShader(new RadialGradient(cx - radius * 0.15f, cy + radius * 0.1f, radius,
                new int[]{withAlpha(secondary, 0.45f), withAlpha(coreColor, 0.18f), withAlpha(bgColor, 0f)},
                null, Shader.TileMode.CLAMP));
        canvas.drawCircle(cx, cy, radius, haloPaint);

        float spin = time * speed;
        int n = 0;
        for (int i = 0; i < FILAMENTS; i++) {
            double tilt = 0.35 + i * (Math.PI / FILAMENTS) + wobble * Math.sin(time * 0.9 + i);
            double yaw = spin * (1 + 0.18 * i) + i * 0.9;
            double roll = 0.25 * Math.sin(spin * 0.6 + i * 1.7);
            double[] prev = null;
            for (int s = 0; s <= SAMPLES; s++) {
                double t = (double) s / SAMPLES * 2 * Math.PI;
                double[] p = rotate(Math.cos(t), Math.sin(t), 0, tilt, yaw, roll);
                if (prev != null) {
                    int k = n * 5;
                    segs[k] = (float) ((prev[2] + p[2]) / 2);
                    segs[k + 1] = projX(prev, cx, scale); segs[k + 2] = projY(prev, cy, scale);
                    segs[k + 3] = projX(p, cx, scale); segs[k + 4] = projY(p, cy, scale);
                    n++;
                }
                prev = p;
            }
        }
        Arrays.sort(order, 0, n, (a, b) -> Float.compare(segs[a * 5], segs[b * 5]));
        for (int j = 0; j < n; j++) {
            int k = order[j] * 5;
            float depth = (segs[k] + 1f) / 2f;
            float width = (0.6f + 2.2f * depth) * getResources().getDisplayMetrics().density;
            glowPaint.setStrokeWidth(width * 3f);
            glowPaint.setColor(withAlpha(primary, 0.10f + 0.18f * depth));
            canvas.drawLine(segs[k + 1], segs[k + 2], segs[k + 3], segs[k + 4], glowPaint);
            linePaint.setStrokeWidth(width);
            linePaint.setColor(withAlpha(mix(coreColor, glow, depth), 0.25f + 0.75f * depth));
            canvas.drawLine(segs[k + 1], segs[k + 2], segs[k + 3], segs[k + 4], linePaint);
        }
    }

    private static double[] rotate(double x, double y, double z, double ax, double ay, double az) {
        double y1 = y * Math.cos(ax) - z * Math.sin(ax), z1 = y * Math.sin(ax) + z * Math.cos(ax);
        double x2 = x * Math.cos(ay) + z1 * Math.sin(ay), z2 = -x * Math.sin(ay) + z1 * Math.cos(ay);
        double x3 = x2 * Math.cos(az) - y1 * Math.sin(az), y3 = x2 * Math.sin(az) + y1 * Math.cos(az);
        return new double[]{x3, y3, z2};
    }

    private static float projX(double[] p, float cx, float scale) { return cx + (float) (p[0] * FOV / (CAMERA - p[2])) * scale; }
    private static float projY(double[] p, float cy, float scale) { return cy - (float) (p[1] * FOV / (CAMERA - p[2])) * scale; }

    private static int withAlpha(int color, float alpha) {
        int a = Math.max(0, Math.min(255, Math.round(alpha * 255)));
        return Color.argb(a, Color.red(color), Color.green(color), Color.blue(color));
    }

    private static int mix(int a, int b, float t) {
        float k = Math.max(0f, Math.min(1f, t));
        return Color.rgb(
                Math.round(Color.red(a) + (Color.red(b) - Color.red(a)) * k),
                Math.round(Color.green(a) + (Color.green(b) - Color.green(a)) * k),
                Math.round(Color.blue(a) + (Color.blue(b) - Color.blue(a)) * k));
    }
}
