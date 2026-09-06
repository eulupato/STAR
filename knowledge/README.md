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
→ scan
→ busca local
→ resposta da STAR
```

Cada pack usa um `manifest.json` e pode opcionalmente declarar `content_file`.
Os formatos aceitos são `knowledge.jsonl` e `knowledge.json`.

O `KnowledgePackManager` é a fonte de verdade para leitura e busca dos packs.
Interfaces podem usar `list_entries(pack_id)` para listar entradas públicas e
`search(query, pack_id=...)` / `answer(query, pack_id=...)` para restringir uma
consulta a um pack sem criar parser ou banco paralelo na GUI.

## Schema de entrada

Exemplo:

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
  },
  "metadata": {
    "domain": "matemática"
  }
}
```

Campos `aliases`, `keywords`, `source` e `metadata` são preservados nas entradas
públicas. O índice interno usado pela busca permanece encapsulado pelo manager.

## Ilha dos Heróis

`knowledge/packs/heroes/` possui na Foundation um **seed local funcional** com 12
entradas estruturadas do catálogo inicial já adotado no projeto: figuras históricas,
mitologia grega, Marvel e DC.

O pack é consultável offline pela mesma infraestrutura de Knowledge Packs do Core.
Ele permanece **EM DESENVOLVIMENTO quanto à cobertura**: não representa um
catálogo universal de todas as editoras/personagens. Variantes de identidade devem
ter registros próprios quando a base for expandida.

Imagens de personagens não são copiadas em massa para o GitHub quando não há
licença/autorização para redistribuição. Nesses casos, o metadata pode registrar
`image_status: missing_authorized_asset` sem quebrar a consulta textual offline.

## Knowledge Packs em pendrive

A STAR V1.9 também reconhece packs externos **sem copiá-los para o repositório**.
Na raiz do pendrive, use exatamente:

```text
STAR_KNOWLEDGE/
└── packs/
    ├── matematica/
    │   ├── manifest.json
    │   └── knowledge.jsonl
    └── fisica/
        ├── manifest.json
        └── knowledge.jsonl
```

No Windows, a STAR procura `STAR_KNOWLEDGE/packs` nas unidades montadas. Em
Linux, procura a mesma estrutura em pontos comuns de montagem. Também é possível
informar caminhos explicitamente pela variável `STAR_KNOWLEDGE_DRIVES`, usando o
separador de caminhos do sistema operacional.

A mídia não executa código. O loader aceita somente manifests JSON e conteúdo
JSON/JSONL dentro da pasta do próprio pack, aplica limites de tamanho e ignora
`content_file` que tente sair do diretório do pack.

Quando um pendrive é conectado ou removido, a próxima consulta da STAR verifica
periodicamente se a lista de raízes mudou e atualiza os packs. IDs duplicados não
sobrescrevem silenciosamente o primeiro pack carregado; o conflito é registrado.

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
