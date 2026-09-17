"""Providers perceptivos locais integrados ao B25/B26.

Esta camada não cria outra percepção ou memória. Ela transforma entradas reais
(imagem, tela e áudio) em observações bounded para ``MultimodalPerception`` e usa
B26 para hipóteses de identidade. Modelos locais são opcionais/lazy.

RECONHECIMENTO != AUTENTICAÇÃO. OBSERVAÇÃO != FATO CANÔNICO.
"""
from __future__ import annotations

import base64
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from core.ai_engine import AIEngine


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _clamp(value: Any, default: float = 0.5) -> float:
    try:
        return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):
        return default


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cosine(a, b) -> float:
    import numpy as np
    av = np.asarray(a, dtype=np.float32).reshape(-1)
    bv = np.asarray(b, dtype=np.float32).reshape(-1)
    if av.size == 0 or av.shape != bv.shape:
        return 0.0
    denom = float(np.linalg.norm(av) * np.linalg.norm(bv))
    if denom <= 1e-9:
        return 0.0
    return max(-1.0, min(float(np.dot(av, bv) / denom), 1.0))


class SemanticVisionProvider:
    """Metadados visuais + face detection + VLM local opcional."""

    VISION_CANDIDATES = (
        "qwen2.5vl", "qwen3-vl", "llava", "gemma3", "minicpm-v", "moondream",
    )
    MAX_IMAGE_BYTES = 16 * 1024 * 1024

    def __init__(self, perception, *, people=None, host: str | None = None, model: str | None = None):
        self.perception = perception
        self.people = people
        self.host = (host or os.getenv("STAR_LOCAL_LLM_HOST", "http://127.0.0.1:11434")).rstrip("/")
        self.preferred_model = (model or os.getenv("STAR_LOCAL_VISION_MODEL", "qwen2.5vl:3b")).strip()
        self.engine = AIEngine(model=self.preferred_model, host=self.host, enabled=True)
        self.last_analysis: dict | None = None

    def _vision_model(self) -> str | None:
        models = self.engine.list_models(timeout=0.5)
        if not models:
            return None
        for name in models:
            if AIEngine._model_matches(name, self.preferred_model):
                self.engine.model = name
                return name
        for name in models:
            low = name.casefold()
            if any(candidate in low for candidate in self.VISION_CANDIDATES):
                self.engine.model = name
                return name
        return None

    @staticmethod
    def _load_image(path: Path):
        from PIL import Image
        image = Image.open(path)
        image.load()
        return image

    @staticmethod
    def _metadata(image) -> dict:
        import numpy as np
        sample = image.convert("RGB")
        sample.thumbnail((64, 64))
        arr = np.asarray(sample, dtype=np.float32)
        mean = arr.mean(axis=(0, 1)) if arr.size else np.array([0.0, 0.0, 0.0])
        luminance = float(0.2126 * mean[0] + 0.7152 * mean[1] + 0.0722 * mean[2]) / 255.0
        return {
            "width": int(image.width),
            "height": int(image.height),
            "mode": str(image.mode),
            "mean_rgb": [round(float(x), 2) for x in mean],
            "luminance": round(luminance, 4),
            "orientation": "landscape" if image.width > image.height else ("portrait" if image.height > image.width else "square"),
        }

    @staticmethod
    def _face_boxes(path: Path) -> list[tuple[int, int, int, int]]:
        if importlib.util.find_spec("cv2") is None:
            return []
        try:
            import cv2
            image = cv2.imread(str(path))
            if image is None:
                return []
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            cascade = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))
            if cascade.empty():
                return []
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(48, 48))
            return [tuple(int(v) for v in row) for row in faces[:16]]
        except (AttributeError, OSError, RuntimeError, ValueError):
            return []

    @staticmethod
    def _face_template(image, box: tuple[int, int, int, int]) -> dict:
        import numpy as np
        x, y, w, h = box
        crop = image.convert("L").crop((x, y, x + w, y + h)).resize((32, 32))
        arr = np.asarray(crop, dtype=np.float32) / 255.0
        arr = (arr - float(arr.mean())) / max(float(arr.std()), 1e-6)
        spectrum = np.log1p(np.abs(np.fft.rfft2(arr))[:8, :8]).astype(np.float32).reshape(-1)
        norm = float(np.linalg.norm(spectrum))
        if norm > 1e-9:
            spectrum /= norm
        return {
            "algorithm": "star-face-spectrum-v1",
            "dimensions": int(spectrum.size),
            "vector": [round(float(value), 6) for value in spectrum],
        }

    @staticmethod
    def _extract_json(text: str) -> dict | None:
        raw = str(text or "").strip()
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.I | re.M).strip()
        try:
            value = json.loads(raw)
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            pass
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            try:
                value = json.loads(raw[start:end + 1])
                return value if isinstance(value, dict) else None
            except json.JSONDecodeError:
                return None
        return None

    def _semantic(self, path: Path) -> tuple[dict | None, str | None]:
        model = self._vision_model()
        if model is None:
            return None, None
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        prompt = (
            "Analise somente o que é visualmente sustentado pela imagem. Responda APENAS JSON com: "
            "scene (string), objects (lista de strings), people (lista de descrições não identificadoras), "
            "visible_text (lista de strings), uncertainties (lista de strings), confidence (0..1). "
            "Não identifique pessoas, não infira atributos sensíveis e não invente itens ocultos."
        )
        try:
            raw = self.engine.generate(
                prompt,
                context=(
                    "Você é um provider perceptivo local da STAR. Observação não é fato canônico. "
                    "Não autentique pessoas e não faça inferências sensíveis."
                ),
                timeout=max(2.0, min(float(os.getenv("STAR_LOCAL_VISION_TIMEOUT", "15")), 45.0)),
                images=[encoded],
            )
        except Exception:
            return None, model
        return self._extract_json(raw), model

    def analyze(self, image_path: str | Path, *, source: str = "local-image", modality: str = "vision") -> dict:
        path = Path(image_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        size = path.stat().st_size
        if size <= 0 or size > self.MAX_IMAGE_BYTES:
            raise ValueError("imagem vazia ou acima do limite de 16 MiB")
        image = self._load_image(path)
        metadata = self._metadata(image)
        boxes = self._face_boxes(path)
        semantic, model = self._semantic(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        observations = []

        observations.append({
            "content": f"Imagem {metadata['width']}x{metadata['height']} ({metadata['orientation']}); luminância {metadata['luminance']:.2f}",
            "confidence": 0.99,
            "importance": 0.5,
            "event_key": f"image:{digest}:metadata",
            "attributes": {"kind": "image_metadata", **metadata, "semantic_inference": False},
        })
        if boxes:
            observations.append({
                "content": f"{len(boxes)} rosto(s) detectado(s) visualmente",
                "confidence": 0.75,
                "importance": 0.7,
                "event_key": f"image:{digest}:faces",
                "entities": [f"face_candidate_{index}" for index in range(len(boxes))],
                "attributes": {"kind": "face_detection", "boxes": boxes, "identity_known": False, "authentication": False},
            })
        if semantic:
            confidence = _clamp(semantic.get("confidence"), 0.6)
            scene = _clean(semantic.get("scene"))
            if scene:
                observations.append({
                    "content": scene,
                    "confidence": confidence,
                    "importance": 0.75,
                    "event_key": f"image:{digest}:scene",
                    "attributes": {"kind": "semantic_scene", "model": model, "model_output": True},
                })
            for index, obj in enumerate(list(semantic.get("objects") or ())[:16]):
                if _clean(obj):
                    observations.append({
                        "content": f"Objeto visual candidato: {_clean(obj)}",
                        "confidence": confidence,
                        "importance": 0.55,
                        "event_key": f"image:{digest}:object:{index}",
                        "attributes": {"kind": "semantic_object_candidate", "model": model, "model_output": True},
                    })
            for index, person in enumerate(list(semantic.get("people") or ())[:8]):
                if _clean(person):
                    observations.append({
                        "content": f"Pessoa visualmente descrita: {_clean(person)}",
                        "confidence": confidence,
                        "importance": 0.7,
                        "event_key": f"image:{digest}:person:{index}",
                        "attributes": {"kind": "semantic_person_candidate", "model": model, "identity_known": False, "authentication": False},
                    })
            text_items = [_clean(value) for value in list(semantic.get("visible_text") or ())[:16] if _clean(value)]
            if text_items:
                observations.append({
                    "content": "Texto visual reportado: " + " | ".join(text_items),
                    "confidence": confidence,
                    "importance": 0.6,
                    "event_key": f"image:{digest}:text",
                    "attributes": {"kind": "visual_text_candidate", "model": model, "model_output": True},
                })

        ingested = [self.perception.ingest(modality, item, source=source) for item in observations]
        result = {
            "path": str(path),
            "source": source,
            "modality": modality,
            "metadata": metadata,
            "faces_detected": len(boxes),
            "face_boxes": boxes,
            "semantic_available": semantic is not None,
            "semantic_model": model,
            "semantic": deepcopy(semantic),
            "observations": ingested,
            "recognition_is_authentication": False,
            "raw_biometric_persisted": False,
        }
        self.last_analysis = deepcopy(result)
        return result

    def face_templates(self, image_path: str | Path) -> list[dict]:
        path = Path(image_path).expanduser().resolve()
        image = self._load_image(path)
        return [self._face_template(image, box) for box in self._face_boxes(path)]

    def enroll_person(self, person_id: str, image_path: str | Path, *, consent: bool, source: str, reference: str) -> dict:
        if self.people is None:
            raise RuntimeError("B26 indisponível")
        if not consent:
            raise PermissionError("template facial exige consentimento explícito")
        templates = self.face_templates(image_path)
        if not templates:
            return {"person_id": person_id, "enrolled": False, "reason": "face_not_detected", "authenticated": False}
        return self.people.store_identity_template(
            person_id,
            modality="face",
            template=templates[0],
            source=source,
            reference=reference,
            consent=True,
        )

    def recognize_people(self, image_path: str | Path, *, limit: int = 5) -> dict:
        if self.people is None:
            return {"status": "unavailable", "candidates": [], "authenticated": False, "grants_permission": False}
        detected = self.face_templates(image_path)
        stored = self.people.identity_templates("face", limit=256)
        candidates = []
        for sample in detected[:4]:
            for record in stored:
                template = record.get("template") or {}
                if sample.get("algorithm") != template.get("algorithm"):
                    continue
                similarity = _cosine(sample.get("vector"), template.get("vector"))
                confidence = max(0.0, min((similarity - 0.55) / 0.45, 1.0))
                if confidence < 0.35:
                    continue
                candidates.append({
                    "person_id": record.get("person_id"),
                    "confidence": confidence,
                    "signal": "face_template_similarity",
                    "algorithm": sample.get("algorithm"),
                })
        best = {}
        for item in candidates:
            pid = item.get("person_id")
            if pid and (pid not in best or item["confidence"] > best[pid]["confidence"]):
                best[pid] = item
        ranked = sorted(best.values(), key=lambda item: item["confidence"], reverse=True)[:max(1, min(int(limit), 8))]
        return self.people.recognition_hypothesis(ranked, signals=[{"modality": "face", "faces_detected": len(detected)}])

    def status(self) -> dict:
        return {
            "provider": "SemanticVisionProvider",
            "opencv": importlib.util.find_spec("cv2") is not None,
            "face_detection": importlib.util.find_spec("cv2") is not None,
            "semantic_model": self._vision_model(),
            "last_analysis": bool(self.last_analysis),
            "recognition_is_authentication": False,
        }


class ScreenPerceptionProvider:
    def __init__(self, vision: SemanticVisionProvider):
        self.vision = vision

    def capture(self) -> dict:
        try:
            from PIL import ImageGrab
            image = ImageGrab.grab(all_screens=True)
        except Exception as exc:
            return {"available": False, "reason": f"screen_capture_failed:{type(exc).__name__}", "observations": []}
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(prefix="star-screen-", suffix=".png", delete=False) as handle:
                temp_path = Path(handle.name)
            image.save(temp_path, format="PNG")
            result = self.vision.analyze(temp_path, source="screen-capture-explicit", modality="screen")
            return {"available": True, **result}
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)


class AmbientAudioProvider:
    """Amostra curta; nunca grava continuamente nem persiste áudio bruto."""

    def __init__(self, perception):
        self.perception = perception

    @staticmethod
    def _features(samples, sample_rate: int) -> dict:
        import numpy as np
        data = np.asarray(samples, dtype=np.float32).reshape(-1)
        if not data.size:
            raise ValueError("áudio vazio")
        data = data - float(data.mean())
        rms = float(np.sqrt(np.mean(data * data)))
        peak = float(np.max(np.abs(data)))
        zcr = float(np.mean(np.abs(np.diff(np.signbit(data))))) if data.size > 1 else 0.0
        spectrum = np.abs(np.fft.rfft(data)) + 1e-9
        freqs = np.fft.rfftfreq(data.size, 1.0 / sample_rate)
        centroid = float(np.sum(freqs * spectrum) / np.sum(spectrum)) if spectrum.size else 0.0
        if rms < 0.006:
            label = "silêncio ou ambiente muito baixo"
        elif peak > 0.8 and rms > 0.12:
            label = "evento sonoro intenso/impulsivo"
        elif zcr < 0.18 and 100.0 <= centroid <= 4500.0:
            label = "fala, música ou som tonal candidato"
        else:
            label = "som ambiente"
        return {
            "rms": round(rms, 6), "peak": round(peak, 6), "zero_crossing_rate": round(zcr, 6),
            "spectral_centroid_hz": round(centroid, 2), "classification": label,
        }

    def sample(self, *, seconds: float = 1.0, sample_rate: int = 16000) -> dict:
        duration = max(0.25, min(float(seconds), 3.0))
        rate = max(8000, min(int(sample_rate), 48000))
        try:
            import sounddevice as sd
            audio = sd.rec(int(duration * rate), samplerate=rate, channels=1, dtype="float32", blocking=True)
        except Exception as exc:
            return {"available": False, "reason": f"audio_capture_failed:{type(exc).__name__}", "persisted_raw_audio": False}
        features = self._features(audio, rate)
        observation = self.perception.ingest(
            "audio",
            {
                "content": features["classification"],
                "confidence": 0.65,
                "importance": 0.55,
                "event_key": f"ambient-audio:{_now()}",
                "attributes": {**features, "duration_seconds": duration, "sample_rate": rate, "continuous_recording": False},
            },
            source="ambient-audio-explicit",
        )
        return {"available": True, "features": features, "observation": observation, "persisted_raw_audio": False}


class SpeakerRecognitionProvider:
    """Fingerprint acústico local para hipótese de speaker identity.

    É deliberadamente um reconhecedor contextual, não um autenticador biométrico.
    Templates derivados só são persistidos com consentimento explícito.
    """

    def __init__(self, people):
        self.people = people

    @staticmethod
    def fingerprint(audio_path: str | Path) -> dict:
        import numpy as np
        import soundfile as sf
        data, sample_rate = sf.read(str(Path(audio_path)), dtype="float32", always_2d=False)
        samples = np.asarray(data, dtype=np.float32)
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        if samples.size < max(800, int(sample_rate * 0.15)):
            raise ValueError("áudio curto demais para fingerprint")
        samples = samples - float(samples.mean())
        peak = float(np.max(np.abs(samples)))
        if peak > 1e-6:
            samples = samples / peak
        spectrum = np.abs(np.fft.rfft(samples)) + 1e-9
        chunks = np.array_split(spectrum, 32)
        bands = np.array([float(np.log1p(chunk.mean())) for chunk in chunks], dtype=np.float32)
        freqs = np.fft.rfftfreq(samples.size, 1.0 / int(sample_rate))
        centroid = float(np.sum(freqs * spectrum) / np.sum(spectrum)) / max(sample_rate / 2.0, 1.0)
        zcr = float(np.mean(np.abs(np.diff(np.signbit(samples))))) if samples.size > 1 else 0.0
        vector = np.concatenate([bands, np.array([centroid, zcr], dtype=np.float32)])
        vector -= float(vector.mean())
        norm = float(np.linalg.norm(vector))
        if norm > 1e-9:
            vector /= norm
        return {
            "algorithm": "star-speaker-spectrum-v1",
            "dimensions": int(vector.size),
            "sample_rate": int(sample_rate),
            "vector": [round(float(value), 6) for value in vector],
        }

    def enroll(self, person_id: str, audio_path: str | Path, *, consent: bool, source: str, reference: str) -> dict:
        if not consent:
            raise PermissionError("template de voz exige consentimento explícito")
        template = self.fingerprint(audio_path)
        return self.people.store_identity_template(
            person_id,
            modality="voice",
            template=template,
            source=source,
            reference=reference,
            consent=True,
        )

    def recognize(self, audio_path: str | Path, *, limit: int = 5) -> dict:
        sample = self.fingerprint(audio_path)
        stored = self.people.identity_templates("voice", limit=256)
        candidates = []
        for record in stored:
            template = record.get("template") or {}
            if template.get("algorithm") != sample.get("algorithm"):
                continue
            similarity = _cosine(sample.get("vector"), template.get("vector"))
            confidence = max(0.0, min((similarity - 0.55) / 0.45, 1.0))
            if confidence >= 0.35:
                candidates.append({
                    "person_id": record.get("person_id"),
                    "confidence": confidence,
                    "signal": "voice_template_similarity",
                    "algorithm": sample.get("algorithm"),
                })
        candidates.sort(key=lambda item: item["confidence"], reverse=True)
        return self.people.recognition_hypothesis(
            candidates[:max(1, min(int(limit), 8))],
            signals=[{"modality": "voice", "algorithm": sample.get("algorithm")}],
        )


class PerceptionRuntime:
    """Facade pequena para providers reais sem polling pesado em background."""

    def __init__(self, star):
        self.star = star
        self.vision = SemanticVisionProvider(star.multimodal_perception, people=star.people_entities)
        self.screen = ScreenPerceptionProvider(self.vision)
        self.audio = AmbientAudioProvider(star.multimodal_perception)
        self.speaker = SpeakerRecognitionProvider(star.people_entities)

    def ingest_image(self, path: str | Path, *, source: str = "chat-attachment") -> dict:
        analysis = self.vision.analyze(path, source=source, modality="vision")
        recognition = self.vision.recognize_people(path)
        return {**analysis, "person_recognition": recognition}

    def register_person_from_image(
        self,
        name: str,
        profile: dict,
        image_path: str | Path,
        *,
        source: str = "declared-profile-with-image",
        reference: str = "",
        biometric_consent: bool = False,
    ) -> dict:
        path = Path(image_path).expanduser().resolve()
        ref = reference or f"image:{hashlib.sha256(path.read_bytes()).hexdigest()[:16]}"
        person_bundle = self.star.people_entities.ingest_profile(
            name,
            profile,
            source=source,
            reference=ref,
            identity_evidence=[{
                "modality": "vision", "source": source, "reference": ref,
                "descriptor": "imagem declarada como referência de identidade", "confidence": 0.8,
            }],
        )
        enrollment = None
        if biometric_consent:
            enrollment = self.vision.enroll_person(
                person_bundle["person"]["person_id"], path,
                consent=True, source=source, reference=ref,
            )
        return {
            **person_bundle,
            "visual_template_enrollment": enrollment,
            "biometric_consent": bool(biometric_consent),
            "authenticated": False,
            "grants_permission": False,
        }

    def status(self) -> dict:
        return {
            "vision": self.vision.status(),
            "screen_capture": True,
            "ambient_audio": True,
            "speaker_recognition": True,
            "background_continuous_capture": False,
            "recognition_is_authentication": False,
        }
