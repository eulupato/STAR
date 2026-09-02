# Knowledge System da STAR

O conhecimento próprio é organizado em **Knowledge Packs** modulares e locais.

## Estado na V1.9

A V1.9 suporta packs estruturados e consulta lexical determinística, sem modelo
externo. O objetivo é permitir bases pequenas e revisadas agora, preservando a
arquitetura simples da Foundation.

Fluxo atual:

```text
fonte revisada
→ conteúdo estruturado
→ Knowledge Pack
→ scan no startup
→ busca local
→ resposta da STAR
```

Cada pack usa um `manifest.json` e pode opcionalmente declarar
`content_file`. Os formatos aceitos são `knowledge.jsonl` e
`knowledge.json`.

Exemplo de entrada:

```json
{
  "id": "algebra.exemplo",
  "title": "Título do conceito",
  "aliases": ["pergunta equivalente", "outra formulação"],
  "keywords": ["termo", "assunto"],
  "answer": "Resposta revisada e autocontida.",
  "source": {
    "document": "nome da fonte",
    "pages": [10, 11]
  }
}
```

## PDFs e livros

O pipeline oficial continua:

```text
PDF
→ extração/OCR quando necessário
→ revisão
→ estruturação
→ Knowledge Pack
→ STAR
```

A ingestão automática completa, embeddings locais, busca semântica e RAG
continuam reservados para a **V3.0 — KNOWLEDGE**, conforme o roadmap.

PDFs brutos e textos integrais de obras protegidas não devem ser publicados no
repositório público sem licença compatível. O GitHub deve conter apenas material
que possa ser redistribuído e/ou conhecimento derivado e revisado com
proveniência.
