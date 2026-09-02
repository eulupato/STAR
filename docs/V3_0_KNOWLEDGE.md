# STAR V3.0 — KNOWLEDGE

## Objetivo

Transformar conhecimento em um subsistema local, consultável, expansível e
independente da GUI.

## Fluxo

```text
Pergunta
  ↓
MIND Planner
  ↓
Universal Search / Entity Resolution
  ↓
SQLite + Packs + Working Memory
  ↓
Knowledge Graph
  ↓
resposta
  ↓
Context Entity Tracking
```

## Estrutura

```text
knowledge/
├── entities.py
├── store.py
├── graph.py
├── engine.py
├── bootstrap.py
├── recipes.py
├── importers/
│   ├── pdf.py
│   └── heroes.py
├── sources/
│   └── official.py
└── packs/
```

Dados gerados em execução:

```text
knowledge/local/
├── star_knowledge.db
├── reports/
└── cache/
```

Esse diretório é local e gitignored. `knowledge/sources/`, por outro lado,
contém **código-fonte** e permanece versionado.

## Entity System

O modelo é genérico para personagens, pessoas, livros, lugares, objetos,
organizações, espécies, eventos e futuros domínios.

Campos ausentes permanecem nulos/vazios. Importadores não devem inventar fatos.

O SQLite mantém também `entity_values`, um índice estrutural para campos
multivalorados como:

- equipe;
- poder;
- habilidade;
- tag;
- afiliação;
- relacionamento;
- tipo de relação.

Isso impede que um filtro de “poder” coincida apenas porque a mesma palavra
aparece na descrição textual da entidade.

A evolução desse índice é registrada em `knowledge_meta`, permitindo migração
automática de bancos V3 anteriores.

## Proveniência

Cada entidade pode possuir múltiplas fontes:

- tipo;
- arquivo;
- página;
- URL, quando aplicável;
- data de recuperação;
- campo associado.

## Universal Search

A implementação atual consulta:

- Entity Database;
- Working Memory;
- Knowledge Pack manifests.

A interface foi desenhada para receber futuramente biblioteca, arquivos,
embeddings e web opcional sem alterar a GUI.

## Ilha dos Heróis

`gui/heroes_view.py` consulta somente `KnowledgeEngine`.

A GUI não executa SQL nem faz parsing dos PDFs.

Filtros atuais:

- universo;
- equipe;
- poder;
- habilidade;
- tag;
- espécie/tipo;
- relacionamento.

A ficha apresenta os campos disponíveis e múltiplas fontes, sem transformar
campo ausente em informação inventada.

A seleção anterior/próximo usa `CarouselController`, reutilizável por Closet,
Biblioteca e outras ilhas.

## PDF pipeline

`PdfDocumentReader`:

1. abre PDF via PyMuPDF;
2. tenta texto embutido;
3. renderiza página somente quando necessário;
4. usa cache;
5. opcionalmente usa Tesseract quando não há texto suficiente.

`HeroEncyclopediaImporter`:

1. detecta entradas;
2. normaliza dados;
3. cria entidades;
4. associa fonte/página;
5. registra relações disponíveis;
6. indexa no store.

## Catálogo mestre Marvel + fontes oficiais

A descoberta de identidades Marvel não depende mais de OCR nem de crawling do
site. A fonte operacional é um snapshot estruturado e versionado:

```text
marvel_characters.jsonl
+ marvel_sources.json
+ marvel_image_manifest.json
+ marvel_themes.json
↓
MarvelMasterCatalog
↓
Entity Store local
```

O snapshot atual possui 1.564 registros e 1.007 referências visuais. A
proveniência registra também que o índice público Marvel foi observado com
2.896 resultados em 01/09/2026; portanto, a cobertura é
`partial_verified_snapshot`, sem alegação de completude.

Regras atuais:

- OCR nunca cria identidade Marvel;
- PDF Marvel só complementa uma entidade já conhecida;
- resíduos do antigo OCR só são removidos quando dependem exclusivamente de
  fonte PDF não confiável;
- seeds, catálogo mestre, knowledge packs e fontes oficiais são preservados;
- biografias longas e imagens oficiais não são versionadas;
- o manifesto guarda apenas URLs e o cache visual permanece local;
- variantes distintas permanecem entidades distintas;
- acesso live à Marvel é opcional e explicitamente habilitado, pois pode sofrer
  HTTP 403;
- DC mantém enriquecimento oficial opcional com validação de identidade.

Falha de rede nunca impede a consulta do catálogo já importado.

## Imagens

O importador não usa uma página escaneada inteira como retrato final. Imagens
embutidas que cobrem quase toda a página são rejeitadas; arte candidata menor
pode ser associada ao personagem. Se não houver imagem adequada, o
enriquecimento oficial pode preencher a imagem e salvá-la no cache local.
Caso tudo falhe, a GUI usa placeholder honesto.

A ficha pode navegar entre múltiplas referências locais. O tema visual possui
overrides de identidade para personagens icônicos e, para todo o restante,
extrai uma paleta escura a partir da imagem local com cache. Assim a Ilha pode
dar identidade visual própria a milhares de personagens sem milhares de regras
hardcoded.

## Cozinha e conhecimento local estruturado

`RecipeBook` demonstra a mesma filosofia fora da Ilha dos Heróis:

- dados locais separados da GUI;
- JSON, Markdown e TXT;
- busca por nome, ingrediente e tag;
- ingredientes e instruções estruturadas;
- `RecipeSession` para acompanhamento passo a passo.

Esse serviço é consumido pela Cozinha da Casa sem colocar parsing de arquivos
dentro da camada visual.

## Copyright e dados locais

Enciclopédias, páginas renderizadas, imagens extraídas, bancos gerados e caches
não são versionados no repositório público. O projeto armazena localmente apenas
o necessário para a base autorizada do usuário.

## Conversation

`core/conversation.py` executa antes de ferramentas caras, mas só responde a
intenções reconhecidas de small talk. Perguntas de conhecimento continuam para
o Knowledge Engine.

## TV

`core/media_intents.py` interpreta intenção.  
`MEDIA_REQUESTED` passa pelo Event Bus.  
`modules/media_controller.py` controla o processo.  
`modules/media_host.py` hospeda o WebView.  
`gui/app.py` recebe o evento no thread principal e atualiza a cena.

O host reporta falhas de comandos via stderr; erros de mídia não derrubam o
Core.

## Status

A arquitetura KNOWLEDGE está implementada e testada progressivamente. A
classificação permanece **DEVELOPMENT / PARTIAL NO CONTEÚDO** até:

- expansão progressiva do snapshot Marvel até cobrir o índice atual e revisão do PDF DC;
- validação de cobertura final de imagens;
- validação física da STAR TV e voz no Windows do projeto.

Veja a auditoria atual em `docs/V3_0_AUDIT_2026-09-01.md`.
