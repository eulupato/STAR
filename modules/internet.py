"""Pesquisa web geral da STAR com proveniência e verificação conservadora.

A rede é sempre opt-in. Resultados de busca são evidência externa, não fatos
automaticamente verdadeiros. A verificação daqui confirma diversidade de fontes,
recuperabilidade e proveniência; não transforma snippets em certeza epistêmica.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from html.parser import HTMLParser
import ipaddress
import os
import re
import socket
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse

import requests


MAX_RESULTS = 20
MAX_VERIFY_BYTES = 1_500_000
USER_AGENT = "STAR-local-research/3.0 (+local-first; provenance-preserving)"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value) -> str:
    return " ".join(str(value or "").split())


def _domain(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower().removeprefix("www.")
    except ValueError:
        return ""


def _safe_public_url(url: str) -> bool:
    """Bloqueia esquemas não HTTP e alvos locais/privados antes de fetch."""
    try:
        parsed = urlparse(str(url))
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    host = parsed.hostname.strip("[]").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return False
    try:
        ip = ipaddress.ip_address(host)
        return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast)
    except ValueError:
        pass
    # DNS só é usado como proteção extra. Falha de DNS não autoriza nem impede a
    # busca; a requisição real ainda possui timeout e valida redirect final.
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
    except OSError:
        pass
    return True


def _decode_duckduckgo_url(href: str) -> str:
    href = str(href or "")
    if href.startswith("//"):
        href = "https:" + href
    parsed = urlparse(href)
    if "duckduckgo.com" in (parsed.hostname or "") and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        if target:
            return unquote(target)
    return href


@dataclass(frozen=True)
class WebResult:
    title: str
    url: str
    snippet: str
    provider: str
    source_domain: str
    retrieved_at: str
    rank: int
    provenance_verified: bool = False
    retrieval_status: str = "not_checked"
    content_type: str | None = None


class _DuckDuckGoParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.results: list[dict] = []
        self._in_title = False
        self._in_snippet = False
        self._href = ""
        self._title_parts: list[str] = []
        self._snippet_parts: list[str] = []
        self._pending: dict | None = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set(str(attrs.get("class") or "").split())
        if tag == "a" and "result__a" in classes:
            self._in_title = True
            self._href = attrs.get("href") or ""
            self._title_parts = []
        elif tag in {"a", "div"} and ("result__snippet" in classes or "result__snippet" in str(attrs.get("class") or "")):
            self._in_snippet = True
            self._snippet_parts = []

    def handle_data(self, data):
        if self._in_title:
            self._title_parts.append(data)
        if self._in_snippet:
            self._snippet_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._in_title:
            self._in_title = False
            url = _decode_duckduckgo_url(self._href)
            title = _clean("".join(self._title_parts))
            if title and url:
                self._pending = {"title": title, "url": url, "snippet": ""}
                self.results.append(self._pending)
        if tag in {"a", "div"} and self._in_snippet:
            self._in_snippet = False
            if self._pending is not None:
                self._pending["snippet"] = _clean("".join(self._snippet_parts))


class GeneralWebSearch:
    """Busca web geral com provider configurável e fallback sem chave."""

    def __init__(self, *, session=None, searxng_url: str | None = None):
        self.session = session or requests.Session()
        self.searxng_url = (searxng_url or os.getenv("STAR_SEARXNG_URL") or "").rstrip("/")

    def search(self, query: str, *, limit: int = 8, network_enabled: bool = False, verify: bool = True) -> dict:
        query = _clean(query)
        if not query:
            raise ValueError("consulta web vazia")
        if not network_enabled:
            return {"ok": False, "reason": "network_disabled", "query": query, "results": [], "verification": self._verification([])}
        limit = max(1, min(int(limit), MAX_RESULTS))
        errors = []
        results = []
        if self.searxng_url:
            try:
                results = self._search_searxng(query, limit)
            except (requests.RequestException, ValueError, KeyError) as exc:
                errors.append(f"searxng:{type(exc).__name__}")
        if not results:
            try:
                results = self._search_duckduckgo(query, limit)
            except (requests.RequestException, ValueError) as exc:
                errors.append(f"duckduckgo:{type(exc).__name__}")
        if verify and results:
            results = self.verify_results(results, max_checks=min(4, len(results)))
        return {
            "ok": bool(results),
            "reason": None if results else "provider_unavailable",
            "query": query,
            "results": [asdict(item) for item in results[:limit]],
            "verification": self._verification(results),
            "provider_errors": errors,
        }

    def _search_searxng(self, query: str, limit: int) -> list[WebResult]:
        endpoint = self.searxng_url + "/search"
        response = self.session.get(endpoint, params={"q": query, "format": "json", "language": "all", "safesearch": 1}, timeout=12, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        rows = response.json().get("results") or []
        out = []
        for row in rows[:limit]:
            url = str(row.get("url") or "")
            if not _safe_public_url(url):
                continue
            out.append(WebResult(_clean(row.get("title")), url, _clean(row.get("content")), "SearXNG", _domain(url), _now(), len(out) + 1))
        return out

    def _search_duckduckgo(self, query: str, limit: int) -> list[WebResult]:
        response = self.session.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query}, timeout=12,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7"},
        )
        response.raise_for_status()
        parser = _DuckDuckGoParser()
        parser.feed(response.text[:4_000_000])
        out, seen = [], set()
        for row in parser.results:
            url = row["url"]
            if url in seen or not _safe_public_url(url):
                continue
            seen.add(url)
            out.append(WebResult(row["title"], url, row.get("snippet", ""), "DuckDuckGo HTML", _domain(url), _now(), len(out) + 1))
            if len(out) >= limit:
                break
        return out

    def verify_results(self, results: list[WebResult], *, max_checks: int = 4) -> list[WebResult]:
        verified = []
        for index, item in enumerate(results):
            if index >= max_checks or not _safe_public_url(item.url):
                verified.append(item)
                continue
            status, content_type, final_url = "unreachable", None, item.url
            try:
                response = self.session.get(item.url, timeout=10, stream=True, allow_redirects=True, headers={"User-Agent": USER_AGENT})
                final_url = str(getattr(response, "url", item.url) or item.url)
                content_type = str(response.headers.get("Content-Type") or "").split(";", 1)[0].lower() or None
                if not _safe_public_url(final_url):
                    status = "blocked_redirect"
                elif 200 <= int(response.status_code) < 400:
                    read = 0
                    for chunk in response.iter_content(chunk_size=65536):
                        read += len(chunk)
                        if read >= MAX_VERIFY_BYTES:
                            break
                    status = "retrievable"
                else:
                    status = f"http_{response.status_code}"
            except requests.RequestException:
                status = "unreachable"
            verified.append(WebResult(
                item.title, final_url if _safe_public_url(final_url) else item.url, item.snippet,
                item.provider, _domain(final_url) or item.source_domain, item.retrieved_at, item.rank,
                provenance_verified=status == "retrievable", retrieval_status=status, content_type=content_type,
            ))
        return verified

    @staticmethod
    def _verification(results) -> dict:
        rows = [asdict(x) if isinstance(x, WebResult) else dict(x) for x in results]
        domains = sorted({str(x.get("source_domain") or "") for x in rows if x.get("source_domain")})
        verified = sum(bool(x.get("provenance_verified")) for x in rows)
        if verified >= 2 and len(domains) >= 2:
            status = "multi_source_provenance_verified"
        elif verified >= 1:
            status = "single_source_provenance_verified"
        elif rows:
            status = "search_results_unverified"
        else:
            status = "no_evidence"
        return {
            "status": status,
            "source_count": len(rows),
            "independent_domains": len(domains),
            "domains": domains,
            "retrievable_sources": verified,
            "truth_claim": False,
            "note": "verificação confirma proveniência/recuperabilidade e diversidade; não prova a veracidade do conteúdo",
        }


def search_web(query: str, *, limit: int = 8, network_enabled: bool = False, session=None) -> dict:
    return GeneralWebSearch(session=session).search(query, limit=limit, network_enabled=network_enabled)
