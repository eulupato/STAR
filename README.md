# ⭐ STAR — V1.9 FINAL

S.T.A.R. — **System for Thought, Analysis and Response**.

A STAR é uma plataforma cognitiva modular **offline-first**, com identidade própria,
memória, conhecimento local, interface, STAR WORLD e ferramentas. A identidade da
STAR permanece separada dos modelos que ela utiliza.

> **V1.9 é a fundação estável. O desenvolvimento seguinte acontece em V2.0 MIND.**

## Execução no Windows

Use `INICIAR_STAR.bat` para a STAR local. Para ativar endpoints LAN experimentais
(iPhone/Watch), use:

`INICIAR_STAR_DEVICES.bat`

`INICIAR_STAR_WATCH.bat` permanece como alias compatível.

Se o ambiente principal ainda não existir, execute `CRIAR_AMBIENTE.bat`.
Para instalar os modelos de voz locais, execute `INSTALAR_VOZ.bat`.

## Voz — arquitetura final da V1.9

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

No modo `official`, a STAR não usa Piper silenciosamente se Chatterbox/referência
estiverem ausentes. `STAR_VOICE_MODE=fast` ativa explicitamente o modo rápido.
A referência da voz oficial é local, privada e não é distribuída pelo GitHub.

## Estrutura principal

```text
STAR/
├── core/                  # identidade, roteamento, memória e cérebro
├── clients/               # endpoints leves iOS/Android
├── database/              # persistência
├── gui/                   # interface 2D atual / STAR WORLD
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

- identidade STAR independente do modelo;
- Core, router e Executive atuais;
- memória persistente básica;
- matemática em linguagem natural;
- Knowledge Packs locais e removíveis;
- chat e interface 2D;
- HUB, ilhas, Casa e Closet;
- skins;
- STT local com faster-whisper tiny;
- voz oficial local com Chatterbox;
- Piper e SAPI como fallbacks;
- controle inicial do computador;
- navegador, busca e Spotify como primeiras ferramentas;
- diagnósticos;
- CI de sintaxe, manifestos e smoke tests.

## 📡 STAR Devices V0.2 — experimental

A Foundation possui uma ponte opt-in para validar o princípio do STAR ONI sem
antecipar V9. Endpoints não possuem MIND separado.

```text
📱 iPhone / ⌚ Watch / futuros endpoints
               │
               │ LAN
               ▼
          ⭐ STAR Core PC
               │
               ▼
        resposta / estado
```

Atualmente:

- `clients/star_mobile_ios/` — STAR Mobile iOS V0, iOS 15+;
- `clients/star_watch_android/` — STAR Watch Android V0.2, Android 8.1+;
- texto → mesmo STAR Core;
- áudio → faster-whisper no PC → mesmo STAR Core;
- imagem → inbox local do Core;
- TTS de endpoint apenas vocaliza a resposta textual;
- ações locais do PC permanecem bloqueadas para origem remota.

### Adaptive Runtime

`STAR_MANIFEST.json > device_ecosystem` é a fonte de verdade para tema, rótulos,
feature flags e perfis `phone/watch`. O Gateway serve `/v1/runtime`; heartbeats
permitem que clientes detectem revisão nova e reapliquem configuração.

Isso sincroniza mudanças de configuração/comportamento sem duplicação. Código
nativo Swift/Java ainda exige rebuild do aplicativo.

A imagem é transportada corretamente, porém não é analisada na V1.9. O Vision
Engine continua reservado para V5 SENSES.

Veja `docs/STAR_DEVICE_ECOSYSTEM_V0.md`, `clients/star_mobile_ios/README.md` e
`clients/star_watch_android/README.md`.

## 💾 Knowledge Packs em pendrive

A STAR reconhece packs estruturados em mídia removível sem copiá-los para o
repositório. Na raiz do pendrive:

```text
STAR_KNOWLEDGE/
└── packs/
    └── nome_do_pack/
        ├── manifest.json
        └── knowledge.jsonl
```

O loader aceita somente JSON/JSONL estruturado, mantém proveniência, limita o
tamanho dos arquivos e impede `content_file` de escapar da pasta do pack. A
mídia não executa código. A ingestão automática de livros/PDFs, embeddings e RAG
continuam pertencendo à V3.0 KNOWLEDGE.

## STAR WORLD

O catálogo atual inclui HUB, Casa, Laboratório, Central de Criação, Biblioteca,
Estúdio, Observatório, Jardim, Correio, Cura, Heróis e Idiomas. Na V1.9 alguns
ambientes ainda são representações visuais ou pontos de entrada.

## Offline-first

- **LOCAL** — STAR funciona no computador sem internet;
- **LAN** — adiciona dispositivos locais;
- **ONLINE** — acrescenta recursos externos opcionais.

Internet amplia a STAR; não constitui a STAR.

## Desenvolvimento

- `main` — releases estáveis;
- `v1.9-development` — branch histórica da construção da V1.9;
- a próxima geração é **V2.0 MIND**.

Veja `docs/MASTER_ROADMAP.md`.

## Segurança e privacidade

Modelos, caches, bancos locais, ambientes virtuais, referências de voz,
credenciais, tokens de dispositivos e arquivos temporários não devem ser
versionados.

O STAR Device Gateway fica desligado por padrão, usa pareamento local e deve ser
usado somente em LAN privada nesta fase. Não exponha a porta do protótipo à
Internet.

## Estado

**STAR V1.9 FINAL / stable**

Bugs descobertos após a release entram como V1.9.x. Novas arquiteturas cognitivas
entram na V2.0 MIND. As pontes mobile/watch permanecem experimentais até seus
marcos oficiais.
