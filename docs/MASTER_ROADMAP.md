# ⭐ STAR — MASTER DEVELOPMENT ROADMAP

Documento vivo oficial do projeto.

## Regras de versionamento
- Versão inteira (`V2.0`, `V3.0`) = nova geração funcional.
- `.1`, `.2` = expansão importante dentro da geração.
- `.x.x` = correção/hotfix.
- Ideias novas entram primeiro neste roadmap e só depois viram código.

## Arquitetura conceitual
A STAR é organizada em oito domínios:

- **MIND** — raciocínio, contexto, memória, planejamento, identidade.
- **SENSES** — audição, visão, tela e sensores.
- **EXPRESSION** — linguagem, voz, avatar e animação.
- **ACTION** — aplicativos, arquivos, sistema operacional, web, dispositivos e robótica.
- **KNOWLEDGE** — biblioteca, Knowledge Packs, busca, Knowledge Graph e ciência.
- **HEALTH** — diagnóstico, Cura, watchdog, backup e recuperação.
- **TRUST** — permissões, criptografia, auditoria, sandbox e segredos.
- **WORLD** — STAR WORLD, ilhas, 3D, interfaces e presença física.

## V1.9 — FOUNDATION
**Objetivo:** congelar a fundação estável.

Inclui:
- Core e identidade atuais;
- memória básica;
- matemática natural;
- interface 2D;
- HUB/ilhas/Casa/Closet/skins;
- Knowledge Packs atuais;
- STT local;
- voz oficial local + fallbacks;
- controle inicial do computador;
- CI, logs, limpeza e documentação.

Pós-release: bugs entram como V1.9.x.

### Infraestrutura experimental pós-release

A Foundation pode receber **pontes pequenas, opt-in e sem mudança de geração**
quando forem necessárias para validar hardware real, desde que não antecipem os
sistemas completos de versões futuras.

Atualmente:

- **STAR Device Gateway V0.2** — ponte LAN + Adaptive Runtime;
- **STAR Mobile iOS V0** — iPhone como sensor/interface, sem MIND próprio;
- **STAR Watch Android V0.3** — Watch como sensor/interface, áudio PCM/WAV orientado a fala e comandos remotos seguros, sem MIND próprio;
- **STAR Watch App V0.4 + Plasma Orbit** — shell Watch-first validado primeiro no PC, preservando o Core compartilhado;
- **Command/Agent Foundation V0** — registro central de intents + catálogo de capacidades/agentes com estados `available/partial/planned`, sem Goal Engine ou autonomia V8;
- **Voice Command Catalog V1.9** — catálogo gerado por intents/slots com contrato mínimo de 4.000 variações, sem milhares de `if/else`;
- **Conversation Foundation V1.9** — small talk composicional com contrato mínimo de 5.000 respostas auditáveis, sem substituir o futuro Context Engine V2;
- **Contextual Weather Provider V1.9** — clima online sob demanda e de domínio estreito, usado para aterrar respostas meteorológicas sem liberar o modo web geral;
- **Knowledge Packs removíveis** — packs JSON/JSONL em `STAR_KNOWLEDGE/packs`.

O runtime compartilhado centraliza tema, rótulos, feature flags e perfis
`phone/watch` em `STAR_MANIFEST.json`. Isso valida adaptação entre endpoints sem
criar Core, identidade ou memória paralelos.

O catálogo de comandos pertence ao Core e é reutilizado por PC/Watch. Ações
remotas sensíveis permanecem bloqueadas até o Permission Manager. O registro de
agentes não antecipa autonomia: agentes são capacidades especializadas da mesma
STAR e recursos futuros permanecem explicitamente marcados como planejados.

A etapa **Watch-first** é uma ponte de validação de interface/dispositivos dentro da
Foundation: primeiro estabiliza shell, voz, comandos, providers e integração no PC;
depois porta a experiência validada para o Watch real. Ela não substitui nem pula
o V2.0 MIND.

Esses itens não significam que V5 SENSES, V8 AGENT ou V9 ECOSYSTEM estão
concluídos. O Gateway apenas entrega entradas ao Core atual; visão, Goal Engine,
Device Manager completo, Offline-first Sync e permissões avançadas continuam em
seus marcos originais.

---

## V2.0 — MIND
**Objetivo:** criar a arquitetura cognitiva permanente.

Inclui:
- Brain Architecture;
- Executive;
- Salience;
- Context Engine;
- Working Memory;
- Metacognição operacional;
- Reasoning/Planning;
- Personality/Identity Core;
- memória episódica, semântica, conversa, projetos e preferências;
- Model Router.

### BLOCO 1 — Princípios invioláveis e modelos fundamentais

O BLOCO 1 é a fundação normativa/cognitiva do V2.0. Pode existir como camada
experimental integrada sobre a V1.9, mas **não significa que V2.0 esteja concluída**.

Ciclo oficial:

```text
PERCEBER
→ IDENTIFICAR
→ COMPREENDER
→ CONTEXTUALIZAR
→ RELACIONAR
→ PREVER
→ INTERPRETAR
→ DECIDIR
→ AGIR
→ OBSERVAR
→ APRENDER
```

Modelos fundamentais:

- WORLD MODEL;
- HUMAN MODEL;
- SOCIAL MODEL;
- SELF MODEL;
- SITUATION MODEL.

Distinções invioláveis:

- MODELO ≠ STAR;
- CORPO ≠ STAR;
- IA ≠ STAR;
- PENSAR ≠ AGIR;
- CURIOSIDADE ≠ AUTORIZAÇÃO;
- INFERÊNCIA ≠ FATO;
- AUTONOMIA COGNITIVA ≠ AUTONOMIA OPERACIONAL.

Implementação central: `core/foundations.py`, reutilizada pelo `STAR Core` e
ancorada na identidade oficial já existente em `core/star_identity.py`.

O catálogo fundacional possui **1.000 nós canônicos × 1.000.000 combinações =
1.000.000.000 de representações operacionais endereçáveis**, materializadas sob
demanda. O número representa espaço combinatório de princípios, regras, estados,
limites e contextos; **não representa 1B de fatos independentes pesquisados** e
não cria 1B de arquivos/linhas em RAM ou no repositório.

Regra operacional permanente: cognição, curiosidade, inferência, previsão ou
planejamento nunca concedem sozinhos autorização para uma ação externa. Ação
requer capacidade + segurança + permissão operacional apropriada.

### BLOCO 2 — Fundação epistêmica

O BLOCO 2 define como a STAR sabe **o que sabe, como sabe, de onde veio, quando
aprendeu, qual fonte sustenta, quais evidências existem, quanta confiança e
incerteza existem, se a informação pode estar errada ou desatualizada, se há
versões conflitantes e qual é seu tipo epistêmico**.

A implementação central é `core/epistemics.py`. A persistência é uma extensão
incremental em `database/epistemic_store.py`, sempre sobre o mesmo `star.db` e o
mesmo `CognitiveStore`; não existe banco ou memória epistêmica paralela.

Cada registro epistêmico pode manter:

- conteúdo e ID estável;
- tipo: `fact`, `hypothesis`, `inference`, `opinion`, `fiction`, `simulation`,
  `unknown`, `observation`, `declared_information` ou `memory`;
- origem e referência de proveniência;
- fonte com tipo, título, confiabilidade e fundamento da confiabilidade;
- data de aprendizado;
- confiança e incerteza calibráveis;
- validade inicial/final, prazo de obsolescência e última verificação;
- múltiplas evidências de suporte, refutação ou contexto;
- relações com outros conhecimentos, inclusive contradição e supersessão;
- histórico auditável de revisões e transições.

Estados oficiais:

```text
DISCOVERED
QUARANTINED
VERIFIED
CANONICAL
SUPERSEDED
RETRACTED
```

Esses estados formam uma máquina de estados explícita. `VERIFIED` exige evidência
rastreável. `CANONICAL` não significa verdade absoluta: exige registro `fact` em
estado `VERIFIED`, proveniência explícita, evidência de suporte, confiança mínima,
incerteza aceitável, validade temporal compatível e ausência de contradição aberta.
Um registro canônico continua revisável, pode voltar à quarentena, ser substituído
ou retraído.

Contradições não são apagadas silenciosamente. Conhecimentos incompatíveis podem
ser relacionados por `contradicts`; se já estavam `VERIFIED` ou `CANONICAL`, são
movidos para `QUARANTINED` até revisão. Versões posteriores podem usar
`supersedes`/`superseded_by`, preservando a história anterior.

A ingestão diária existente continua usando os mesmos contadores e regras de
deduplicação. Registros válidos de crescimento passam também a ser registrados de
forma idempotente no ledger epistêmico como `DISCOVERED`, sem serem promovidos
automaticamente a `VERIFIED` ou `CANONICAL`.

O catálogo do BLOCO 2 possui **1.000 nós canônicos × 1.000.000 combinações =
1.000.000.000 de representações epistêmicas endereçáveis**, materializadas sob
demanda. As combinações cobrem área, lente, família cognitiva, estilo, contexto,
tipo epistêmico, faixa de confiabilidade da fonte e faixa de incerteza.

Assim como no BLOCO 1, **1B é capacidade/endereço lógico, não 1B de fatos
pesquisados, arquivos ou linhas pré-carregadas**. Somente conhecimentos realmente
descobertos/materializados ocupam o SQLite e recebem proveniência, evidências,
relações e histórico persistentes.

### BLOCO 3 — Arquitetura Universal do Conhecimento

O BLOCO 3 organiza a camada universal que conecta conhecimento canônico,
claims/evidências, grafo, relações semânticas, índices e cache sem criar sistemas
paralelos. Ele é uma fundação experimental compartilhada entre MIND e KNOWLEDGE e
**não significa que V2.2 ou V3.0 estejam concluídos**.

Pipeline oficial:

```text
CANONICAL KNOWLEDGE
↓
CLAIMS
↓
EVIDENCE
↓
KNOWLEDGE GRAPH
↓
SEMANTIC RELATIONS
↓
INDEXES
↓
CACHE
↓
STAR
```

Fontes de verdade e reutilização:

- `CANONICAL KNOWLEDGE`: `core/universal_knowledge.py`;
- `CLAIMS` e `EVIDENCE`: ledger epistêmico do BLOCO 2;
- `KNOWLEDGE GRAPH` e `SEMANTIC RELATIONS`: tabelas existentes
  `knowledge_nodes`/`knowledge_edges`;
- persistência/indexação adicional: `database/universal_knowledge_store.py` no
  mesmo `star.db`;
- integração com a STAR: `core/star_core.py`;
- cache: memória limitada LRU/TTL, descartável e nunca fonte de verdade.

Um objeto universal só pode entrar como `CANONICAL KNOWLEDGE` se seu claim
principal já estiver em estado `CANONICAL` no BLOCO 2. `DISCOVERED`,
`QUARANTINED` ou `VERIFIED` nunca são promovidos silenciosamente pelo BLOCO 3.

A camada universal organiza:

- conceitos e entidades;
- aliases normalizados e aliases localizados;
- propriedades;
- categorias, subtemas e contextos como facetas indexáveis;
- taxonomias sobre arestas do Knowledge Graph;
- eventos temporais;
- regras e exceções;
- fontes/evidências por referência aos registros do BLOCO 2;
- temporalidade e proveniência;
- claims adicionais com papéis `supporting`, `corroborating`, `contextual`,
  `exception` ou `historical`;
- relações semânticas e cross-links interdomínio.

Deduplicação usa identidade estável composta por **namespace + tipo de conhecimento
+ rótulo canônico normalizado**. Registrar novamente a mesma identidade reutiliza
o objeto existente e liga claims adicionais em vez de gerar duplicação. Claims
retraídos só podem permanecer como histórico explícito.

Consulta e atualização:

- lookup exato por rótulo canônico normalizado;
- lookup indexado por aliases;
- filtros indexados por facetas;
- SQLite FTS5/BM25 quando disponível;
- fallback textual SQLite quando FTS5 não estiver disponível;
- cache LRU/TTL com invalidação em qualquer escrita relevante;
- atualizações de metadados incrementam revisão e geram eventos auditáveis;
- taxonomias/cross-links invalidam o cache e permanecem no grafo compartilhado.

Escala do BLOCO 3:

- **20 áreas × 50 lentes = 1.000 nós canônicos**;
- **1.000.000 combinações por nó**;
- **1.000.000.000 de representações endereçáveis em `B03`**;
- materialização sob demanda; zero requisito de 1B de linhas físicas.

A arquitetura usa namespaces independentes com IDs textuais. `B01`, `B02` e
`B03` registram cada um capacidade lógica própria de **1B**; blocos futuros podem
registrar novos namespaces de 1B sem alteração de schema ou colisão de IDs. Assim,
a soma de namespaces pode ultrapassar 1B sem transformar o SQLite em um banco
pré-populado gigantesco. Apenas conhecimento efetivamente materializado ocupa
disco, RAM, índices e cache.

Embeddings locais, Biblioteca completa, Knowledge Packs V2 e o restante da busca
universal madura continuam pertencendo ao V3.0; o BLOCO 3 apenas estabelece a
arquitetura central limpa sobre a qual esses sistemas poderão crescer.

### V2.1
Memory Architecture.

### V2.2
Knowledge Graph base.

### V2.3
Model Router e seleção automática de motores.

---

## V3.0 — KNOWLEDGE
**Objetivo:** transformar a STAR em uma plataforma de conhecimento offline expansível.

Inclui:
- Biblioteca;
- ingestão de PDF/texto;
- metadados e proveniência;
- embeddings locais;
- busca universal;
- Knowledge Packs V2;
- Knowledge Graph expandido;
- Scientific Engine;
- matemática simbólica, estatística, unidades, física, química e simulações.

---

## V4.0 — OPERATOR
**Objetivo:** controlar o computador e aplicativos de forma geral e segura.

Inclui:
- Application Manager;
- skills por aplicativo;
- File Index;
- busca semântica de arquivos;
- controle de janelas e sistema;
- automações;
- clipboard, volume, processos e dispositivos;
- permissões e logs por ação.

Spotify, navegador, VS Code e outros são apenas aplicações dentro desse sistema.

---

## V5.0 — SENSES
**Objetivo:** percepção multimodal.

Inclui:
- wake word opcional;
- VAD;
- interrupção/barge-in;
- voz com streaming;
- visão;
- webcam;
- interpretação de imagens;
- Screen Awareness;
- Spatial Awareness;
- Multimodal Fusion.

---

## V6.0 — STAR WORLD 3D
**Objetivo:** reconstruir toda a experiência visual em 3D.

Princípio:

```text
STAR CORE
   ↕
Event Bus / API
   ↕
STAR WORLD 3D
```

Inclui:
- avatar 3D;
- rig;
- lip sync;
- animação procedural;
- olhar, piscar, gestos e locomoção;
- ilhas tridimensionais;
- Casa;
- Laboratório;
- Central de Criação;
- Biblioteca;
- Estúdio;
- Ateliê;
- Jardim;
- Observatório;
- Cura;
- Closet;
- Correio;
- Heróis;
- Idiomas;
- Digital Twin.

---

## V7.0 — GUARDIAN
**Objetivo:** transformar Cura em saúde, segurança e recuperação.

Inclui:
- Health Supervisor;
- watchdog;
- integridade de arquivos;
- hashes;
- integração com antimalware/antivírus local;
- Permission Manager;
- Secrets Vault;
- Audit Log;
- snapshots;
- backup;
- rollback;
- sandbox;
- diagnóstico inteligente;
- proposta de reparo e aplicação autorizada.

---

## V8.0 — AGENT
**Objetivo:** trabalhar por objetivos, não apenas comandos isolados.

Inclui:
- Goal Engine;
- Planner;
- Task Manager;
- Scheduler;
- Attention Manager;
- Simulation Mode;
- Skill SDK;
- Capability Registry;
- tarefas persistentes;
- verificação de resultado;
- autonomia controlada por permissões.

---

## V9.0 — ECOSYSTEM
**Objetivo:** expandir a STAR para a rede local e outros dispositivos.

Inclui:
- STAR LAN;
- PC;
- celular;
- tablet;
- Watch;
- Device Manager;
- Offline-first Sync;
- automação residencial;
- sensores;
- Mobile STAR;
- Network Awareness.

Princípio permanente: endpoints percebem, transmitem e executam; a fonte central
processa. Os protótipos Device Gateway/Mobile/Watch da Foundation validam esse
princípio, mas não substituem o Device Manager/Sync desta versão.

LOCAL continua funcional sem LAN ou Internet.

---

## V10.0 — EMBODIED
**Objetivo:** presença física sem prender a STAR a um fabricante.

Inclui:
- Robot Abstraction Layer;
- câmera;
- microfone;
- alto-falante;
- display;
- motores;
- sensores;
- bateria;
- telemetria;
- controle motor;
- percepção física;
- navegação segura quando apropriado.

---

## V11.0 — UNIFIED
**Objetivo:** integrar MIND, SENSES, ACTION, KNOWLEDGE, HEALTH, TRUST, WORLD e robótica em uma plataforma coerente.

Inclui:
- Event Bus maduro;
- observabilidade;
- resiliência;
- degradação graciosa;
- Capability Tree;
- Cura global;
- sincronização de estado entre interfaces.

---

## V12+ — EXPANSION
Expansões sobre a arquitetura consolidada:

- Research Engine;
- Maker Engine;
- CAD;
- eletrônica;
- microcontroladores;
- impressão 3D;
- Coding Lab;
- Creative Engine;
- música;
- arte;
- vídeo;
- modelagem 3D;
- Language Engine;
- tradução offline;
- mapas e referência offline;
- novos Knowledge Packs;
- novas skills.

---

# Sistemas transversais
Evoluem em várias gerações:

- Event Bus;
- Resource Governor;
- perfis ECO / NORMAL / MAX;
- Model Registry;
- Sleep Processing;
- Universal Inbox / Correio;
- Backup;
- Audit Trail;
- Capability Registry;
- Local Secrets Vault;
- Crash Recovery;
- Health Supervisor;
- Hardware Abstraction Layer;
- Plugin/Skill SDK;
- Task Scheduler;
- Notification Center;
- Semantic File Index;
- Personal Knowledge Graph.

# Modos oficiais
## LOCAL
STAR completa no computador.

## LAN
STAR + dispositivos locais.

## ONLINE
Recursos externos opcionais.

**Internet amplia a STAR; não constitui a STAR.**

# Regra de execução
Cada geração segue:
1. especificação;
2. arquitetura;
3. implementação incremental;
4. testes e diagnóstico;
5. documentação;
6. release;
7. freeze.

# Próximo marco
**V1.9 FINAL → estabilizar a ponte Watch-first → abrir V2.0 MIND.**
