# ⭐ STAR — S.T.A.R.

**S.T.A.R. — System for Thought, Analysis and Response**

A STAR é uma arquitetura **offline-first** formada por identidade, Core, memória,
conhecimento local, voz, ferramentas, interfaces e dispositivos. Modelos locais ou
cloud são recursos utilizados pela STAR; nenhum modelo isolado é a STAR.

## Direção atual do projeto

A prioridade prática passa a ser o **STAR Watch App**.

```text
1. construir e validar a experiência do relógio no PC;
2. portar o shell validado para Android/smartwatch real;
3. integrar sensores e hardware reais por providers;
4. depois construir a nova experiência principal para PC.
```

A Foundation V1.9 continua preservada como base estável do Core. Ela não está sendo
reconstruída nem descartada; o Watch reutiliza o que já funciona.

## ⌚ STAR Watch App V0.4

A V0.4 inaugura a abordagem **Watch-first** e roda atualmente como simulador no PC.

Para abrir:

```bat
INICIAR_STAR_WATCH_APP.bat
```

ou:

```powershell
.\.venv\Scripts\python.exe clients\star_watch_app.py
```

### STAR Ring

A interação do relógio não depende de um modelo específico de hardware.
O app trabalha com um contrato de entrada equivalente a:

```text
ROTATE_LEFT
ROTATE_RIGHT
PRESS
BACK
```

No simulador:

- roda do mouse ou setas esquerda/direita = girar o STAR Ring;
- clique no núcleo ou Enter = pressionar/confirmar;
- Backspace = voltar;
- Espaço = iniciar/encerrar voz.

No hardware real esses mesmos eventos poderão vir de bezel, coroa ou do futuro
anel físico próprio da STAR.

### Modos atuais

- **VOZ** — microfone → STT local → STAR Core → resposta → TTS;
- **BUSCA** — usa a capacidade de pesquisa já existente no Core;
- **SAÚDE** — UX pronta com provider simulado claramente identificado;
- **GPS** — UX pronta com provider simulado claramente identificado;
- **VISÃO** — prepara STAR Scan e permite selecionar uma imagem no simulador;
- **PEOPLE** — cadastro pessoal manual e local;
- **MEDIR** — UX STAR Measure com provider simulado até existir laser real;
- **MÍDIA** — reaproveita comandos de mídia existentes;
- **CLIMA** — interface pronta, sem inventar meteorologia;
- **CONFIG** — simulação e resposta falada.

### O que é real e o que é simulado

A V0.4 **não finge possuir hardware inexistente**.

No PC, GPS, saúde e distância aparecem como `SIMULAÇÃO` quando ativados. Vision AI,
laser físico, reconhecimento automático de pessoas, clima online e agregação
multi-loja avançada ainda não são declarados como disponíveis.

O cadastro PEOPLE fica em:

```text
runtime/star_watch/people.json
```

e permanece fora da base versionada.

Veja `docs/STAR_WATCH_APP_V0_4.md`.

## Android Watch V0.3

A base Android já existente continua sendo preservada em:

```text
clients/star_watch_android/
```

Ela fornece:

- Android 8.1+ (`minSdk 27`);
- pareamento LAN;
- texto;
- microfone PCM 16-bit mono/WAV;
- STT no Core;
- resposta falada pelo TTS do endpoint;
- câmera;
- heartbeat;
- runtime adaptativo;
- comandos de voz centralizados.

A V0.4 não cria um segundo cliente Android. Primeiro valida a experiência no PC e,
no próximo marco, porta o shell circular para essa base Android.

## Voz

Arquitetura local atual:

```text
Microfone
    ↓
AudioRecorder / PCM
    ↓
faster-whisper local PT-BR
    ↓
STAR Core
    ↓
Chatterbox oficial / modo rápido local
    ↓
Alto-falante
```

A referência da voz oficial continua privada e local. Não deve ser enviada ao Git.
Seed-VC permanece opcional e separado do ambiente principal.

## Command / Capability Foundation

A STAR usa um registro central de intents em `core/commands.py`.
Mais de mil frases podem ser geradas a partir de templates sem manter milhares de
`if/else` duplicados.

`core/agents.py` funciona como catálogo/dispatcher de capacidades especializadas.
Essas capacidades **não são personalidades nem STARs separadas**.

Comandos sensíveis originados de Watch/Mobile permanecem restritos. Screenshot,
busca de arquivos, terminal, PowerShell, fechamento de aplicações e bloqueio do PC
não devem ser liberados remotamente sem confirmação local/permissões apropriadas.

## Estrutura principal

```text
STAR/
├── clients/
│   ├── star_watch_app.py       # STAR Watch V0.4 — simulador principal
│   ├── star_watch_android/     # transporte Android V0.3
│   └── star_mobile_ios/        # cliente iOS experimental
├── core/                       # identidade, Core, comandos e capacidades
├── database/                   # persistência
├── gui/                        # interface PC anterior preservada
├── knowledge/                  # Knowledge Packs
├── modules/                    # ferramentas
├── voice/                      # STT/TTS/Seed-VC opcional
├── tests/                      # testes automatizados
├── docs/                       # documentação
├── STAR_MANIFEST.json          # capacidades/versões declaradas
├── INICIAR_STAR_WATCH_APP.bat
├── INICIAR_STAR.bat
└── main.py
```

## STAR Core no PC

A interface desktop anterior continua disponível e pode ser iniciada por:

```bat
INICIAR_STAR.bat
```

ou:

```powershell
.\.venv\Scripts\python.exe main.py
```

Ela permanece preservada enquanto a nova experiência Watch-first é desenvolvida.
A nova versão principal para PC será construída depois que o shell do relógio estiver
estável.

## STAR Device Gateway

A ponte LAN permanece experimental e desligada por padrão.

Para testes de dispositivos:

```bat
INICIAR_STAR_DEVICES.bat
```

O Gateway possui pareamento local, token por dispositivo, runtime adaptativo e rate
limits. Deve permanecer em rede privada; não exponha a porta experimental à Internet.

## Offline-first

A STAR mantém três níveis operacionais:

- **LOCAL** — funções fundamentais no dispositivo/PC;
- **LAN** — cooperação entre dispositivos locais;
- **ONLINE** — internet expande capacidades quando autorizada.

Internet não define a existência da STAR.

## Desenvolvimento

Antes de considerar uma atualização concluída:

```powershell
python diagnostico.py
python -m pytest -q tests
```

Além dos testes automáticos, interfaces, microfone, sensores e hardware precisam de
validação física quando a mudança depender deles.

Nunca versione `.env`, tokens, bancos pessoais, referências privadas de voz, modelos,
caches, fotos pessoais ou arquivos temporários.

## Estado atual

- **STAR Core/Foundation:** V1.9 stable;
- **STAR Watch App:** V0.4 functional simulator;
- **STAR Watch Android transport:** V0.3 experimental;
- **STAR Mobile iOS:** experimental;
- **hardware STAR próprio:** conceito/futuro.

A prioridade atual é transformar o STAR Watch V0.4 em um aplicativo de relógio sólido,
rápido e coerente antes de iniciar a nova experiência principal de PC.
