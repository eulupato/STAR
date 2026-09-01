"""Capability Registry da STAR MIND."""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Capability:
    name: str
    domain: str
    description: str
    enabled: bool = True
    requires_network: bool = False

    def to_dict(self):
        return asdict(self)


class CapabilityRegistry:
    def __init__(self):
        self._items: dict[str, Capability] = {}

    def register(self, capability: Capability):
        self._items[capability.name] = capability
        return capability

    def get(self, name: str):
        return self._items.get(str(name))

    def is_available(self, name: str, network_enabled: bool = False) -> bool:
        capability = self.get(name)
        if capability is None or not capability.enabled:
            return False
        if capability.requires_network and not network_enabled:
            return False
        return True

    def list(self, network_enabled: bool = False) -> dict[str, dict]:
        result = {}
        for name, capability in self._items.items():
            data = capability.to_dict()
            data["available"] = self.is_available(name, network_enabled)
            result[name] = data
        return result

    @classmethod
    def defaults(cls):
        registry = cls()
        for capability in (
            Capability("context", "MIND", "Continuidade, entidades e fatos da sessão."),
            Capability("conversation", "EXPRESSION", "Small talk procedural e anti-repetição."),
            Capability("computer_control", "ACTION", "Ações locais e comandos do computador."),
            Capability("math", "KNOWLEDGE", "Cálculo determinístico offline."),
            Capability("universal_search", "KNOWLEDGE", "Busca local em entidades, packs e memória."),
            Capability("legacy_reasoning", "MIND", "Router e Executive consolidados."),
            Capability("internal_knowledge", "KNOWLEDGE", "Conhecimento interno local."),
            Capability("knowledge_packs", "KNOWLEDGE", "Pacotes locais de conhecimento."),
            Capability(
                "network_actions",
                "ACTION",
                "Ações que dependem do modo ONLINE.",
                requires_network=True,
            ),
        ):
            registry.register(capability)
        return registry
