"""BLOCO 27 — corpo, propriocepção e cinemática.

O corpo continua sendo endpoint. B27 descreve/configura/observa e calcula FK/IK;
a execução física pertence a ``BodyActuationExecutor`` e sempre atravessa a
fronteira operacional B01/B33 antes de alcançar um endpoint de hardware.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from math import prod
import re
import socket
import unicodedata
from typing import Any, Iterable

from core.universal_knowledge import UniversalKnowledgeArchitecture


def _clean(v: Any) -> str:
    return " ".join(str(v or "").strip().split())


def _norm(v: Any) -> str:
    text = unicodedata.normalize("NFKD", _clean(v))
    text = "".join(c for c in text if not unicodedata.combining(c)).casefold()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _clamp(v: Any, default=.5) -> float:
    try:
        return max(0.0, min(float(v), 1.0))
    except (TypeError, ValueError):
        return default


def _matmul(a, b):
    rows, cols, shared = len(a), len(b[0]), len(b)
    return [[sum(a[i][k] * b[k][j] for k in range(shared)) for j in range(cols)] for i in range(rows)]


def _identity4():
    return [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def _invert3(matrix):
    a = [list(map(float, row)) + [1.0 if i == j else 0.0 for j in range(3)] for i, row in enumerate(matrix)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-12:
            raise ValueError("jacobiano singular")
        a[col], a[pivot] = a[pivot], a[col]
        scale = a[col][col]
        a[col] = [value / scale for value in a[col]]
        for row in range(3):
            if row == col:
                continue
            factor = a[row][col]
            a[row] = [a[row][j] - factor * a[col][j] for j in range(6)]
    return [row[3:] for row in a]


DOMAINS = {
    "kinematics": ("position", "velocity", "acceleration", "trajectory", "frame", "transform", "forward_kinematics", "inverse_kinematics", "constraint", "uncertainty"),
    "orientation": ("roll", "pitch", "yaw", "quaternion", "gravity_reference", "heading", "pose", "frame_alignment", "drift", "uncertainty"),
    "movement": ("commanded_motion", "observed_motion", "motion_state", "direction", "speed", "stability", "collision_candidate", "reach", "locomotion", "stop"),
    "energy": ("battery", "voltage", "current", "power", "consumption", "thermal", "reserve", "charging", "energy_limit", "unknown"),
    "sensors": ("encoder", "imu", "force", "torque", "proximity", "temperature", "current_sensor", "camera_reference", "sensor_health", "fusion"),
    "joints": ("joint", "angle", "velocity", "torque", "range", "limit", "backlash", "load", "joint_state", "fault"),
    "servos": ("servo", "target", "feedback", "load", "temperature", "limit", "health", "latency", "controller_reference", "fault"),
    "dimensions": ("length", "width", "height", "mass", "center_of_mass", "reach_envelope", "clearance", "geometry", "payload", "uncertainty"),
    "calibration": ("zero", "offset", "scale", "alignment", "bias", "drift", "reference", "timestamp", "quality", "recalibration"),
    "hardware": ("endpoint", "device", "bus", "controller", "driver_reference", "capability", "availability", "health", "boundary", "disconnect"),
}
LENSES = ("concept", "state", "measurement", "relation", "limit", "risk", "calibration", "prediction", "uncertainty", "interaction")
AXES = (("body", tuple(str(i) for i in range(10))), ("state", tuple(str(i) for i in range(10))), ("context", tuple(str(i) for i in range(10))), ("confidence", tuple(str(i) for i in range(10))), ("temporal", tuple(str(i) for i in range(10))), ("interaction", tuple(str(i) for i in range(10))))
CANONICAL_NODES = len(DOMAINS) * 10 * len(LENSES)
VARIANTS_PER_NODE = prod(len(x) for _, x in AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE
if CANONICAL_NODES != 1000 or VARIANTS_PER_NODE != 1_000_000 or ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("escala B27 inválida")


class TcpJsonBodyEndpoint:
    """Adapter real e leve para controladores robóticos TCP/JSON-line."""

    MAX_RESPONSE = 256 * 1024

    def __init__(self, host: str, port: int, *, timeout: float = 2.0, token: str | None = None):
        self.host = str(host or "").strip()
        self.port = int(port)
        self.timeout = max(0.1, min(float(timeout), 30.0))
        self.token = str(token or "").strip() or None
        if not self.host or not 1 <= self.port <= 65535:
            raise ValueError("endpoint corporal TCP inválido")

    def _request(self, op: str, payload=None) -> dict:
        request = {"op": str(op), "payload": payload or {}}
        if self.token:
            request["token"] = self.token
        wire = (json.dumps(request, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.settimeout(self.timeout)
            sock.sendall(wire)
            chunks, total = [], 0
            while total < self.MAX_RESPONSE:
                chunk = sock.recv(min(8192, self.MAX_RESPONSE - total))
                if not chunk:
                    break
                chunks.append(chunk); total += len(chunk)
                if b"\n" in chunk:
                    break
        raw = b"".join(chunks).split(b"\n", 1)[0]
        if not raw:
            raise OSError("endpoint corporal não respondeu")
        result = json.loads(raw.decode("utf-8"))
        if not isinstance(result, dict):
            raise ValueError("resposta corporal inválida")
        if result.get("ok") is False:
            raise RuntimeError(str(result.get("error") or "endpoint recusou operação"))
        return result

    def read_proprioception(self) -> dict:
        result = self._request("read_proprioception")
        state = result.get("state", result.get("payload", result))
        if not isinstance(state, dict):
            raise ValueError("endpoint não devolveu estado proprioceptivo")
        return state

    def execute_motion(self, command: dict) -> dict:
        if not isinstance(command, dict) or not command:
            raise ValueError("comando corporal vazio")
        return self._request("execute_motion", command)

    def health(self) -> dict:
        return self._request("health")


class BodyProprioception:
    NAMESPACE = "B27"
    MAX_JOINTS = 256
    MAX_SENSORS = 256

    def __init__(self, knowledge: UniversalKnowledgeArchitecture, *, physical_world=None, perception=None, operational_boundary=None):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.physical_world = physical_world
        self.perception = perception
        self.operational_boundary = operational_boundary
        self._config = {}
        self._state = {}
        self._calibration = {}
        self._endpoint = None
        knowledge.register_namespace(
            "B27", "BLOCO 27 — CORPO E PROPRIOCEPÇÃO", logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/body_proprioception.py",
            metadata={"materialization": "on-demand", "body_is_endpoint": True, "body_is_star_identity": False,
                      "direct_actuation": False, "sensor_fusion": "B25", "default_deny": True,
                      "forward_kinematics": True, "inverse_kinematics": "numerical-dls"},
        )

    def configure(self, *, body_id: str, dimensions: dict | None = None, joints: Iterable[dict] = (), servos: Iterable[dict] = (), sensors: Iterable[dict] = (), limits: dict | None = None, hardware: dict | None = None) -> dict:
        body_id = _clean(body_id)
        if not body_id:
            raise ValueError("body_id obrigatório")
        js = [deepcopy(x) for x in joints if isinstance(x, dict)][:self.MAX_JOINTS]
        ss = [deepcopy(x) for x in servos if isinstance(x, dict)][:self.MAX_JOINTS]
        sns = [deepcopy(x) for x in sensors if isinstance(x, dict)][:self.MAX_SENSORS]
        self._config = {"body_id": body_id, "dimensions": deepcopy(dimensions or {}), "joints": js,
                        "servos": ss, "sensors": sns, "limits": deepcopy(limits or {}),
                        "hardware": deepcopy(hardware or {}), "body_is_endpoint": True}
        return deepcopy(self._config)

    def attach_endpoint(self, endpoint: Any) -> None:
        self._endpoint = endpoint

    def detach_endpoint(self) -> None:
        self._endpoint = None

    def update_proprioception(self, observation: dict | None = None, *, source: str = "body_endpoint", **fields) -> dict:
        if observation is None:
            observation = fields
        elif fields:
            observation = {**observation, **fields}
        if not isinstance(observation, dict):
            raise TypeError("observation deve ser dict")
        timestamp = _clean(observation.get("timestamp")) or datetime.now(timezone.utc).isoformat()
        state = {
            "timestamp": timestamp,
            "position": deepcopy(observation.get("position")),
            "orientation": deepcopy(observation.get("orientation")),
            "movement": deepcopy(observation.get("movement")),
            "energy": deepcopy(observation.get("energy")),
            "joints": deepcopy(list(observation.get("joints") or ()))[:self.MAX_JOINTS],
            "servos": deepcopy(list(observation.get("servos") or ()))[:self.MAX_JOINTS],
            "sensors": deepcopy(list(observation.get("sensors") or ()))[:self.MAX_SENSORS],
            "confidence": _clamp(observation.get("confidence"), .5), "source": _clean(source),
            "fabricated": False, "operational_authorization": False,
        }
        self._state = state
        if self.perception is not None:
            summary = f"body pose/state update: position={state['position']} orientation={state['orientation']} movement={state['movement']}"
            self.perception.ingest(
                "sensor",
                {"content": summary, "timestamp": timestamp, "confidence": state["confidence"],
                 "entities": [self._config.get("body_id", "body")],
                 "event_key": f"body-proprioception:{timestamp}",
                 "attributes": {"block": "B27", "physical_endpoint": self._endpoint is not None}},
                source=source,
            )
        return deepcopy(state)

    def calibrate(self, calibration: dict, *, source: str, reference: str = "") -> dict:
        if not isinstance(calibration, dict) or not calibration:
            raise ValueError("calibração vazia")
        self._calibration = {"values": deepcopy(calibration), "source": _clean(source), "reference": _clean(reference),
                             "timestamp": datetime.now(timezone.utc).isoformat(), "applied_to_hardware": False}
        return deepcopy(self._calibration)

    def poll_endpoint(self) -> dict:
        if self._endpoint is None or not hasattr(self._endpoint, "read_proprioception"):
            return {"available": False, "state": None, "fabricated": False}
        try:
            raw = self._endpoint.read_proprioception()
        except (AttributeError, OSError, RuntimeError, ValueError, json.JSONDecodeError):
            return {"available": False, "state": None, "fabricated": False}
        return {"available": True, "state": self.update_proprioception(raw, source="body_endpoint"), "fabricated": False}

    @staticmethod
    def _joint_spec(joint: dict) -> dict:
        joint_type = str(joint.get("type") or "revolute").strip().lower()
        if joint_type not in {"revolute", "prismatic", "fixed"}:
            raise ValueError("joint type deve ser revolute/prismatic/fixed")
        return {
            "type": joint_type,
            "a": float(joint.get("a", 0.0)), "alpha": float(joint.get("alpha", 0.0)),
            "d": float(joint.get("d", 0.0)), "theta_offset": float(joint.get("theta_offset", 0.0)),
            "min": None if joint.get("min") is None else float(joint.get("min")),
            "max": None if joint.get("max") is None else float(joint.get("max")),
            "name": str(joint.get("name") or "joint"),
        }

    @staticmethod
    def _dh(a: float, alpha: float, d: float, theta: float):
        ct, st, ca, sa = math.cos(theta), math.sin(theta), math.cos(alpha), math.sin(alpha)
        return [[ct, -st * ca, st * sa, a * ct],
                [st, ct * ca, -ct * sa, a * st],
                [0.0, sa, ca, d],
                [0.0, 0.0, 0.0, 1.0]]

    def forward_kinematics(self, joint_values: Iterable[float]) -> dict:
        specs = [self._joint_spec(j) for j in self._config.get("joints", ())]
        values = [float(value) for value in joint_values]
        movable = sum(1 for spec in specs if spec["type"] != "fixed")
        if len(values) != movable:
            raise ValueError(f"FK requer {movable} valores de juntas")
        transform = _identity4(); index = 0; frames = []
        for spec in specs:
            value = 0.0 if spec["type"] == "fixed" else values[index]
            if spec["type"] != "fixed":
                index += 1
                if spec["min"] is not None and value < spec["min"] - 1e-9:
                    raise ValueError(f"{spec['name']} abaixo do limite")
                if spec["max"] is not None and value > spec["max"] + 1e-9:
                    raise ValueError(f"{spec['name']} acima do limite")
            theta = spec["theta_offset"] + (value if spec["type"] == "revolute" else 0.0)
            d = spec["d"] + (value if spec["type"] == "prismatic" else 0.0)
            transform = _matmul(transform, self._dh(spec["a"], spec["alpha"], d, theta))
            frames.append(deepcopy(transform))
        x, y, z = transform[0][3], transform[1][3], transform[2][3]
        pitch = math.atan2(-transform[2][0], math.sqrt(transform[0][0] ** 2 + transform[1][0] ** 2))
        roll = math.atan2(transform[2][1], transform[2][2])
        yaw = math.atan2(transform[1][0], transform[0][0])
        return {"transform": transform, "frames": frames, "position": {"x": x, "y": y, "z": z},
                "orientation_rpy": {"roll": roll, "pitch": pitch, "yaw": yaw},
                "joint_values": values, "executed": False}

    def inverse_kinematics(self, target: dict, *, initial: Iterable[float] | None = None, tolerance: float = 1e-4, max_iterations: int = 120, damping: float = 1e-2) -> dict:
        specs = [self._joint_spec(j) for j in self._config.get("joints", ()) if self._joint_spec(j)["type"] != "fixed"]
        n = len(specs)
        if n == 0:
            raise ValueError("IK requer juntas móveis configuradas")
        target_vec = [float(target[k]) for k in ("x", "y", "z")]
        q = list(map(float, initial)) if initial is not None else [0.0] * n
        if len(q) != n:
            raise ValueError(f"IK requer {n} valores iniciais")
        tolerance = max(1e-8, float(tolerance)); iterations = max(1, min(int(max_iterations), 500)); damping = max(1e-6, float(damping))

        def position(values):
            pose = self.forward_kinematics(values)["position"]
            return [pose["x"], pose["y"], pose["z"]]

        converged = False; residual = float("inf")
        for iteration in range(iterations):
            current = position(q); error = [target_vec[i] - current[i] for i in range(3)]
            residual = math.sqrt(sum(v * v for v in error))
            if residual <= tolerance:
                converged = True; break
            eps = 1e-5
            jac = [[0.0] * n for _ in range(3)]
            for j in range(n):
                shifted = q[:]; shifted[j] += eps
                shifted_pos = position(shifted)
                for row in range(3):
                    jac[row][j] = (shifted_pos[row] - current[row]) / eps
            jj_t = [[sum(jac[r][k] * jac[c][k] for k in range(n)) + (damping * damping if r == c else 0.0) for c in range(3)] for r in range(3)]
            try:
                inv = _invert3(jj_t)
            except ValueError:
                break
            temp = [sum(inv[r][c] * error[c] for c in range(3)) for r in range(3)]
            delta = [sum(jac[r][j] * temp[r] for r in range(3)) for j in range(n)]
            for j, spec in enumerate(specs):
                q[j] += max(-0.25, min(delta[j], 0.25))
                if spec["min"] is not None:
                    q[j] = max(q[j], spec["min"])
                if spec["max"] is not None:
                    q[j] = min(q[j], spec["max"])
        pose = self.forward_kinematics(q)
        return {"converged": converged, "iterations": iteration + 1, "residual": residual,
                "joint_values": q, "pose": pose, "target": deepcopy(target), "executed": False,
                "solver": "damped-least-squares-position"}

    def request_motion(self, command: dict, *, permission: bool = False, capability: bool = False, safety_ok: bool = False, authorization_source: str | None = None) -> dict:
        if self.operational_boundary is not None:
            boundary = self.operational_boundary.evaluate(
                f"body motion: {_clean(command)}", permission=permission, capability=capability,
                safety_ok=safety_ok, authorization_source=authorization_source,
            )
        else:
            boundary = {"can_act": bool(permission and capability and safety_ok)}
        return {"command": deepcopy(command), "boundary": boundary,
                "eligible_for_separate_endpoint_execution": bool(boundary.get("can_act")),
                "executed": False, "body_module_actuates_hardware": False}

    def state(self) -> dict:
        return {"configuration": deepcopy(self._config), "proprioception": deepcopy(self._state),
                "calibration": deepcopy(self._calibration), "endpoint_available": self._endpoint is not None}

    def stats(self) -> dict:
        return {"status": "experimental-integrated", "namespace": self.knowledge.store.get_namespace("B27"),
                "addressable_contents": ADDRESSABLE_CONTENTS, "body_is_endpoint": True, "direct_actuation": False,
                "endpoint_available": self._endpoint is not None, "forward_kinematics": True,
                "inverse_kinematics": "damped-least-squares-position"}

    def handle(self, text: str) -> str | None:
        if _clean(text).casefold() in {"status bloco 27", "status corpo", "status propriocepção", "status propriocepcao"}:
            return (f"🤖 BLOCO 27 — CORPO/PROPRIOCEPÇÃO: {ADDRESSABLE_CONTENTS} conhecimentos endereçáveis | "
                    f"endpoint={'CONECTADO' if self._endpoint is not None else 'AUSENTE'} | FK/IK=ATIVOS | atuação direta=NÃO.")
        return None


class BodyActuationExecutor:
    """Única ponte de movimento: gate explícito -> endpoint -> observação B27."""

    def __init__(self, body: BodyProprioception, *, max_audit: int = 128):
        self.body = body
        self.audit = deque(maxlen=max(16, min(int(max_audit), 512)))

    def execute(self, command: dict, *, permission: bool, capability: bool, safety_ok: bool, authorization_source: str | None) -> dict:
        decision = self.body.request_motion(
            command, permission=permission, capability=capability, safety_ok=safety_ok,
            authorization_source=authorization_source,
        )
        record = {"timestamp": datetime.now(timezone.utc).isoformat(), "command": deepcopy(command),
                  "boundary": deepcopy(decision.get("boundary")), "executed": False}
        endpoint = self.body._endpoint
        if not decision["eligible_for_separate_endpoint_execution"]:
            record["reason"] = "boundary_denied"; self.audit.append(record); return deepcopy(record)
        if endpoint is None or not hasattr(endpoint, "execute_motion"):
            record["reason"] = "endpoint_unavailable"; self.audit.append(record); return deepcopy(record)
        try:
            result = endpoint.execute_motion(deepcopy(command))
            record.update({"executed": True, "result": deepcopy(result), "reason": "endpoint_executed"})
            # Observa o resultado real quando o controlador também oferece leitura.
            self.body.poll_endpoint()
        except (OSError, RuntimeError, ValueError, AttributeError, json.JSONDecodeError) as exc:
            record.update({"executed": False, "reason": "endpoint_error", "error": f"{type(exc).__name__}: {exc}"[:240]})
        self.audit.append(record)
        return deepcopy(record)

    def recent(self, limit: int = 20) -> list[dict]:
        return [deepcopy(item) for item in list(self.audit)[-max(1, min(int(limit), 100)):]]
