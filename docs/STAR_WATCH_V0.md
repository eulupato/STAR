# ⌚ STAR Watch V0.3 — Functional Beta

## Estado

**EXPERIMENTAL / opt-in / beta funcional.**

A direção atual do projeto prioriza uma STAR útil no dia a dia antes da expansão de STAR WORLD. O Watch é uma extensão leve da mesma STAR que roda no PC; não existe um segundo cérebro, identidade ou memória no relógio.

```text
STAR WATCH / PC PREVIEW
    interface + sensores
            │
            ▼
      STAR CORE NO PC
 identidade + conhecimento
 memória + raciocínio + voz
            │
            ▼
       resposta / estado
```

STAR WORLD, Ilhas e experiência 3D ficam fora do cliente Watch.

## Beta visual no PC

O arquivo `clients/star_watch_pc.py` permite testar a experiência do relógio imediatamente, sem possuir o hardware físico.

Inicie por:

```powershell
.\INICIAR_STAR_WATCH_PC.bat
```

O preview reutiliza diretamente:

- `main.create_star()` como composição oficial da STAR;
- identidade e conhecimento atuais;
- STAR Core;
- `AudioRecorder` existente;
- `VoiceManager` existente;
- STT local no PC;
- resposta falada local;
- `STAR_MANIFEST.json > device_ecosystem` como fonte do perfil visual.

Ele **não importa `gui.app`, não instancia `StarApp` e não carrega STAR WORLD**.

Ações privilegiadas do computador permanecem bloqueadas neste cliente com `allow_actions=False`.

## Design System do Watch

A interface foi desenhada para uma tela quadrada com cantos arredondados.

Base visual:

- fundo quase preto;
- conteúdo central simples;
- moldura luminosa contínua ao redor da tela;
- azul/ciano para escuta e presença;
- lilás/violeta para processamento;
- rosa/magenta para resposta e atividade;
- dourado reservado para eventos especiais;
- branco para informação principal.

O `STAR_MANIFEST.json` é a fonte única da paleta e das feature flags compartilhadas.

### Living Energy Frame

A moldura muda de comportamento conforme o estado:

```text
idle       → respiração lenta
listening  → energia ciano/azul mais ativa
thinking   → violeta/rosa em circulação
speaking   → azul → violeta → rosa
error      → vermelho/rosa/dourado
```

### Símbolo STAR

A identidade visual beta usa:

```text
círculo fino
    +
triângulo invertido
```

Ao interagir, o triângulo revela uma estrela por aproximadamente **720 ms** e retorna ao estado original. O símbolo é uma direção original da STAR e não replica um ativo da Marvel.

## Telas do PC Preview

### HOME

- hora e data locais;
- núcleo STAR;
- estado atual;
- acesso rápido à conversa.

### VOZ

- texto → mesmo STAR Core;
- microfone → áudio local → STT → STAR Core;
- resposta textual;
- resposta falada;
- estados `ouvindo`, `pensando` e `respondendo`.

### SAÚDE

A tela existe como estrutura, mas **não inventa batimentos, sono ou atividade**. Todos os valores ficam marcados como aguardando smartwatch até sensores reais e permissões serem integrados.

### GPS

O mapa atual é somente uma demonstração visual. Localização real e navegação não são declaradas como implementadas.

### VISÃO

O Android já possui transporte de câmera para o PC. O Vision Engine ainda não existe nesta versão, portanto imagens não são fingidas como analisadas.

### CONFIGURAÇÕES

A beta permite alternar:

- resposta falada;
- animações.

Também mostra explicitamente:

- ações remotas bloqueadas;
- pareamento/token no cliente Android;
- identidade STAR/creator;
- biometria e Permission Manager como ainda não implementados.

## Gestos do PC Preview

Como o PC não possui a tela touch do relógio, os gestos são simulados:

- clique no núcleo → iniciar/parar voz;
- arrastar horizontalmente → próxima/anterior tela;
- duplo clique → Home;
- pressionar por ~0,75 s → Configurações;
- roda do mouse ou setas ← → → navegar;
- Espaço → iniciar/parar voz;
- Esc → fechar.

Esses gestos validam o conceito de interação; a implementação nativa final depende do hardware comprado.

## Cliente Android V0.3

O projeto real continua em:

```text
clients/star_watch_android/
```

Compatibilidade atual:

```text
Android 8.1+
minSdk 27
versionName 0.3.0
```

Recursos preservados do V0.2:

- pareamento LAN por código temporário;
- token privado por dispositivo;
- texto → STAR Core;
- microfone → AAC/M4A → STT no PC → Core;
- resposta falada via TTS do endpoint;
- câmera → JPEG → inbox local do Core;
- heartbeat e Adaptive Runtime.

V0.3 acrescenta a nova direção visual, `StarVisualView`, moldura animada, símbolo STAR e layout escuro adequado ao Watch.

## Executar com o relógio Android

### 1. Iniciar o Core + Gateway no PC

```powershell
.\INICIAR_STAR_DEVICES.bat
```

`INICIAR_STAR_WATCH.bat` continua como alias compatível.

O terminal mostra:

- endereço LAN, como `http://192.168.1.20:8765`;
- código temporário de 6 dígitos.

### 2. Gerar o APK

O workflow `STAR Watch Android` compila o APK de debug. Também é possível abrir `clients/star_watch_android` no Android Studio ou executar:

```powershell
gradle -p clients\star_watch_android :app:assembleDebug
```

### 3. Instalar por ADB

Com o relógio conectado por USB e depuração habilitada:

```powershell
.\INSTALAR_STAR_WATCH.bat
```

### 4. Parear

No app:

1. informar `http://IP_DO_PC:8765`;
2. informar o código exibido pelo PC;
3. tocar `PAREAR`;
4. autorizar microfone/câmera somente quando usados.

PC e relógio devem estar na mesma LAN privada. Não exponha a porta 8765 à Internet.

## Segurança atual

A beta mantém:

- Gateway desligado por padrão;
- ativação explícita;
- código de pareamento temporário;
- token aleatório por dispositivo;
- somente hash SHA-256 persistido no PC;
- rate limit;
- limites de payload;
- ações locais privilegiadas bloqueadas para endpoints remotos;
- nenhum segredo versionado.

Não estão concluídos ainda:

- biometria facial;
- autenticação por voz;
- Permission Manager completo;
- Secrets Vault completo;
- TLS/endurecimento de rede para uso fora da LAN.

## Validação automatizada — 08/09/2026

No primeiro commit do V0.3 passaram:

- ✅ STAR CI;
- ✅ STAR quality;
- ✅ STAR security;
- ✅ STAR Windows smoke;
- ✅ STAR Watch Android build;
- ✅ STAR Mobile iOS build.

A validação visual/interativa do PC Preview ainda precisa ser feita no PC real. A validação do APK em smartwatch físico depende da compra do hardware.

## Próximos passos do Watch

1. validar o PC Preview localmente;
2. ajustar ergonomia e animações com base no uso real;
3. testar APK em emulador/hardware;
4. mapear gestos touch conforme o relógio comprado;
5. integrar localização real somente com permissão explícita;
6. integrar sensores de saúde suportados pelo hardware, sem inventar dados;
7. integrar o Voice Engine mais avançado conforme o STAR Voice evoluir;
8. adicionar autenticação/Permission Manager no marco de segurança adequado.

O Watch continua sendo **uma interface da STAR**, nunca uma STAR paralela.
