# ⌚ STAR Watch V0 — Experimental Device Bridge

## Estado

**EXPERIMENTAL / opt-in.** Este trabalho não antecipa o ECOSYSTEM completo da
V9.0. Ele valida somente a ponte mínima necessária para usar um relógio Android
como endpoint da mesma STAR que roda no PC.

## Princípio arquitetural

```text
STAR WATCH / CELULAR / FUTURO CORPO
        sensores + interface
                │
                │ LAN
                ▼
            STAR CORE
        processamento central
                │
                ▼
        resposta / comando
```

O relógio **não contém uma segunda STAR**, não possui identidade separada e não
executa o raciocínio principal. Ele captura entradas e apresenta/execute saídas.

## Gateway do PC

O gateway fica desligado por padrão. Para iniciar a STAR com a ponte do relógio:

```powershell
.\INICIAR_STAR_WATCH.bat
```

O terminal mostrará:

- endereço LAN, por exemplo `http://192.168.1.20:8765`;
- código temporário de pareamento com 6 dígitos.

O cliente Android usa esse endereço e código uma vez. O servidor devolve um token
aleatório; somente o hash SHA-256 é persistido em `runtime/oni/devices.json`.
`runtime/` não deve ser versionado.

## Protocolo V0

- `GET /v1/health` — status do gateway;
- `POST /v1/pair` — pareamento por código temporário;
- `POST /v1/heartbeat` — presença do dispositivo;
- `POST /v1/text` — texto → mesmo `StarCore.process()` → resposta;
- `POST /v1/audio` — áudio → STT local do PC → StarCore → resposta;
- `POST /v1/image` — entrega imagem ao Core e salva na inbox local.

### Limite honesto da V0

O transporte de imagem é funcional, mas **STAR Vision ainda não existe na V1.9**.
A imagem é recebida e armazenada para integrar ao Vision Engine no marco V5.0.
O gateway informa explicitamente `vision_available: false` em vez de fingir que
analisou a imagem.

## Segurança inicial

- gateway desligado por padrão;
- ativação explícita pelo launcher do Watch;
- pareamento por código temporário;
- token por dispositivo;
- somente hash do token persiste no PC;
- limites de payload;
- nenhum segredo é commitado;
- usar apenas em uma LAN privada neste protótipo;
- não encaminhar a porta 8765 para a Internet.

O Permission Manager completo continua no roadmap posterior; portanto ações de
alto risco não devem ser expostas por este gateway experimental.

## Cliente Android

O projeto está em `clients/star_watch_android/` e usa Android nativo com
`minSdk 27`, compatível com Android 8.1. O objetivo da V0 é funcionar inclusive
em hardware modesto como o HW Ultra2 2/64 GB.

A primeira interface oferece:

1. endereço do STAR Core;
2. código de pareamento;
3. chat textual;
4. gravação de áudio e envio para o STT do PC;
5. captura de foto e envio ao Core.

A câmera V0 usa o app de câmera do Android e recebe um bitmap de preview. Isso é
proposital: primeiro validamos o protocolo e o fluxo; câmera de resolução total e
módulo STAR Vision físico entram depois da prova de conceito.
