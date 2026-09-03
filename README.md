# ⭐ STAR — V3.0 KNOWLEDGE

S.T.A.R. — **System for Thought, Analysis and Response**.

A STAR é uma plataforma cognitiva modular **local-first**. A V3.0 absorve a
fundação estável anterior, consolida a MIND e introduz uma arquitetura de
conhecimento offline expansível integrada ao STAR WORLD.

> **LOCAL é a STAR completa. LAN e Internet são expansões, não requisitos para
> que ela exista.**

## Versão

A única fonte de verdade da versão pública é:

`STAR_MANIFEST.json`

O restante do projeto lê a versão por `core/release.py`. Launcher, GUI,
diagnóstico e configuração não devem possuir números de versão pública
hardcoded.

Estado desta branch:

- versão: **3.0**
- codename: **KNOWLEDGE**
- canal: **development**
- status: **knowledge-foundation**

## Arquitetura ativa

```text
Entrada
  ↓
MIND
  ├── Context + Entity Tracking
  ├── Working Memory
  ├── Salience
  ├── Planner
  ├── Capability Registry
  └── Executive
       ↓
       ├── Conversation Variation Engine
       ├── Media intents
       ├── Computer control
       ├── Math Engine
       ├── Knowledge Engine
       └── fallback interno
```

## V3.0 — Knowledge Engine

O diretório `knowledge/` contém:

- Entity System genérico;
- SQLite local dedicado;
- aliases normalizados;
- campos estruturados multivalorados;
- relações/Knowledge Graph;
- fontes e proveniência;
- Universal Search;
- Knowledge Packs;
- importadores reutilizáveis;
- pipeline de PDF;
- fontes oficiais opcionais DC/Marvel;
- Livro de Receitas local;
- primeira Ilha de Conhecimento: Heróis.

Dados gerados em execução permanecem fora do Git.

## 🦸 Ilha dos Heróis

A ilha está ligada ao Knowledge Engine e oferece:

- interface pixel-art integrada ao STAR WORLD conforme o concept aprovado;
- busca livre por nome, alias e conteúdo indexado;
- roster paginado com até 8 personagens por página e miniaturas locais;
- filtros estruturados por universo, equipe, poder, habilidade, tag,
  espécie/tipo e relacionamento, preservados em painel sobreposto;
- navegação anterior/próximo por componente genérico;
- palco visual do personagem com galeria multi-imagem e pedestal neon;
- abas de Informações, Biografia, Relações, História e Aparições;
- ficha completa do personagem em janela própria;
- múltiplas fontes, página e URL quando disponíveis;
- múltiplas referências visuais locais por personagem;
- tema visual por personagem: overrides icônicos + paleta derivada da imagem;
- fallback visual honesto quando não existe retrato válido;
- contexto da entidade selecionada para a conversa.

Estatísticas visuais só aparecem quando existem como dados estruturados explícitos; campos ausentes permanecem como `—`, sem valores inventados.

O antigo `heroes.json` permanece somente como seed de compatibilidade até que
a base local seja importada integralmente.

### Cobertura estruturada e enriquecimento official-first

A auditoria do snapshot Marvel versionado confirmou **1.564 identidades** e
**1.007 referências visuais** (**64,39%** dos registros). O pack versionado é
um catálogo de identidade: os campos detalhados são enriquecidos no banco
**local**, preservando a arquitetura local-first e evitando publicar conteúdo
de terceiros em massa no GitHub.

Ordem de enriquecimento:

1. perfil oficial Marvel/DC compatível com a identidade;
2. PDF local já autorizado, quando aplicável;
3. Wikidata para descrição curta e campos estruturados ainda ausentes;
4. Wikimedia Commons somente para imagens com licença/metadados recuperáveis.

A proveniência é registrada por campo em `metadata.field_provenance`.
Imagens do Commons guardam autor, licença, URL de licença e URL de origem.
Imagens vindas de perfis oficiais ficam somente no cache local e são marcadas
como referência oficial sem alegar licença aberta.

Relatórios locais:

```text
knowledge/local/reports/heroes_build_report.json
knowledge/local/reports/heroes_coverage_report.json
```

O relatório mede cobertura por campo global e por universo, imagens com
proveniência/licença, imagens oficiais de referência, fichas ricas e listas de
lacunas. Para auditar sem alterar o banco:

```powershell
.\.venv\Scripts\python.exe tools\build_heroes_island.py --audit-only
```

### Política de imagens e motivos de rejeição

A cadeia visual não depende exclusivamente da Marvel oficial. Para reduzir
falhas e travamentos, a ordem operacional agora é:

1. **thumbnail do manifesto Marvel/API**, quando o personagem Marvel já possui
   referência ligada por ID;
2. **Wikimedia Commons ligado por Wikidata**, para preencher lacunas ou promover
   uma alternativa com licença aberta verificável;
3. **perfil oficial Marvel/DC**, somente quando ainda não existe imagem local
   aceita, marcado como referência oficial sem alegar licença aberta.

A correção de 02/09/2026 eliminou quatro fontes de falsos negativos:

- o match Wikidata exigia texto explícito da editora mesmo em resultados
  claramente ficcionais e de nome exato;
- o Commons não solicitava thumbnail rasterizada, então arquivos vetoriais
  podiam chegar em formato incompatível com a UI;
- somente `LicenseShortName` era aceito, embora o Commons também exponha
  termos verificáveis em `UsageTerms`;
- thumbnails Marvel cacheadas não recebiam metadados de direitos, fazendo o
  auditor tratá-las como imagem sem proveniência suficiente.

O relatório `heroes_build_report.json` agora inclui
`image_rejection_reasons` e `image_rejections`, com motivos como
`http_403`, `wikidata_identity_unresolved`,
`missing_license_metadata`, `non_open_license`,
`unsupported_image_format` e `unsupported_source_host`.

Nenhuma imagem aleatória da web é aceita e nenhuma associação
personagem-imagem é inferida apenas por semelhança de nome.

### Limpeza do legado confirmado

Nesta consolidação foram removidos apenas resíduos comprovadamente fora do
runtime: backups antigos em `archive/legacy/` e o script redundante
`tools/enrich_heroes_official.py`, já substituído pela pipeline única
`tools/build_heroes_island.py`. A validação de higiene agora impede que
`archive/legacy/` volte a ser versionado.

Assets ativos, Knowledge Engine, Entity System, UI, seeds de compatibilidade e
dados necessários ao runtime não foram apagados.

### Atualização de dados das fichas

O catálogo mestre Marvel versionado guarda principalmente identidade. Por isso,
nomes e imagens podiam aparecer enquanto as abas continuavam vazias. A correção
atual adiciona uma etapa resumível de dados:

```powershell
.\.venv\Scripts\python.exe tools\build_heroes_island.py --scan-data
```

Essa etapa usa Wikidata para identidade, descrição curta e campos estruturados e
usa somente fatos de infobox da Wikipedia como fonte suplementar. O artigo
completo não é copiado. Quando disponível, podem ser preenchidos nome real,
ocupação, afiliações, equipes, poderes, habilidades, equipamento, espécie,
primeira aparição, criadores e relações explícitas. Cada campo recebe
proveniência.

Checkpoint e relatório:

```text
knowledge/local/reports/heroes_data_scan_state.json
knowledge/local/reports/heroes_data_scan_report.json
```

Se nenhuma fonte estruturada for encontrada, a ficha recebe apenas uma
descrição básica marcada como `catalog_fallback`, sem inventar fatos.

### Varredura visual personagem por personagem

A STAR agora pode percorrer **todo o catálogo existente** e buscar uma referência
visual por personagem com checkpoint resumível. A varredura não cria personagens
novos e usa a identidade já registrada como chave.

Ordem aplicada a cada personagem:

1. Marvel por ID → manifesto/thumbnail oficial, quando disponível;
2. Wikidata → Wikimedia Commons com licença aberta verificável;
3. perfil oficial Marvel/DC apenas para personagens ainda sem imagem.

Comando direto:

```powershell
.\.venv\Scripts\python.exe tools\build_heroes_island.py --scan-images
```

A execução salva progresso a cada lote e pode ser interrompida. Rodar o mesmo
comando novamente continua do checkpoint:

```text
knowledge/local/reports/heroes_image_scan_state.json
```

Resumo final:

```text
knowledge/local/reports/heroes_image_scan_report.json
```

Para reavaliar personagens já concluídos, inclusive referências oficiais que
possam agora ter uma alternativa Commons licenciada:

```powershell
.\.venv\Scripts\python.exe tools\build_heroes_island.py --scan-images --restart-image-scan
```

Para testar em um subconjunto:

```powershell
.\.venv\Scripts\python.exe tools\build_heroes_island.py --scan-images --image-scan-limit 50
```

O relatório classifica cada registro como `accepted_open_license`,
`accepted_official_reference`, `accepted_unclassified_local` ou
`unresolved`, além de guardar os motivos de rejeição encontrados durante a
busca.

### Sincronizar a Ilha dos Heróis

A Marvel usa agora um **catálogo mestre versionado**, não OCR nem crawling web
para descobrir identidades:

```text
knowledge/packs/heroes/
├── marvel_characters.jsonl
├── marvel_image_manifest.json
├── marvel_sources.json
└── marvel_themes.json
        ↓
Knowledge Engine / SQLite local
        ↓
Ilha dos Heróis
```

O snapshot atual contém **1.564 IDs/identidades verificáveis** derivados de
dados da Marvel API e **1.007 referências visuais**. A página pública da Marvel
foi observada com **2.896 perfis/resultados em 01/09/2026**. Esse número maior
inclui variantes e nomes de exibição repetidos e **não equivale a 2.896
codinomes únicos**.

A lacuna verificável atual é de **1.332 resultados**: o snapshot cobre
**54,01%** do total observado no índice. Por isso o catálogo permanece
explicitamente **parcial**; a STAR não completa a diferença com OCR,
inferência ou nomes não certificados.

O repositório não incorpora biografias longas nem imagens oficiais em massa.
O manifesto armazena apenas URLs de referência. As imagens são baixadas, quando
solicitado, para o cache local gitignored.

No Windows:

```powershell
ATUALIZAR_CATALOGO_MARVEL.bat
```

Esse comando:

- sincroniza o catálogo mestre para o SQLite;
- remove somente antigas entidades Marvel criadas por OCR sem fonte confiável;
- tenta primeiro enriquecer os perfis pela fonte oficial;
- usa Wikidata/Commons apenas para lacunas verificáveis;
- preserva seeds, fontes, proveniência e direitos das imagens;
- baixa referências visuais somente para o cache local;
- mostra progresso real `X / total (%)`;
- não exige PDF nem Tesseract.

Um PDF Marvel ainda pode ser fornecido manualmente, mas ele é **somente
complementar**: o importador não cria uma nova identidade Marvel a partir do
OCR. Ele apenas acrescenta campos/proveniência a personagens já presentes no
catálogo confiável.

```powershell
.\.venv\Scripts\python.exe tools\build_heroes_island.py `
  --marvel-pdf "C:\caminho\Marvel Encyclopedia New Edition.pdf"
```

O acesso live a perfis Marvel continua sujeito a HTTP 403. O atualizador tenta
a fonte oficial primeiro e, quando ela não responde ou não fornece um campo,
segue para fontes suplementares verificáveis sem fabricar conteúdo. DC usa a
mesma regra de prioridade de fonte.

Ao final é criado:

`knowledge/local/reports/heroes_build_report.json`

O banco, PDFs e imagens continuam locais. A Ilha funciona offline com o conteúdo
já sincronizado.

## 🏠 STAR WORLD — Casa

`Iniciar` leva ao HUB, não a uma tela central de chat.

Fluxo principal:

```text
Menu → HUB → Casa → Sala / Cozinha / Quarto
                         Quarto → Closet → Álbum
```

O chat é uma camada global contextual: pode ser aberto dentro dos ambientes e
mantém a localização atual como contexto.

Estado atual da Casa:

- **Sala — experimental:** STAR TV possui processo WebView isolado, handshake
  de inicialização, fechamento não bloqueante, ocultação antes do encerramento
  e recuperação automática; validação física do WebView2 no Windows ainda é
  necessária;
- **Cozinha — disponível:** Livro de Receitas local, busca, ingredientes,
  preparo e guia passo a passo;
- **Quarto — disponível:** espaço pessoal e acesso ao Closet;
- **Closet — disponível:** skins e acesso ao Álbum;
- **Álbum — disponível:** galeria local com Adicionar Fotos, Escolher Pasta,
  Abrir Pasta, Pasta Padrão, atualização e pré-visualização; metadados e
  agrupamentos avançados continuam como expansões futuras.

## 💬 Conversation Variation Engine

Small talk não é uma lista de 1000 frases.

A resposta é composta proceduralmente por blocos compatíveis, com:

- reconhecimento de saudações equivalentes;
- horário;
- contexto;
- personalidade separada de modelos;
- buffers pequenos anti-repetição;
- mais de 1000 combinações para greeting/status sem armazenar 1000 strings.

## 📺 STAR TV

A Sala possui um `MediaController` genérico.

Para manter o Core leve, o backend WebView é opcional e carregado somente ao
abrir a TV.

Instalação:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-media.txt
```

A frase:

`STAR, abrir YouTube na TV`

é reconhecida no Core, gera `MEDIA_REQUESTED` no Event Bus e é executada pela
GUI no thread do Tkinter.

Controles:

- abrir;
- play/pause;
- volume;
- fullscreen;
- restore;
- fechar;
- estado.

O lifecycle da TV não bloqueia mais o Tkinter. Ao sair da Sala, o WebView é
ocultado imediatamente e encerrado em worker separado. O processo envia um
evento de `ready`; se a inicialização não responder, a STAR recupera o estado
da Sala em vez de deixar a interface presa. A sincronização de posição também
é limitada à Sala e só ocorre quando a TV está realmente ativa.

## 📸 Álbum local

O Álbum não exige edição manual de `user_settings.json`.

Na interface:

1. **ADICIONAR FOTOS** copia PNG/JPG/JPEG/WEBP para a biblioteca escolhida;
2. **ESCOLHER PASTA** usa uma pasta existente sem copiar o conteúdo;
3. **ABRIR PASTA** abre a biblioteca no sistema;
4. **PASTA PADRÃO** usa/cria `STAR/photos/`;
5. clicar numa miniatura abre uma pré-visualização.

Importar uma foto **copia** o arquivo: a imagem original não é removida. Nomes
repetidos recebem sufixos (`foto_2.jpg`, etc.). Todo o conteúdo do Álbum
permanece local e fora do Git.

## 🎙️ Voz local

A interface pode iniciar mesmo que os componentes de voz não estejam prontos.

`INSTALAR_VOZ.bat` prepara explicitamente:

- faster-whisper + modelo local em `voice/models/whisper/`;
- Piper local para modo rápido quando necessário;
- ambiente Chatterbox da voz oficial.

O runtime recebe um **caminho local absoluto** para o Whisper. Abrir a STAR ou
usar o microfone não deve iniciar download de modelo automaticamente.

A preferência do modo rápido (`sapi` ou `piper`) é definida em `config.py`.

## Execução

```powershell
INICIAR_STAR.bat
```

ou:

```powershell
.\.venv\Scripts\python.exe main.py
```

Diagnóstico geral:

```powershell
.\.venv\Scripts\python.exe diagnostico.py
```

Diagnóstico físico de voz:

```powershell
DIAGNOSTICO_VOZ.bat
```

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

GitHub Actions valida Linux e Windows. O Windows smoke também executa o
diagnóstico geral.

## Dados locais e privacidade

Ficam fora do Git, entre outros:

- `knowledge/local/` e caches gerados;
- PDFs locais;
- `star.db` e arquivos SQLite auxiliares;
- `user_settings.json`;
- modelos de voz;
- referência privada de voz;
- biblioteca pessoal de fotos.

`knowledge/sources/` **não** é ignorado: essa pasta contém código-fonte dos
adaptadores oficiais.

## Estado de desenvolvimento

A arquitetura V3 está integrada. A release só deve ser marcada como **READY**
depois de:

1. expandir/revisar a cobertura Marvel/DC e a associação final de imagens e
   descrições verificadas;
2. testar fisicamente a STAR TV em Windows com WebView2/pywebview;
3. validar microfone, alto-falante e voz oficial no hardware local;
4. executar toda a suíte CI do HEAD final sem falhas.

A ausência de sprites emocionais específicos não é mascarada: os antigos
arquivos eram placeholders vazios. Até existirem artes reais, a GUI usa uma
skin/asset válido com indicador de emoção.

Veja:

- `docs/V3_0_AUDIT_2026-09-02.md` — auditoria atual;
- `docs/V3_0_AUDIT_2026-09-01.md` — histórico da consolidação anterior;
- `docs/V3_0_AUDIT_2026-08-31.md` — histórico da consolidação inicial;
- `docs/V3_0_KNOWLEDGE.md`;
- `docs/MASTER_ROADMAP.md`.
