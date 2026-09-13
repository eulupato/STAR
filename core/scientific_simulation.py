"""Simulações científicas locais, leves e auditáveis para a STAR.

Complementa `core.labs.SimulationLab` com modelos numéricos úteis sem adicionar
SciPy ao boot. Usa NumPy já presente. Modelos são educacionais/engenharia inicial e
não substituem solvers validados de CFD/FEA/SPICE/relatividade numérica.
"""
from __future__ import annotations

import math
import numpy as np


class ScientificSimulationEngine:
    MAX_STEPS = 200_000

    @staticmethod
    def _steps(dt: float, duration: float) -> int:
        dt, duration = float(dt), float(duration)
        if dt <= 0 or duration <= 0:
            raise ValueError("dt e duration devem ser positivos")
        steps = int(math.ceil(duration / dt)) + 1
        if steps > ScientificSimulationEngine.MAX_STEPS:
            raise ValueError("simulação excede o limite de passos")
        return steps

    def rk4_system(self, derivative, initial_state, *, dt: float, duration: float, params=None) -> dict:
        steps = self._steps(dt, duration)
        state = np.asarray(initial_state, dtype=float)
        if state.ndim != 1 or state.size == 0:
            raise ValueError("initial_state deve ser vetor 1D não vazio")
        times = np.linspace(0.0, float(dt) * (steps - 1), steps)
        states = np.empty((steps, state.size), dtype=float); states[0] = state
        params = params or {}
        for i in range(1, steps):
            t = times[i - 1]; y = states[i - 1]; h = float(dt)
            k1 = np.asarray(derivative(t, y, params), dtype=float)
            k2 = np.asarray(derivative(t + h/2, y + h*k1/2, params), dtype=float)
            k3 = np.asarray(derivative(t + h/2, y + h*k2/2, params), dtype=float)
            k4 = np.asarray(derivative(t + h, y + h*k3, params), dtype=float)
            if any(k.shape != y.shape for k in (k1, k2, k3, k4)):
                raise ValueError("derivative deve retornar vetor com mesmo formato do estado")
            states[i] = y + h * (k1 + 2*k2 + 2*k3 + k4) / 6
            if not np.all(np.isfinite(states[i])):
                raise FloatingPointError("estado numérico não finito")
        return {"times": times.tolist(), "states": states.tolist(), "method": "RK4-vector"}

    def two_body_orbit(self, *, r0=(7_000_000.0, 0.0), v0=(0.0, 7_546.0),
                       mu=3.986004418e14, dt=10.0, duration=5400.0) -> dict:
        mu = float(mu)
        if mu <= 0:
            raise ValueError("mu deve ser positivo")
        def derivative(_t, state, params):
            x, y, vx, vy = state; radius = math.hypot(x, y)
            if radius <= 0:
                raise ValueError("raio orbital inválido")
            factor = -params["mu"] / radius**3
            return np.array([vx, vy, factor*x, factor*y])
        result = self.rk4_system(derivative, [*r0, *v0], dt=dt, duration=duration, params={"mu": mu})
        first, last = np.asarray(result["states"][0]), np.asarray(result["states"][-1])
        def energy(s):
            radius = math.hypot(s[0], s[1]); speed2 = s[2]**2 + s[3]**2
            return 0.5 * speed2 - mu / radius
        e0, e1 = energy(first), energy(last)
        result.update({"model": "two-body-newtonian-2d", "specific_energy_initial": e0,
                       "specific_energy_final": e1,
                       "relative_energy_drift": abs(e1-e0) / max(abs(e0), 1e-30)})
        return result

    def damped_pendulum(self, *, theta0=0.3, omega0=0.0, length=1.0, damping=0.05,
                        gravity=9.80665, dt=0.01, duration=10.0) -> dict:
        if length <= 0 or gravity <= 0 or damping < 0:
            raise ValueError("parâmetros físicos inválidos")
        def derivative(_t, state, params):
            theta, omega = state
            return np.array([omega, -(params["g"] / params["L"]) * math.sin(theta) - params["b"] * omega])
        result = self.rk4_system(derivative, [theta0, omega0], dt=dt, duration=duration,
                                 params={"g": gravity, "L": length, "b": damping})
        result["model"] = "nonlinear-damped-pendulum"
        return result

    def heat_1d(self, initial, *, alpha=1e-4, dx=0.01, dt=0.1, steps=100,
                left_boundary=None, right_boundary=None) -> dict:
        u = np.asarray(initial, dtype=float).copy()
        if u.ndim != 1 or u.size < 3:
            raise ValueError("initial deve ter pelo menos 3 pontos")
        alpha, dx, dt = float(alpha), float(dx), float(dt); steps = int(steps)
        if alpha <= 0 or dx <= 0 or dt <= 0 or not 1 <= steps <= self.MAX_STEPS:
            raise ValueError("parâmetros numéricos inválidos")
        r = alpha * dt / (dx * dx)
        if r > 0.5:
            raise ValueError("esquema explícito instável: alpha*dt/dx² deve ser <= 0.5")
        left = float(u[0] if left_boundary is None else left_boundary)
        right = float(u[-1] if right_boundary is None else right_boundary)
        snapshots = [u.tolist()]
        sample_every = max(1, steps // 100)
        for step in range(1, steps + 1):
            nxt = u.copy(); nxt[1:-1] = u[1:-1] + r * (u[2:] - 2*u[1:-1] + u[:-2]); nxt[0] = left; nxt[-1] = right; u = nxt
            if step % sample_every == 0 or step == steps:
                snapshots.append(u.tolist())
        return {"model": "heat-equation-1d-explicit", "stability_ratio": r, "final": u.tolist(), "snapshots": snapshots}

    def wave_1d(self, initial_displacement, *, c=1.0, dx=0.01, dt=0.005, steps=100,
                initial_velocity=None) -> dict:
        u0 = np.asarray(initial_displacement, dtype=float)
        if u0.ndim != 1 or u0.size < 3:
            raise ValueError("initial_displacement deve ter pelo menos 3 pontos")
        c, dx, dt, steps = float(c), float(dx), float(dt), int(steps)
        if c <= 0 or dx <= 0 or dt <= 0 or not 1 <= steps <= self.MAX_STEPS:
            raise ValueError("parâmetros numéricos inválidos")
        courant = c * dt / dx
        if courant > 1.0:
            raise ValueError("condição CFL violada: c*dt/dx deve ser <= 1")
        velocity = np.zeros_like(u0) if initial_velocity is None else np.asarray(initial_velocity, dtype=float)
        if velocity.shape != u0.shape:
            raise ValueError("initial_velocity incompatível")
        u_prev = u0.copy(); u = u0.copy(); lam2 = courant**2
        u[1:-1] = u0[1:-1] + dt*velocity[1:-1] + 0.5*lam2*(u0[2:] - 2*u0[1:-1] + u0[:-2])
        u[0] = u[-1] = 0.0
        snapshots = [u0.tolist(), u.tolist()]; sample_every = max(1, steps // 100)
        for step in range(2, steps + 1):
            nxt = np.zeros_like(u); nxt[1:-1] = 2*u[1:-1] - u_prev[1:-1] + lam2*(u[2:] - 2*u[1:-1] + u[:-2]); u_prev, u = u, nxt
            if step % sample_every == 0 or step == steps:
                snapshots.append(u.tolist())
        return {"model": "wave-equation-1d-explicit", "courant": courant, "final": u.tolist(), "snapshots": snapshots}

    def rc_circuit(self, *, resistance=1000.0, capacitance=1e-6, voltage=5.0, dt=1e-4, duration=0.01, initial_voltage=0.0) -> dict:
        r, c = float(resistance), float(capacitance)
        if r <= 0 or c <= 0:
            raise ValueError("R e C devem ser positivos")
        def derivative(_t, state, params):
            return np.array([(params["vin"] - state[0]) / (params["R"] * params["C"])])
        result = self.rk4_system(derivative, [initial_voltage], dt=dt, duration=duration,
                                 params={"vin": float(voltage), "R": r, "C": c})
        result.update({"model": "RC-charge", "time_constant": r*c})
        return result

    @staticmethod
    def stats() -> dict:
        return {"status": "alpha-local", "numpy": True,
                "models": ["vector RK4", "two-body orbit 2D", "damped pendulum", "heat 1D", "wave 1D", "RC circuit"],
                "validation": ["energy drift for orbit", "explicit heat stability", "wave CFL"],
                "not_a_replacement_for": ["validated CFD", "validated FEA", "SPICE", "high-fidelity astrodynamics", "numerical relativity"]}
