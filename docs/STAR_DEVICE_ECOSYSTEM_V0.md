# ⭐ STAR Device Ecosystem V0.2 — ponte experimental

## Estado

**EXPERIMENTAL / opt-in.** Esta infraestrutura valida PC + iPhone + Watch sem
antecipar o ECOSYSTEM completo da V9.0.

## Regra permanente

```text
ENDPOINTS
(iPhone / Watch / futuro corpo)
      │
      │ sensores + interface
      ▼
STAR DEVICE GATEWAY
      │
      ▼
STAR CORE NO PC
      │
      │ processamento / resposta
      ▼
ENDPOINT ADEQUADO
```

Não existe uma STAR separada no celular ou relógio. Identidade, memória,
conhecimento, raciocínio e decisões continuam na fonte central.

## Adaptive Runtime

A fonte de verdade é:

```text
STAR_MANIFEST.json
└── device_ecosystem
```

O Gateway transforma esse bloco em `/v1/runtime` e escolhe um perfil conforme os
metadados do dispositivo:

- `phone` — interface confortável para celular;
- `watch` — interface compacta para relógio.

O runtime inclui:

- `revision` por hash;
- schema/protocolo;
- tema;
- rótulos;
- feature flags;
- perfil de layout;
- intervalo de sincronização.

Os endpoints enviam heartbeat com a revisão que possuem. Se o Core informa que
a revisão mudou, o cliente baixa o runtime novamente.

### O que muda sem recompilar os apps

- rótulos e textos controlados pelo runtime;
- paleta/tema nos clientes que aplicam essas propriedades;
- feature flags;
- comportamento central da STAR;
- disponibilidade de recursos expostos pelo Core.

### O que ainda exige atualização do app

- novo código Swift/Java;
- nova permissão do sistema operacional;
- mudança estrutural de tela não representada pelo runtime;
- novos sensores/APIs nativas.

Isso evita prometer atualização impossível: iOS e Android continuam exigindo
rebuild quando o binário nativo muda.

## Endpoints V0.2

- `GET /v1/health` — saúde, protocolo e revisão do runtime;
- `POST /v1/pair` — pareamento + metadados/capacidades + runtime inicial;
- `GET /v1/device` — registro público do endpoint;
- `GET /v1/runtime` — experiência adaptativa;
- `POST /v1/heartbeat` — presença + detecção de runtime alterado;
- `POST /v1/text` — texto → mesmo STAR Core;
- `POST /v1/audio` — áudio → STT no PC → STAR Core;
- `POST /v1/image` — imagem → inbox do Core.

## Voz

Entrada:

```text
microfone endpoint
→ AAC/M4A
→ LAN
→ faster-whisper no PC
→ STAR Core
```

Saída V0:

```text
resposta textual do Core
→ endpoint
→ TTS nativo iOS/Android
```

O TTS do endpoint apenas vocaliza texto; ele não pensa nem substitui a voz
oficial da STAR no PC. Streaming de voz e voz unificada entre dispositivos
continuam pertencendo a V5 SENSES.

## Imagem

A câmera já transporta imagens para o Core. **Análise visual continua desligada**
na V1.9 e só entra corretamente com V5 SENSES. O sistema retorna
`vision_available=false` em vez de fingir percepção.

## Segurança V0

- Gateway desligado por padrão;
- ativação explícita por `INICIAR_STAR_DEVICES.bat`;
- usar apenas em LAN privada;
- pareamento por código temporário;
- token aleatório por dispositivo;
- somente SHA-256 do token persiste no PC;
- payloads limitados;
- ações locais do PC continuam bloqueadas para origem remota (`allow_actions=False`);
- nenhum Device/Permission Manager completo é declarado como pronto.

## Clientes

### STAR Mobile iOS V0

- iOS 15+;
- iPhone XR no iOS 18 como alvo de compatibilidade;
- chat, voz, câmera, resposta falada e runtime adaptativo;
- build verificado por Xcode em GitHub Actions;
- instalação física requer assinatura Apple.

### STAR Watch Android V0.2

- Android 8.1+;
- chat, voz, câmera, TTS e runtime adaptativo;
- APK via Android build/ADB.

## Relação com o roadmap

Esta ponte prova conceitos de V9, mas **V9 continua não implementada**. Device
Manager completo, descoberta, Offline-first Sync, permissões avançadas e Network
Awareness permanecem no marco oficial.
