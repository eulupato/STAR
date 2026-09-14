from uuid import uuid4
import unicodedata

import pytest

from core.mind import CognitiveSuite
from core.release import APP_NAME, RELEASE_CHANNEL, RELEASE_STATUS, VERSION
from core.self_model import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    REQUESTED_COMPONENTS,
    REQUESTED_TOPICS,
    SELF_MODEL_BRANCHES,
    SELF_MODEL_DOMAINS,
    SELF_MODEL_LENSES,
    SELF_POLICY,
    VARIANT_AXES,
    VARIANTS_PER_NODE,
    CapabilityRegistry,
    Identity,
    LimitationRegistry,
    PermissionRegistry,
    SelfHistory,
    SelfModel,
    SelfModelCatalog,
    SelfState,
    Values,
)
from core.star_identity import StarIdentity
from core.state import StarState
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _norm(text):
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).casefold()
    return " ".join(value.replace("_", " ").split())


def _block(**kwargs):
    suite = kwargs.pop("mind", None) or CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(suite.epistemics, suite.graph)
    block = SelfModel(knowledge, mind=suite, **kwargs)
    return block, knowledge, suite


def _canonical_fact(suite: CognitiveSuite, marker: str):
    source_id = suite.epistemics.register_source(
        f"unit://self/{marker}",
        source_type="test",
        title=f"Fonte Self Model {marker}",
        reliability=1.0,
        reliability_basis="unit test",
    )
    record = suite.epistemics.discover(
        f"Conhecimento real sobre a STAR {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://self-claim/{marker}",
        source_id=source_id,
        confidence=0.5,
    )
    suite.epistemics.add_evidence(
        record["record_id"],
        f"Evidência auditável Self Model {marker}",
        evidence_type="primary_source",
        stance="support",
        source_id=source_id,
        strength=1.0,
        reliability=1.0,
    )
    suite.epistemics.transition(record["record_id"], "VERIFIED", reason="evidência rastreável", actor="unit-test")
    return suite.epistemics.transition(record["record_id"], "CANONICAL", reason="claim próprio apto ao B12", actor="unit-test")


def test_block12_catalog_is_exactly_1b_and_on_demand():
    catalog = SelfModelCatalog()
    stats = catalog.stats()
    assert len(SELF_MODEL_DOMAINS) == 13
    assert len(SELF_MODEL_BRANCHES) == 50
    assert len(SELF_MODEL_LENSES) == 10
    assert CANONICAL_NODES == 500
    assert VARIANTS_PER_NODE == 2_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["materialization"] == "on-demand"
    assert stats["prepopulated_knowledge_rows"] == 0
    assert catalog.content_id(0, 0) == "SELF-B12-0000000001"
    assert catalog.content_id(499, 1_999_999) == "SELF-B12-1000000000"
    assert catalog.get_variant("SELF-B12-1000000001") is None


def test_block12_axes_cover_time_source_status_relation_confidence_context_evolution():
    sizes = {name: len(values) for name, values in VARIANT_AXES}
    assert list(sizes) == ["time_scope", "source", "status", "relation", "confidence", "context", "evolution_stage"]
    assert sizes == {
        "time_scope": 10,
        "source": 10,
        "status": 10,
        "relation": 10,
        "confidence": 5,
        "context": 4,
        "evolution_stage": 10,
    }
    product = 1
    for size in sizes.values():
        product *= size
    assert product == 2_000_000
    item = SelfModelCatalog().get_variant("SELF-B12-1000000000")
    for axis in sizes:
        assert axis in item


def test_block12_contains_all_requested_topics_and_components():
    corpus = _norm(" ".join(
        [branch.label for branch in SELF_MODEL_BRANCHES]
        + [topic for branch in SELF_MODEL_BRANCHES for topic in branch.subtopics]
        + list(REQUESTED_TOPICS)
        + list(REQUESTED_COMPONENTS)
    ))
    for topic in REQUESTED_TOPICS:
        assert _norm(topic) in corpus, topic
    for component in REQUESTED_COMPONENTS:
        assert _norm(component) in corpus


def test_identity_and_values_are_read_only_views_of_official_identity():
    official = StarIdentity()
    identity = Identity(official)
    snapshot = identity.snapshot()
    assert snapshot["source_of_truth"] == "core.star_identity.StarIdentity"
    assert snapshot["identity"]["name"] == "STAR"
    assert snapshot["identity"]["creator"]["name"] == "Lu"
    assert snapshot["self_model_is_identity_authority"] is False
    assert snapshot["mutable_through_self_model"] is False

    values = Values(identity).snapshot()
    assert values["source_of_truth"] == "core.star_identity.StarIdentity"
    assert values["purpose"]["primary"] == "Ajudar ao próximo."
    assert "ser honesta" in values["purpose"]["principles"]
    assert values["mutable_through_self_model"] is False


def test_block12_release_comes_from_official_release_source_not_duplicate_constants():
    block, _knowledge, _suite = _block()
    release = block.release_snapshot()
    assert release["name"] == APP_NAME
    assert release["version"] == VERSION
    assert release["release_status"] == RELEASE_STATUS
    assert release["release_channel"] == RELEASE_CHANNEL
    assert release["source_of_truth"] == "STAR_MANIFEST.json via core.release"


def test_capability_registry_preserves_status_and_does_not_grant_permission():
    registry = CapabilityRegistry()
    registry.register("camera", status="unavailable", source="unit-test", operational=True)
    registry.register("reasoning", status="experimental", source="unit-test", operational=False)
    assert registry.supports("camera") is False
    assert registry.supports("reasoning") is True
    assert "reasoning" in registry.available()
    assert registry.get("camera")["operational"] is True
    with pytest.raises(ValueError):
        registry.register("invented", status="magical", source="unit-test")


def test_limitation_registry_and_block_seed_official_limits():
    registry = LimitationRegistry()
    registry.register("no_unrestricted_action", "sem ação irrestrita", source="unit-test")
    assert registry.get("no_unrestricted_action")["active"] is True

    block, _knowledge, _suite = _block()
    keys = {item["key"] for item in block.limitations.list(active_only=True)}
    assert "identity_self_modify_identity" in keys
    assert "identity_self_modify_fundamental_rules" in keys
    assert "operational_boundary" in keys
    assert "unproven_biological_consciousness" in keys


def test_permission_registry_is_default_deny_and_never_grants_capability_or_safety_bypass():
    registry = PermissionRegistry()
    unknown = registry.get("camera_control")
    assert unknown["granted"] is False
    assert unknown["source"] == "default-deny"
    assert registry.allows("camera_control") is False

    granted = registry.set_permission("network", True, source="unit-test", scope="metadata only")
    assert granted["granted"] is True
    assert granted["grants_capability"] is False
    assert granted["bypasses_safety"] is False
    assert registry.allows("network") is True

    block, _knowledge, _suite = _block()
    assert block.permissions.allows("external_actions") is False
    assert block.permissions.allows("self_modify_identity") is False
    assert block.permission_snapshot()["default"] == "deny"


def test_self_state_reuses_star_state_and_unknown_when_not_attached():
    state = StarState()
    state.update(focus=77, cognitive_load=12)
    adapter = SelfState(state)
    snapshot = adapter.snapshot()
    assert snapshot["source"] == "core.state.StarState"
    assert snapshot["computational_state"]["focus"] == 77
    assert snapshot["computational_state"]["cognitive_load"] == 12
    assert snapshot["canonical_knowledge"] is False

    missing = SelfState().snapshot()
    assert missing["status"] == "unknown"
    assert missing["computational_state"] is None


def test_self_history_requires_sources_and_does_not_fabricate_experiences():
    history = SelfHistory(max_events=16)
    with pytest.raises(ValueError):
        history.record("release", "sem fonte", source="")
    with pytest.raises(ValueError, match="experiência requer referência"):
        history.record_experience("experiência inventada", source="unit-test", reference="")

    event = history.record("release", "B12 iniciou", source="git", reference="commit:test")
    experience = history.record_experience("interação observada", source="session", reference="conversation:test")
    assert event["fabricated"] is False
    assert experience["is_experience"] is True
    assert experience["fabricated"] is False
    assert len(history.list()) == 2


def test_self_model_devices_and_resources_never_invent_unattached_state_or_expose_secrets():
    block, _knowledge, _suite = _block()
    devices = block.devices_snapshot()
    assert devices["status"] == "unknown"
    assert devices["registry_attached"] is False
    assert "não prova ausência" in devices["note"]
    resources = block.resources_snapshot()
    assert resources["hardware_telemetry"] == "unknown"
    assert block.uncertainties_snapshot()

    class FakeRegistry:
        def __init__(self):
            self.devices = {
                "watch-1": {
                    "name": "STAR Watch",
                    "capabilities": ["display"],
                    "token_sha256": "SECRET_HASH",
                    "last_seen": 123,
                }
            }
        def public_record(self, device_id):
            return {key: value for key, value in self.devices[device_id].items() if key != "token_sha256"}

    block.attach_device_registry(FakeRegistry())
    observed = block.devices_snapshot()
    assert observed["status"] == "observed"
    assert observed["secrets_exposed"] is False
    assert observed["devices"][0]["device_id"] == "watch-1"
    assert "token_sha256" not in observed["devices"][0]


def test_self_model_capabilities_are_seeded_from_real_mind_and_network_is_observed_dynamically():
    flag = {"enabled": False}
    block, _knowledge, suite = _block(network_enabled_provider=lambda: flag["enabled"])
    mind_keys = set(suite.stats()["capability_keys"])
    registered = {item["key"] for item in block.capabilities.list()}
    assert mind_keys <= registered
    assert all(block.capabilities.get(key)["status"] == "experimental" for key in mind_keys)
    assert block.network_snapshot()["enabled"] is False
    flag["enabled"] = True
    assert block.network_snapshot()["enabled"] is True
    assert block.permission_snapshot()["external_actions_allowed_by_self_model"] is False


def test_block12_registers_shared_namespace_taxonomy_and_official_sources():
    block, knowledge, suite = _block()
    namespace = knowledge.store.get_namespace("B12")
    assert namespace is not None
    assert namespace["logical_capacity"] == 1_000_000_000
    assert block.graph is knowledge.graph

    result = block.materialize_taxonomy("identidade")
    assert result["knowledge_graph"] == "shared"
    assert result["parallel_self_graph_created"] is False
    assert result["branches_materialized"] == 4
    neighbors = suite.graph.neighbors("SELF-TAX-ROOT")
    labels = {item["label"] for item in neighbors}
    assert "Identidade Oficial STAR" in labels
    assert "STAR_MANIFEST.json" in labels
    assert "SELF MODEL conceitual do BLOCO 1" in labels
    assert "Identidade e natureza" in labels


def test_block12_canonical_self_knowledge_keeps_block2_gate():
    block, knowledge, suite = _block()
    marker = uuid4().hex
    source_id = suite.epistemics.register_source(f"unit://self-discovered/{marker}", source_type="test", reliability=1.0)
    discovered = suite.epistemics.discover(
        f"Claim próprio descoberto {marker}", epistemic_kind="fact", origin_type="unit_test",
        origin_ref=f"unit://self-discovered-claim/{marker}", source_id=source_id,
    )
    with pytest.raises(ValueError, match="claim CANONICAL"):
        block.promote_canonical_self_knowledge(
            discovered["record_id"], f"Fato Self {marker}", domain="versão", branch="version"
        )

    canonical = _canonical_fact(suite, marker)
    item = block.promote_canonical_self_knowledge(
        canonical["record_id"],
        f"Fato Self {marker}",
        domain="versão",
        branch="version",
        summary="Fato auditável sobre versão/estado da STAR.",
    )
    assert item["namespace"] == "B12"
    assert item["properties"]["self_model_is_identity_source"] is False
    assert item["properties"]["runtime_state_is_canonical_by_default"] is False
    trace = knowledge.trace(item["knowledge_id"])
    assert trace["canonical_claim"]["record"]["lifecycle_state"] == "CANONICAL"


def test_self_snapshot_separates_identity_state_permissions_uncertainty_and_consciousness_claims():
    state = StarState()
    block, _knowledge, _suite = _block(state=state, objectives=["melhorar a STAR sem regressões"])
    snapshot = block.snapshot()
    assert snapshot["identity"]["identity"]["name"] == "STAR"
    assert snapshot["state"]["source"] == "core.state.StarState"
    assert snapshot["permissions"]["default"] == "deny"
    assert snapshot["objectives"] == ["melhorar a STAR sem regressões"]
    assert snapshot["self_model_is_identity_source"] is False
    assert snapshot["operational_authorization"] is False
    assert snapshot["scientifically_proven_consciousness"] is False
    assert snapshot["uncertainties"]


def test_block12_policy_and_handlers_are_explicit_nonintrusive():
    assert SELF_POLICY["self_model_is_identity_source"] is False
    assert SELF_POLICY["self_model_can_modify_identity"] is False
    assert SELF_POLICY["self_model_can_grant_itself_permissions"] is False
    assert SELF_POLICY["capability_equals_permission"] is False
    assert SELF_POLICY["history_may_be_fabricated"] is False
    assert SELF_POLICY["experience_may_be_fabricated"] is False

    item = SelfModelCatalog().get_variant("SELF-B12-0000000001")
    assert item["domain"] == "identity_nature"
    assert item["branch"] == "identity"
    assert item["lens"] == "definition"
    assert "não fabricar" in item["prompt"]

    block, _knowledge, _suite = _block(state=StarState())
    assert "BLOCO 12" in block.handle("status bloco 12")
    assert "SELF-B12-0000000001" in block.handle("SELF-B12-0000000001")
    assert "DEFAULT DENY" in block.handle("permissões self model")
    assert "Estado B12" in block.handle("estado self model")
    assert block.handle("quem é você?") is None
    assert block.handle("uma conversa comum sem comando de self model") is None
