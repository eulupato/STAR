"""Motor 3D procedural da STAR (somente stdlib, sem Tk).

Convenções de coordenadas:
- x para a direita, y para cima, z para *dentro* da tela (z maior = mais longe).
- ``project`` devolve coordenadas de tela (y para baixo) e mantém ``z`` para
  ordenação de profundidade (painter's algorithm: desenhar do maior z ao menor).

Tudo é determinístico em função de ``t`` para ser testável sem display.
"""
from __future__ import annotations

import math
import random
from typing import Iterable, Sequence

Point3 = tuple[float, float, float]

_TAU = math.tau


# --------------------------------------------------------------------------- #
# Transformações básicas
# --------------------------------------------------------------------------- #
def rotate_y(points: Iterable[Point3], angle: float) -> list[Point3]:
    c, s = math.cos(angle), math.sin(angle)
    return [(x * c + z * s, y, -x * s + z * c) for x, y, z in points]


def rotate_x(points: Iterable[Point3], angle: float) -> list[Point3]:
    c, s = math.cos(angle), math.sin(angle)
    return [(x, y * c - z * s, y * s + z * c) for x, y, z in points]


def rotate_z(points: Iterable[Point3], angle: float) -> list[Point3]:
    c, s = math.cos(angle), math.sin(angle)
    return [(x * c - y * s, x * s + y * c, z) for x, y, z in points]


def project(point: Sequence[float], cx: float, cy: float, fov: float = 600) -> tuple[float, float, float]:
    """Projeção em perspectiva. ``point`` já em unidades de pixel.

    Retorna ``(x2d, y2d, z)``; y de tela cresce para baixo.
    """
    x, y, z = point
    denom = fov + z
    if denom <= 1e-6:
        denom = 1e-6
    f = fov / denom
    return cx + x * f, cy - y * f, z


def _mean_z(points: Sequence[Point3]) -> float:
    return sum(p[2] for p in points) / len(points) if points else 0.0


def _sub(a: Point3, b: Point3) -> Point3:
    return a[0] - b[0], a[1] - b[1], a[2] - b[2]


def _cross(a: Point3, b: Point3) -> Point3:
    return a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]


def _dot(a: Point3, b: Point3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _normalize(v: Point3) -> Point3:
    n = math.sqrt(_dot(v, v))
    return (0.0, 0.0, 0.0) if n < 1e-12 else (v[0] / n, v[1] / n, v[2] / n)


# --------------------------------------------------------------------------- #
# Orb de filamentos
# --------------------------------------------------------------------------- #
def orb_filaments(
    t: float,
    n_circles: int = 9,
    n_pts: int = 48,
    wobble: float = 0.05,
    radius: float = 1.0,
) -> list[list[Point3]]:
    """Great circles inclinados com velocidades próprias + wobble senoidal.

    Retorna ``n_circles`` polilinhas (cada uma com ``n_pts`` pontos, fechamento
    implícito) ordenadas do mais distante para o mais próximo (z médio desc.).
    """
    n_circles = max(0, int(n_circles))
    n_pts = max(3, int(n_pts))
    filaments: list[list[Point3]] = []
    for i in range(n_circles):
        golden = i * 2.399963  # ângulo áureo → distribuição uniforme dos planos
        tilt = 0.35 + 1.05 * ((i * 0.618034) % 1.0)
        speed = 1.0 + 0.11 * math.sin(i * 1.7)
        phase = golden + t * speed
        pts: list[Point3] = []
        for k in range(n_pts):
            u = _TAU * k / n_pts
            r = radius * (1.0 + wobble * math.sin(3 * u + t * 1.3 + i) + 0.5 * wobble * math.sin(5 * u - t * 0.9 + 2 * i))
            pts.append((r * math.cos(u), r * math.sin(u), 0.0))
        pts = rotate_x(pts, tilt)
        pts = rotate_z(pts, golden * 0.5)
        pts = rotate_y(pts, phase)
        filaments.append(pts)
    filaments.sort(key=_mean_z, reverse=True)
    return filaments


# --------------------------------------------------------------------------- #
# Estrela cristalina de 8 pontas
# --------------------------------------------------------------------------- #
LIGHT_DIR: Point3 = _normalize((-0.45, 0.6, -0.75))  # esquerda, cima, em direção ao observador


def _crystal_vertices(angle: float, r_in: float, r_tip: float, width: float, thick: float) -> list[Point3]:
    """Bipirâmide alongada no plano XY apontando para ``angle``.

    Vértices: 0=base interna, 1=ponta, 2=lado esq., 3=frente (−z), 4=lado dir., 5=trás (+z).
    """
    dx, dy = math.cos(angle), math.sin(angle)
    px, py = -dy, dx  # perpendicular no plano
    mid = r_in + (r_tip - r_in) * 0.32
    mx, my = dx * mid, dy * mid
    return [
        (dx * r_in, dy * r_in, 0.0),
        (dx * r_tip, dy * r_tip, 0.0),
        (mx + px * width, my + py * width, 0.0),
        (mx, my, -thick),
        (mx - px * width, my - py * width, 0.0),
        (mx, my, thick),
    ]


# 4 facetas por cristal (quads em torno do eixo longo → aresta central visível)
_CRYSTAL_FACES = ((0, 2, 1, 3), (0, 3, 1, 4), (0, 4, 1, 5), (0, 5, 1, 2))


def crystal_star_geometry(
    t: float,
    n_long: int = 4,
    n_short: int = 4,
    r_long: float = 1.0,
    r_short: float = 0.55,
    tilt: float = 0.28,
) -> list[dict]:
    """Geometria da estrela de 8 pontas girando em Y.

    Retorna uma lista de cristais ordenados por profundidade (mais distante
    primeiro). Cada cristal: ``{"crystal_idx", "kind", "verts", "normal_z",
    "depth", "faces"}``; cada face: ``{"verts", "normal_z", "light",
    "face_idx", "depth"}`` também ordenadas do fundo para a frente.
    ``normal_z`` > 0 significa faceta voltada para o observador.
    """
    specs = []
    for i in range(max(0, int(n_long))):
        specs.append(("long", _TAU * i / max(1, n_long) + math.pi / 2, 0.10, r_long, 0.105, 0.07))
    for i in range(max(0, int(n_short))):
        specs.append(("short", _TAU * i / max(1, n_short) + math.pi / 4, 0.16, r_short, 0.085, 0.06))

    yaw = t
    pitch = tilt * math.sin(t * 0.37)
    crystals = []
    for idx, (kind, ang, r_in, r_tip, width, thick) in enumerate(specs):
        verts = _crystal_vertices(ang, r_in * r_long, r_tip, width * r_long, thick * r_long)
        verts = rotate_y(rotate_x(verts, pitch), yaw)
        center = tuple(sum(v[k] for v in verts) / len(verts) for k in range(3))
        faces = []
        for f_idx, face in enumerate(_CRYSTAL_FACES):
            fv = [verts[j] for j in face]
            normal = _normalize(_cross(_sub(fv[2], fv[0]), _sub(fv[3], fv[1])))
            fc = tuple(sum(v[k] for v in fv) / 4 for k in range(3))
            if _dot(normal, _sub(fc, center)) < 0:
                normal = (-normal[0], -normal[1], -normal[2])
            faces.append({
                "verts": fv,
                "normal_z": -normal[2],
                "light": max(0.0, _dot(normal, LIGHT_DIR)),
                "face_idx": f_idx,
                "depth": _mean_z(fv),
            })
        faces.sort(key=lambda f: f["depth"], reverse=True)
        crystals.append({
            "crystal_idx": idx,
            "kind": kind,
            "verts": verts,
            "normal_z": sum(f["normal_z"] for f in faces) / len(faces),
            "depth": _mean_z(verts),
            "faces": faces,
        })
    crystals.sort(key=lambda c: c["depth"], reverse=True)
    return crystals


# --------------------------------------------------------------------------- #
# Transição de estado e partículas
# --------------------------------------------------------------------------- #
def _lerp_value(a, b, t: float):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return a + (b - a) * t
    if isinstance(a, str) and isinstance(b, str) and len(a) == 7 == len(b) and a.startswith("#") and b.startswith("#"):
        try:
            ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
            cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
        except ValueError:
            return b if t >= 0.5 else a
        return "#" + "".join(f"{int(round(x + (y - x) * t)):02x}" for x, y in zip(ca, cb))
    if isinstance(a, dict) and isinstance(b, dict):
        return lerp_state(a, b, t)
    return b if t >= 0.5 else a


def lerp_state(state_a: dict, state_b: dict, t: float) -> dict:
    """Interpola dois dicionários de parâmetros (números e cores hex)."""
    t = max(0.0, min(1.0, float(t)))
    t = t * t * (3 - 2 * t)  # smoothstep
    out = {}
    for key in set(state_a) | set(state_b):
        if key in state_a and key in state_b:
            out[key] = _lerp_value(state_a[key], state_b[key], t)
        else:
            out[key] = state_b.get(key, state_a.get(key))
    return out


def particle_field(t: float, n: int = 60, seed: int = 42) -> list[dict]:
    """Partículas em posições fixas (0..1) com cintilação senoidal lenta."""
    rng = random.Random(seed)
    out = []
    for _ in range(max(0, int(n))):
        x, y = rng.random(), rng.random()
        size = 0.6 + rng.random() * 1.6
        phase = rng.random() * _TAU
        freq = 0.4 + rng.random() * 1.2
        base = 0.25 + rng.random() * 0.45
        alpha = base + (1 - base) * 0.5 * (1 + math.sin(t * freq + phase))
        out.append({"x": x, "y": y, "r": size, "alpha": max(0.0, min(1.0, alpha))})
    return out
