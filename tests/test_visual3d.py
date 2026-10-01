"""Testes headless da camada visual 3D (tokens, geometria, widgets)."""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gui import theme, visual3d  # noqa: E402

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
TOKENS = [
    "BG_VOID", "BG_DEEP", "PANEL", "PANEL_EDGE", "TEXT", "MUTED",
    "ORB_CORE", "ORB_MID", "ORB_GLOW",
    "CRYSTAL_BLUE", "CRYSTAL_MID", "CRYSTAL_LILAC", "CRYSTAL_LIGHT", "CRYSTAL_PINK", "CRYSTAL_HI",
    "ACCENT_OK", "ACCENT_WARN", "ACCENT_ERR",
]


def test_theme_tokens_are_valid_hex():
    for name in TOKENS:
        assert HEX.match(getattr(theme, name)), name
    for name in dir(theme):
        value = getattr(theme, name)
        if name.isupper() and isinstance(value, str) and value.startswith("#"):
            assert HEX.match(value), name


def test_theme_has_no_tk_dependency():
    source = (ROOT / "gui" / "theme.py").read_text(encoding="utf-8")
    assert "tkinter" not in source
    source3d = (ROOT / "gui" / "visual3d.py").read_text(encoding="utf-8")
    assert "tkinter" not in source3d


def test_state_colors_have_five_states():
    assert set(theme.STATE_COLORS) == {"neutral", "listening", "thinking", "speaking", "error"}
    for colors in theme.STATE_COLORS.values():
        assert set(colors) == {"primary", "secondary", "glow"}
        assert all(HEX.match(c) for c in colors.values())
    assert set(theme.STATE_MOTION) == set(theme.STATE_COLORS)


def test_mix_endpoints():
    assert theme.mix("#000000", "#ffffff", 0).lower() == "#000000"
    assert theme.mix("#000000", "#ffffff", 1).lower() == "#ffffff"
    assert theme.mix("#000000", "#ffffff", 5).lower() == "#ffffff"


def test_rotations_preserve_length():
    pts = [(1.0, 2.0, 3.0), (-0.5, 0.2, 0.9)]
    for fn in (visual3d.rotate_x, visual3d.rotate_y, visual3d.rotate_z):
        for a, b in zip(pts, fn(pts, 0.77)):
            assert math.isclose(math.dist((0, 0, 0), a), math.dist((0, 0, 0), b), rel_tol=1e-9)


def test_project_returns_2d_plus_depth():
    x, y, z = visual3d.project((10.0, 20.0, 0.0), 100, 100, fov=600)
    assert (x, y, z) == (110.0, 80.0, 0.0)
    far = visual3d.project((10.0, 0.0, 300.0), 0, 0, fov=600)
    near = visual3d.project((10.0, 0.0, -300.0), 0, 0, fov=600)
    assert abs(far[0]) < 10 < abs(near[0])
    assert all(math.isfinite(v) for v in visual3d.project((1, 1, -600), 0, 0, fov=600))


def test_orb_filaments_shape_and_depth_order():
    fil = visual3d.orb_filaments(1.3, n_circles=9, n_pts=48)
    assert len(fil) == 9
    for line in fil:
        assert len(line) == 48
        assert all(len(p) == 3 and all(math.isfinite(c) for c in p) for p in line)
    depths = [sum(p[2] for p in line) / len(line) for line in fil]
    assert depths == sorted(depths, reverse=True)
    low = visual3d.orb_filaments(0.0, n_circles=5, n_pts=32)
    assert len(low) == 5 and all(len(line) == 32 for line in low)


def test_orb_filaments_deterministic():
    assert visual3d.orb_filaments(2.0) == visual3d.orb_filaments(2.0)
    assert visual3d.orb_filaments(2.0) != visual3d.orb_filaments(2.5)


def test_crystal_star_has_eight_crystals_with_faces():
    crystals = visual3d.crystal_star_geometry(0.4)
    assert len(crystals) == 8
    assert sorted(c["crystal_idx"] for c in crystals) == list(range(8))
    assert sum(c["kind"] == "long" for c in crystals) == 4
    for c in crystals:
        assert "verts" in c and "normal_z" in c
        assert len(c["faces"]) == 4
        for face in c["faces"]:
            assert {"verts", "normal_z", "face_idx"} <= set(face)
            assert -1.0 - 1e-9 <= face["normal_z"] <= 1.0 + 1e-9
    depths = [c["depth"] for c in crystals]
    assert depths == sorted(depths, reverse=True)


def test_crystal_star_long_points_are_longer():
    crystals = visual3d.crystal_star_geometry(0.0, tilt=0.0)
    reach = {c["kind"]: max(math.dist((0, 0, 0), v) for v in c["verts"]) for c in crystals}
    assert math.isclose(reach["long"], 1.0, rel_tol=1e-6)
    assert math.isclose(reach["short"], 0.55, rel_tol=1e-6)


def test_lerp_state_numbers_and_colors():
    a = {"speed": 0.0, "primary": "#000000", "name": "a"}
    b = {"speed": 1.0, "primary": "#ffffff", "name": "b"}
    assert visual3d.lerp_state(a, b, 0) == {"speed": 0.0, "primary": "#000000", "name": "a"}
    end = visual3d.lerp_state(a, b, 1)
    assert end["speed"] == 1.0 and end["primary"] == "#ffffff" and end["name"] == "b"
    mid = visual3d.lerp_state(a, b, 0.5)
    assert 0 < mid["speed"] < 1


def test_particle_field_deterministic_and_bounded():
    p1 = visual3d.particle_field(0.0, n=60, seed=42)
    assert p1 == visual3d.particle_field(0.0, n=60, seed=42)
    assert len(p1) == 60
    for part in visual3d.particle_field(3.1, n=60, seed=42):
        assert 0 <= part["x"] <= 1 and 0 <= part["y"] <= 1 and 0 <= part["alpha"] <= 1


def test_config_visual_flags():
    import config
    assert config.VISUAL_3D_ENABLED is True
    assert isinstance(config.VISUAL_3D_FPS, int) and config.VISUAL_3D_FPS > 0
    assert config.VISUAL_3D_QUALITY in {"high", "low"}


def test_state_aliases_cover_avatar_emotions():
    from gui.widgets3d import normalize_state
    for emotion in ("neutral", "thinking", "speaking", "listening"):
        assert normalize_state(emotion) == emotion
    assert normalize_state("unknown") == "neutral"
    assert normalize_state(None) == "neutral"


@pytest.fixture
def tk_root():
    tk = pytest.importorskip("tkinter")
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Sem display para Tk: {exc}")
    root.withdraw()
    yield root
    root.destroy()


def test_widgets_instantiate_render_and_stop(tk_root):
    from gui.widgets3d import CrystalStar3D, StarOrb3D

    orb = StarOrb3D(tk_root, size=160, quality="high")
    orb.pack()
    orb.start(); orb.start()  # idempotente
    assert orb.running
    orb._tick()
    orb.set_state("thinking"); orb._tick()
    assert orb.state == "thinking"
    assert len(orb.find_all()) > 0
    orb.stop(); orb.stop()
    assert not orb.running

    low = StarOrb3D(tk_root, size=48, quality="low", fps=60)
    assert low.fps <= 20 and low.n_circles == 5
    low.render_once()

    star = CrystalStar3D(tk_root, size=120)
    star.pack(); star.start(); star._tick()
    visible = [i for i in star.find_all() if star.type(i) == "polygon" and star.itemcget(i, "state") != "hidden"]
    assert visible
    star.destroy(); star.destroy()  # destroy seguro/idempotente
    orb.destroy(); low.destroy()
