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

Catálogos muito grandes que servem como **inventário** podem ser declarados no
mesmo manifest e instalados em `knowledge/local/<pack_id>/catalog.tsv`. Eles não
entram em `entries`, não atrasam o boot e só são indexados quando a função de
catálogo é usada. A API correspondente continua pertencendo ao mesmo
`KnowledgePackManager`:

```python
manager.catalog_stats("heroes")
manager.catalog_list("heroes", entity_type="character", limit=100)
manager.catalog_search("Peter Parker", "heroes", entity_type="character")
```

Isso mantém uma única fonte de verdade para o pack sem obrigar a Foundation a
transformar 100 mil nomes em fichas falsas.

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

`knowledge/packs/heroes/` possui na Foundation **12 fichas locais enriquecidas e
revisadas**: figuras históricas, mitologia grega, Marvel e DC. Essas fichas
continuam respondíveis pela infraestrutura normal de Knowledge Packs.

Além delas, a STAR agora suporta um **inventário Marvel local amplo** instalado
fora do GitHub. O snapshot auditado em 06/09/2026 contém:

- 104.173 personagens;
- 6.851 equipes;
- 111.024 registros tipados no total.

A origem desse inventário é a **Marvel Database / Fandom**, uma fonte comunitária
e não oficial da Marvel. O catálogo preserva variantes de continuidades diferentes
como registros separados e mantém personagens/equipes tipados.

O dataset massivo fica em:

```text
knowledge/
└── local/
    └── heroes/
        ├── catalog.tsv
        └── catalog.meta.json
```

Essa pasta já é ignorada pelo Git. Para gerar o índice local a partir dos TXT
coletados:

```powershell
python .\tools\install_marvel_catalog.py
```

O instalador procura automaticamente por:

```text
MARVEL_DATABASE_PERSONAGENS.txt
MARVEL_DATABASE_EQUIPES.txt
```

na pasta atual e em `Downloads`. Também é possível indicar a origem:

```powershell
python .\tools\install_marvel_catalog.py --source-dir "C:\caminho\dos\arquivos"
```

Depois da instalação, reinicie a STAR e abra `HUB → HERÓIS`. O catálogo só é
carregado na primeira consulta da ilha, evitando colocar ~111 mil registros no
startup.

### O que um registro de inventário significa

Um item presente no `catalog.tsv` confirma apenas que aquele título/tipo está no
snapshot importado da Marvel Database. Ele **não** vira automaticamente uma
biografia completa.

Enquanto uma entidade não possuir ficha enriquecida, a STAR não inventa:

- poderes;
- história;
- relações;
- identidade civil;
- equipes;
- imagens.

Esses campos só entram quando forem enriquecidos e validados. Assim, inventário e
conhecimento detalhado permanecem claramente separados.

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

A ingestão automática completa, embeddings locais, busca semântica, relações
semânticas e RAG continuam reservados para a **V3.0 — KNOWLEDGE**, conforme o
roadmap.

O inventário Marvel amplo integrado agora **não declara V3 concluída**. Ele é uma
camada local de catálogo/indexação que prepara o caminho para o enriquecimento
posterior sem duplicar arquitetura.

PDFs brutos e textos integrais de obras protegidas não devem ser publicados no
repositório público sem licença compatível. O GitHub deve conter apenas material
que possa ser redistribuído e/ou conhecimento derivado e revisado com
proveniência.
