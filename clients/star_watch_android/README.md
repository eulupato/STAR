# STAR Watch Android V0.3

Cliente experimental Android 8.1+ (`minSdk 27`). O relógio **não contém o MIND da STAR**: ele funciona como interface/sensor da mesma STAR processada pelo PC.

## Funções atuais

- pareamento LAN por código temporário;
- chat textual;
- microfone → AAC/M4A → STT local no PC → STAR Core → resposta;
- resposta falada por TTS do Android, conforme runtime do Core;
- câmera → JPEG → inbox local do STAR Core;
- heartbeat e sincronização de `/v1/runtime`;
- token persistido no armazenamento privado do app;
- interface V0.3 com fundo OLED escuro, living energy frame e símbolo STAR;
- círculo + triângulo invertido com revelação curta de estrela.

A captura de câmera continua usando `ACTION_IMAGE_CAPTURE` e bitmap de preview. Isso mantém a beta pequena. Captura de resolução total/streaming e análise visual pertencem à evolução do STAR Vision.

Saúde e GPS são **estruturas planejadas**, não dados simulados nesta versão.

## 1. Iniciar o PC

Na raiz da STAR:

```powershell
.\INICIAR_STAR_DEVICES.bat
```

`INICIAR_STAR_WATCH.bat` continua como alias compatível.

## 2. Testar o conceito sem smartwatch

A beta possui uma interface funcional para Windows:

```powershell
.\INICIAR_STAR_WATCH_PC.bat
```

Ela reutiliza o STAR Core, identidade, conhecimento, STT e TTS do projeto e não carrega STAR WORLD.

## 3. Gerar o APK

O workflow `STAR Watch Android` gera o APK de debug. Também é possível abrir `clients/star_watch_android` no Android Studio ou executar:

```powershell
gradle -p clients\star_watch_android :app:assembleDebug
```

## 4. Transferir por USB

Com ADB instalado e depuração USB habilitada no relógio:

```powershell
.\INSTALAR_STAR_WATCH.bat
```

## 5. Parear

1. informe `http://IP_DO_PC:8765`;
2. informe o código exibido no PC;
3. toque `PAREAR`;
4. autorize microfone/câmera quando solicitado.

PC e relógio precisam estar na mesma LAN. Não exponha a porta 8765 à Internet.

## Runtime adaptativo

Depois do pareamento o Watch recebe o perfil `watch` do mesmo `STAR_MANIFEST.json` usado pelos outros endpoints. Tema, rótulos e feature flags permanecem centralizados.

Mudanças nativas Java/layout ainda exigem um novo APK.

## Limites honestos

Ainda não existem no Watch V0.3:

- Vision Engine;
- dados reais de saúde sem hardware/sensor;
- GPS conectado nesta beta;
- biometria facial/voz;
- Permission Manager completo;
- ações privilegiadas remotas do PC;
- full duplex/streaming voice.

O foco é validar uma interface diária simples e funcional antes de expandir o ecossistema.
