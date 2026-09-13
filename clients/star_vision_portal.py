"""STAR Vision Portal — AR gestual local, fluido e offline após setup.

A implementação usa a API atual MediaPipe Tasks/HandLandmarker. OpenCV e
MediaPipe são opcionais: só entram quando este cliente é executado.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import math
import time

from modules.vision import (
    AdaptivePointSmoother,
    GeometryGate,
    GestureHysteresis,
    PerformanceGovernor,
    PORTAL_FILTERS,
)
from modules.vision_model import ensure_hand_model

ROOT = Path(__file__).resolve().parents[1]
CAPTURE_DIR = ROOT / "runtime" / "vision" / "captures"
INDEX_TIP = 8
THUMB_TIP = 4


def _imports():
    try:
        import cv2
        import mediapipe as mp
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "Dependências de visão ausentes. Execute: pip install -r requirements-vision.txt"
        ) from exc
    if not hasattr(mp, "tasks"):
        raise RuntimeError("MediaPipe instalado sem a API Tasks necessária ao STAR Vision.")
    return cv2, mp, np


@dataclass
class PortalState:
    filter_index: int = 0
    hud: bool = True
    fullscreen: bool = False
    captures: int = 0

    @property
    def filter_meta(self) -> dict:
        return PORTAL_FILTERS[self.filter_index % len(PORTAL_FILTERS)]

    def cycle(self, step: int = 1) -> None:
        self.filter_index = (self.filter_index + int(step)) % len(PORTAL_FILTERS)


class FilterEngine:
    """Banco de efeitos vetorizados aplicados somente no interior do portal."""

    def __init__(self, cv2, np):
        self.cv2, self.np = cv2, np

    def apply(self, key: str, roi, tick: float):
        fn = getattr(self, f"_fx_{key}", None)
        return roi.copy() if fn is None else fn(roi, tick)

    def _gray(self, roi):
        return self.cv2.cvtColor(roi, self.cv2.COLOR_BGR2GRAY)

    def _fx_hologram(self, roi, tick):
        cv2, np = self.cv2, self.np
        gray = self._gray(roi)
        base = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR).astype(np.float32)
        base[:, :, 0] = np.clip(base[:, :, 0] * 1.35 + 25, 0, 255)
        base[:, :, 1] = np.clip(base[:, :, 1] * 1.14 + 20, 0, 255)
        base[:, :, 2] = np.clip(base[:, :, 2] * 0.34, 0, 255)
        phase = int(tick * 45) % 6
        base[phase::6] *= 0.52
        edges = cv2.Canny(gray, 55, 130)
        glow = cv2.GaussianBlur(edges, (0, 0), 4)
        return cv2.addWeighted(
            base.astype(np.uint8), 0.84,
            cv2.cvtColor(glow, cv2.COLOR_GRAY2BGR), 0.55, 0,
        )

    def _fx_neon(self, roi, tick):
        np = self.np
        gray = self._gray(roi).astype(np.float32)
        out = np.zeros_like(roi)
        out[:, :, 0] = np.clip(50 + gray * 0.95, 0, 255)
        out[:, :, 1] = np.clip(10 + gray * 0.45, 0, 255)
        out[:, :, 2] = np.clip(75 + (255 - gray) * 0.62, 0, 255)
        return out.astype(np.uint8)

    def _halftone(self, roi, fg, bg, cell):
        np = self.np
        gray = self._gray(roi)
        h, w = gray.shape
        yy, xx = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
        dx = (xx % cell) - cell / 2.0
        dy = (yy % cell) - cell / 2.0
        radius = (1.0 - gray.astype(np.float32) / 255.0) * (cell / 1.30)
        mask = np.sqrt(dx * dx + dy * dy) < radius
        out = np.empty_like(roi)
        out[:] = bg
        out[mask] = fg
        return out

    def _fx_halftone(self, roi, tick):
        return self._halftone(roi, (12, 12, 12), (244, 244, 244), 6)

    def _fx_magenta(self, roi, tick):
        return self._halftone(roi, (78, 18, 140), (220, 186, 248), 5)

    def _fx_chromatic(self, roi, tick):
        cv2, np = self.cv2, self.np
        shift = max(3, min(12, roi.shape[1] // 80))
        b, g, r = cv2.split(roi)
        out = cv2.merge([np.roll(b, shift, 1), g, np.roll(r, -shift, 1)])
        out[::3] = (out[::3] * 0.68).astype(np.uint8)
        return out

    def _fx_thermal(self, roi, tick):
        gray = self.cv2.equalizeHist(self._gray(roi))
        return self.cv2.applyColorMap(gray, self.cv2.COLORMAP_TURBO)

    def _fx_vintage(self, roi, tick):
        cv2, np = self.cv2, self.np
        kernel = np.array(
            [[0.272, 0.534, 0.131], [0.349, 0.686, 0.168], [0.393, 0.769, 0.189]],
            dtype=np.float32,
        )
        sepia = np.clip(cv2.transform(roi, kernel), 0, 255).astype(np.uint8)
        h, w = roi.shape[:2]
        yy, xx = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
        dist = np.sqrt((xx - w / 2.0) ** 2 + (yy - h / 2.0) ** 2)
        vignette = np.clip(1.0 - 0.48 * dist / max(1.0, math.hypot(w / 2, h / 2)), 0, 1)
        noise = np.random.default_rng(int(tick * 12)).normal(0, 5, roi.shape)
        return np.clip(sepia * vignette[..., None] + noise, 0, 255).astype(np.uint8)

    def _fx_frosted(self, roi, tick):
        cv2, np = self.cv2, self.np
        kernel = max(9, (min(roi.shape[:2]) // 18) | 1)
        blur = cv2.GaussianBlur(roi, (kernel, kernel), 0)
        veil = np.full_like(roi, 245)
        return cv2.addWeighted(blur, 0.66, veil, 0.34, 0)

    def _fx_edges(self, roi, tick):
        cv2, np = self.cv2, self.np
        gray = self._gray(roi)
        edges = cv2.Canny(gray, 45, 115)
        glow = cv2.GaussianBlur(edges, (0, 0), 2.8)
        out = np.zeros_like(roi)
        out[:, :, 0] = np.clip(glow * 1.35, 0, 255)
        out[:, :, 1] = np.clip(edges * 0.95, 0, 255)
        out[:, :, 2] = np.clip(glow * 0.68, 0, 255)
        return out.astype(np.uint8)

    def _fx_night(self, roi, tick):
        np = self.np
        gray = self.cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(self._gray(roi))
        out = np.zeros_like(roi)
        out[:, :, 1] = np.clip(gray.astype(np.float32) * 1.25 + 12, 0, 255)
        out[:, :, 0] = np.clip(gray.astype(np.float32) * 0.28, 0, 255)
        return out.astype(np.uint8)

    def _fx_xray(self, roi, tick):
        cv2, np = self.cv2, self.np
        inv = 255 - self._gray(roi)
        edges = cv2.Canny(inv, 40, 100)
        out = cv2.applyColorMap(inv, cv2.COLORMAP_BONE).astype(np.float32)
        out[:, :, 0] = np.clip(out[:, :, 0] + edges * 0.30, 0, 255)
        return out.astype(np.uint8)

    def _fx_cyber(self, roi, tick):
        cv2, np = self.cv2, self.np
        gray = self._gray(roi)
        levels = (gray // 42) * 42
        out = np.zeros_like(roi)
        out[:, :, 0] = np.clip(levels.astype(np.float32) * 1.15 + 28, 0, 255)
        out[:, :, 1] = np.clip((255 - levels).astype(np.float32) * 0.30 + 28, 0, 255)
        out[:, :, 2] = np.clip(levels.astype(np.float32) * 0.74 + 65, 0, 255)
        edges = cv2.Canny(gray, 65, 150)
        out[edges > 0] = (255, 230, 255)
        return out.astype(np.uint8)


class PortalRenderer:
    def __init__(self, cv2, np, filters: FilterEngine):
        self.cv2, self.np, self.filters = cv2, np, filters

    def draw(self, frame, points, filter_key: str, tick: float):
        cv2, np = self.cv2, self.np
        # points: left-index, left-thumb, right-index, right-thumb
        polygon = np.asarray([points[0], points[2], points[3], points[1]], dtype=np.int32)
        h, w = frame.shape[:2]
        x, y, bw, bh = cv2.boundingRect(polygon)
        x, y = max(0, x), max(0, y)
        bw, bh = min(bw, w - x), min(bh, h - y)
        if bw < 4 or bh < 4:
            return frame
        roi = frame[y:y + bh, x:x + bw]
        local = polygon - np.array([x, y], dtype=np.int32)
        mask = np.zeros((bh, bw), dtype=np.uint8)
        cv2.fillConvexPoly(mask, local, 255)
        feather = max(3, min(17, int(min(bw, bh) * 0.035)) | 1)
        soft = cv2.GaussianBlur(mask, (feather, feather), 0).astype(np.float32) / 255.0
        filtered = self.filters.apply(filter_key, roi, tick)
        mixed = filtered.astype(np.float32) * soft[..., None] + roi.astype(np.float32) * (1 - soft[..., None])
        frame[y:y + bh, x:x + bw] = np.clip(mixed, 0, 255).astype(np.uint8)

        pulse = 0.5 + 0.5 * math.sin(tick * 4.2)
        primary = (255, int(232 - 35 * pulse), 114)
        secondary = (255, 118, int(162 + 80 * pulse))
        overlay = frame.copy()
        cv2.polylines(overlay, [polygon], True, secondary, 9, cv2.LINE_AA)
        frame[:] = cv2.addWeighted(overlay, 0.18, frame, 0.82, 0)
        cv2.polylines(frame, [polygon], True, primary, 2, cv2.LINE_AA)
        for px, py in polygon:
            cv2.circle(frame, (int(px), int(py)), 7, secondary, -1, cv2.LINE_AA)
            cv2.circle(frame, (int(px), int(py)), 3, (255, 255, 255), -1, cv2.LINE_AA)
        return frame


class HandPortalTracker:
    """MediaPipe Tasks HandLandmarker em VIDEO mode, com tracking temporal."""

    def __init__(self, cv2, mp, np, detection=0.62, tracking=0.66):
        self.cv2, self.mp, self.np = cv2, mp, np
        model = ensure_hand_model(download=True)
        vision = mp.tasks.vision
        options = vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=float(detection),
            min_hand_presence_confidence=0.58,
            min_tracking_confidence=float(tracking),
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self.smoother = AdaptivePointSmoother()
        self.gate = GeometryGate()
        self._last_timestamp_ms = 0

    def close(self):
        self.landmarker.close()

    @staticmethod
    def _anchors(landmarks, width, height):
        return (
            (landmarks[INDEX_TIP].x * width, landmarks[INDEX_TIP].y * height),
            (landmarks[THUMB_TIP].x * width, landmarks[THUMB_TIP].y * height),
        )

    def detect(self, frame, scale=1.0):
        cv2, mp = self.cv2, self.mp
        h, w = frame.shape[:2]
        scale = min(1.0, max(0.50, float(scale)))
        processing = frame if scale >= 0.995 else cv2.resize(
            frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA
        )
        rgb = cv2.cvtColor(processing, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = max(self._last_timestamp_ms + 1, int(time.monotonic() * 1000))
        self._last_timestamp_ms = timestamp_ms
        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        hands = list(result.hand_landmarks or [])
        if len(hands) < 2:
            self.smoother.reset()
            return None

        # Ordenação geométrica evita depender do nome Left/Right após espelhamento.
        hands.sort(key=lambda marks: sum(float(p.x) for p in marks) / max(1, len(marks)))
        left, right = hands[0], hands[-1]
        li, lt = self._anchors(left, w, h)
        ri, rt = self._anchors(right, w, h)
        smooth = self.smoother.update([li, lt, ri, rt])
        polygon = [smooth[0], smooth[2], smooth[3], smooth[1]]
        return smooth if self.gate.accept(polygon, w, h) else None


class StarVisionPortalApp:
    WINDOW = "STAR Vision Portal"

    def __init__(self, camera=0, width=1280, height=720, target_fps=30.0):
        cv2, mp, np = _imports()
        self.cv2, self.mp, self.np = cv2, mp, np
        self.camera_index = int(camera)
        self.width, self.height = int(width), int(height)
        self.state = PortalState()
        self.filter_engine = FilterEngine(cv2, np)
        self.renderer = PortalRenderer(cv2, np, self.filter_engine)
        self.tracker = HandPortalTracker(cv2, mp, np)
        self.gesture = GestureHysteresis()
        self.governor = PerformanceGovernor(target_fps=float(target_fps))
        self.fps = 0.0
        self._last_frame_at = time.perf_counter()
        self._last_notice = ""
        self._notice_until = 0.0

    def _notice(self, text, seconds=1.3):
        self._last_notice = str(text)
        self._notice_until = time.monotonic() + float(seconds)

    def _open_camera(self):
        cv2 = self.cv2
        backend = cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else 0
        cap = cv2.VideoCapture(self.camera_index, backend)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(
                f"Não consegui abrir a câmera {self.camera_index}. Verifique permissões e índice."
            )
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cap

    @staticmethod
    def _portal_width(points):
        return (math.dist(points[0], points[2]) + math.dist(points[1], points[3])) * 0.5

    def _draw_hud(self, frame, tracking_ok):
        if not self.state.hud:
            return
        cv2 = self.cv2
        h, w = frame.shape[:2]
        lines = (
            f"STAR VISION // {self.state.filter_meta['name'].upper()}",
            f"{self.fps:4.1f} FPS | TRACK {'LOCK' if tracking_ok else 'SEARCH'} | SCALE {self.governor.scale:.2f}",
            "GESTO: aproxime as maos | A/D filtro | S captura | H HUD | F fullscreen | Q sair",
        )
        overlay = frame.copy()
        cv2.rectangle(overlay, (18, 16), (min(w - 18, 930), 104), (3, 5, 10), -1)
        frame[:] = cv2.addWeighted(overlay, 0.62, frame, 0.38, 0)
        for i, text in enumerate(lines):
            color = (255, 232, 114) if i == 0 else (220, 225, 235)
            cv2.putText(frame, text, (32, 42 + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.56, color, 1, cv2.LINE_AA)
        if time.monotonic() < self._notice_until:
            cv2.putText(frame, self._last_notice, (32, h - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (255, 255, 255), 2, cv2.LINE_AA)

    def _capture(self, frame):
        CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        self.state.captures += 1
        name = f"star-vision-{time.strftime('%Y%m%d-%H%M%S')}-{self.state.captures:02d}.png"
        path = CAPTURE_DIR / name
        self._notice(f"CAPTURA: {name}" if self.cv2.imwrite(str(path), frame) else "Falha ao salvar captura")

    def _handle_key(self, key, frame):
        cv2 = self.cv2
        if key in (ord("q"), 27):
            return False
        if key in (ord("d"), ord("D")):
            self.state.cycle(1)
            self._notice(self.state.filter_meta["name"])
        elif key in (ord("a"), ord("A")):
            self.state.cycle(-1)
            self._notice(self.state.filter_meta["name"])
        elif key in (ord("h"), ord("H")):
            self.state.hud = not self.state.hud
        elif key in (ord("s"), ord("S")):
            self._capture(frame)
        elif key in (ord("f"), ord("F")):
            self.state.fullscreen = not self.state.fullscreen
            cv2.setWindowProperty(
                self.WINDOW, cv2.WND_PROP_FULLSCREEN,
                cv2.WINDOW_FULLSCREEN if self.state.fullscreen else cv2.WINDOW_NORMAL,
            )
        return True

    def run(self):
        cv2 = self.cv2
        cap = self._open_camera()
        cv2.namedWindow(self.WINDOW, cv2.WINDOW_NORMAL)
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    raise RuntimeError("A câmera parou de entregar frames.")
                frame = cv2.flip(frame, 1)
                now = time.perf_counter()
                dt = max(1e-6, now - self._last_frame_at)
                self._last_frame_at = now
                instant = 1.0 / dt
                self.fps = instant if self.fps <= 0 else self.fps * 0.88 + instant * 0.12
                self.governor.update(self.fps)

                points = self.tracker.detect(frame, self.governor.scale)
                tracking_ok = points is not None
                if tracking_ok:
                    if self.gesture.update(self._portal_width(points), frame.shape[1]):
                        self.state.cycle(1)
                        self._notice(self.state.filter_meta["name"])
                    self.renderer.draw(frame, points, self.state.filter_meta["key"], time.monotonic())

                self._draw_hud(frame, tracking_ok)
                cv2.imshow(self.WINDOW, frame)
                key = cv2.waitKeyEx(1)
                if key != -1 and not self._handle_key(key & 0xFFFFFFFF, frame):
                    break
        finally:
            cap.release()
            self.tracker.close()
            cv2.destroyAllWindows()


def parse_args():
    parser = argparse.ArgumentParser(description="STAR Vision Portal")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=float, default=30.0)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    StarVisionPortalApp(args.camera, args.width, args.height, args.fps).run()
