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

- busca livre por nome, alias e conteúdo indexado;
- filtros estruturados por universo, equipe, poder, habilidade, tag,
  espécie/tipo e relacionamento;
- navegação anterior/próximo por componente genérico;
- ficha ampliada do personagem;
- múltiplas fontes, página e URL quando disponíveis;
- múltiplas referências visuais locais por personagem;
- tema visual por personagem: overrides icônicos + paleta derivada da imagem;
- fallback visual honesto quando não existe retrato válido;
- contexto da entidade selecionada para a conversa.

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

O snapshot atual contém **1.564 identidades verificáveis** derivadas de dados da
Marvel API e **1.007 referências visuais**. A página pública da Marvel foi
observada com **2.896 resultados em 01/09/2026**; portanto, o snapshot é
explicitamente marcado como **parcial**, nunca como catálogo completo.

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

- **Sala — experimental:** STAR TV implementada; validação física do WebView no
  Windows ainda é necessária;
- **Cozinha — disponível:** Livro de Receitas local, busca, ingredientes,
  preparo e guia passo a passo;
- **Quarto — disponível:** espaço pessoal e acesso ao Closet;
- **Closet — disponível:** skins e acesso ao Álbum;
- **Álbum — parcial:** galeria local funcional; metadados/agrupamentos e seletor
  visual de pasta ainda são expansões futuras.

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

1. importar e revisar integralmente as enciclopédias locais Marvel/DC;
2. validar a cobertura e associação final de imagens;
3. testar a STAR TV em Windows com WebView2/pywebview;
4. validar microfone, alto-falante e voz oficial no hardware local;
5. executar toda a suíte CI do HEAD final sem falhas.

A ausência de sprites emocionais específicos não é mascarada: os antigos
arquivos eram placeholders vazios. Até existirem artes reais, a GUI usa uma
skin/asset válido com indicador de emoção.

Veja:

- `docs/V3_0_AUDIT_2026-09-01.md` — auditoria atual;
- `docs/V3_0_AUDIT_2026-08-31.md` — histórico da consolidação inicial;
- `docs/V3_0_KNOWLEDGE.md`;
- `docs/MASTER_ROADMAP.md`.
