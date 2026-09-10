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

O arquivo `clients/star_watch_pc.py` continua concentrando a lógica funcional do preview. A camada visual oficial do HOME fica em `clients/star_watch_visual.py`, que **reutiliza** `StarWatchPC` em vez de duplicar identidade, voz, memória ou lógica de interação.

Inicie por:

```powershell
.\INICIAR_STAR_WATCH_PC.bat
```

O launcher abre o renderer plasma oficial, que reutiliza diretamente:

- `main.create_star()` por meio do cliente funcional existente;
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

A direção visual oficial aprovada para o HOME é **Minimal Plasma Core**:

- fundo quase preto;
- grande área de respiro sem painéis desnecessários;
- moldura de plasma vivo acompanhando os cantos arredondados;
- um único núcleo central em plasma translúcido;
- símbolo STAR integrado ao núcleo: triângulo invertido com revelação breve de estrela;
- status mínimo abaixo do núcleo;
- sem relógio, data, cards, CTA grande ou barra de navegação no HOME;
- azul/ciano, lilás/violeta e rosa/magenta como energia principal;
- dourado reservado para eventos especiais/erro contextual quando necessário.

O `STAR_MANIFEST.json` é a fonte única da paleta, das feature flags e da declaração do estilo `minimal_plasma_core`.

### Plasma Frame

A moldura deixa de parecer uma linha rígida. Ela é formada por vários filamentos luminosos deslocados por ondas suaves, criando aparência de plasma/luz líquida contida na borda.

O comportamento muda conforme o estado:

```text
idle       → plasma lento e discreto
listening  → ciano/azul mais vivo
thinking   → violeta/rosa em circulação mais rápida
speaking   → azul → violeta → rosa com maior intensidade
error      → alerta visual sem substituir a linguagem principal da STAR
```

O PC Preview gera esse efeito proceduralmente com Pillow; não depende de GIF, vídeo externo ou asset de terceiros.

### Plasma Core

O núcleo central é a principal interface do HOME.

Ele combina:

- corpo translúcido azul/violeta/rosa;
- manchas suaves internas para sensação de fluido/plasma;
- múltiplos halos luminosos;
- órbitas finas em movimento;
- triângulo invertido da STAR;
- revelação de estrela por aproximadamente **720 ms** quando há interação.

A identidade visual continua sendo original da STAR e não replica um ativo da Marvel.

## HOME minimalista

O HOME oficial não exibe informação que não seja necessária.

Visualmente:

```text
fundo escuro
+
moldura plasma
+
núcleo central
+
status mínimo
```

O status acompanha o fluxo real:

- `PRONTA`;
- `OUVINDO`;
- `PENSANDO`;
- `RESPONDENDO`;
- `ATENÇÃO` em erro.

Ao iniciar voz a partir do HOME, o preview permanece nessa superfície minimalista durante `ouvindo → pensando → respondendo`, em vez de trocar de tela imediatamente. Depois da resposta falada, retorna a `PRONTA`.

## Telas funcionais preservadas

A simplificação do HOME **não removeu** as demais funções.

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

Como o HOME não possui barra de navegação visível, a navegação fica prioritariamente gestual:

- clique no núcleo → iniciar/parar voz;
- arrastar horizontalmente → próxima/anterior tela;
- duplo clique → Home;
- pressionar por ~0,75 s → Configurações;
- roda do mouse ou setas ← → → navegar;
- Espaço → iniciar/parar voz;
- Esc → fechar.

Nas telas funcionais secundárias, a navegação visual existente continua disponível.

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

O Android continua com `StarVisualView` e o perfil compartilhado. O acabamento final do layout físico continuará condicionado à validação do smartwatch real para não sacrificar pareamento, legibilidade ou ergonomia antes de conhecer a tela/hardware exatos.

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

## Validação

A beta funcional anterior já havia passado:

- ✅ STAR CI;
- ✅ STAR quality;
- ✅ STAR security;
- ✅ STAR Windows smoke;
- ✅ STAR Watch Android build;
- ✅ STAR Mobile iOS build.

Em 08/09/2026 o PC Preview original também foi validado visualmente no PC real, e o redesenho **Minimal Plasma Core** substituiu o HOME informativo anterior sem alterar o STAR Core nem remover as telas funcionais.

A validação física do APK em smartwatch continua dependente da compra do hardware.

## Próximos passos do Watch

1. validar o novo HOME plasma no PC real;
2. medir fluidez/CPU do renderer procedural e otimizar se necessário;
3. testar APK em emulador/hardware;
4. adaptar o mesmo minimalismo ao layout Android depois de conhecer ergonomia e resolução reais;
5. mapear gestos touch conforme o relógio comprado;
6. integrar localização real somente com permissão explícita;
7. integrar sensores de saúde suportados pelo hardware, sem inventar dados;
8. integrar o Voice Engine mais avançado conforme o STAR Voice evoluir;
9. adicionar autenticação/Permission Manager no marco de segurança adequado.

O Watch continua sendo **uma interface da STAR**, nunca uma STAR paralela.
