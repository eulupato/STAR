# ⭐ STAR — V1.9 FINAL

S.T.A.R. — **System for Thought, Analysis and Response**.

A STAR é uma plataforma cognitiva modular **offline-first**, com identidade própria, memória, conhecimento local, voz, ferramentas e interfaces. A identidade da STAR permanece separada dos modelos que ela utiliza.

> **V1.9 é a fundação estável. O próximo marco estrutural é V2.0 MIND.**

## Foco atual

Em setembro de 2026 o projeto entrou em um período de **foco funcional**: novas expansões de STAR WORLD ficam temporariamente pausadas enquanto conversa, voz, MIND, conhecimento, funções cotidianas e Watch são consolidados.

Nada do WORLD é descartado. O objetivo é evitar continuar ampliando muitas partes incompletas antes da STAR estar útil no dia a dia.

## Execução no Windows

STAR desktop tradicional:

```powershell
.\INICIAR_STAR.bat
```

ou:

```powershell
.\.venv\Scripts\python.exe main.py
```

STAR Watch Functional Beta no PC, **sem carregar STAR WORLD**:

```powershell
.\INICIAR_STAR_WATCH_PC.bat
```

Endpoints LAN experimentais (iPhone/Watch):

```powershell
.\INICIAR_STAR_DEVICES.bat
```

`INICIAR_STAR_WATCH.bat` permanece como alias compatível.

Se o ambiente principal ainda não existir, execute `CRIAR_AMBIENTE.bat`. Para instalar modelos locais de voz, execute `INSTALAR_VOZ.bat`.

Diagnóstico:

```powershell
.\DIAGNOSTICO_VOZ.bat
```

## Voz — arquitetura atual

```text
🎤 Microfone
    ↓
sounddevice / AudioRecorder
    ↓
faster-whisper tiny (STT PT-BR, local, CPU INT8)
    ↓
STAR Core
    ↓
⭐ Chatterbox — voz oficial da STAR
    ↓
sounddevice
    ↓
🔊 Alto-falante
```

### Política da voz na V1.9

No modo `official`, a STAR não usa Piper silenciosamente se Chatterbox ou a referência de voz estiverem ausentes. A falha é explícita.

```text
official → Chatterbox + referência local
fast     → Windows SAPI PT-BR/feminina quando disponível → Piper PT-BR
```

A referência oficial é privada/local, aceita `STAR_VOICE_REFERENCE` e também pode ser resolvida dentro de `voice/reference/`. Ela não deve ser distribuída pelo GitHub.

A conversa da GUI usa o modo rápido por padrão para baixa latência; o Chatterbox oficial continua disponível para alta fidelidade.

## Estrutura principal

```text
STAR/
├── core/                  # identidade, roteamento, memória e cérebro
├── clients/               # endpoints leves PC/iOS/Android
├── database/              # persistência
├── gui/                   # interface desktop / STAR WORLD atual
├── knowledge/             # Knowledge Packs
├── modules/               # ferramentas e automações
├── voice/                 # STT/TTS local
├── tests/                 # testes automatizados
├── docs/                  # roadmap e documentação
├── assets/                # recursos visuais
├── SKINS/                 # aparências locais
├── main.py
├── config.py
├── STAR_MANIFEST.json
└── INICIAR_STAR.bat
```

## Capacidades da V1.9

- identidade STAR independente de modelos;
- Core, Router e Executive;
- memória persistente básica;
- matemática em linguagem natural;
- Knowledge Packs locais e removíveis;
- chat e interface 2D;
- HUB, ilhas, Casa e Closet;
- skins;
- STT local com faster-whisper;
- voz oficial local com Chatterbox;
- Piper/SAPI para modo rápido;
- controle inicial do computador;
- primeiras ferramentas de navegador/busca/Spotify;
- diagnósticos e CI.

As capacidades existentes de STAR WORLD permanecem no repositório, mas novas expansões estão temporariamente congeladas pelo foco funcional atual.

## ⌚ STAR Watch V0.3 — Functional Beta

O Watch é uma **interface da mesma STAR do PC**. Não possui identidade, memória, conhecimento ou MIND paralelo.

```text
⌚ Watch / PC Preview
       │
       │ interface + sensores
       ▼
 ⭐ STAR Core no PC
       │
       ▼
 resposta / estado
```

### Preview funcional no PC

`clients/star_watch_pc.py` permite desenvolver e testar a experiência antes de possuir o hardware físico:

- não carrega `gui.app`/STAR WORLD;
- reutiliza `main.create_star()`;
- texto → STAR Core;
- microfone → STT → STAR Core;
- resposta falada;
- tela arredondada escura;
- living energy frame azul/ciano/lilás/rosa;
- símbolo círculo + triângulo invertido com revelação de estrela;
- Home, Voz, Saúde, GPS, Visão e Configurações;
- gestos simulados por mouse/teclado;
- ações privilegiadas bloqueadas.

Execute:

```powershell
.\INICIAR_STAR_WATCH_PC.bat
```

### Watch Android V0.3

`clients/star_watch_android/` mantém Android 8.1+ e o protocolo LAN já existente:

- pareamento por código temporário;
- token por dispositivo;
- texto → STAR Core;
- áudio → faster-whisper no PC → STAR Core;
- câmera → inbox local do Core;
- resposta falada por TTS Android;
- Adaptive Runtime;
- novo design visual V0.3.

O workflow `STAR Watch Android` compila o APK e `INSTALAR_STAR_WATCH.bat` mantém a instalação via ADB/USB.

### Limites honestos do Watch

Ainda não estão implementados:

- Vision Engine;
- sensores reais de saúde nesta beta;
- GPS real conectado;
- biometria facial/voz;
- Permission Manager completo;
- full duplex/streaming voice;
- ações privilegiadas remotas do PC.

Saúde/GPS aparecem apenas como estrutura visual e não inventam dados. A câmera é transportada, mas `vision_analysis=false`.

Veja:

- `docs/STAR_WATCH_V0.md`;
- `docs/STAR_DEVICE_ECOSYSTEM_V0.md`;
- `clients/star_watch_android/README.md`.

## 📱 STAR Devices — experimental

A Foundation possui uma ponte opt-in para iPhone/Watch/futuros endpoints, sem antecipar V9 ECOSYSTEM.

`STAR_MANIFEST.json > device_ecosystem` é a fonte de verdade compartilhada de tema, rótulos, feature flags e perfis `phone/watch`. O Gateway serve `/v1/runtime` e os clientes detectam revisões por heartbeat.

Mudanças de configuração podem refletir sem duplicar a STAR. Mudanças em código nativo ainda exigem rebuild do aplicativo.

## 💾 Knowledge Packs em mídia removível

A STAR reconhece packs estruturados sem copiá-los para o repositório:

```text
STAR_KNOWLEDGE/
└── packs/
    └── nome_do_pack/
        ├── manifest.json
        └── knowledge.jsonl
```

O loader aceita JSON/JSONL estruturado, mantém proveniência, limita tamanho e impede escape de caminho. A mídia não executa código.

Ingestão geral de livros/PDFs, embeddings, busca universal e Knowledge Graph ampliado permanecem em V3.0 KNOWLEDGE.

## STAR WORLD

O catálogo atual inclui HUB, Casa, Laboratório, Central de Criação, Biblioteca, Estúdio, Observatório, Jardim, Correio, Cura, Heróis e Idiomas.

Parte desses ambientes ainda é representação visual/ponto de entrada. O trabalho permanece preservado, mas novas expansões estão pausadas até a base funcional da STAR amadurecer. A reconstrução 3D continua no roadmap V6.0.

## Offline-first

Três estados arquiteturais:

- **LOCAL** — STAR no PC sem Internet;
- **LAN** — adiciona dispositivos locais;
- **ONLINE** — acrescenta recursos externos opcionais.

**Internet amplia a STAR; não constitui a STAR.**

## Segurança e privacidade

Modelos, caches, bancos locais, ambientes virtuais, referências de voz, credenciais, tokens e arquivos temporários não devem ser versionados.

O Device Gateway fica desligado por padrão, usa pareamento local, rate limits e deve ser utilizado apenas em LAN privada nesta fase. Não encaminhe a porta 8765 para a Internet.

Ações privilegiadas do PC permanecem bloqueadas nos endpoints remotos enquanto o Permission Manager completo não existe.

## Desenvolvimento

- `main` — releases estáveis;
- branches `feature/*` — desenvolvimento isolado;
- próximo marco estrutural: **V2.0 MIND**;
- Watch V0.3 — ponte experimental transversal, não uma nova geração da STAR.

Veja `docs/MASTER_ROADMAP.md`.

## Estado

**STAR V1.9 FINAL / stable**

Bugs após release entram como V1.9.x. Novas arquiteturas cognitivas entram na V2.0 MIND. Pontes Watch/Mobile permanecem experimentais até seus marcos oficiais.
