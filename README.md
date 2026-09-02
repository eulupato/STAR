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
- preserva seeds/fonte oficial/conteúdo confiável;
- baixa as referências visuais disponíveis para o cache local;
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

O acesso live a perfis Marvel deixou de ser requisito. Ele permanece opcional e
explícito porque o site pode responder HTTP 403. DC continua podendo usar
enriquecimento web opcional.

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
