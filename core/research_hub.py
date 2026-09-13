"""Research Hub multiprovedor da STAR.

Providers são opt-in de rede e retornam um esquema comum. O hub não confunde
metadados encontrados com evidência validada e deduplica DOI/URL/título.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

from database.cognitive_store import CognitiveStore


@dataclass(frozen=True)
class ResearchSource:
    provider: str
    title: str
    url: str | None = None
    doi: str | None = None
    published: str | None = None
    authors: tuple[str, ...] = ()
    source_type: str | None = None
    cited_by: int | None = None
    metadata: dict | None = None


class ResearchHub:
    PROVIDERS = ("crossref", "openalex", "arxiv", "pubmed")

    def __init__(self, store: CognitiveStore | None = None, *, session=None):
        self.store = store or CognitiveStore(); self._session = session

    def _http(self):
        import requests
        return self._session or requests.Session()

    def crossref(self, query: str, limit: int) -> list[ResearchSource]:
        response = self._http().get("https://api.crossref.org/works", params={"query.bibliographic": query, "rows": limit,
            "select": "DOI,title,author,published,URL,type,publisher,is-referenced-by-count"}, timeout=15,
            headers={"User-Agent": "STAR-local-research/3.0"}); response.raise_for_status()
        result = []
        for item in response.json().get("message", {}).get("items", []):
            title = (item.get("title") or [""])[0]
            parts = ((item.get("published") or {}).get("date-parts") or [[]])[0]
            result.append(ResearchSource("Crossref", title, item.get("URL"), item.get("DOI"),
                "-".join(map(str, parts)) if parts else None,
                tuple(" ".join(filter(None, [a.get("given"), a.get("family")])) for a in item.get("author", [])[:20]),
                item.get("type"), item.get("is-referenced-by-count"), {"publisher": item.get("publisher")}))
        return result

    def openalex(self, query: str, limit: int) -> list[ResearchSource]:
        response = self._http().get("https://api.openalex.org/works", params={"search": query, "per-page": limit}, timeout=15,
                                    headers={"User-Agent": "STAR-local-research/3.0"}); response.raise_for_status()
        result = []
        for item in response.json().get("results", []):
            ids = item.get("ids") or {}; doi = (ids.get("doi") or "").replace("https://doi.org/", "") or None
            authors = tuple(((a.get("author") or {}).get("display_name") or "") for a in item.get("authorships", [])[:20])
            result.append(ResearchSource("OpenAlex", item.get("display_name") or "", item.get("id"), doi,
                item.get("publication_date"), tuple(x for x in authors if x), item.get("type"), item.get("cited_by_count"),
                {"open_access": item.get("open_access"), "primary_location": item.get("primary_location")}))
        return result

    def arxiv(self, query: str, limit: int) -> list[ResearchSource]:
        url = f"https://export.arxiv.org/api/query?search_query=all:{quote_plus(query)}&start=0&max_results={limit}"
        response = self._http().get(url, timeout=15, headers={"User-Agent": "STAR-local-research/3.0"}); response.raise_for_status()
        root = ET.fromstring(response.text); ns = {"a": "http://www.w3.org/2005/Atom"}; result = []
        for entry in root.findall("a:entry", ns):
            title = " ".join((entry.findtext("a:title", default="", namespaces=ns)).split())
            authors = tuple(x.findtext("a:name", default="", namespaces=ns) for x in entry.findall("a:author", ns))
            result.append(ResearchSource("arXiv", title, entry.findtext("a:id", default=None, namespaces=ns), None,
                entry.findtext("a:published", default=None, namespaces=ns), tuple(x for x in authors if x), "preprint", None,
                {"updated": entry.findtext("a:updated", default=None, namespaces=ns)}))
        return result

    def pubmed(self, query: str, limit: int) -> list[ResearchSource]:
        session = self._http()
        search = session.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "pubmed", "term": query, "retmode": "json", "retmax": limit}, timeout=15); search.raise_for_status()
        ids = search.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        summary = session.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"}, timeout=15); summary.raise_for_status()
        data = summary.json().get("result", {}); result = []
        for pmid in ids:
            item = data.get(str(pmid), {})
            authors = tuple(a.get("name", "") for a in item.get("authors", [])[:20] if a.get("name"))
            doi = None
            for article_id in item.get("articleids", []):
                if article_id.get("idtype") == "doi": doi = article_id.get("value"); break
            result.append(ResearchSource("PubMed", item.get("title") or "", f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                doi, item.get("pubdate"), authors, "biomedical-literature", None, {"pmid": pmid, "source": item.get("source")}))
        return result

    @staticmethod
    def _key(source: ResearchSource) -> str:
        if source.doi:
            return "doi:" + source.doi.lower().strip()
        if source.url:
            return "url:" + source.url.lower().strip()
        return "title:" + re.sub(r"\W+", " ", source.title.lower()).strip()

    def search(self, query: str, *, providers=None, limit_per_provider: int = 5, network_enabled: bool = False) -> dict:
        query = str(query).strip()
        if not network_enabled:
            return {"ok": False, "reason": "network_disabled", "query": query, "sources": [], "errors": {}}
        selected = tuple(providers or self.PROVIDERS); limit = max(1, min(int(limit_per_provider), 25)); all_sources = {}; errors = {}
        for provider in selected:
            if provider not in self.PROVIDERS:
                errors[provider] = "unknown_provider"; continue
            try:
                for source in getattr(self, provider)(query, limit):
                    all_sources.setdefault(self._key(source), source)
            except Exception as exc:
                errors[provider] = f"{type(exc).__name__}: {exc}"
        sources = [asdict(source) for source in all_sources.values()]
        sources.sort(key=lambda item: (item.get("cited_by") or 0, bool(item.get("doi"))), reverse=True)
        if hasattr(self.store, "cache_research_sources"):
            try:
                self.store.cache_research_sources(query, [{"title": x["title"], "url": x["url"], "doi": x["doi"], "published": x["published"], "provider": x["provider"]} for x in sources])
            except Exception:
                pass
        return {"ok": bool(sources), "query": query, "providers": selected, "sources": sources, "errors": errors,
                "note": "descoberta bibliográfica; qualidade metodológica e evidência ainda precisam de verificação"}

    def stats(self) -> dict:
        return {"status": "active-opt-in-network", "providers": list(self.PROVIDERS), "network_default": False,
                "deduplication": "DOI > URL > normalized title", "full_text_download": False}
