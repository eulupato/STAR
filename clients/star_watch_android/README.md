# STAR Watch Android V0

Cliente experimental para Android 8.1+ (`minSdk 27`). O app não contém o MIND da
STAR: ele envia sensores/entradas ao STAR Core no PC e mostra a resposta.

## Funções da V0

- pareamento LAN por código temporário;
- chat textual;
- microfone → áudio AAC/M4A → STT local no PC → STAR Core → resposta;
- câmera → JPEG → inbox local do STAR Core;
- token persistido no armazenamento privado do app.

A captura de câmera usa `ACTION_IMAGE_CAPTURE` e envia o bitmap de preview. Isso
mantém a prova de conceito compatível e pequena. Captura de resolução total e
streaming ficam para a evolução do STAR Vision.

## 1. Iniciar o PC

Na raiz da STAR:

```powershell
.\INICIAR_STAR_WATCH.bat
```

Anote o endereço e o código de 6 dígitos mostrados no terminal.

## 2. Gerar o APK

### GitHub Actions

O workflow `STAR Watch Android` gera `star-watch-debug.apk` como artifact.

### Android Studio

Abra `clients/star_watch_android` como projeto e execute `Build > Build APK(s)`.

### Gradle instalado no PC

```powershell
gradle -p clients\star_watch_android :app:assembleDebug
```

Saída:

```text
clients/star_watch_android/app/build/outputs/apk/debug/app-debug.apk
```

## 3. Transferir por USB

Com ADB instalado e depuração USB habilitada no relógio:

```powershell
.\INSTALAR_STAR_WATCH.bat
```

Ou manualmente:

```powershell
adb install -r clients\star_watch_android\app\build\outputs\apk\debug\app-debug.apk
```

## 4. Parear

No relógio:

1. informe `http://IP_DO_PC:8765`;
2. informe o código exibido no PC;
3. toque `PAREAR`;
4. autorize microfone/câmera quando solicitado.

PC e relógio precisam estar na mesma LAN. Não exponha a porta 8765 à Internet.
