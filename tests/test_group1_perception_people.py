import math
import uuid

import numpy as np
import soundfile as sf
from PIL import Image

from core.ai_engine import AIEngine
from core.person_auth import LocalPersonAuthenticator
from main import create_star


def _unique(prefix="Pessoa"):
    return prefix + uuid.uuid4().hex[:10]


def test_ai_engine_resolves_an_already_installed_ollama_model_without_download(monkeypatch):
    engine = AIEngine(model="qwen3:8b", enabled=True)
    monkeypatch.setattr(engine, "list_models", lambda **kwargs: ("llama3.2:3b", "gemma3:4b"))
    selected = engine.resolve_model(preferred="qwen3:8b")
    assert selected == "llama3.2:3b"
    assert engine.model == "llama3.2:3b"


def test_local_authentication_is_separate_from_recognition_and_never_grants_permission(tmp_path):
    auth = LocalPersonAuthenticator(tmp_path / "credentials.json")
    person_id = "PERSON-UNIT-1"
    enrolled = auth.enroll(person_id, "123456", consent=True)
    assert enrolled["enrolled"] is True
    assert enrolled["secret_persisted"] is False
    assert auth.verify(person_id, {"pin": "000000"})["authenticated"] is False
    verified = auth.verify(person_id, {"pin": "123456"})
    assert verified["authenticated"] is True
    assert verified["recognition_used_as_authentication"] is False
    assert verified["operational_permission"] is False
    raw = (tmp_path / "credentials.json").read_text(encoding="utf-8")
    assert "123456" not in raw


def test_b26_profile_preferences_events_consent_and_trust_share_official_memory():
    star = create_star()
    name = _unique("Mia")
    bundle = star.people_entities.ingest_profile(
        name,
        {"apelido": "Mi", "cor_preferida": "azul"},
        source="unit-profile",
        reference=f"profile:{uuid.uuid4().hex}",
    )
    person_id = bundle["person"]["person_id"]
    star.people_entities.remember_preference(
        person_id, "bebida", "café", source="unit-profile", reference="pref:1"
    )
    star.people_entities.remember_event(
        person_id, "visitou o laboratório", source="unit-profile", reference="event:1"
    )
    consent = star.people_entities.set_consent(
        person_id, "face_template", True, purpose="reconhecimento local",
        source="unit-profile", reference="consent:1"
    )
    trust = star.people_entities.record_trust(
        person_id, "agenda", 0.72, source="unit-profile", reference="trust:1", basis="histórico declarado"
    )
    context = star.people_entities.person_context(person_id, limit=32)
    contents = "\n".join(item["content"] for item in context["memories"])
    assert "Preferência declarada" in contents
    assert "Evento relacionado" in contents
    assert "Consentimento concedido" in contents
    assert "Confiança contextual" in contents
    assert consent["operational_permission"] is False
    assert trust["permission"] is False


def test_identity_template_requires_consent_and_recognition_stays_a_hypothesis(monkeypatch):
    star = create_star()
    person = star.people_entities.upsert_declared_person(
        _unique("Ana"), source="unit", reference=f"person:{uuid.uuid4().hex}"
    )
    vector = [1.0] + [0.0] * 15
    template = {"algorithm": "star-face-spectrum-v1", "dimensions": len(vector), "vector": vector}
    try:
        star.people_entities.store_identity_template(
            person["person_id"], modality="face", template=template,
            source="unit", reference="face:denied", consent=False,
        )
        assert False, "template sem consentimento não deveria ser persistido"
    except PermissionError:
        pass
    star.people_entities.store_identity_template(
        person["person_id"], modality="face", template=template,
        source="unit", reference="face:allowed", consent=True,
    )
    monkeypatch.setattr(star.perception_runtime.vision, "face_templates", lambda path: [template])
    result = star.perception_runtime.vision.recognize_people("ignored.jpg")
    assert result["status"] == "hypothesis"
    assert result["candidates"][0]["person_id"] == person["person_id"]
    assert result["authenticated"] is False
    assert result["grants_permission"] is False


def test_image_attachment_pipeline_ingests_semantic_evidence_into_b25(tmp_path, monkeypatch):
    star = create_star()
    image_path = tmp_path / "look.png"
    Image.new("RGB", (120, 80), (32, 64, 96)).save(image_path)
    vision = star.perception_runtime.vision
    monkeypatch.setattr(vision, "_face_boxes", lambda path: [])
    monkeypatch.setattr(
        vision,
        "_semantic",
        lambda path: ({
            "scene": "uma pessoa diante de uma parede clara",
            "objects": ["camisa preta"],
            "people": ["uma pessoa em pé"],
            "visible_text": [],
            "uncertainties": [],
            "confidence": 0.88,
        }, "fake-local-vlm"),
    )
    result = star.perception_runtime.ingest_image(image_path, source="unit-chat-attachment")
    assert result["semantic_available"] is True
    assert result["semantic_model"] == "fake-local-vlm"
    observations = star.multimodal_perception.workspace_observations(limit=16)
    combined = " | ".join(str(item.get("content") or "") for item in observations)
    assert "pessoa diante de uma parede clara" in combined
    assert result["person_recognition"]["authenticated"] is False


def test_screen_and_audio_commands_are_local_only_and_use_existing_dispatcher():
    star = create_star()

    class FakeScreen:
        def __init__(self):
            self.calls = 0
        def capture(self):
            self.calls += 1
            return {"available": True, "observations": [{"content": "janela do editor aberta"}]}

    class FakeAudio:
        def __init__(self):
            self.calls = 0
        def sample(self, seconds=1.0):
            self.calls += 1
            return {"available": True, "features": {"classification": "som ambiente", "rms": 0.02}}

    star.perception_runtime.screen = FakeScreen()
    star.perception_runtime.audio = FakeAudio()
    local = star.agents.dispatch("olhe minha tela", remote=False)
    assert "janela do editor aberta" in local
    assert star.perception_runtime.screen.calls == 1
    remote = star.agents.dispatch("olhe minha tela", remote=True)
    assert "solicitação local explícita" in remote
    assert star.perception_runtime.screen.calls == 1
    heard = star.agents.dispatch("escute o ambiente", remote=False)
    assert "som ambiente" in heard
    assert star.perception_runtime.audio.calls == 1


def test_speaker_recognition_uses_derived_template_and_does_not_authenticate(tmp_path):
    star = create_star()
    person = star.people_entities.upsert_declared_person(
        _unique("Voz"), source="unit", reference=f"speaker:{uuid.uuid4().hex}"
    )
    rate = 16000
    t = np.arange(rate, dtype=np.float32) / rate
    samples = (0.25 * np.sin(2.0 * math.pi * 220.0 * t) + 0.08 * np.sin(2.0 * math.pi * 440.0 * t)).astype(np.float32)
    wav = tmp_path / "speaker.wav"
    sf.write(wav, samples, rate)
    enrolled = star.perception_runtime.speaker.enroll(
        person["person_id"], wav, consent=True, source="unit-voice", reference="voice:1"
    )
    assert enrolled["raw_biometric_stored"] is False
    result = star.perception_runtime.speaker.recognize(wav)
    assert result["candidates"]
    assert result["candidates"][0]["person_id"] == person["person_id"]
    assert result["authenticated"] is False
    assert result["grants_permission"] is False


def test_people_authenticate_uses_separate_verifier(tmp_path):
    star = create_star()
    person = star.people_entities.upsert_declared_person(
        _unique("Auth"), source="unit", reference=f"auth:{uuid.uuid4().hex}"
    )
    verifier = LocalPersonAuthenticator(tmp_path / "auth.json")
    verifier.enroll(person["person_id"], "segredo-forte", consent=True)
    result = star.people_entities.authenticate(
        person["person_id"], verifier=verifier, challenge={"secret": "segredo-forte"}
    )
    assert result["authenticated"] is True
    assert result["recognition_used_as_authentication"] is False
    assert result["operational_permission"] is False



def test_semantic_vision_failure_is_degraded_but_diagnosable(tmp_path, monkeypatch):
    star = create_star()
    image_path = tmp_path / "semantic-failure.png"
    Image.new("RGB", (64, 64), (24, 48, 72)).save(image_path)

    vision = star.perception_runtime.vision
    monkeypatch.setattr(vision, "_vision_model", lambda: "fake-local-vlm")
    monkeypatch.setattr(vision, "_face_boxes", lambda path: [])

    def fail_generate(*args, **kwargs):
        raise RuntimeError("provider indisponível")

    monkeypatch.setattr(vision.engine, "generate", fail_generate)
    result = star.perception_runtime.ingest_image(
        image_path,
        source="unit-semantic-failure",
    )

    assert result["semantic_available"] is False
    assert result["semantic_model"] == "fake-local-vlm"
    assert "RuntimeError" in result["semantic_error"]
    assert "provider indisponível" in result["semantic_error"]
    # Metadados locais continuam úteis mesmo quando o VLM falha.
    assert result["observations"]
