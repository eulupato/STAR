# ⭐ STAR — MASTER DEVELOPMENT ROADMAP

Documento vivo oficial do projeto.

## Regras de versionamento

- Versão inteira (`V2.0`, `V3.0`) = nova geração funcional.
- `.1`, `.2` = expansão importante dentro da geração.
- `.x.x` = correção/hotfix.
- Ideias novas entram primeiro neste roadmap e só depois viram código.
- Um componente alpha de uma geração futura **não significa** que a geração inteira foi concluída.
- Contagens composicionais/endereçáveis nunca devem ser apresentadas como fatos pesquisados individualmente.

## Arquitetura conceitual

A STAR é organizada em oito domínios:

- **MIND** — raciocínio, contexto, memória, planejamento, identidade.
- **SENSES** — audição, visão, tela e sensores.
- **EXPRESSION** — linguagem, voz, avatar e animação.
- **ACTION** — aplicativos, arquivos, sistema operacional, web, dispositivos e robótica.
- **KNOWLEDGE** — biblioteca, M.drives, busca, Knowledge Graph, ciência e conhecimento cultural.
- **HEALTH** — diagnóstico, Cura, watchdog, backup e recuperação.
- **TRUST** — permissões, criptografia, auditoria, sandbox e segredos.
- **WORLD** — STAR WORLD, ilhas, 3D, interfaces e presença física.

---

## V1.9 — FOUNDATION

**Objetivo:** congelar a fundação estável.

Inclui:

- Core e identidade atuais;
- memória básica;
- matemática natural;
- interface 2D;
- HUB/ilhas/Casa/Closet/skins;
- M.drives locais/removíveis, com leitura compatível dos antigos Knowledge Packs;
- STT local;
- voz oficial local + fallbacks;
- controle inicial do computador;
- CI, logs, limpeza e documentação.

Pós-release: bugs entram como V1.9.x.

### Infraestrutura experimental pós-release

A Foundation pode receber **pontes pequenas, opt-in e sem mudança de geração** para
validar arquitetura futura, desde que o estado alpha seja explícito e não substitua
os marcos completos do roadmap.

Atualmente:

- **STAR Device Gateway V0.2** — ponte LAN + Adaptive Runtime;
- **STAR Mobile iOS V0** — iPhone como sensor/interface, sem MIND próprio;
- **STAR Watch Android V0.3** — Watch como sensor/interface, áudio PCM/WAV orientado a fala e comandos remotos seguros, sem MIND próprio;
- **STAR Watch App V0.4 + Plasma Orbit** — shell Watch-first validado primeiro no PC, preservando o Core compartilhado;
- **Command/Agent Foundation V0** — intents + catálogo de capacidades com estados `available/partial/planned`;
- **Voice Command Catalog V1.9** — catálogo por intents/slots;
- **Conversation Foundation V1.9** — small talk composicional;
- **Contextual Weather Provider V1.9** — clima online sob demanda de domínio estreito;
- **M.drives** — módulos removíveis de memória/conhecimento; `knowledge/packs` permanece apenas como compatibilidade legada.

### Integrated Evolution Alpha

A partir da Foundation foram implementadas fundações antecipadas, sem declarar as
releases futuras completas:

- **Cognitive Runtime** — Working Context, Salience e Model Router de engines registrados;
- **Goal Engine** — objetivos/tarefas persistentes, dependências, checkpoints e retomada;
- **Guardian alpha** — default-deny, confirmação, audit log e idempotência;
- **RAG híbrido** — FTS5/BM25 + índice semântico derivado; backend neural opcional;
- **OCR seletivo** — `pypdf` primeiro, PyMuPDF/Tesseract opcional;
- **Scientific/Cultural Knowledge Graph Indexer** — currículo científico e taxonomia cultural materializáveis no mesmo grafo;
- **Scientific Simulation Engine** — RK4 vetorial, órbita de dois corpos, pêndulo, calor 1D, onda 1D e RC;
- **Research Hub** — Crossref, OpenAlex, arXiv e PubMed/NCBI, opt-in de rede;
- **Operator File Index** — índice local somente leitura;
- **Senses Observation Contract** — formato único para observações/sensores, sem scene understanding;
- **M.drives** — nome oficial e loader compatível com legado;
- **Religion & Magic Knowledge 5M** — 100 tradições/relações religiosas + 25 campos de magia/esoterismo, 40 eixos por assunto, 5.000 nós canônicos e 5M visões endereçáveis lazy.

A expansão cultural usa política epistemológica explícita: autodescrição de praticantes,
registro histórico/etnográfico, interpretação acadêmica e evidência física são camadas
diferentes. Alegações sobrenaturais não viram automaticamente mecanismos científicos.
Conhecimento indígena/iniciático marcado como sensível não deve ser reconstruído quando
for fechado ou restrito pela comunidade.

Documentos principais:

- `docs/STAR_INTEGRATED_EVOLUTION_ALPHA.md`;
- `docs/STAR_RELIGION_MAGIC_5M.md`;
- `STAR_RELIGION_MAGIC_MANIFEST.json`.

Esses componentes adiantam trabalho de V2/V3/V4/V5/V7/V8, mas **não promovem a STAR
além da V1.9 estável** até que cada geração cumpra seus critérios completos.

O runtime compartilhado continua centralizando tema, rótulos, feature flags e perfis
`phone/watch` em `STAR_MANIFEST.json`. Endpoints não recebem MIND paralelo.

Ações remotas/sensíveis continuam bloqueadas até o Guardian completo integrar todas
as ações do Operator, autenticação, vault e sandbox.

---

## V2.0 — MIND

**Objetivo:** criar e amadurecer a arquitetura cognitiva permanente.

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

**Estado antecipado:** Reasoning/Planner/Memory já existem em alpha; Working Context,
Salience e Model Router explícito já possuem uma fundação alpha. Ainda faltam integração
cognitiva madura, compressão/seleção de contexto longo, consolidação e esquecimento
controlado de memória, seleção real de todos os modelos e critérios de release V2.

### V2.1 — Memory Architecture

Consolidar memória episódica/semântica/projetos, retenção, relevância, esquecimento
controlado, temporalidade, consolidação e avaliação.

### V2.2 — Knowledge Graph base

O armazenamento e os indexadores curricular/cultural já existem em alpha. Falta expandir
relações semânticas/proveniência em escala, resolução de entidades, contradições,
avaliações e integração profunda com consulta/RAG.

### V2.3 — Model Router

A fundação seleciona engines registrados. Falta registry completo de modelos locais/cloud,
benchmark, orçamento de recursos, fallback e seleção automática baseada em capacidade.

---

## V3.0 — KNOWLEDGE

**Objetivo:** transformar a STAR em plataforma de conhecimento offline expansível.

Inclui:

- Biblioteca;
- ingestão de PDF/texto;
- metadados e proveniência;
- embeddings locais;
- busca universal;
- M.drives V2;
- Knowledge Graph expandido;
- Scientific Engine;
- Cultural/History Engine;
- matemática simbólica, estatística, unidades, física, química e simulações.

**Estado antecipado:** ingestão documental/FTS5, RAG híbrido alpha, OCR opcional,
Knowledge Graph curricular/cultural, Research Hub, 5M culturais e simulações científicas
iniciais já existem. Faltam avaliação/reranking, vector backend maduro opcional, ingestão
multimodal robusta, proveniência em todo o conhecimento, resolução/retração de claims,
materialização licenciada de corpora e solvers especializados.

### Regra para conhecimento cultural

- não copiar obras protegidas integralmente apenas por estarem na web;
- preferir taxonomia, metadados, síntese original e fontes com licença clara;
- para tradições vivas, cruzar pesquisa acadêmica com autodescrição/comunidade;
- respeitar conhecimento restrito e não reconstruir rituais fechados;
- separar crença, relato, hipótese acadêmica e evidência científica.

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

**Estado antecipado:** comandos locais simples e File Index read-only existem. Escrita,
movimentação, automações gerais e ações destrutivas continuam bloqueadas até integração
com o Guardian completo.

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

**Estado antecipado:** Vision Portal/hand tracking e um contrato unificado de observações
já existem. **Scene understanding, Screen Awareness semântico e multimodal fusion ainda
não estão implementados.**

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

Inclui avatar 3D, rig, lip sync, animação procedural, olhar/piscar/gestos/locomoção,
ilhas tridimensionais, Casa, Laboratório, Central de Criação, Biblioteca, Estúdio,
Ateliê, Jardim, Observatório, Cura, Closet, Correio, Heróis, Idiomas e Digital Twin.

---

## V7.0 — GUARDIAN

**Objetivo:** transformar Cura em saúde, segurança e recuperação.

Inclui:

- Health Supervisor;
- watchdog;
- integridade de arquivos/hashes;
- integração antimalware/antivírus local;
- Permission Manager;
- Secrets Vault;
- Audit Log;
- snapshots;
- backup/rollback;
- sandbox;
- diagnóstico inteligente;
- proposta de reparo e aplicação autorizada.

**Estado antecipado:** Guardian alpha já fornece default-deny, política de ação, confirmação,
audit log, redaction básica e idempotência. Sandbox de SO, vault criptográfico, autenticação,
backup/rollback e cobertura de todas as ações ainda faltam.

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

**Estado antecipado:** Goal Engine alpha com persistência/dependências/checkpoints e o
orquestrador básico já existem. Scheduler, attention manager maduro, workers duráveis,
approval gates completos e autonomia controlada ponta-a-ponta ainda faltam.

---

## V9.0 — ECOSYSTEM

**Objetivo:** expandir a STAR para rede local e outros dispositivos.

Inclui STAR LAN, PC, celular, tablet, Watch, Device Manager, Offline-first Sync,
automação residencial, sensores, Mobile STAR e Network Awareness.

Princípio permanente: endpoints percebem, transmitem e executam; a fonte central
processa. Os protótipos Gateway/Mobile/Watch validam esse princípio, mas não substituem
Device Manager/Sync completos.

LOCAL continua funcional sem LAN ou Internet.

---

## V10.0 — EMBODIED

**Objetivo:** presença física sem prender a STAR a um fabricante.

Inclui Robot Abstraction Layer, câmera, microfone, alto-falante, display, motores,
sensores, bateria, telemetria, controle motor, percepção física e navegação segura.

---

## V11.0 — UNIFIED

**Objetivo:** integrar MIND, SENSES, ACTION, KNOWLEDGE, HEALTH, TRUST, WORLD e
robótica em uma plataforma coerente.

Inclui Event Bus maduro, observabilidade, resiliência, degradação graciosa,
Capability Tree, Cura global e sincronização de estado entre interfaces.

---

## V12+ — EXPANSION

Expansões sobre a arquitetura consolidada:

- Research Engine completo;
- Maker Engine;
- CAD;
- eletrônica;
- microcontroladores;
- impressão 3D;
- Coding Lab ampliado;
- Creative Engine;
- música/arte/vídeo/modelagem 3D;
- Language Engine;
- tradução offline ampliada;
- mapas e referência offline;
- expansão cultural/histórica com corpora licenciados;
- novos M.drives;
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

**V1.9 FINAL + Integrated Evolution Alpha → estabilizar CI/Windows e Watch-first →
concluir critérios de V2.0 MIND → amadurecer Knowledge/RAG/Graph/Research e Guardian.**
