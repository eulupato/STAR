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

### Construir a Ilha dos Heróis

O fluxo recomendado usa um único comando. O PDF é a base local complementar e
mantém página/proveniência; quando `--online` é informado, a fonte oficial
Marvel/DC é tratada como autoritativa para os campos que realmente fornece.

Para Marvel, o builder também descobre em lote o índice oficial de personagens,
preserva variantes de identidade (por exemplo, Peter Parker e Miles Morales)
como entidades distintas e percorre todos os registros encontrados sem um
limite artificial de enriquecimento.

A enciclopédia Marvel usada no projeto é majoritariamente escaneada. Para a
extração integral por OCR, o executável Tesseract precisa estar instalado e
disponível no `PATH`. Se OCR for solicitado sem Tesseract, o builder interrompe
com uma mensagem explícita em vez de fingir que a importação foi completa.

```powershell
.\.venv\Scripts\python.exe tools\build_heroes_island.py `
  --marvel-pdf "C:\caminho\Marvel Encyclopedia New Edition.pdf" `
  --dc-pdf "C:\caminho\The DC COMICS Encyclopedia.pdf" `
  --online
```

Fontes oficiais autorizadas pelo projeto:

- `https://www.marvel.com/characters`
- índice A-Z oficial em `https://www.marvel.com/comics/characters`
- `https://www.dc.com/characters`

O builder grava apenas dados estruturados, proveniência e caches locais. Ele
não coloca PDFs, páginas das enciclopédias ou cache web no GitHub.

No Windows, o catálogo Marvel completo pode ser construído também por:

```powershell
ATUALIZAR_CATALOGO_MARVEL.bat
```

O arquivo pede o caminho do PDF, executa a importação OCR, descobre o catálogo
oficial, enriquece os perfis e salva as imagens apenas no cache local.

Ao final é criado:

`knowledge/local/reports/heroes_build_report.json`

com total de personagens, cobertura de imagens, fontes PDF/oficiais e itens
ainda incompletos.

A ilha continua funcionando sem internet depois que a base foi construída.

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
