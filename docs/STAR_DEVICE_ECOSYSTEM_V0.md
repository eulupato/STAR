# ⭐ STAR Device Ecosystem V0.3 — ponte experimental

## Estado

**EXPERIMENTAL / opt-in.** Esta infraestrutura valida PC + iPhone + Watch sem antecipar o ECOSYSTEM completo da V9.0.

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

Não existe uma STAR separada no celular ou relógio. Identidade, memória, conhecimento, raciocínio e decisões continuam na fonte central.

## Adaptive Runtime

A fonte de verdade é:

```text
STAR_MANIFEST.json
└── device_ecosystem
```

O Gateway transforma esse bloco em `/v1/runtime` e escolhe perfil pelo form factor:

- `phone` — interface confortável;
- `watch` — interface compacta de cantos arredondados.

O runtime inclui revisão por hash, schema/protocolo, tema, rótulos, feature flags e perfil.

No V0.3 o perfil Watch também declara a direção visual do living energy frame, o símbolo círculo + triângulo invertido/estrela e as telas Home, Voz, Saúde, GPS, Visão e Configurações.

## Endpoints

- `GET /v1/health` — saúde do gateway;
- `POST /v1/pair` — pareamento + runtime inicial;
- `GET /v1/device` — registro público do endpoint;
- `GET /v1/runtime` — experiência adaptativa;
- `POST /v1/heartbeat` — presença + revisão;
- `POST /v1/text` — texto → mesmo STAR Core;
- `POST /v1/audio` — áudio → STT no PC → STAR Core;
- `POST /v1/image` — imagem → inbox do Core.

## Voz

Entrada atual:

```text
microfone endpoint
→ AAC/M4A
→ LAN
→ faster-whisper no PC
→ STAR Core
```

Saída atual no Android:

```text
resposta textual do Core
→ endpoint
→ TTS nativo Android
```

O PC Preview usa o `VoiceManager` local da STAR. Streaming/full duplex e unificação final da voz entre dispositivos continuam vinculados à evolução do STAR Voice/SENSES.

## Imagem

A câmera transporta imagens para o Core, porém `vision_analysis=false`. A V1.9 não finge percepção visual.

## Saúde e localização

`health_transport=false` e `location_transport=false` nesta beta. As telas existem para validar a experiência, mas não inventam sensores nem coordenadas.

## Segurança

- Gateway desligado por padrão;
- ativação explícita;
- LAN privada;
- pareamento por código temporário;
- token aleatório por dispositivo;
- somente SHA-256 do token persiste no PC;
- payloads limitados;
- rate limit de pareamento e dispositivo;
- erros internos não são expostos ao endpoint;
- ações locais do PC bloqueadas para origem remota com `allow_actions=False`;
- `privileged_actions=false` no runtime.

Isso ainda não substitui firewall, TLS, biometria, Permission Manager ou a segurança completa de GUARDIAN/ECOSYSTEM.

## Clientes

### STAR Mobile iOS V0

- iOS 15+;
- chat, voz, câmera, resposta falada e runtime adaptativo;
- instalação física exige assinatura Apple.

### STAR Watch Android V0.3

- Android 8.1+;
- texto, voz, câmera, TTS e runtime adaptativo;
- nova direção visual do Watch;
- APK via Android build/ADB.

### STAR Watch PC Preview V0.3

- Windows/Tkinter;
- reutiliza a mesma STAR local;
- não carrega STAR WORLD;
- permite testar interface, logo, estados, gestos simulados, texto e voz antes do hardware físico.

## Relação com o roadmap

Esta ponte continua sendo uma validação transversal na Foundation. Ela **não declara V5 SENSES ou V9 ECOSYSTEM concluídas**. Device Manager completo, sync offline-first, permissões avançadas, sensores e visão permanecem nos marcos apropriados.
