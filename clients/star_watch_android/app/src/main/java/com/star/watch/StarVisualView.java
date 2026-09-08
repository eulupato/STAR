package com.star.watch;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Shader;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;

import org.json.JSONObject;

/**
 * Lightweight visual core for STAR Watch.
 *
 * It renders the rounded-square living frame and the original STAR symbol:
 * circle + inverted triangle, with a short star reveal animation. It is visual
 * only; cognition and device permissions remain in the PC/Core and Activity.
 */
public class StarVisualView extends View {
    private static final long LOGO_ANIMATION_MS = 720L;

    private final Paint glowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint framePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint symbolPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint auraPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF frameRect = new RectF();
    private final Matrix shaderMatrix = new Matrix();

    private int background = Color.parseColor("#05070D");
    private int cyan = Color.parseColor("#6FE7FF");
    private int blue = Color.parseColor("#4F7BFF");
    private int violet = Color.parseColor("#9B72FF");
    private int pink = Color.parseColor("#FF79C8");
    private int gold = Color.parseColor("#F6D35F");
    private int danger = Color.parseColor("#FF6B8A");

    private String state = "idle";
    private long startedAt = System.currentTimeMillis();
    private long logoAnimationStarted = 0L;

    public StarVisualView(Context context) {
        super(context);
        init();
    }

    public StarVisualView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    public StarVisualView(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }

    private void init() {
        setWillNotDraw(false);
        setClickable(true);

        glowPaint.setStyle(Paint.Style.STROKE);
        glowPaint.setStrokeWidth(dp(9));
        glowPaint.setStrokeCap(Paint.Cap.ROUND);

        framePaint.setStyle(Paint.Style.STROKE);
        framePaint.setStrokeWidth(dp(3));
        framePaint.setStrokeCap(Paint.Cap.ROUND);

        symbolPaint.setStyle(Paint.Style.STROKE);
        symbolPaint.setStrokeWidth(dp(2.4f));
        symbolPaint.setStrokeJoin(Paint.Join.ROUND);
        symbolPaint.setStrokeCap(Paint.Cap.ROUND);

        auraPaint.setStyle(Paint.Style.STROKE);
        auraPaint.setStrokeWidth(dp(7));
    }

    public void setState(String value) {
        state = value == null ? "idle" : value.trim().toLowerCase();
        invalidate();
    }

    public void triggerLogoAnimation() {
        logoAnimationStarted = System.currentTimeMillis();
        invalidate();
    }

    public void applyTheme(JSONObject theme) {
        if (theme == null) {
            return;
        }
        background = color(theme, "background", background);
        cyan = color(theme, "energy_cyan", color(theme, "primary", cyan));
        blue = color(theme, "energy_blue", blue);
        violet = color(theme, "energy_violet", color(theme, "secondary", violet));
        pink = color(theme, "energy_pink", color(theme, "accent", pink));
        gold = color(theme, "gold", gold);
        danger = color(theme, "danger", danger);
        invalidate();
    }

    private static int color(JSONObject source, String key, int fallback) {
        String value = source.optString(key, "");
        if (value == null || value.trim().isEmpty()) {
            return fallback;
        }
        try {
            return Color.parseColor(value);
        } catch (IllegalArgumentException ignored) {
            return fallback;
        }
    }

    private float dp(float value) {
        return value * getResources().getDisplayMetrics().density;
    }

    private int[] colorsForState() {
        switch (state) {
            case "listening":
                return new int[]{cyan, blue, cyan, violet};
            case "thinking":
                return new int[]{violet, pink, blue, violet};
            case "speaking":
                return new int[]{cyan, blue, violet, pink};
            case "error":
                return new int[]{danger, pink, gold, danger};
            default:
                return new int[]{
                        withAlpha(blue, 120),
                        withAlpha(violet, 110),
                        withAlpha(pink, 85),
                        withAlpha(cyan, 95)
                };
        }
    }

    private static int withAlpha(int color, int alpha) {
        return Color.argb(
                Math.max(0, Math.min(255, alpha)),
                Color.red(color),
                Color.green(color),
                Color.blue(color)
        );
    }

    private float speedForState() {
        switch (state) {
            case "listening":
                return 1.5f;
            case "thinking":
                return 2.2f;
            case "speaking":
                return 1.8f;
            case "error":
                return 0.7f;
            default:
                return 0.45f;
        }
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        int width = getWidth();
        int height = getHeight();
        if (width <= 0 || height <= 0) {
            return;
        }

        long now = System.currentTimeMillis();
        float elapsed = (now - startedAt) / 1000f;
        float phase = elapsed * speedForState();
        float margin = dp(7);
        float radius = dp(28);

        frameRect.set(margin, margin, width - margin, height - margin);

        int[] colors = colorsForState();
        LinearGradient gradient = new LinearGradient(
                -width * 0.20f,
                0,
                width * 1.20f,
                height,
                colors,
                new float[]{0f, 0.34f, 0.67f, 1f},
                Shader.TileMode.CLAMP
        );
        shaderMatrix.reset();
        shaderMatrix.setTranslate(
                (float) Math.sin(phase) * width * 0.12f,
                (float) Math.cos(phase * 0.7f) * height * 0.03f
        );
        gradient.setLocalMatrix(shaderMatrix);

        glowPaint.setShader(gradient);
        glowPaint.setAlpha(state.equals("idle") ? 68 : 105);
        framePaint.setShader(gradient);
        framePaint.setAlpha(235);

        canvas.drawRoundRect(frameRect, radius, radius, glowPaint);
        canvas.drawRoundRect(frameRect, radius, radius, framePaint);

        float cx = width / 2f;
        float cy = Math.min(height * 0.37f, dp(104));
        float symbolRadius = Math.min(width, height) * 0.115f;
        drawSymbol(canvas, cx, cy, symbolRadius, now);

        postInvalidateDelayed(33L);
    }

    private void drawSymbol(Canvas canvas, float cx, float cy, float radius, long now) {
        float breath = (float) ((Math.sin((now - startedAt) / 700.0) + 1.0) * 0.5);
        auraPaint.setColor(withAlpha(violet, 30 + (int) (breath * 30)));
        auraPaint.setShader(null);
        canvas.drawCircle(cx, cy, radius + dp(10) + breath * dp(2), auraPaint);

        symbolPaint.setShader(null);
        symbolPaint.setColor(cyan);
        symbolPaint.setAlpha(255);
        canvas.drawCircle(cx, cy, radius, symbolPaint);

        float morph = 0f;
        if (logoAnimationStarted > 0L) {
            long delta = now - logoAnimationStarted;
            if (delta >= LOGO_ANIMATION_MS) {
                logoAnimationStarted = 0L;
            } else {
                morph = (float) Math.sin(Math.PI * (delta / (double) LOGO_ANIMATION_MS));
            }
        }

        Path triangle = new Path();
        triangle.moveTo(cx - radius * 0.48f, cy - radius * 0.34f);
        triangle.lineTo(cx + radius * 0.48f, cy - radius * 0.34f);
        triangle.lineTo(cx, cy + radius * 0.52f);
        triangle.close();

        symbolPaint.setColor(cyan);
        symbolPaint.setAlpha(Math.max(12, (int) (255 * (1f - morph))));
        canvas.drawPath(triangle, symbolPaint);

        Path star = starPath(cx, cy, radius * 0.52f, radius * 0.22f);
        symbolPaint.setColor(pink);
        symbolPaint.setAlpha((int) (255 * morph));
        if (morph > 0.01f) {
            canvas.drawPath(star, symbolPaint);
        }

        symbolPaint.setAlpha(255);
    }

    private static Path starPath(float cx, float cy, float outer, float inner) {
        Path path = new Path();
        for (int i = 0; i < 10; i++) {
            double angle = -Math.PI / 2 + i * Math.PI / 5;
            float radius = i % 2 == 0 ? outer : inner;
            float x = cx + (float) Math.cos(angle) * radius;
            float y = cy + (float) Math.sin(angle) * radius;
            if (i == 0) {
                path.moveTo(x, y);
            } else {
                path.lineTo(x, y);
            }
        }
        path.close();
        return path;
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (event.getAction() == MotionEvent.ACTION_UP) {
            performClick();
            return true;
        }
        return true;
    }

    @Override
    public boolean performClick() {
        super.performClick();
        triggerLogoAnimation();
        return true;
    }
}
