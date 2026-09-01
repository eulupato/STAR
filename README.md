# ⭐ STAR — V3.0 KNOWLEDGE

S.T.A.R. — **System for Thought, Analysis and Response**.

A STAR é uma plataforma cognitiva modular **local-first**. A V3.0 absorve a
fundação V1.9, consolida a MIND construída na V2.0 e introduz a arquitetura de
conhecimento offline expansível.

> **LOCAL é a STAR completa. LAN e Internet são expansões, não requisitos para
> que ela exista.**

## Versão

A única fonte de verdade da versão pública é:

`STAR_MANIFEST.json`

O restante do projeto lê a versão por `core/release.py`. Launcher, GUI,
diagnóstico e configuração não devem possuir números de versão hardcoded.

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
- relações/Knowledge Graph;
- fontes e proveniência;
- Universal Search;
- Knowledge Packs;
- importadores reutilizáveis;
- pipeline de PDF;
- primeira Ilha de Conhecimento: Heróis.

Dados locais, PDFs e caches ficam fora do Git.

## 🦸 Ilha dos Heróis

A ilha está ligada ao Knowledge Engine e oferece:

- busca por nome, alias, universo, espécie, descrição, poderes e tags;
- filtro de universo;
- navegação anterior/próximo por componente genérico;
- ficha do personagem;
- fonte e página;
- fallback de imagem;
- contexto da entidade selecionada para a conversa.

O antigo `heroes.json` permanece somente como seed de compatibilidade até que
a base local seja importada.

### Importar enciclopédias locais

```powershell
.\.venv\Scripts\python.exe tools\import_heroes.py "C:\caminho\Marvel Encyclopedia New Edition.pdf" --universe Marvel --publisher "Marvel Comics" --ocr

.\.venv\Scripts\python.exe tools\import_heroes.py "C:\caminho\The DC COMICS Encyclopedia.pdf" --universe DC --publisher "DC Comics"
```

`--ocr` usa Tesseract local somente quando a página não possui texto
suficiente. O PDF e as imagens renderizadas permanecem na máquina local.

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

Controles preparados:

- abrir;
- play/pause;
- volume;
- fullscreen;
- restore;
- fechar;
- estado.

## Execução

```powershell
INICIAR_STAR.bat
```

ou:

```powershell
.\.venv\Scripts\python.exe main.py
```

Diagnóstico:

```powershell
.\.venv\Scripts\python.exe diagnostico.py
```

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

GitHub Actions valida Linux e Windows.

## Estado de desenvolvimento

A arquitetura V3 está integrada nesta branch, mas a release só deve ser marcada
como **READY** depois de:

1. importar e revisar integralmente as enciclopédias locais;
2. validar a extração de imagens/associação de referências;
3. testar a STAR TV em Windows com WebView2/pywebview;
4. executar toda a suíte CI sem falhas;
5. validar regressões de voz, GUI e hardware local.

Veja:

- `docs/V3_0_AUDIT_2026-08-31.md`
- `docs/V3_0_KNOWLEDGE.md`
- `docs/MASTER_ROADMAP.md`
