"""Ferramentas cognitivas locais da STAR: matemática, simulação, código, RAG e pesquisa."""
from __future__ import annotations

import ast
from dataclasses import dataclass
import json
import math
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
from typing import Callable

from database.cognitive_store import CognitiveStore


class MathLab:
    """CAS local com SymPy e fallback numérico da STAR."""

    _VARIABLES = set("xyz.tabcnmrsuvw")
    _FUNCTIONS = {"sin", "cos", "tan", "asin", "acos", "atan", "exp", "log", "sqrt", "Abs"}

    def __init__(self):
        self.available = False
        self.version = None
        try:
            import sympy as sp
            self.sp = sp
            self.available = True
            self.version = sp.__version__
        except ImportError:
            self.sp = None

    def _parse(self, expression: str):
        if not self.available:
            raise RuntimeError("SymPy não está instalado")
        expression = str(expression).strip().replace("^", "**")
        if len(expression) > 1000 or "__" in expression or not re.fullmatch(r"[A-Za-z0-9+\-*/()., =\s*]+", expression):
            raise ValueError("expressão contém elementos não permitidos")
        identifiers = set(re.findall(r"[A-Za-z]+", expression))
        allowed = self._VARIABLES | self._FUNCTIONS | {"pi", "E"}
        unknown = {x for x in identifiers if x not in allowed and not (len(x) == 1 and x.isalpha())}
        if unknown:
            raise ValueError("identificadores não permitidos: " + ", ".join(sorted(unknown)))
        sp = self.sp
        local = {name: sp.Symbol(name) for name in identifiers if len(name) == 1 and name.isalpha()}
        local.update({"pi": sp.pi, "E": sp.E, "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
                      "asin": sp.asin, "acos": sp.acos, "atan": sp.atan, "exp": sp.exp,
                      "log": sp.log, "sqrt": sp.sqrt, "Abs": sp.Abs})
        from sympy.parsing.sympy_parser import parse_expr
        globals_safe = {"Integer": sp.Integer, "Float": sp.Float, "Rational": sp.Rational, "Symbol": sp.Symbol}
        return parse_expr(expression, local_dict=local, global_dict=globals_safe, evaluate=True)

    def simplify(self, expression: str) -> str:
        return str(self.sp.simplify(self._parse(expression)))

    def solve(self, equation: str, variable: str = "x") -> list[str]:
        sp = self.sp
        variable = variable.strip()
        if not re.fullmatch(r"[A-Za-z]", variable):
            raise ValueError("variável inválida")
        symbol = sp.Symbol(variable)
        if "=" in equation:
            left, right = equation.split("=", 1)
            expr = self._parse(left) - self._parse(right)
        else:
            expr = self._parse(equation)
        return [str(v) for v in sp.solve(expr, symbol)]

    def derivative(self, expression: str, variable: str = "x", order: int = 1) -> str:
        symbol = self.sp.Symbol(variable)
        return str(self.sp.diff(self._parse(expression), symbol, max(1, int(order))))

    def integral(self, expression: str, variable: str = "x") -> str:
        symbol = self.sp.Symbol(variable)
        return str(self.sp.integrate(self._parse(expression), symbol))

    def evaluate(self, expression: str, digits: int = 12) -> str:
        return str(self.sp.N(self._parse(expression), max(2, min(int(digits), 50))))

    def stats(self) -> dict:
        return {"sympy_available": self.available, "sympy_version": self.version}


class SimulationLab:
    """Simulações determinísticas pequenas; evita depender de SciPy no Core."""

    @staticmethod
    def projectile(speed: float, angle_deg: float, *, g: float = 9.80665, height: float = 0.0, steps: int = 101) -> dict:
        speed, angle, g, height = float(speed), math.radians(float(angle_deg)), float(g), float(height)
        if speed < 0 or g <= 0 or not 2 <= int(steps) <= 10000:
            raise ValueError("parâmetros físicos inválidos")
        vx, vy = speed * math.cos(angle), speed * math.sin(angle)
        disc = vy * vy + 2 * g * max(0.0, height)
        flight = (vy + math.sqrt(max(0.0, disc))) / g
        times = [flight * i / (int(steps) - 1) for i in range(int(steps))]
        points = [(t, vx * t, height + vy * t - 0.5 * g * t * t) for t in times]
        return {"flight_time_s": flight, "range_m": vx * flight, "max_height_m": height + max(0.0, vy) ** 2 / (2 * g), "points": points, "assumptions": ["gravidade uniforme", "sem arrasto aerodinâmico", "solo em y=0"]}

    @staticmethod
    def exponential(initial: float, rate: float, duration: float, *, steps: int = 101) -> dict:
        initial, rate, duration = float(initial), float(rate), float(duration)
        if duration < 0 or not 2 <= int(steps) <= 10000:
            raise ValueError("parâmetros inválidos")
        series = []
        for i in range(int(steps)):
            t = duration * i / (int(steps) - 1)
            series.append((t, initial * math.exp(rate * t)))
        return {"initial": initial, "rate": rate, "duration": duration, "final": series[-1][1], "series": series}

    @staticmethod
    def monte_carlo_pi(samples: int = 10000, *, seed: int = 42) -> dict:
        samples = max(100, min(int(samples), 2_000_000))
        rng = random.Random(int(seed))
        inside = 0
        for _ in range(samples):
            x, y = rng.random(), rng.random()
            inside += x * x + y * y <= 1.0
        estimate = 4.0 * inside / samples
        return {"samples": samples, "seed": int(seed), "estimate": estimate, "absolute_error": abs(math.pi - estimate)}

    @staticmethod
    def integrate_ode(func: Callable[[float, float], float], y0: float, t0: float, t1: float, dt: float) -> dict:
        """RK4 escalar para experimentos locais reproduzíveis."""
        t, y, dt = float(t0), float(y0), float(dt)
        t1 = float(t1)
        if dt <= 0 or t1 < t or (t1 - t) / dt > 1_000_000:
            raise ValueError("intervalo ou passo inválido")
        series = [(t, y)]
        while t < t1 - 1e-15:
            h = min(dt, t1 - t)
            k1 = func(t, y)
            k2 = func(t + h / 2, y + h * k1 / 2)
            k3 = func(t + h / 2, y + h * k2 / 2)
            k4 = func(t + h, y + h * k3)
            y += h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
            t += h
            series.append((t, y))
        return {"method": "RK4", "t0": float(t0), "t1": t1, "dt": dt, "final": y, "series": series}


class CodeLab:
    """Execução local limitada para pequenos testes de Python.

    Não é um sandbox de segurança do sistema operacional. O validador bloqueia
    I/O, rede, introspecção e imports perigosos; tarefas não confiáveis ainda
    devem usar o Sandbox/Guardian futuro da STAR.
    """

    SAFE_MODULES = {"math", "statistics", "random", "json", "re", "itertools", "functools", "collections", "decimal", "fractions"}
    FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "input", "globals", "locals", "vars", "getattr", "setattr", "delattr", "__import__", "breakpoint", "help", "dir", "memoryview"}

    def validate(self, code: str) -> dict:
        code = str(code)
        if len(code) > 50_000:
            return {"ok": False, "errors": ["código acima do limite de 50k caracteres"]}
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return {"ok": False, "errors": [f"SyntaxError: {exc}"]}
        errors = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name.split(".")[0] for a in node.names] if isinstance(node, ast.Import) else [(node.module or "").split(".")[0]]
                for name in names:
                    if name not in self.SAFE_MODULES:
                        errors.append(f"import bloqueado: {name}")
            if isinstance(node, ast.Name) and node.id in self.FORBIDDEN_NAMES:
                errors.append(f"nome bloqueado: {node.id}")
            if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
                errors.append(f"atributo privado/dunder bloqueado: {node.attr}")
        return {"ok": not errors, "errors": sorted(set(errors))}

    def run(self, code: str, *, timeout: float = 3.0) -> dict:
        validation = self.validate(code)
        if not validation["ok"]:
            return {"ok": False, "stdout": "", "stderr": "\n".join(validation["errors"]), "returncode": None, "timed_out": False}
        runner = r'''
import builtins, json, math, statistics, random, re, itertools, functools, collections, decimal, fractions
_ALLOWED = {"math","statistics","random","json","re","itertools","functools","collections","decimal","fractions"}
def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    root=name.split('.')[0]
    if root not in _ALLOWED: raise ImportError(f"import bloqueado: {root}")
    return builtins.__import__(name, globals, locals, fromlist, level)
_SAFE = {k:getattr(builtins,k) for k in ("abs","all","any","bool","dict","enumerate","filter","float","int","len","list","map","max","min","next","pow","print","range","repr","reversed","round","set","sorted","str","sum","tuple","zip","Exception","ValueError","TypeError")}
_SAFE["__import__"]=_safe_import
code=json.loads(CODE_JSON)
exec(compile(code,"<star-codelab>","exec"), {"__builtins__":_SAFE})
'''
        payload = runner.replace("CODE_JSON", repr(json.dumps(str(code))))
        try:
            with tempfile.TemporaryDirectory(prefix="star_codelab_") as tmp:
                proc = subprocess.run([sys.executable, "-I", "-S", "-c", payload], cwd=tmp, env={}, text=True, capture_output=True, timeout=max(0.1, min(float(timeout), 10.0)))
            return {"ok": proc.returncode == 0, "stdout": proc.stdout[-20000:], "stderr": proc.stderr[-20000:], "returncode": proc.returncode, "timed_out": False}
        except subprocess.TimeoutExpired as exc:
            return {"ok": False, "stdout": (exc.stdout or "")[-20000:] if isinstance(exc.stdout, str) else "", "stderr": "tempo limite excedido", "returncode": None, "timed_out": True}


@dataclass(frozen=True)
class RetrievalHit:
    chunk_id: int
    title: str
    source: str
    content: str
    score: float | None
    document_id: int
    chunk_index: int
    metadata: dict


class DocumentRAG:
    def __init__(self, store: CognitiveStore | None = None):
        self.store = store or CognitiveStore()

    @staticmethod
    def chunk_text(text: str, *, words_per_chunk: int = 220, overlap: int = 40) -> list[str]:
        words = str(text).split()
        words_per_chunk = max(50, min(int(words_per_chunk), 1000))
        overlap = max(0, min(int(overlap), words_per_chunk // 2))
        if not words:
            return []
        chunks, start = [], 0
        step = words_per_chunk - overlap
        while start < len(words):
            chunk = " ".join(words[start:start + words_per_chunk]).strip()
            if chunk:
                chunks.append(chunk)
            start += step
        return chunks

    def ingest_text(self, text: str, *, source: str, title: str, metadata=None) -> dict:
        chunks = self.chunk_text(text)
        if not chunks:
            raise ValueError("documento sem texto indexável")
        doc_id, created = self.store.add_document(source, title, str(text), chunks, metadata=metadata)
        return {"document_id": doc_id, "created": created, "chunks": len(chunks) if created else 0, "fts5": self.store.fts5_available}

    def ingest_file(self, path: str | Path, *, metadata=None) -> dict:
        path = Path(path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_size > 100 * 1024 * 1024:
            raise ValueError("arquivo acima do limite de 100 MB")
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise RuntimeError("pypdf não está instalado") from exc
            reader = PdfReader(str(path))
            text_content = "\n\n".join((page.extract_text() or "") for page in reader.pages)
        elif suffix in {".txt", ".md", ".csv", ".json", ".py", ".rst"}:
            text_content = path.read_text(encoding="utf-8", errors="replace")
        else:
            raise ValueError(f"formato ainda não suportado pelo RAG: {suffix}")
        return self.ingest_text(text_content, source=str(path), title=path.name, metadata=metadata)

    def search(self, query: str, *, top_k: int = 5) -> list[RetrievalHit]:
        rows = self.store.search_documents(query, top_k)
        hits = []
        for row in rows:
            rank = row.get("rank")
            score = None if rank is None else -float(rank)
            hits.append(RetrievalHit(int(row["chunk_id"]), row["title"], row["source"], row["content"], score, int(row["document_id"]), int(row["chunk_index"]), row.get("metadata", {})))
        return hits

    def grounded_context(self, query: str, *, top_k: int = 5, max_chars: int = 12000) -> dict:
        hits = self.search(query, top_k=top_k)
        pieces, citations, used = [], [], 0
        for i, hit in enumerate(hits, 1):
            piece = f"[{i}] {hit.title} | {hit.source}\n{hit.content}"
            if used + len(piece) > max_chars:
                break
            pieces.append(piece); used += len(piece)
            citations.append({"index": i, "title": hit.title, "source": hit.source, "document_id": hit.document_id, "chunk_index": hit.chunk_index})
        return {"query": query, "context": "\n\n".join(pieces), "citations": citations, "hits": len(citations)}


class ResearchAgent:
    """Pesquisa acadêmica opcional via Crossref; não é requisito para o Core local."""

    def __init__(self, store: CognitiveStore | None = None, *, session=None):
        self.store = store or CognitiveStore()
        self._session = session

    def search_crossref(self, query: str, *, rows: int = 10, network_enabled: bool = False, mailto: str | None = None) -> dict:
        if not network_enabled:
            return {"ok": False, "reason": "network_disabled", "query": query, "sources": []}
        import requests
        session = self._session or requests.Session()
        rows = max(1, min(int(rows), 50))
        params = {"query.bibliographic": query, "rows": rows, "select": "DOI,title,author,published,URL,type,publisher,is-referenced-by-count"}
        if mailto:
            params["mailto"] = mailto
        response = session.get("https://api.crossref.org/works", params=params, timeout=12, headers={"User-Agent": "STAR-local-research/2.0"})
        response.raise_for_status()
        items = response.json().get("message", {}).get("items", [])
        sources = []
        for item in items:
            title_value = item.get("title") or [""]
            date_parts = ((item.get("published") or {}).get("date-parts") or [[]])[0]
            published = "-".join(str(x) for x in date_parts) if date_parts else None
            sources.append({"title": title_value[0] if title_value else "", "doi": item.get("DOI"), "url": item.get("URL"), "published": published, "type": item.get("type"), "publisher": item.get("publisher"), "citations": item.get("is-referenced-by-count"), "authors": [" ".join(filter(None, [a.get("given"), a.get("family")])) for a in item.get("author", [])[:10]]})
        self.store.cache_research_sources(query, sources)
        return {"ok": True, "query": query, "provider": "Crossref", "sources": sources}

    @staticmethod
    def research_plan(question: str) -> dict:
        q = str(question).strip()
        return {"question": q, "steps": ["definir termos centrais e sinônimos", "buscar metadados e fontes primárias/peer-reviewed", "priorizar recência, relevância e qualidade metodológica", "procurar evidência contrária e retrações/correções", "comparar resultados e registrar incertezas", "produzir síntese com proveniência e lacunas"]}
