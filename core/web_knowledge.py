"""Busca web determinística e aprendizado local da STAR.

A web é fallback, nunca a base da STAR. O módulo não usa LLM: busca resultados,
extrai texto, ranqueia sentenças por relevância/diversidade e persiste evidências
no CognitiveStore já existente. Em modo offline, somente o cache/RAG local é usado.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
import ipaddress
import os
import re
import socket
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse

from database.cognitive_store import CognitiveStore


@dataclass(frozen=True)
class WebHit:
    title: str
    url: str
    snippet: str = ""
    provider: str = "web"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokens(value: str) -> set[str]:
    stop = {
        "a", "o", "e", "de", "da", "do", "das", "dos", "em", "um", "uma",
        "para", "por", "com", "que", "the", "of", "and", "to", "in", "is",
    }
    return {
        item for item in re.findall(r"[\wÀ-ÿ]+", str(value).casefold(), flags=re.UNICODE)
        if len(item) > 1 and item not in stop
    }


def _sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", str(text or "")).strip()
    if not compact:
        return []
    return [x.strip() for x in re.split(r"(?<=[.!?。！？])\s+", compact) if 45 <= len(x.strip()) <= 700]


def _domain(url: str) -> str:
    return (urlparse(url).hostname or "").casefold().removeprefix("www.")


def _public_http_url(url: str) -> bool:
    """Bloqueia localhost/rede privada para evitar transformar fetch em SSRF."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        host = parsed.hostname.casefold()
        if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
            return False
        try:
            direct = ipaddress.ip_address(host)
            return not (direct.is_private or direct.is_loopback or direct.is_link_local or direct.is_reserved)
        except ValueError:
            pass
        for info in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM):
            address = ipaddress.ip_address(info[4][0])
            if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
                return False
        return True
    except (OSError, ValueError):
        return False


class _DuckParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hits: list[WebHit] = []
        self._title_url = ""
        self._title_parts: list[str] = []
        self._snippet_parts: list[str] = []
        self._in_title = False
        self._in_snippet = False

    @staticmethod
    def _clean_url(value: str) -> str:
        if value.startswith("//"):
            value = "https:" + value
        parsed = urlparse(value)
        if parsed.path.startswith("/l/"):
            qs = parse_qs(parsed.query)
            target = (qs.get("uddg") or [""])[0]
            if target:
                return unquote(target)
        return value

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        cls = data.get("class", "")
        if tag == "a" and "result__a" in cls:
            self._in_title = True
            self._title_url = self._clean_url(data.get("href", ""))
            self._title_parts = []
        elif tag in {"a", "div"} and "result__snippet" in cls:
            self._in_snippet = True
            self._snippet_parts = []

    def handle_endtag(self, tag):
        if self._in_title and tag == "a":
            self._in_title = False
            title = re.sub(r"\s+", " ", " ".join(self._title_parts)).strip()
            if title and self._title_url:
                self.hits.append(WebHit(title, self._title_url, "", "duckduckgo-html"))
        elif self._in_snippet and tag in {"a", "div"}:
            self._in_snippet = False
            snippet = re.sub(r"\s+", " ", " ".join(self._snippet_parts)).strip()
            if snippet and self.hits and not self.hits[-1].snippet:
                previous = self.hits[-1]
                self.hits[-1] = WebHit(previous.title, previous.url, snippet, previous.provider)

    def handle_data(self, data):
        if self._in_title:
            self._title_parts.append(data)
        if self._in_snippet:
            self._snippet_parts.append(data)


class _TextParser(HTMLParser):
    BLOCKED = {"script", "style", "noscript", "svg", "canvas", "template"}

    def __init__(self):
        super().__init__()
        self._blocked = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCKED:
            self._blocked += 1
        elif tag in {"p", "article", "main", "section", "h1", "h2", "h3", "li"} and not self._blocked:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.BLOCKED and self._blocked:
            self._blocked -= 1
        elif tag in {"p", "article", "main", "section", "h1", "h2", "h3", "li"} and not self._blocked:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._blocked:
            self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"[ \t]+", " ", "".join(self.parts)).replace("\r", "").strip()


class WebKnowledgeEngine:
    """Fallback web atual + cache local, sem modelo generativo."""

    def __init__(self, store: CognitiveStore | None = None, *, session=None, searxng_url: str | None = None):
        self.store = store or CognitiveStore()
        self._session = session
        self.searxng_url = (searxng_url or os.getenv("STAR_SEARXNG_URL", "")).strip().rstrip("/")
        self.max_page_bytes = max(100_000, min(int(os.getenv("STAR_WEB_MAX_BYTES", "900000")), 3_000_000))
        self.timeout = max(3.0, min(float(os.getenv("STAR_WEB_TIMEOUT", "10")), 30.0))

    def _http(self):
        if self._session is not None:
            return self._session
        import requests
        session = requests.Session()
        session.headers.update({"User-Agent": "STAR-local-web-knowledge/1.0 (+offline-first; deterministic-synthesis)"})
        self._session = session
        return session

    def _searxng(self, query: str, limit: int) -> list[WebHit]:
        if not self.searxng_url:
            return []
        response = self._http().get(
            self.searxng_url + "/search",
            params={"q": query, "format": "json", "safesearch": 1},
            timeout=self.timeout,
        )
        response.raise_for_status()
        hits = []
        for item in response.json().get("results", [])[:limit]:
            url = str(item.get("url") or "").strip()
            title = str(item.get("title") or url).strip()
            if url and _public_http_url(url):
                hits.append(WebHit(title, url, str(item.get("content") or "").strip(), "searxng"))
        return hits

    def _duckduckgo(self, query: str, limit: int) -> list[WebHit]:
        response = self._http().get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            timeout=self.timeout,
        )
        response.raise_for_status()
        parser = _DuckParser()
        parser.feed(response.text)
        return [hit for hit in parser.hits if _public_http_url(hit.url)][:limit]

    def search(self, query: str, *, network_enabled: bool = False, limit: int = 8) -> dict:
        query = str(query or "").strip()
        if not query:
            return {"ok": False, "reason": "empty_query", "hits": []}
        if not network_enabled:
            return {"ok": False, "reason": "network_disabled", "hits": []}
        limit = max(1, min(int(limit), 20))
        errors = {}
        hits: list[WebHit] = []
        if self.searxng_url:
            try:
                hits = self._searxng(query, limit)
            except Exception as exc:
                errors["searxng"] = f"{type(exc).__name__}: {exc}"
        if not hits:
            try:
                hits = self._duckduckgo(query, limit)
            except Exception as exc:
                errors["duckduckgo-html"] = f"{type(exc).__name__}: {exc}"
        unique = []
        seen = set()
        for hit in hits:
            key = hit.url.rstrip("/")
            if key in seen:
                continue
            seen.add(key)
            unique.append(hit)
        return {"ok": bool(unique), "query": query, "hits": [asdict(x) for x in unique], "errors": errors}

    def _extract_page(self, url: str) -> str:
        if not _public_http_url(url):
            return ""
        response = self._http().get(url, timeout=self.timeout, stream=True, allow_redirects=True)
        response.raise_for_status()
        final_url = str(response.url)
        if not _public_http_url(final_url):
            return ""
        content_type = (response.headers.get("content-type") or "").casefold()
        if "text/html" not in content_type and "text/plain" not in content_type and "application/xhtml" not in content_type:
            return ""
        raw = bytearray()
        for chunk in response.iter_content(32_768):
            if not chunk:
                continue
            raw.extend(chunk)
            if len(raw) >= self.max_page_bytes:
                break
        encoding = response.encoding or "utf-8"
        html = bytes(raw).decode(encoding, errors="replace")
        try:
            import trafilatura
            extracted = trafilatura.extract(html, include_comments=False, include_tables=False, no_fallback=False)
            if extracted and len(extracted.strip()) >= 120:
                return extracted.strip()
        except (ImportError, OSError, ValueError):
            pass
        if "text/plain" in content_type:
            return re.sub(r"\s+", " ", html).strip()
        parser = _TextParser()
        parser.feed(html)
        return parser.text()

    @staticmethod
    def _rank_sentences(query: str, pages: list[dict], limit: int = 7) -> list[dict]:
        q = _tokens(query)
        candidates = []
        for page_index, page in enumerate(pages):
            source_domain = _domain(page["url"])
            for position, sentence in enumerate(_sentences(page.get("text") or page.get("snippet") or "")[:180]):
                st = _tokens(sentence)
                if not st:
                    continue
                overlap = len(q & st) / max(1, len(q))
                density = len(q & st) / max(1, len(st))
                early = 1.0 / (1.0 + position / 15.0)
                score = 0.70 * overlap + 0.20 * density + 0.10 * early
                if overlap > 0:
                    candidates.append((score, page_index, source_domain, sentence))
        candidates.sort(key=lambda item: item[0], reverse=True)
        selected = []
        per_domain = {}
        seen_sentences = set()
        for score, page_index, domain, sentence in candidates:
            normalized = re.sub(r"\W+", " ", sentence.casefold()).strip()
            if normalized in seen_sentences or per_domain.get(domain, 0) >= 2:
                continue
            seen_sentences.add(normalized)
            per_domain[domain] = per_domain.get(domain, 0) + 1
            page = pages[page_index]
            selected.append({"text": sentence, "url": page["url"], "title": page["title"], "domain": domain, "score": round(score, 4)})
            if len(selected) >= limit:
                break
        return selected

    def _learn(self, query: str, pages: list[dict], statements: list[dict]) -> dict:
        added_documents = 0
        for page in pages:
            text = str(page.get("text") or "").strip()
            if len(text) < 120:
                continue
            chunks = [text[i:i + 2400] for i in range(0, min(len(text), 48_000), 2400)]
            try:
                _doc_id, created = self.store.add_document(
                    page["url"],
                    page["title"],
                    text[:48_000],
                    chunks,
                    metadata={"kind": "web-retrieved", "query": query, "retrieved_at": _now(), "provider": page.get("provider")},
                )
                added_documents += int(bool(created))
            except Exception:
                continue
        distinct_domains = len({item["domain"] for item in statements if item.get("domain")})
        confidence = 0.72 if distinct_domains >= 2 else 0.55
        records = [
            {
                "content": item["text"],
                "source": item["url"],
                "source_type": "web-retrieved-evidence",
                "retrieved_at": _now(),
                "confidence": confidence,
                "metadata": {"query": query, "title": item["title"], "domain": item["domain"], "deterministic_synthesis": True},
            }
            for item in statements
        ]
        facts = self.store.ingest_facts("web:" + query.casefold()[:160], records, target_count=max(1, len(records))) if records else {"accepted": 0, "duplicates": 0}
        return {"documents_added": added_documents, "statements_added": facts.get("accepted", 0), "duplicates": facts.get("duplicates", 0), "confidence": confidence}

    def cached(self, query: str, *, limit: int = 5) -> list[dict]:
        try:
            return self.store.search_documents(query, limit=limit)
        except Exception:
            return []

    def answer(self, query: str, *, network_enabled: bool = False, auto_learn: bool = True) -> str | None:
        query = str(query or "").strip()
        if not query:
            return None
        if not network_enabled:
            cached = self.cached(query, limit=4)
            if not cached:
                return None
            body = "\n".join(f"- {hit['content'][:420].strip()}\n  Fonte local: {hit.get('source', 'cache')}" for hit in cached)
            return "📚 Encontrei evidência já aprendida no cache local (offline):\n" + body

        found = self.search(query, network_enabled=True, limit=8)
        if not found.get("ok"):
            cached = self.cached(query, limit=4)
            if cached:
                return "A busca online falhou; usei o cache local:\n" + "\n".join(f"- {x['content'][:420]}" for x in cached)
            return None

        pages = []
        for hit in found["hits"][:5]:
            text = ""
            try:
                text = self._extract_page(hit["url"])
            except Exception:
                text = ""
            pages.append({**hit, "text": text or hit.get("snippet", "")})
        statements = self._rank_sentences(query, pages, limit=7)
        if not statements:
            statements = [
                {"text": hit.get("snippet", ""), "url": hit["url"], "title": hit["title"], "domain": _domain(hit["url"]), "score": 0.0}
                for hit in found["hits"][:5] if hit.get("snippet")
            ]
        if not statements:
            return None
        learned = self._learn(query, pages, statements) if auto_learn else {"documents_added": 0, "statements_added": 0}
        lines = []
        for index, item in enumerate(statements, 1):
            lines.append(f"{index}. {item['text']}\n   Fonte: {item['title']} — {item['url']}")
        return (
            "🌐 Resultado web formulado deterministicamente, sem IA generativa:\n"
            + "\n".join(lines)
            + f"\n\nAprendizado local: {learned.get('documents_added', 0)} documento(s) e {learned.get('statements_added', 0)} evidência(s) nova(s). "
              "Conteúdo web permanece com proveniência e não vira verdade absoluta automaticamente."
        )

    def stats(self) -> dict:
        return {
            "status": "active-opt-in-network",
            "generative_ai": False,
            "providers": ["SearXNG (preferido/configurável)", "DuckDuckGo HTML fallback"],
            "searxng_configured": bool(self.searxng_url),
            "offline_cache": True,
            "auto_learning": "provenance-preserving evidence cache",
            "ssrf_private_network_block": True,
        }
