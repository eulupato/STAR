from clients.star_vision_portal import PortalState
from modules.vision import (
    AdaptivePointSmoother,
    GeometryGate,
    GestureHysteresis,
    PerformanceGovernor,
    PORTAL_FILTERS,
    filter_summary,
    handle_vision_command,
)


def test_portal_has_12_unique_filters():
    assert len(PORTAL_FILTERS) == 12
    assert len({item["key"] for item in PORTAL_FILTERS}) == 12
    assert "Hologram" in filter_summary()
    assert "12 filtros" in filter_summary()


def test_portal_state_wraps_filters():
    state = PortalState()
    state.cycle(-1)
    assert state.filter_meta["key"] == PORTAL_FILTERS[-1]["key"]
    state.cycle(1)
    assert state.filter_meta["key"] == PORTAL_FILTERS[0]["key"]


def test_gesture_hysteresis_requires_confirmation_and_rearm():
    detector = GestureHysteresis(
        close_ratio=0.20,
        reopen_ratio=0.30,
        confirm_frames=3,
        cooldown_seconds=0.5,
    )
    assert detector.update(15, 100, now=1.00) is False
    assert detector.update(15, 100, now=1.01) is False
    assert detector.update(15, 100, now=1.02) is True
    assert detector.update(15, 100, now=1.20) is False
    assert detector.update(35, 100, now=1.30) is False
    assert detector.update(15, 100, now=1.60) is False
    assert detector.update(15, 100, now=1.61) is False
    assert detector.update(15, 100, now=1.62) is True


def test_adaptive_smoother_reduces_large_jump_without_freezing():
    smoother = AdaptivePointSmoother(min_alpha=0.2, max_alpha=0.6, speed_for_max=100)
    assert smoother.update([(0, 0)]) == [(0.0, 0.0)]
    point = smoother.update([(100, 0)])[0]
    assert 40 <= point[0] <= 65
    assert point[1] == 0


def test_geometry_gate_rejects_tiny_and_implausible_jump():
    gate = GeometryGate(min_area_ratio=0.01, max_jump_ratio=0.20)
    assert gate.accept([(10, 10), (200, 10), (200, 160), (10, 160)], 640, 480)
    assert not gate.accept([(400, 300), (620, 300), (620, 470), (400, 470)], 640, 480)

    tiny = GeometryGate(min_area_ratio=0.01)
    assert not tiny.accept([(1, 1), (3, 1), (3, 3), (1, 3)], 640, 480)


def test_performance_governor_downscales_and_can_recover():
    governor = PerformanceGovernor(target_fps=30, scale=1.0)
    for _ in range(10):
        governor.update(10)
    assert governor.scale < 1.0
    reduced = governor.scale
    for _ in range(10):
        governor.update(60)
    assert governor.scale > reduced


def test_remote_devices_cannot_open_or_stop_pc_camera():
    response = handle_vision_command("STAR, abra o portal visual", allow_actions=False)
    assert response is not None
    assert "não podem ativar remotamente" in response.lower()

    response = handle_vision_command("STAR, feche o portal visual", allow_actions=False)
    assert response is not None
    assert "execução local" in response.lower()


def test_status_and_filter_list_are_read_only_commands():
    status = handle_vision_command("status do star vision", allow_actions=False)
    filters = handle_vision_command("filtros do portal", allow_actions=False)
    assert "STAR Vision Portal V1" in status
    assert "12 filtros" in filters
