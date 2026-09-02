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
│   ├── official.py
│   └── wikidata.py
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

A ficha apresenta os campos disponíveis e múltiplas fontes. Descrições vindas
de fonte estruturada são identificadas pela proveniência; quando nenhuma
biografia verificável foi localizada, a STAR cria apenas uma descrição básica
do catálogo usando fatos já conhecidos e marca explicitamente que a biografia
verificada continua pendente. Assim nenhum personagem fica com a ficha vazia e
o sistema não inventa história.

A seleção anterior/próximo usa `CarouselController`, reutilizável por Closet,
Biblioteca e outras ilhas.

### Interface de catálogo pixel-art

A Ilha dos Heróis agora segue o concept visual aprovado do STAR WORLD sem
substituir a arquitetura de dados já funcional. A tela é construída em Tkinter,
sem novo framework e sem dependência visual de rede:

- cabeçalho próprio STAR WORLD / ILHA DOS HERÓIS;
- contador real do catálogo local e cobertura Marvel parcial explícita;
- busca instantânea com roster paginado de 8 personagens e miniaturas locais;
- filtros avançados preservados em painel sobreposto;
- seleção por lista e navegação anterior/próximo;
- palco central com múltiplas referências visuais e pedestal neon;
- painel DADOS DO PERSONAGEM;
- cards de poderes, equipamento, afiliações e estatísticas;
- abas funcionais de Informações, Biografia, Relações, História e Aparições;
- ficha completa em janela própria com fontes;
- acesso ao HUB, Chat e Configurações sem quebrar o NavigationManager;
- tema icônico/dinâmico continua sendo usado como acento do personagem.

Estatísticas só são exibidas quando existem como dados estruturados explícitos
em attributes.statistics, attributes.stats, metadata.statistics ou campos
equivalentes em escala 0..10. A interface mostra — quando não existe dado, em
vez de fabricar força, defesa ou inteligência.

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

O snapshot atual possui **1.564 IDs/identidades verificáveis** e **1.007
referências visuais**. O índice público Marvel foi observado com **2.896
perfis/resultados** em 01/09/2026. Esse total inclui variantes e nomes de
exibição repetidos e não equivale a 2.896 codinomes únicos.

A lacuna registrada é de **1.332 resultados** e a cobertura numérica do
snapshot é **54,01%** do índice observado. O estado permanece
`partial_verified_snapshot`, sem alegação de completude e sem usar OCR ou
inferência para inflar a contagem.

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
- DC mantém enriquecimento oficial opcional com validação de identidade;
- Wikidata/Wikimedia Commons formam uma camada suplementar opcional para
  preencher lacunas de descrição curta e referência visual;
- essa camada suplementar nunca sobrescreve descrição oficial/PDF já validada;
- candidatos suplementares precisam combinar identidade e editora/universo;
- imagens do Commons só são usadas quando possuem metadados de licença e
  permanecem no cache local com atribuição/proveniência.

Falha de rede nunca impede a consulta do catálogo já importado.

### Auditoria por campo e proveniência

A Ilha agora mede a cobertura dos campos realmente consumidos pela interface:
descrição verificada, nome real, poderes, habilidades, equipamento, ocupação,
afiliações, equipes, origem, primeira aparição, relações, criadores, espécie e
gênero. O relatório separa ainda imagem local válida, imagem com metadados de
origem/direitos, imagem licenciada do Wikimedia Commons e referência visual
oficial usada somente no cache local.

A auditoria do snapshot Marvel versionado em 02/09/2026 confirmou **1.564
identidades** e **1.007 referências visuais** (**64,39%**). O pack mestre é um
catálogo de identidade; os campos detalhados não são versionados em massa e são
preenchidos no banco local pelas fontes autorizadas.

A proveniência é registrada por campo em `metadata.field_provenance`. A ficha
completa mostra essa origem junto das fontes gerais, permitindo distinguir dados
oficiais de complementos estruturados. O enriquecimento segue a ordem:
Marvel/DC oficial → dados locais autorizados → Wikidata → Wikimedia Commons
licenciado para imagens.

Dois relatórios ficam disponíveis em `knowledge/local/reports/`:

- `heroes_build_report.json` após sincronização/enriquecimento;
- `heroes_coverage_report.json` para auditoria somente-leitura com
  `--audit-only`.

### Aparições oficiais e relações

A pipeline oficial agora registra também **aparições** quando Marvel/DC expõem
links de quadrinhos ou listas de leitura no perfil do personagem. Esses títulos
são armazenados em `Entity.attributes["appearances"]`, sem criar outro modelo
de entidade. Relações oficiais continuam em `Entity.relationships`.

Tanto `appearances` quanto `relationships` recebem proveniência por campo e
aparecem respectivamente na aba **Aparições**, na aba **Relações** e na ficha
completa. Se a fonte oficial não publicar esse dado, a interface mantém a
lacuna explícita em vez de inferir aparições ou vínculos.

### Qualidade das fichas

`heroes_build_report.json` agora diferencia:

- total de personagens;
- imagens locais realmente válidas;
- descrições presentes;
- descrições verificadas;
- descrições básicas de fallback;
- fichas completas (imagem local + descrição verificada);
- quantidade e lista de imagens faltantes;
- quantidade e lista de descrições verificadas faltantes.

Isso impede que um caminho de imagem inexistente ou um registro sem biografia
seja contabilizado como ficha completa.

## Imagens

O importador não usa uma página escaneada inteira como retrato final. Imagens
embutidas que cobrem quase toda a página são rejeitadas; arte candidata menor
pode ser associada ao personagem. Se não houver imagem adequada, o
enriquecimento oficial pode preencher a imagem e salvá-la no cache local. Se a
fonte oficial não fornecer uma referência, o enriquecimento suplementar pode
tentar uma imagem licenciada do Wikimedia Commons e registrar autor, licença e
URL de origem junto à entidade. Caso tudo falhe, a GUI usa placeholder honesto
e o relatório mantém o registro na lista de imagens pendentes.

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

O repositório também não versiona em massa biografias longas de terceiros.
Wikidata é usado somente como fonte estruturada suplementar de descrições
curtas. Arquivos do Wikimedia Commons ficam fora do Git e carregam metadados de
atribuição/licença no banco local.

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

A auditoria de 02/09 encontrou duas causas concretas para a interface ficar
presa ao abrir/sair do YouTube: `_media_sync_job` era usado sem inicialização e
o fechamento do processo WebView esperava sincronamente dentro do thread
Tkinter. O lifecycle agora é não bloqueante: a janela é ocultada antes do
fechamento, o processo é destacado da GUI e reaped em worker, existe handshake
`ready`, timeout de recuperação e debounce de sincronização de geometria apenas
quando a Sala está ativa. O host continua reportando falhas via stderr.

A Sala permanece `experimental` somente porque o comportamento visual do
WebView2 precisa de validação física na máquina Windows do projeto; o código e o
contrato de recuperação possuem testes automatizados.

## Álbum

O `PhotoLibrary` continua local-first, mas o fluxo principal agora está
**available**:

- cria a pasta padrão `photos/` quando necessário;
- adiciona fotos pela própria GUI;
- copia imagens sem apagar a origem;
- resolve colisões de nomes com sufixo incremental;
- permite apontar para uma pasta existente;
- abre a pasta no sistema;
- atualiza a galeria;
- abre pré-visualização ao clicar na miniatura;
- aceita PNG, JPG, JPEG e WEBP.

`user_settings.json` continua armazenando apenas o caminho escolhido e permanece
fora do Git. Metadados, agrupamentos e memórias visuais mais profundas seguem
como expansões, mas não bloqueiam o uso básico do Álbum.

## Status

A arquitetura KNOWLEDGE está implementada e testada progressivamente. A
classificação permanece **DEVELOPMENT / PARTIAL NO CONTEÚDO** até:

- expansão progressiva do snapshot Marvel até cobrir o índice atual e revisão do PDF DC;
- execução/revisão local do enriquecimento suplementar e cobertura final de
  imagens/descrições verificadas;
- validação física da STAR TV e voz no Windows do projeto.

Veja a auditoria atual em `docs/V3_0_AUDIT_2026-09-02.md`.
