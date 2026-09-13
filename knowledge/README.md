# M.drives — Knowledge System da STAR

O conhecimento removível/modular da STAR agora usa o nome oficial **M.drives**:
**Memory + Drives/Pendrives**.

O antigo nome **Knowledge Packs** fica apenas como compatibilidade de legado. Novas
extensões devem usar `knowledge/m_drives`; instalações antigas em `knowledge/packs`
continuam legíveis durante a migração.

## Estrutura

Fluxo atual:

```text
fonte revisada
→ conteúdo estruturado / documento
→ M.drive
→ descoberta e validação de manifesto
→ busca local / RAG
→ resposta da STAR
```

Cada M.drive usa um `manifest.json`. O conteúdo pode ser estruturado em JSON/JSONL
ou disponibilizado em formatos aceitos pelo pipeline documental local, sempre com
proveniência e sem executar código automaticamente.

## M.drives em pendrive

A ideia permanece removível e local. Para novos dispositivos/mídias, a estrutura
preferida é:

```text
STAR_KNOWLEDGE/
└── m_drives/
    ├── matematica/
    │   ├── manifest.json
    │   └── knowledge.jsonl
    └── fisica/
        ├── manifest.json
        └── knowledge.jsonl
```

O caminho legado `STAR_KNOWLEDGE/packs` pode continuar sendo lido por adaptadores de
compatibilidade enquanto a migração acontece. A migração nunca deve apagar a origem
automaticamente.

A mídia não executa código. O loader/registry trabalha com manifests e conteúdo de
dados dentro do próprio M.drive. IDs duplicados devem ser resolvidos por identidade,
versão e proveniência, nunca sobrescritos silenciosamente.

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

## PDFs, livros, OCR e RAG

O pipeline atual evoluiu para:

```text
PDF/texto
→ extração textual
→ OCR local quando necessário e disponível
→ chunking
→ SQLite/FTS5
→ índice semântico derivado opcional
→ recuperação híbrida
→ contexto com origem
```

O RAG textual existente continua como fonte de verdade. Embeddings são índices
derivados e reconstruíveis; Sentence Transformers e `sqlite-vec` são opcionais e não
fazem parte do boot mínimo. OCR de PDFs escaneados pode usar PyMuPDF + Tesseract
quando o stack opcional estiver instalado.

PDFs brutos e textos integrais de obras protegidas não devem ser publicados no
repositório público sem licença compatível. O GitHub deve conter somente material
redistribuível ou conhecimento derivado/revisado com proveniência apropriada.
