# ⭐ STAR — S.T.A.R.

**S.T.A.R. — System for Thought, Analysis and Response**

A STAR é uma arquitetura **offline-first** composta por identidade, Core, memória,
conhecimento, MIND, ferramentas, voz, interfaces e dispositivos. Um modelo local ou
cloud é somente um recurso utilizado pela STAR; nenhum modelo isolado é a STAR.

## Estado oficial

- **release estável:** STAR V1.9 Foundation;
- **camada cognitiva:** STAR MIND experimental-alpha;
- **Integrated Evolution:** alpha sobre V1.9, sem promover artificialmente V2+;
- **direção de produto:** Watch-first;
- **internet:** desligada por padrão e autorizada por capacidades/providers declarados;
- **trava central de rede:** `StarCore.network_enabled`;
- **banco cognitivo:** um único `star.db`;
- **branch `main`:** fonte oficial do estado versionado após merge e validação.

## 🧠 Conhecimento

A base factual endereçável anterior continua em **22,15M de variações composicionais**
(Física, Química, Multidisciplinar e Knowledge PLUS). Esse número não representa
22,15M fatos pesquisados individualmente.

A expansão curricular adiciona:

- **56 temas**;
- **956 menções** consolidadas em **885 conceitos canônicos únicos**;
- **71 duplicações** removidas por identidade/alias;
- **941.000.000** de visões curriculares endereçáveis on-demand.

Os 941M são um espaço determinístico de estudo/pesquisa sobre os conceitos canônicos,
e não 941M afirmações factuais independentes.

## 🌍 Religiões, tradições e história da magia — 5M

A STAR possui uma base cultural separada da contagem factual/científica:

- **100 tradições/relações religiosas** de várias regiões e épocas;
- **25 campos de magia, esoterismo e história da magia**;
- **40 eixos canônicos** por assunto;
- **5.000 nós canônicos**;
- **1.000 perspectivas** por nó;
- **5.000.000 de conteúdos/visões culturais endereçáveis** sob demanda.

Os 5M **não são cinco milhões de fatos pesquisados individualmente**. São perspectivas
determinísticas para organizar estudo, comparação e pesquisa sobre os 5.000 nós. O
aprofundamento pode usar Research Hub/RAG/M.drives com proveniência.

A política epistemológica separa:

1. autodescrição de praticantes/comunidades;
2. registro histórico ou etnográfico;
3. interpretação acadêmica;
4. evidência física/experimental.

Assim, uma crença ou alegação sobrenatural pode ser descrita fielmente como parte de
uma tradição sem ser apresentada como mecanismo físico demonstrado. Tradições vivas
marcadas como sensíveis priorizam fontes da própria comunidade; conhecimento fechado,
iniciático ou restrito não é reconstruído a partir de fragmentos públicos.

Veja `STAR_RELIGION_MAGIC_MANIFEST.json` e `docs/STAR_RELIGION_MAGIC_5M.md`.

## 💾 M.drives

**M.drive = Memory + Drive/Pendrive.** É o nome oficial dos antigos **Knowledge Packs**.

Novos módulos ficam em:

```text
knowledge/m_drives/
```

Mídia removível usa preferencialmente:

```text
STAR_KNOWLEDGE/m_drives/
```

Para não quebrar dados existentes, `knowledge/packs` e `STAR_KNOWLEDGE/packs`
continuam legíveis como caminhos **legados**. O repositório não mantém cópias atuais
em ambos os caminhos. A migração é explícita e não destrutiva; nenhum M.drive executa
código automaticamente por ser descoberto.

O antigo módulo `heroes` foi convertido para um M.drive estruturado e carregável. O
manifesto vazio de matemática básica foi removido em vez de duplicar o Math Engine.

## 🧠 STAR MIND + Integrated Evolution

O MIND alpha mantém 15 capacidades cognitivas: raciocínio, planejamento, memória,
Knowledge Graph, raciocínio científico, matemática, simulação, coding, verificação,
RAG documental, pesquisa, projetos, user model, multiagentes e autoavaliação.

A camada Integrated Evolution acrescenta, sobre os mesmos sistemas:

### Cognitive Runtime

- Working Context limitado em RAM;
- Salience por relevância/novidade/risco/urgência/prioridade;
- Model Router para engines explicitamente registrados;
- sem criar memória persistente paralela.

### Goal Engine + Scheduler alpha

- objetivos e tarefas persistentes;
- dependências;
- checkpoints e retomada;
- `not_before`, prazo e prioridade persistentes;
- ordenação por prioridade;
- execução por handlers explicitamente registrados;
- idempotência em conjunto com Guardian;
- **sem autonomia em background**.

### Guardian alpha

- default-deny para ações desconhecidas;
- política e confirmação por ação;
- restrições remotas;
- audit log;
- claims idempotentes;
- redaction básica de segredos.

Ainda **não** existe sandbox de SO, autenticação forte ou Secrets Vault criptográfico completo.

### 🩹 Cura local alpha

`core/cure.py` funciona sem GitHub e sem IA generativa:

- health check de Python/JSON e integridade SQLite;
- hashes SHA-256;
- snapshot conhecido como bom (`known-good`);
- watchdog local;
- snapshot pré-reparo;
- restauração somente de arquivos permitidos do snapshot;
- validação depois da restauração;
- rollback automático da tentativa se o reparo não resolver;
- alterações saudáveis não são apagadas só porque diferem do baseline.

Isso **não é auto-reescrita irrestrita**. Sandbox de SO, vault, antimalware, Permission
Manager completo e backup/restore amplo continuam pertencendo ao Guardian futuro.

### 👥 People alpha

People utiliza o mesmo `star.db` e `runtime/people` para perfis e assets fornecidos
explicitamente. Imagens recebem SHA-256 e dHash técnico para deduplicação.

Políticas atuais:

- funciona offline;
- não faz reconhecimento facial/biométrico;
- não infere raça, religião, saúde, orientação sexual, personalidade ou outros traços
  sensíveis a partir de foto;
- não ingere GPS de EXIF;
- imagem genérica recebida por câmera não é associada automaticamente a uma pessoa sem
  contexto explícito.

### 🌐 Web Knowledge sem IA generativa

Quando as fontes locais não possuem resposta confiável, a STAR pode — **somente no modo
ONLINE** — pesquisar a web, extrair texto, ranquear trechos deterministicamente e montar
um resultado com título/URL/proveniência. SearXNG configurado é preferido e DuckDuckGo
HTML funciona como fallback.

O conteúdo aceito pode ser gravado no CognitiveStore existente e reutilizado offline.
Ele não vira verdade absoluta automaticamente. URLs privadas/localhost são bloqueadas
no fetch para reduzir risco de SSRF.

### RAG híbrido + OCR

A fonte de verdade continua sendo documentos/chunks no SQLite com FTS5/BM25. A camada
semântica é derivada:

```text
PDF/texto
→ extração
→ OCR seletivo quando necessário
→ chunks
→ SQLite / FTS5
→ embedding derivado opcional
→ recuperação híbrida
```

- fallback hashing é local/determinístico;
- Sentence Transformers é opcional;
- `sqlite-vec` está preparado como opcional, mas não é o armazenamento vetorial ativo atual;
- PyMuPDF + Tesseract são opcionais para OCR;
- nenhum modelo neural é carregado no boot base.

Dependências opcionais:

```powershell
python -m pip install -r requirements-intelligence.txt
```

### Knowledge Graph científico + cultural

`core/scientific_graph.py` pode materializar no mesmo grafo oficial:

- 56 temas científicos/curriculares;
- 885 conceitos canônicos;
- 125 assuntos culturais;
- 40 aspectos culturais;
- relações derivadas das taxonomias.

As 5M perspectivas culturais não são materializadas no grafo; apenas a estrutura
canônica. O sistema não inventa causalidade científica nem verdade teológica.

### Simulation Engine

Modelos NumPy locais atuais:

- RK4 vetorial;
- órbita Newtoniana 2D de dois corpos;
- pêndulo não linear amortecido;
- equação do calor 1D;
- equação da onda 1D;
- circuito RC.

Existem verificações como drift de energia, estabilidade explícita e condição CFL.
Isso ainda não substitui CFD/FEA/SPICE/astrodinâmica de alta fidelidade ou relatividade numérica.

### Research Hub

Pesquisa científica estruturada opt-in usa Crossref, OpenAlex, arXiv e PubMed/NCBI.
Resultados são deduplicados por DOI → URL → título. Encontrar um paper não significa
que sua conclusão foi automaticamente validada; avaliação de evidência continua uma
etapa separada.

### Operator e Senses

- File Index persistente **somente leitura**, iniciado apenas por ação explícita;
- contrato unificado para observações de câmera/tela/sensores;
- buffer de fusão temporal;
- `semantic_scene_understanding=false` por enquanto;
- ações sensíveis continuam bloqueadas.

## Comandos alpha explícitos

Exemplos:

```text
status evolução
status agora
contexto cognitivo
rotear engine math
m.drives
cadastrar pessoa Ada Lovelace: profissão: matemática
listar pessoas
cura status
diagnosticar star
executar cura
buscar web computação quântica topológica
criar objetivo Estudo: revisar relatividade geral
listar objetivos
pesquisar profundamente gravitational waves
pesquisa cultural história do candomblé
rag semântico decoerência quântica
ocr C:\documentos\paper.pdf
indexar arquivos C:\Development\Projects
indexar grafo científico
indexar grafo cultural
simular órbita
simular pêndulo
```

Esses comandos são estreitos de propósito: o router estável da V1.9 continua com
prioridade e a nova camada não sequestra termos genéricos.

## 🌍 Idiomas

A fonte canônica de conhecimento continua única em `pt-BR`. A camada de idioma possui
**18 perfis em 13 famílias**:

- Português Brasil;
- Inglês EUA e Reino Unido;
- Espanhol, Italiano e Francês;
- Japonês, Polonês e Coreano;
- Grego moderno e Grego antigo;
- Latim clássico, tardio, medieval e neolatim;
- Árabe padrão moderno e Árabe egípcio;
- Egípcio antigo.

Egípcio antigo (`egy-EG`) **não é árabe**. `ar-EG` representa o árabe egípcio moderno.

O catálogo contextual humano revisado continua sendo **500 mil conteúdos semânticos**
para as 5 famílias/6 superfícies originais. Os 18 perfis não multiplicam artificialmente
essa contagem. Novos idiomas usam UI embutida, dicionários locais e Argos opcional já
materializado quando disponível.

Grego antigo, latim histórico e egípcio antigo são perfis de léxico/corpus; a STAR não
finge que um MT moderno fornece tradução histórica correta. Se não houver tradução
completa e segura, o original é preservado.

Setup neural opcional:

```powershell
python -m pip install -r requirements-translation.txt
python scripts/setup_offline_translation.py --install
```

O script só instala pares realmente publicados pelo índice Argos atual. O startup da
STAR nunca baixa modelos automaticamente.

Veja `STAR_LANGUAGE_MANIFEST.json`.

## 🎙️ Voz e conversa

Arquitetura local:

```text
Microfone
→ faster-whisper
→ STAR Core
→ Chatterbox oficial / Piper / SAPI fallback
→ alto-falante
```

A referência oficial de voz é privada/local e nunca deve ser versionada.

O catálogo contém **27.804 variações auditáveis de comandos operacionais** e
**1.000.000 de variações temáticas de estudo**. A conversa local possui **6.000
combinações auditáveis**.

Voz para perfis históricos não é apresentada como reconstrução histórica validada sem
um voice pack local apropriado.

## 🌦️ Clima e rede

O clima ao vivo via Open-Meteo é uma capacidade online. O Core começa OFFLINE e o
`WeatherService` compartilha a mesma trava `StarCore.network_enabled`; portanto uma
conversa genérica sobre clima não pode furar o modo offline.

Hora/data, People, Cura, conhecimento e painel AGORA continuam funcionais localmente.

Configuração opcional:

```text
STAR_WEATHER_ENABLED=1
STAR_WEATHER_LOCATION=Cidade, Estado
STAR_WEATHER_AUTOLOCATE=0
STAR_WEATHER_CACHE_SECONDS=600
```

A variável de ambiente não substitui a autorização do Core: o provider também precisa
estar habilitado pelo modo ONLINE.

## 👁️ STAR Vision

O Vision Portal local possui webcam, MediaPipe HandLandmarker, tracking de duas mãos,
suavização, portal AR, HUD/captura/fullscreen e 12 filtros.

Isso **não é ainda compreensão semântica de cena**. Abertura/fechamento remoto da
câmera do PC permanece bloqueado.

## ⌚ STAR Watch

A prioridade prática continua Watch-first:

```text
1. validar shell/voz/providers no PC;
2. portar Plasma Orbit para a base Android Watch existente;
3. integrar sensores/hardware reais;
4. validar em hardware físico;
5. depois construir a nova experiência principal de PC.
```

### Watch App V0.4

Simulador funcional no PC com Plasma Orbit:

```bat
INICIAR_STAR_WATCH_APP.bat
```

Modos atuais incluem:

`VOZ · AGORA · BUSCA · SAÚDE · GPS · VISÃO · PEOPLE · MEDIR · MÍDIA · CLIMA · IDIOMA · CONFIG`

- `IDIOMA` percorre os 18 perfis do Core;
- `PEOPLE` usa o armazenamento central em vez de JSON paralelo;
- `AGORA` mostra hora/data locais e o estado compartilhado da STAR;
- clima no AGORA só atualiza quando ONLINE;
- saúde/GPS/distância continuam marcados como **SIMULAÇÃO** quando não há provider físico real.

### Android Watch V0.3

A base em `clients/star_watch_android/` preserva transporte LAN, texto, áudio PCM/WAV,
STT no Core, resposta falada, câmera, heartbeat e runtime adaptativo. Uma segunda página
AGORA é acessível por swipe horizontal; sem pareamento ela mantém hora/data locais.
O shell Plasma Orbit completo ainda precisa ser levado ao hardware e validado fisicamente.

## 📱 Mobile / Device Gateway

- cliente iOS experimental com `TabView` principal ↔ AGORA;
- Device Gateway LAN experimental e desligado por padrão;
- Device Runtime distribui tema, feature flags e locale sem MIND paralelo;
- processamento cognitivo permanece no STAR Core;
- ações remotas sensíveis continuam bloqueadas;
- a porta do Gateway não deve ser exposta à internet.

## 🖥️ PC

A interface desktop V1.9 continua preservada e a camada localizada adiciona o popup
**AGORA** sem reconstruir a GUI:

```bat
INICIAR_STAR.bat
```

ou:

```powershell
.\.venv\Scripts\python.exe main.py
```

O Operator atual ainda é parcial. Volume, mídia, screenshot, busca/abertura limitada e
algumas ações existem; automação geral, escrita destrutiva e controle irrestrito do SO
não são liberados sem a arquitetura completa de permissões.

## Estrutura principal

```text
STAR/
├── clients/                    # Watch, Android, iOS, Vision
├── core/                       # Core, MIND, Evolution, conhecimento e engines
├── database/                   # persistência única
├── gui/                        # interface PC
├── knowledge/
│   ├── m_drives/               # nome oficial
│   └── packs/                  # somente compatibilidade legada
├── modules/                    # ferramentas
├── voice/                      # STT/TTS
├── tests/
├── docs/
├── STAR_MANIFEST.json
├── STAR_MIND_MANIFEST.json
├── STAR_LANGUAGE_MANIFEST.json
├── STAR_RELIGION_MAGIC_MANIFEST.json
├── requirements.txt
├── requirements-intelligence.txt
├── requirements-translation.txt
└── main.py
```

## Testes e diagnóstico

Antes de considerar uma atualização concluída:

```powershell
python diagnostico.py
python -m pytest -q tests
```

O merge deve usar o **mesmo SHA** aprovado por CI, Quality, Security, Windows, Android
e iOS relevantes. Dependências opcionais não devem ser necessárias para o boot/teste
base. Interfaces, microfone, câmera, sensores e hardware físico exigem validação real
além do CI.

Nunca versione `.env`, tokens, bancos pessoais, referências privadas de voz, modelos,
caches, fotos pessoais ou arquivos temporários.

## O que ainda não está concluído

Mesmo com as fundações novas, continuam futuros/parciais:

- V2 MIND completo: consolidação/esquecimento de memória e contexto longo;
- Model Registry completo e roteamento de modelos reais;
- embeddings neurais/materialização de vector backend maduro no PC do usuário;
- OCR até Tesseract/PyMuPDF serem instalados e testados localmente;
- Knowledge Graph de todos os fatos, claims, contradições e proveniências;
- solvers CFD/FEA/SPICE e simulação científica de alta fidelidade;
- Research Engine full-text/avaliação metodológica/retrações;
- materialização local de corpora culturais/linguísticos somente quando licença permitir;
- reconhecimento/scene understanding visual semântico;
- People com identidade biométrica automática — **não implementado**;
- Operator geral e seguro;
- Guardian com sandbox, vault, autenticação, antimalware e backup/restore amplo;
- Agent com workers duráveis e approval gates ponta-a-ponta;
- sync offline completo do ecossistema;
- sensores reais completos do Watch validados em hardware;
- STAR WORLD 3D;
- robótica física.

Consulte `docs/MASTER_ROADMAP.md`, `docs/STAR_INTEGRATED_EVOLUTION_ALPHA.md`,
`docs/STAR_OFFLINE_EVOLUTION_ALPHA.md` e `docs/STAR_RELIGION_MAGIC_5M.md` para a
separação entre **estável, alpha, parcial e planejado**.
