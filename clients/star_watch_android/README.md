# STAR Watch Android V0.2

Cliente experimental para Android 8.1+ (`minSdk 27`). O app não contém o MIND da
STAR: ele envia sensores/entradas ao STAR Core no PC e mostra a resposta.

## Funções

- pareamento LAN por código temporário;
- chat textual;
- microfone → áudio AAC/M4A → STT local no PC → STAR Core → resposta;
- resposta falada pelo TTS do Android, controlada pelo runtime do Core;
- câmera → JPEG → inbox local do STAR Core;
- heartbeat e sincronização de `/v1/runtime`;
- rótulos e feature flags compartilhados com STAR Mobile iOS;
- token persistido no armazenamento privado do app.

A captura de câmera usa `ACTION_IMAGE_CAPTURE` e envia o bitmap de preview. Isso
mantém a prova de conceito pequena. Captura de resolução total e streaming ficam
para a evolução do STAR Vision.

## 1. Iniciar o PC

Na raiz da STAR:

```powershell
.\INICIAR_STAR_DEVICES.bat
```

`INICIAR_STAR_WATCH.bat` continua existindo como alias compatível.

## 2. Gerar o APK

O workflow `STAR Watch Android` gera `star-watch-debug-apk` como artifact. Também
é possível abrir `clients/star_watch_android` no Android Studio ou executar:

```powershell
gradle -p clients\star_watch_android :app:assembleDebug
```

## 3. Transferir por USB

Com ADB instalado e depuração USB habilitada no relógio:

```powershell
.\INSTALAR_STAR_WATCH.bat
```

## 4. Parear

1. informe `http://IP_DO_PC:8765`;
2. informe o código exibido no PC;
3. toque `PAREAR`;
4. autorize microfone/câmera quando solicitado.

PC e relógio precisam estar na mesma LAN. Não exponha a porta 8765 à Internet.

## Runtime adaptativo

Depois do pareamento o Watch recebe o perfil `watch` do mesmo
`STAR_MANIFEST.json` usado pelo iPhone. A cada 30 segundos envia heartbeat; se a
revisão do runtime mudou, baixa novamente rótulos e feature flags. Mudanças de
código Java ainda exigem um novo APK.
