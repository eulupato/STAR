# ⭐ STAR — V1.9 FINAL

S.T.A.R. — **System for Thought, Analysis and Response**.

A STAR é uma plataforma cognitiva modular **offline-first**, com identidade própria,
memória, conhecimento local, interface, STAR WORLD e ferramentas. A identidade da
STAR permanece separada dos modelos que ela utiliza.

> **V1.9 é a fundação estável. O desenvolvimento seguinte acontece em V2.0 MIND.**

## Execução no Windows

Use:

`INICIAR_STAR.bat`

ou:

`\.venv\Scripts\python.exe main.py`

Se o ambiente principal ainda não existir, execute `CRIAR_AMBIENTE.bat`.
Para instalar os modelos de voz locais, execute `INSTALAR_VOZ.bat`.

Diagnóstico:

`DIAGNOSTICO_VOZ.bat`

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

### Política definitiva da voz na V1.9

No modo `official`, a STAR **não usa mais Piper silenciosamente** se o
Chatterbox ou a referência de voz estiverem ausentes. Em vez disso, a GUI e o
diagnóstico mostram a causa real.

```text
official → Chatterbox + referência local
fast     → Windows SAPI PT-BR/feminina quando disponível → Piper PT-BR
```

Para escolher o modo rápido explicitamente:

`STAR_VOICE_MODE=fast`

A referência da voz oficial é local e privada. A V1.9 aceita um caminho definido
por `STAR_VOICE_REFERENCE` e também detecta arquivos de áudio compatíveis dentro
de `voice/reference/`, portanto o nome do arquivo não precisa ser fixo.

Ela **não é distribuída pelo GitHub**. Use apenas uma referência de voz que você
tenha autorização para utilizar.

A V1.9 FINAL também cancela falas antigas quando uma nova interação começa,
evitando que uma resposta atrasada seja reproduzida depois de outra pergunta.


## Estrutura principal

```text
STAR/
├── core/                  # identidade, roteamento, memória e cérebro
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
- Knowledge Packs atuais;
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

## STAR WORLD

O catálogo atual inclui HUB, Casa, Laboratório, Central de Criação, Biblioteca,
Estúdio, Observatório, Jardim, Correio, Cura, Heróis e Idiomas.

Na V1.9 alguns ambientes ainda são representações visuais ou pontos de entrada.
A transformação em ambientes totalmente funcionais e posteriormente 3D está
planejada no roadmap.

## Offline-first

A arquitetura segue três estados:

- **LOCAL** — STAR funciona no computador sem internet;
- **LAN** — adiciona dispositivos da rede local;
- **ONLINE** — acrescenta recursos externos opcionais.

Internet amplia a STAR; não constitui a STAR.

## Desenvolvimento

- `main` — releases estáveis;
- `v1.9-development` — branch histórica da construção da V1.9;
- a próxima geração é **V2.0 MIND**.

Veja:

- `docs/MASTER_ROADMAP.md`
- `docs/V1_9_PLAN.md`
- `docs/V1_9_TEST_CHECKLIST.md`

## Segurança e privacidade

Modelos, caches, bancos locais, ambientes virtuais, referências de voz,
credenciais e arquivos temporários não devem ser versionados.

Nenhuma integração externa de voz é necessária para a V1.9.

## Estado

**STAR V1.9 FINAL / stable**

Bugs descobertos após a release entram como V1.9.x.
Novas arquiteturas cognitivas entram na V2.0 MIND.


## Auditoria de estabilidade — 31/08/2026

A interface não depende mais da existência de um nome fixo de referência de voz
para iniciar. O STT é pré-carregado em segundo plano, enquanto o Chatterbox
oficial só é carregado quando solicitado.

A conversa da GUI usa o modo rápido por padrão para que toda resposta textual
também tenha retorno falado em baixa latência. O modo oficial Chatterbox continua
disponível nas Configurações para testes e uso de alta fidelidade.

O modo OFFLINE agora bloqueia comandos de internet; ações locais continuam
disponíveis.
