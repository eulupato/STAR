"""Catálogo estruturado compartilhado para blocos cognitivos de escala 1B.

A escala é lógica: 1.000 nós canônicos × 1.000.000 combinações por nó.
Nada aqui materializa 1B de linhas, arquivos ou textos artificiais. Cada bloco
fornece sua taxonomia; variantes são endereçadas e materializadas sob demanda.
"""
from __future__ import annotations

from math import prod
import re
from typing import Mapping, Sequence


class StructuredBillionCatalog:
    """Catálogo determinístico de exatamente 1B de representações endereçáveis."""

    EXPECTED_CANONICAL_NODES = 1_000
    EXPECTED_VARIANTS_PER_NODE = 1_000_000
    EXPECTED_ADDRESSABLE_CONTENTS = 1_000_000_000

    def __init__(
        self,
        *,
        namespace: str,
        domains: Mapping[str, Sequence[str]],
        lenses: Sequence[str],
        axes: Sequence[tuple[str, Sequence[str]]],
        truthfulness_note: str,
    ):
        namespace = str(namespace or "").strip().upper()
        if not re.fullmatch(r"B\d{2}", namespace):
            raise ValueError("namespace de bloco inválido")
        self.namespace = namespace
        self.domains = {str(key): tuple(values) for key, values in domains.items()}
        self.lenses = tuple(lenses)
        self.axes = tuple((str(name), tuple(values)) for name, values in axes)
        self.truthfulness_note = str(truthfulness_note).strip()

        if len(self.domains) != 10:
            raise ValueError("catálogo 1B exige exatamente 10 domínios")
        if any(len(branches) != 10 for branches in self.domains.values()):
            raise ValueError("cada domínio deve possuir exatamente 10 ramos")
        if len(self.lenses) != 10:
            raise ValueError("catálogo 1B exige exatamente 10 lentes")
        if len(self.axes) != 6 or any(len(values) != 10 for _, values in self.axes):
            raise ValueError("catálogo 1B exige 6 eixos com exatamente 10 valores cada")

        self.canonical_nodes = sum(len(v) for v in self.domains.values()) * len(self.lenses)
        self.variants_per_node = prod(len(values) for _, values in self.axes)
        self.addressable_contents = self.canonical_nodes * self.variants_per_node
        if self.canonical_nodes != self.EXPECTED_CANONICAL_NODES:
            raise RuntimeError("catálogo deve manter exatamente 1.000 nós canônicos")
        if self.variants_per_node != self.EXPECTED_VARIANTS_PER_NODE:
            raise RuntimeError("catálogo deve manter exatamente 1.000.000 variantes por nó")
        if self.addressable_contents != self.EXPECTED_ADDRESSABLE_CONTENTS:
            raise RuntimeError("catálogo deve manter exatamente 1B de representações")

    def stats(self) -> dict:
        return {
            "namespace": self.namespace,
            "domains": len(self.domains),
            "branches": sum(len(v) for v in self.domains.values()),
            "lenses": len(self.lenses),
            "canonical_nodes": self.canonical_nodes,
            "variants_per_node": self.variants_per_node,
            "addressable_contents": self.addressable_contents,
            "materialization": "on-demand",
            "prepopulated_rows": 0,
            "truthfulness_note": self.truthfulness_note,
        }

    def content_id(self, node_index: int, variant_index: int) -> str:
        node_index = int(node_index)
        variant_index = int(variant_index)
        if not 0 <= node_index < self.canonical_nodes:
            raise IndexError(node_index)
        if not 0 <= variant_index < self.variants_per_node:
            raise IndexError(variant_index)
        absolute = node_index * self.variants_per_node + variant_index + 1
        return f"{self.namespace}-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(
            rf"{re.escape(self.namespace)}-(\d{{10}})",
            str(identifier or "").strip().upper(),
        )
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= self.addressable_contents:
            return None

        node_index, variant_index = divmod(absolute - 1, self.variants_per_node)
        domain_index, within_domain = divmod(node_index, 100)
        branch_index, lens_index = divmod(within_domain, 10)
        domain = tuple(self.domains)[domain_index]
        branch = self.domains[domain][branch_index]

        remainder = variant_index
        decoded: dict[str, str] = {}
        for name, values in reversed(self.axes):
            remainder, index = divmod(remainder, len(values))
            decoded[name] = values[index]
        decoded = {name: decoded[name] for name, _ in self.axes}

        return {
            "id": f"{self.namespace}-{absolute:010d}",
            "namespace": self.namespace,
            "node_index": node_index,
            "variant_index": variant_index,
            "domain": domain,
            "branch": branch,
            "lens": self.lenses[lens_index],
            **decoded,
            "materialized": True,
            "source_of_truth": False,
        }
