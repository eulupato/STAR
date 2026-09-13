"""Integração incremental das próximas capacidades da STAR sobre a Foundation V1.9."""
from __future__ import annotations

import json
import re

from core.cognition_runtime import CognitiveRuntime
from core.goal_engine import GoalEngine
from core.guardian import Guardian
from core.mdrives import MDriveRegistry
from core.ocr import OCREngine, OCRUnavailable
from core.operator_index import FileIndex
from core.research_hub import ResearchHub
from core.scientific_graph import ScientificGraphIndexer
from core.scientific_simulation import ScientificSimulationEngine
from core.semantic_rag import HybridSemanticRAG
from core.senses import SensorFusionBuffer, senses_stats


class IntegratedEvolutionSuite:
    """Facade única para capacidades novas sem substituir STAR MIND/Core."""

    def __init__(self, mind):
        self.mind = mind
        self.guardian = Guardian()
        self.goals = GoalEngine(self.guardian)
        self.cognition = CognitiveRuntime()
        self.mdrives = MDriveRegistry()
        self.semantic_rag = HybridSemanticRAG(self.mind.store, prefer_neural=False)
        self.ocr = OCREngine(self.mind.rag)
        self.research = ResearchHub(self.mind.store)
        self.files = FileIndex()
        self.graph = ScientificGraphIndexer(self.mind.store)
        self.simulation = ScientificSimulationEngine()
        self.senses = SensorFusionBuffer()

    def stats(self) -> dict:
        return {
            "status": "integrated-alpha",
            "cognition_runtime": self.cognition.stats(),
            "goal_engine": self.goals.stats(),
            "guardian": self.guardian.stats(),
            "mdrives": self.mdrives.stats(),
            "semantic_rag": self.semantic_rag.stats(),
            "ocr": self.ocr.stats(),
            "research": self.research.stats(),
            "knowledge_graph": self.graph.stats(),
            "simulation": self.simulation.stats(),
            "operator": self.files.stats(),
            "senses": senses_stats(),
            "principle": "local-first; adapters optional; no autonomous sensitive actions",
        }

    def handle(self, text: str, *, network_enabled: bool = False, allow_actions: bool = True) -> str | None:
        raw = " ".join(str(text or "").strip().split()); lower = raw.lower()
        if raw:
            self.cognition.observe("user_input", raw, relevance=0.7, novelty=0.5, user_priority=0.7,
                                   metadata={"network_enabled": bool(network_enabled), "local_action": bool(allow_actions)})
        if lower in {"status evolução", "status evolucao", "status evolução star", "status evolution", "status m.drives"}:
            return json.dumps(self.stats(), ensure_ascii=False, indent=2)
        if lower in {"contexto cognitivo", "working context", "contexto ativo"}:
            selected = self.cognition.context.select("", limit=10)
            return "Contexto ativo: vazio." if not selected else "Contexto ativo:\n" + "\n".join(f"- [{x['kind']}] {x['content']} | saliência={x['salience']:.3f}" for x in selected)
        match = re.match(r"^(?:rotear engine|escolher engine|model router)\s+(.+)$", raw, re.I)
        if match:
            route = self.cognition.router.choose(match.group(1).strip(), network_enabled=network_enabled)
            return "Nenhum engine registrado satisfaz essa capacidade nas restrições atuais." if route is None else json.dumps(route, ensure_ascii=False, indent=2)
        if lower in {"listar m.drives", "listar mdrives", "m.drives", "mdrives"}:
            drives = self.mdrives.scan()
            return "M.drives: nenhum instalado." if not drives else "M.drives:\n" + "\n".join(f"- {d['name']} v{d['version']} ({d['entries']} entradas{' | legado' if d['legacy'] else ''})" for d in drives)
        match = re.match(r"^(?:criar objetivo|novo objetivo)\s+([^:]+):\s*(.+)$", raw, re.I)
        if match:
            goal = self.goals.create(match.group(1).strip(), match.group(2).strip())
            return f"Objetivo #{goal['goal_id']} criado: {goal['name']}."
        if lower in {"listar objetivos", "meus objetivos", "objetivos"}:
            goals = self.goals.list()
            return "Nenhum objetivo persistente." if not goals else "Objetivos:\n" + "\n".join(f"- #{g['goal_id']} {g['name']} [{g['status']}] — {g['objective']}" for g in goals)
        match = re.match(r"^(?:pesquisa profunda|pesquisar profundamente|research hub)\s+(.+)$", raw, re.I)
        if match:
            result = self.research.search(match.group(1), network_enabled=network_enabled)
            if not result["ok"]:
                return "Research Hub requer modo ONLINE autorizado." if result.get("reason") == "network_disabled" else json.dumps(result, ensure_ascii=False)
            return "Pesquisa:\n" + "\n".join(f"- [{s['provider']}] {s['title']} — {s.get('doi') or s.get('url') or 'sem identificador'}" for s in result["sources"][:12])
        match = re.match(r"^(?:rag semantico|rag semântico|busca semantica|busca semântica)\s+(.+)$", raw, re.I)
        if match:
            hits = self.semantic_rag.search(match.group(1), top_k=5)
            return "Nenhum trecho indexado." if not hits else "RAG híbrido:\n" + "\n".join(f"- {h['title']} | score={h['score']:.3f}: {h['content'][:240]}" for h in hits)
        match = re.match(r"^ocr\s+(.+\.pdf)$", raw, re.I)
        if match:
            decision = self.guardian.authorize("read.files", remote=not allow_actions, confirmed=allow_actions, subject=match.group(1))
            if not decision.allowed:
                return f"OCR bloqueado pelo Guardian: {decision.reason}."
            try:
                result = self.ocr.ingest_pdf(match.group(1))
                return f"PDF ingerido: {result['document_id']} | OCR={result['ocr_used']} | páginas OCR={result['ocr_pages']}."
            except OCRUnavailable as exc:
                return str(exc)
        match = re.match(r"^(?:indexar arquivos|indexar pasta)\s+(.+)$", raw, re.I)
        if match:
            decision = self.guardian.authorize("read.files", remote=not allow_actions, confirmed=allow_actions, subject=match.group(1))
            if not decision.allowed:
                return f"Indexação bloqueada pelo Guardian: {decision.reason}."
            result = self.files.index(match.group(1))
            return f"Índice local atualizado: {result['indexed']} arquivo(s), {result['skipped']} ignorado(s)."
        if lower in {"indexar grafo científico", "indexar grafo cientifico", "materializar grafo curricular"}:
            if not allow_actions:
                return "Indexação do Knowledge Graph exige ação local autorizada."
            result = self.graph.index_curriculum()
            return (f"Knowledge Graph atualizado: {result['themes']} temas, {result['concepts']} conceitos, "
                    f"{result['edges_touched']} relações taxonômicas tocadas.")
        if lower in {"simular órbita", "simular orbita", "simulação orbital", "simulacao orbital"}:
            result = self.simulation.two_body_orbit()
            return ("Simulação orbital 2-corpos concluída: "
                    f"{len(result['times'])} passos | drift relativo de energia={result['relative_energy_drift']:.3e}.")
        if lower in {"simular pêndulo", "simular pendulo", "simulação pêndulo", "simulacao pendulo"}:
            result = self.simulation.damped_pendulum()
            final = result["states"][-1]
            return f"Pêndulo não linear concluído: θ_final={final[0]:.6f} rad | ω_final={final[1]:.6f} rad/s."
        return None
