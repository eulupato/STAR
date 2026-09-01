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
├── importers/
│   ├── pdf.py
│   └── heroes.py
└── packs/
```

Dados gerados em execução:

```text
knowledge/local/
├── star_knowledge.db
└── cache/
    └── pdf/
```

Esse diretório é local e gitignored.

## Entity System

O modelo é genérico para personagens, pessoas, livros, lugares, objetos,
organizações, espécies, eventos e futuros domínios.

Campos ausentes permanecem nulos/vazios. O importador não deve inventar fatos.

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

## Copyright e dados locais

Enciclopédias, páginas renderizadas e imagens extraídas não são versionadas no
repositório público. O código armazena localmente somente o conteúdo necessário
para a base do usuário.

## Conversation

`core/conversation.py` executa antes de ferramentas caras. Saudações e small
talk não chamam modelo, internet nem banco de conhecimento.

## TV

`core/media_intents.py` interpreta intenção.  
`MEDIA_REQUESTED` passa pelo Event Bus.  
`modules/media_controller.py` controla o processo.  
`modules/media_host.py` hospeda o WebView.  
`gui/app.py` apenas recebe o evento no thread principal e atualiza a cena.

## Fontes da Ilha dos Heróis

Prioridade de conhecimento:

```text
PDF local
↓
dados já indexados/cache
↓
perfil oficial DC/Marvel, quando ONLINE for autorizado
↓
campo desconhecido permanece nulo
```

O enriquecimento oficial usa somente `dc.com` e `marvel.com`, mantém cache
local e registra a URL em `KnowledgeSource`. Uma falha HTTP nunca impede a
consulta dos dados locais.

O `HeroesKnowledgeBuilder` orquestra os dois PDFs, enriquecimento opcional,
cache de imagens e relatório de cobertura.

## Imagens

O importador não usa mais uma página escaneada inteira como retrato final.
Imagens embutidas que cobrem quase toda a página são rejeitadas; arte candidata
menor pode ser associada ao personagem. Se não houver imagem adequada, o
enriquecimento oficial pode preencher a imagem e salvá-la no cache local.
Caso tudo falhe, a GUI usa placeholder.

## Status

A arquitetura está implementada e testada por CI progressivo. A classificação
permanece **PARTIAL** até a importação/revisão integral dos dois PDFs e a
validação física da STAR TV/voz no Windows do projeto.
