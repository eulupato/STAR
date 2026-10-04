# ⭐ STAR — S.T.A.R.

**S.T.A.R. — System for Thought, Analysis and Response**

A STAR é uma arquitetura **offline-first** formada por identidade, Core, memória,
conhecimento local, voz, ferramentas, interfaces e dispositivos. Modelos locais ou
cloud são recursos utilizados pela STAR; nenhum modelo isolado é a STAR.

## Direção atual do projeto

A release atual é a **STAR V2.0**. A Foundation V1.9 permanece apenas como base
histórica preservada do Core; não é a versão atual do produto. PC, Mobile e Watch
são superfícies da mesma STAR: compartilham identidade, raciocínio, memória,
conhecimento e capacidades do `StarCore`. Nenhum endpoint possui um cérebro paralelo.

As diferenças são de apresentação e hardware:

- **PC** — experiência completa Cosmic Crystal, incluindo STAR World/Ilhas e Device Gateway LAN;
- **Mobile** — experiência compacta Cosmic Crystal baseada na mesma identidade visual do PC, sem Ilhas;
- **Watch** — experiência minimalista circular Cosmic Crystal, voltada a voz e ações rápidas.

A camada visual **Cosmic Crystal** usa cosmos azul/violeta, brilho lilás/ciano e a
estrela cristalina de 8 pontas como símbolo principal da STAR. No PC, a experiência
padrão agora é um mundo 3D real em **Godot 4**, com menu, Hub, ilhas e STAR House.
O renderer Tkinter/Pillow anterior continua preservado como fallback clássico. No
Watch, o orb continua sendo a presença visual principal no uso cotidiano e a estrela
cristalina funciona como símbolo/ícone da STAR. O identificador legado
`plasma-orbit` permanece apenas onde é necessário para compatibilidade com contratos
V0.4 já versionados.

No PC existem três entradas oficiais e somente elas devem ser usadas para iniciar
as superfícies do produto: `INICIAR_PC.bat`, `INICIAR_MOBILE.bat` e
`INICIAR_WATCH.bat`.

`INICIAR_PC.bat` chama `star_world_launcher.py`, abre o STAR WORLD 3D e sobe o
único STAR Core + Device Gateway. O cliente Godot conecta ao Core exclusivamente pelo
loopback local. Se o Godot não estiver disponível, o launcher retorna automaticamente
à interface clássica Tkinter/Pillow; `STAR_PC_CLASSIC=1` força esse fallback de forma
explícita. Os simuladores Mobile e Watch não constroem outro cérebro: conectam-se ao
Core do PC pela sessão local do Gateway. Portanto, para testar as três superfícies
juntas, inicie primeiro o PC e depois Mobile/Watch. Em hardware real, o mesmo contrato
usa a LAN privada.

### STAR WORLD 3D no PC

O Hub apresenta as ilhas como espaços 3D distintos dentro do mesmo cosmos. A
**Casa** é a ilha disponível nesta etapa; Laboratório, Biblioteca, Estúdio de Música,
Ateliê, Jardim, Observatório, Correio e Heróis aparecem bloqueados e não são
declarados como funcionais.

A STAR House é caminhável em primeira pessoa e possui uma arquitetura interna
contínua com **sala, cozinha, banheiro, escada, quarto e varanda**. Sala, cozinha,
banheiro e quarto são construídos como ambientes próprios, com paredes/aberturas,
pisos, mobiliário, iluminação e decoração específicos — não como marcadores vazios.

O estado funcional atual continua deliberadamente honesto:

- a TV da sala e a TV do quarto usam o mesmo sistema local da STAR TV;
- o roupeiro do quarto abre o seletor de skins e persiste `world_skin` sem destruir
  a preferência visual legada;
- as miniaturas do seletor reutilizam os arquivos canônicos de `SKINS/`, sem cópias;
- o PC do quarto, livros, quadros e objetos geek já existem fisicamente no cenário,
  mas permanecem não interativos enquanto suas funções futuras não forem implementadas;
- a STAR usa um avatar procedural de alta densidade baseado nas referências visuais
  existentes, com rosto, cabelo, corpo suavizado, mãos e seis conjuntos de roupa
  geometricamente distintos; rig avançado, lip sync e animação corporal madura
  continuam pertencendo à evolução futura;
- o botão **CHAT** abre a conversa da mesma STAR/Core; não existe um cérebro separado
  dentro do mundo 3D;
- o céu do Hub, Casa e varanda compartilha o mesmo estado de ambiente;
- o ciclo dia/noite usa o fuso IANA salvo em `user_settings.json` e continua
  disponível offline com o último valor persistido.

Controles atuais: `WASD` para movimento, mouse para câmera em primeira pessoa,
`Shift` para correr e `E` para interagir. O ray de interação acompanha a câmera
verticalmente. O diagnóstico headless do mundo (`STAR_WORLD_SMOKE=1`) valida Hub,
Casa, quatro cômodos mobiliados, câmera yaw/pitch, interação e densidade mínima do
avatar.

## 🧠 Knowledge Foundation

A base factual endereçável anterior continua em **22,15M** de variações, composta
pelos engines de Física, Química, Multidisciplinar e Knowledge PLUS. Esse número é
composicional e não significa 22,15M fatos escritos/pesquisados individualmente.

A expansão curricular canônica adiciona uma camada granular sobre o mesmo Core:

- **56 temas** de ciência, matemática, física, engenharia, computação, química,
  biologia, neurociência e Ciências da Terra;
- **956 menções** de subtemas consolidadas em **885 conceitos canônicos únicos**;
- **71 duplicações** removidas por identidade semântica/alias;
- **1.000.000** de variações endereçáveis por tema;
- **1.000.000** de variações endereçáveis por conceito único;
- **941.000.000** de conteúdos/visões curriculares endereçáveis no total,
  materializados sob demanda;
- uma **fundação factual real para os 56 temas**, com resumos e três fundamentos
  por tema (168 afirmações temáticas curadas), além de uma fundação temática real
  para os **885 conceitos canônicos**, sem voltar a respostas de metadados;
- **100 registros factuais diretos** de alta frequência e **76 entradas/aliases de
  capitais**, incluindo anatomia/fisiologia humana, biologia, neurociência, química,
  física, computação, geografia, Ciências da Terra, astronomia, cultura e história;
- **29 referências factuais registradas**, incluindo NIST, OpenStax, NASA,
  NIH/NHLBI, NCBI Bookshelf, IUPAC, PubChem, USGS, NOAA, IPCC, IETF, UN/UNGEGN,
  Nobel Prize, Natural History Museum e Recording Academy.

Os 941M curriculares **não são 941M novos fatos independentes** e permanecem como
métrica separada dos 22,15M factuais legados. Um conceito existe uma vez e pode
pertencer a várias áreas; por exemplo, visão computacional conecta Robótica, IA e
Percepção Computacional sem manter três cópias do mesmo conceito.

Arquivos principais:

```text
core/curriculum_taxonomy.py
core/curriculum_foundations.py
core/curriculum_knowledge.py
STAR_CURRICULUM_MANIFEST.json
docs/STAR_CURRICULUM_EXPANSION.md
```

A STAR também possui localização global para `pt-BR`, `en-US`, `en-GB`, `es-ES`,
`it-IT` e `fr-FR`. O conhecimento canônico continua único; idioma é camada de
apresentação. Traduções protegem IDs, números/unidades, URLs, paths, código e
matemática, e uma tradução parcial insegura é rejeitada em vez de alterar informação.

## ⌚ STAR Watch App V0.4

A V0.4 inaugura a abordagem **Watch-first** e roda atualmente como simulador no PC,
com a interface oficial **Cosmic Crystal**. O renderer preserva o identificador
`plasma-orbit` como contrato de compatibilidade, mas a aparência atual é violeta,
tridimensional e usa a estrela cristalina de 8 pontas.

Para abrir:

```bat
INICIAR_WATCH.bat
```

ou:

```powershell
.\.venv\Scripts\python.exe clients\star_watch_visual.py
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
- **BUSCA** — usa a capacidade de pesquisa já existente no Core quando autorizada;
- **SAÚDE** — UX pronta com provider simulado claramente identificado;
- **GPS** — UX pronta com provider simulado claramente identificado;
- **VISÃO** — prepara STAR Scan e permite selecionar uma imagem no simulador;
- **PEOPLE** — cadastro pessoal manual e local;
- **MEDIR** — UX STAR Measure com provider simulado até existir laser real;
- **MÍDIA** — reaproveita comandos de mídia existentes;
- **CLIMA** — tela preservada no shell; o Core possui provider meteorológico contextual separado;
- **CONFIG** — simulação e resposta falada.

### O que é real e o que é simulado

A V0.4 **não finge possuir hardware inexistente**.

No PC, GPS, saúde e distância aparecem como `SIMULAÇÃO` quando ativados. Vision AI,
laser físico e reconhecimento automático de pessoas ainda não são declarados como
disponíveis. O clima contextual do Core é uma capacidade online sob demanda e não
transforma GPS/hardware do Watch em recurso real.

O cadastro PEOPLE fica em:

```text
runtime/star_watch/people.json
```

e permanece fora da base versionada.

Veja `docs/STAR_WATCH_APP_V0_4.md` e `docs/STAR_WATCH_VISUAL_SYSTEM.md`.

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
- voz oficial gerada pelo `VoiceManager` do PC e transmitida em WAV pelo `/v1/speech`;
- TTS do endpoint apenas como fallback degradado quando a voz do Core estiver indisponível;
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
VoiceManager único no PC
    ├── Chatterbox oficial
    └── Piper → SAPI fallback no modo rápido
    ↓
PC: saída local resolvida por `voice/audio_devices.py`
Mobile/Watch: `/v1/speech` → WAV → alto-falante do endpoint
```

A STAR não fica presa ao primeiro endpoint que o PortAudio reportar (por exemplo,
HDMI/TV). A entrada e a saída podem ser fixadas em `user_settings.json` por
`audio_input_device`/`audio_output_device`, ou temporariamente por
`STAR_AUDIO_INPUT_DEVICE`/`STAR_AUDIO_OUTPUT_DEVICE`. Sem override, o Windows usa
o driver primário do sistema.

PC, Mobile e Watch usam a mesma fonte de voz sempre que o Core está acessível. O TTS
nativo de Mobile/Watch permanece somente como fallback explícito de disponibilidade.
A referência da voz oficial continua privada e local. Não deve ser enviada ao Git.
Seed-VC permanece opcional e separado do ambiente principal.

### Voz em tempo real e barge-in

A interface desktop preserva a gravação manual existente e agora também oferece um
modo **mãos-livres opt-in**. Ele só é iniciado por ação explícita do usuário.

Nesse modo:

- o VAD é local e usa RMS + noise floor adaptativo + histerese;
- ruídos curtos são descartados antes do STT;
- o limiar sobe enquanto a STAR fala para reduzir eco/auto-disparo;
- fala humana confirmada durante o TTS executa **barge-in** e interrompe a resposta;
- pausas acústicas e fim de pensamento são tratados separadamente: segmentos podem
  ser agrupados em um único turno antes de chegar ao Core;
- o assembler reconhece continuações comuns em português/inglês e possui limite
  máximo de retenção para nunca deixar um turno aberto indefinidamente;
- somente segmentos detectados viram WAV temporário para o faster-whisper;
- os arquivos temporários são removidos depois da transcrição;
- não existe gravação bruta contínua persistida pelo VAD;
- `VoiceManager.runtime_snapshot()` expõe estado e métricas leves para diagnóstico;
- a fala remove emojis, URLs cruas e marcação visual de Markdown sem alterar o
  texto que continua aparecendo integralmente na interface.

O botão `◉` ao lado do microfone controla esse modo. O gravador manual continua
disponível e não foi substituído.

## Command / Capability Foundation

A STAR usa um registro central de intents em `core/commands.py`.
O catálogo atual gera **27.804 variações auditáveis de comandos de voz**, acima do
contrato mínimo de 4.000, sem manter milhares de `if/else` duplicados.

Os comandos são formados por intents + aliases + wake words + slots/variáveis. Entre
os slots atuais estão:

- `open_app.target` e `close_app.target`;
- `web_search.query`;
- `find_file.query`;
- `spotify_search.query`;
- `weather_current.location`.

Os campos de pesquisa, arquivo, Spotify e localização climática aceitam texto livre;
o catálogo de exemplos existe para teste e auditoria, não como limite do vocabulário.

`core/agents.py` funciona como catálogo/dispatcher de capacidades especializadas.
Essas capacidades **não são personalidades nem STARs separadas**.

Comandos sensíveis originados de Watch/Mobile permanecem restritos. Screenshot,
busca de arquivos, terminal, PowerShell, fechamento de aplicações e bloqueio do PC
não devem ser liberados remotamente sem confirmação local/permissões apropriadas.

## 💬 Conversa natural

`core/conversation.py` adiciona small talk local antes do fallback genérico do Core.
O sistema compõe atualmente **6.000 respostas únicas**, acima do mínimo de 5.000,
organizadas em famílias de:

- saudação;
- bem-estar;
- agradecimento;
- conversa casual;
- apoio cotidiano;
- despedida.

As respostas são combinadas deterministicamente a partir da mensagem recebida. Isso
mantém variedade sem armazenar milhares de respostas copiadas ou gerar comportamento
aleatório impossível de reproduzir em testes.

## 🌦️ Clima contextual

A STAR agora consulta condições meteorológicas quando a conversa realmente depende
do clima. Exemplos:

```text
"o dia está bonito"
"o dia está chuvoso"
"está frio hoje"
"que calor"
"como está o tempo"
"como está o tempo em Porto Alegre"
```

A resposta é confrontada com temperatura, sensação térmica, precipitação, nuvens e
código meteorológico. Assim, por exemplo, uma leitura de **30 °C não é confirmada
como frio** apenas para concordar com a frase do usuário.

O provider usa **Open-Meteo** para geocoding e condições atuais. Quando nenhuma
localização foi configurada, a estimativa automática por IP pode usar `ipwho.is`.
Essa consulta é sob demanda, possui cache em memória e esta camada não persiste
coordenadas em disco.

Configuração opcional:

```text
STAR_WEATHER_ENABLED=1
STAR_WEATHER_LOCATION=Cidade, Estado
STAR_WEATHER_AUTOLOCATE=1
STAR_WEATHER_CACHE_SECONDS=600
```

Para maior privacidade, configure `STAR_WEATHER_LOCATION` localmente e use
`STAR_WEATHER_AUTOLOCATE=0`.

O acesso meteorológico é propositalmente estreito: ele **não habilita o modo web
geral**, navegador, Spotify ou pesquisa arbitrária. Veja
`docs/STAR_CONVERSATION_WEATHER_V1_9.md`.

## Estrutura principal

```text
STAR/
├── clients/
│   ├── star_mobile_app.py      # simulador Mobile, mesmo Core/GUI funcional
│   ├── star_mobile_ios/        # cliente iOS experimental
│   ├── star_watch_visual.py    # shell oficial Cosmic Crystal no PC
│   ├── star_watch_app.py       # base funcional reutilizada pelo renderer
│   └── star_watch_android/     # transporte Android V0.3
├── core/                       # identidade, Core, comandos, conversa e capacidades
├── database/                   # persistência
├── gui/                        # interface PC clássica preservada como fallback
├── star_world/                 # superfície oficial PC 3D em Godot
├── knowledge/                  # Knowledge Packs
├── modules/                    # ferramentas
├── voice/                      # STT/TTS/Seed-VC opcional
├── tests/                      # testes automatizados
├── docs/                       # documentação
├── STAR_MANIFEST.json          # capacidades/versões declaradas
├── INICIAR_PC.bat              # PC completo + Gateway LAN
├── INICIAR_MOBILE.bat          # simulador Mobile no PC
├── INICIAR_WATCH.bat           # simulador Watch no PC
├── star_world_launcher.py      # orquestra Core + Gateway + Godot + fallback
└── main.py                     # Core e superfície clássica/fallback
```

## STAR Core no PC

A superfície oficial do PC é iniciada por:

```bat
INICIAR_PC.bat
```

O launcher detecta o Godot pelo `STAR_GODOT_EXE`, pelo `PATH` ou por uma instalação
WinGet. Se o runtime 3D não estiver disponível, ele preserva a operação abrindo a
interface clássica. Para abrir deliberadamente apenas o fallback clássico:

```powershell
$env:STAR_PC_CLASSIC="1"
.\INICIAR_PC.bat
```

`main.py` continua válido como entrypoint técnico do Core/superfície clássica, mas
não é mais a experiência padrão do PC. O PC continua sendo a fonte central de
processamento. Mobile e Watch reutilizam esse mesmo Core e evoluem como
interfaces/endpoints especializados, sem duplicar identidade, memória ou raciocínio.

## STAR Device Gateway

A ponte LAN continua experimental no Core e permanece desligada quando `main.py`
é iniciado isoladamente. O launcher oficial `INICIAR_PC.bat` a ativa para que
Mobile e Watch usem o mesmo processamento, identidade e raciocínio do PC.

O Gateway possui pareamento local, token por dispositivo, runtime adaptativo e rate
limits. Deve permanecer em rede privada; não exponha a porta experimental à Internet.

## Offline-first

A STAR mantém três níveis operacionais:

- **LOCAL** — funções fundamentais no dispositivo/PC;
- **LAN** — cooperação entre dispositivos locais;
- **ONLINE** — internet expande capacidades quando autorizada ou por providers online estreitos e declarados.

Internet não define a existência da STAR. Providers online específicos devem ser
sob demanda, limitados ao seu domínio e documentados no Manifest.

## Desenvolvimento

Antes de considerar uma atualização concluída:

```powershell
python tools/repo_hygiene.py
python diagnostico.py
python -m pytest -q tests
```

Os catálogos pesados de Física, Química, Multidisciplinar, Knowledge PLUS e Currículo
são carregados sob demanda para não atrasar a abertura da STAR. Para materializar
esses catálogos e imprimir métricas detalhadas também durante o startup, use
`STAR_STARTUP_VERBOSE=1`.

O diagnóstico valida também os contratos mínimos de catálogo de voz e conversa,
os limites da expansão curricular e distingue Knowledge Packs descobertos de entradas
efetivamente carregadas.

Além dos testes automáticos, interfaces, microfone, sensores e hardware precisam de
validação física quando a mudança depender deles.

Nunca versione `.env`, tokens, bancos pessoais, referências privadas de voz, modelos,
caches, fotos pessoais ou arquivos temporários.

## Estado atual

- **STAR release:** V2.0 stable (**Foundation V1.9 preservada como base histórica**);
- **conhecimento factual endereçável legado:** 22,15M variações composicionais;
- **currículo canônico:** 56 temas + 885 conceitos únicos = 941M variações curriculares on-demand;
- **idiomas:** 6 locales de apresentação sobre uma fonte canônica única;
- **voz:** 27.804 variações auditáveis de comandos no catálogo atual;
- **conversa local:** 6.000 combinações auditáveis;
- **clima contextual:** provider online sob demanda integrado ao Core;
- **camada visual compartilhada:** Cosmic Crystal no PC, Mobile e Watch;
- **STAR Watch App:** V0.4 functional simulator + Cosmic Crystal (`plasma-orbit` como ID compatível);
- **STAR Watch Android transport:** V0.3 experimental;
- **STAR Mobile iOS:** experimental;
- **hardware STAR próprio:** conceito/futuro.

A prioridade atual é validar a camada Cosmic Crystal nas três superfícies na release V2.0 sem regredir
a Foundation V1.9: PC responsivo, Mobile conectado ao mesmo Core e Watch V0.4 fluido. Builds
nativos e hardware real continuam exigindo validação no ambiente de cada plataforma.
