# 📱 STAR Mobile iOS V0

Cliente iOS experimental para a mesma STAR que roda no PC. O iPhone não possui
um MIND separado: câmera, microfone, tela e alto-falante são interfaces/sensores;
o processamento continua no STAR Core.

## Compatibilidade

- deployment target: **iOS 15.0+**;
- projeto pensado para iPhone, incluindo iPhone XR no iOS 18;
- SwiftUI + APIs nativas (AVFoundation, UIKit e URLSession);
- sem dependências de terceiros.

O iPhone XR não recebeu iOS 26, portanto o projeto deliberadamente não depende
de APIs novas dessas versões.

## Funções da V0

- pareamento LAN por código temporário;
- chat textual → STAR Core;
- comando de voz → gravação AAC/M4A → faster-whisper no PC → STAR Core;
- resposta em texto;
- resposta falada pelo sintetizador do próprio iOS (somente saída, sem raciocínio local);
- câmera → JPEG → inbox do STAR Core;
- heartbeat;
- sincronização do Adaptive Runtime;
- tema, rótulos e feature flags vindos do `STAR_MANIFEST.json` do PC.

## Executar o Core

Na raiz da STAR no Windows:

```powershell
.\INICIAR_STAR_WATCH.bat
```

Apesar do nome histórico do launcher, ele inicia o **STAR Device Gateway** geral,
usado por iPhone e Watch. O terminal mostra o endereço LAN e o código de
pareamento.

## Abrir o projeto iOS

Abra no Xcode:

```text
clients/star_mobile_ios/STARMobile.xcodeproj
```

Selecione o target `STARMobile` e o iPhone desejado.

### Instalação em iPhone físico

iOS exige assinatura de código. Para instalar diretamente em um iPhone XR é
necessário usar Xcode em macOS com uma Apple ID/equipe de desenvolvimento válida,
ou futuramente distribuir por TestFlight/App Store. O workflow do GitHub valida
compilação no Simulator, mas o artefato sem assinatura não pode ser instalado em
um iPhone físico.

## Pareamento

1. PC e iPhone na mesma LAN;
2. inicie o Device Gateway no PC;
3. no iPhone informe `http://IP_DO_PC:8765`;
4. informe o código de 6 dígitos;
5. toque `PAREAR`;
6. permita Rede Local, Microfone e Câmera quando o iOS solicitar.

A V0 usa HTTP somente na LAN privada para simplificar a prova de conceito. Não
encaminhe a porta 8765 para a Internet.

## Runtime adaptativo

O app consulta `/v1/runtime`. A fonte de verdade é o bloco `device_ecosystem` do
`STAR_MANIFEST.json`. O Core devolve o perfil `phone`, enquanto relógios recebem
`watch`.

Mudanças em tema, textos, feature flags e comportamento central podem aparecer
nos endpoints sem recompilar o app. Mudança em código Swift/Java continua
exigindo rebuild/atualização do binário.
