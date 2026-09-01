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

Inclui Core e identidade, memória básica, matemática natural, interface 2D,
HUB/ilhas/Casa/Closet/skins, Knowledge Packs, STT local, voz local, controle
inicial do computador, CI, logs e documentação.

Pós-release: bugs entram como V1.9.x.

---

## V2.0 — MIND
**Objetivo:** criar a arquitetura cognitiva permanente.

**Status em 31/08/2026: MIND consolidada e absorvida pela V3.0 KNOWLEDGE.**

Implementado na fundação V2.0:
- Cognitive Loop;
- Event Bus;
- Executive MIND;
- Salience Engine;
- Context Engine;
- Working Memory;
- planejamento operacional determinístico;
- Capability Registry;
- metacognição operacional observável;
- fallback seguro para a fundação V1.9;
- diagnóstico da MIND.

Consolidação incorporada à V3:
- contexto com Entity Tracking e resolução de referências;
- Personality Engine separado de modelos;
- Conversation Variation Engine local;
- Knowledge Search integrado ao Planner;
- Capability Registry expandido;
- Event Bus usado por WORLD/mídia;
- modelos externos permanecem opcionais e desativados por padrão.

Expansões profundas de memória persistente e múltiplos modelos continuam
incrementais, sem redefinir a identidade da STAR.

### V2.1
Memory Architecture.

### V2.2
Knowledge Graph base.

### V2.3
Model Router e seleção automática de motores.

---

## V3.0 — KNOWLEDGE
**Objetivo:** transformar a STAR em uma plataforma de conhecimento offline expansível e conectar essa base ao STAR WORLD funcional.

**Status em 01/09/2026: arquitetura integrada em DEVELOPMENT / knowledge-foundation.**

Implementado nesta fundação:
- Entity System genérico;
- SQLite local dedicado com conexões curtas para Windows;
- aliases, fontes e proveniência;
- Knowledge Graph;
- índice estrutural `entity_values` e migração versionada;
- Universal Search;
- pipeline PDF reutilizável;
- fontes oficiais DC/Marvel opcionais com validação de identidade;
- primeira ilha de conhecimento navegável: Heróis;
- busca, carrossel e filtros estruturados;
- Conversation Variation Engine;
- STAR TV com MediaController e WebView opcional;
- STAR WORLD com navegação contextual e overlays sem ciclos;
- Casa navegável: Sala, Cozinha, Quarto, Closet e Álbum;
- Cozinha com RecipeBook e guia passo a passo;
- PhotoLibrary local inicial;
- memória de conversa persistente gravada e restaurada;
- voz degradável no startup;
- Whisper/Piper preparados explicitamente pelo instalador;
- runtime sem download implícito de modelo;
- higiene de repositório e CI Linux/Windows.

Status dos ambientes V3 atuais:
- **Casa:** available;
- **Cozinha:** available;
- **Quarto:** available;
- **Closet:** available;
- **Álbum:** partial;
- **Sala / STAR TV:** experimental;
- **Ilha dos Heróis:** partial.

Pendente antes de release READY:
- ingestão e revisão integral dos dois PDFs locais de heróis;
- validação da cobertura/associação final de imagens;
- validação física da STAR TV no Windows real;
- regressão física de microfone, alto-falante, Chatterbox e referência local;
- sprites emocionais reais para substituir indicadores de fallback;
- expansão de metadados/seletor de pasta do Álbum;
- persistência completa do estado de objetos/cenas do STAR WORLD;
- expansão progressiva da Biblioteca/Scientific Engine.

A ausência desses itens não deve ser mascarada por porcentagens ou estados
falsos: componentes incompletos permanecem `partial`, `experimental` ou
`planned` no catálogo.

Auditoria atual: `docs/V3_0_AUDIT_2026-09-01.md`.

---

## V4.0 — OPERATOR
**Objetivo:** controlar o computador e aplicativos de forma geral e segura.

Inclui Application Manager, skills por aplicativo, File Index, busca semântica
de arquivos, controle de janelas/sistema, automações, clipboard, volume,
processos, dispositivos, permissões e logs por ação.

---

## V5.0 — SENSES
**Objetivo:** percepção multimodal.

Inclui wake word opcional, VAD, interrupção/barge-in, voz com streaming,
visão, webcam, imagens, Screen Awareness, Spatial Awareness e Multimodal Fusion.

---

## V6.0 — STAR WORLD 3D
**Objetivo:** reconstruir a experiência visual em 3D.

Princípio: STAR CORE ↔ Event Bus/API ↔ STAR WORLD 3D.

Inclui avatar 3D, rig, lip sync, animação procedural, ilhas tridimensionais e
os ambientes oficiais da STAR.

---

## V7.0 — GUARDIAN
**Objetivo:** transformar Cura em saúde, segurança e recuperação.

Inclui Health Supervisor, watchdog, integridade, hashes, antimalware local,
Permission Manager, Secrets Vault, Audit Log, snapshots, backup, rollback,
sandbox, diagnóstico e reparo autorizado.

---

## V8.0 — AGENT
**Objetivo:** trabalhar por objetivos, não apenas comandos isolados.

Inclui Goal Engine, Planner, Task Manager, Scheduler, Attention Manager,
Simulation Mode, Skill SDK, Capability Registry, tarefas persistentes e
verificação de resultado.

---

## V9.0 — ECOSYSTEM
**Objetivo:** expandir a STAR para rede local e outros dispositivos.

Inclui STAR LAN, PC, celular, tablet, Device Manager, Offline-first Sync,
automação residencial, sensores, Mobile STAR e Network Awareness.

LOCAL continua funcional sem LAN ou Internet.

---

## V10.0 — EMBODIED
**Objetivo:** presença física sem prender a STAR a um fabricante.

Inclui Robot Abstraction Layer, câmera, microfone, alto-falante, display,
motores, sensores, bateria, telemetria, controle motor e percepção física.

---

## V11.0 — UNIFIED
**Objetivo:** integrar MIND, SENSES, ACTION, KNOWLEDGE, HEALTH, TRUST, WORLD e robótica.

Inclui Event Bus maduro, observabilidade, resiliência, degradação graciosa,
Capability Tree, Cura global e sincronização entre interfaces.

---

## V12+ — EXPANSION
Expansões sobre a arquitetura consolidada: Research Engine, Maker Engine, CAD,
eletrônica, microcontroladores, impressão 3D, Coding Lab, Creative Engine,
música, arte, vídeo, modelagem 3D, Language Engine, tradução offline, mapas,
novos Knowledge Packs e novas skills.

# Sistemas transversais
Event Bus, Resource Governor, perfis ECO/NORMAL/MAX, Model Registry, Sleep
Processing, Universal Inbox, Backup, Audit Trail, Capability Registry, Secrets
Vault, Crash Recovery, Health Supervisor, Hardware Abstraction Layer, Plugin/Skill
SDK, Task Scheduler, Notification Center, Semantic File Index e Personal
Knowledge Graph.

# Modos oficiais
- **LOCAL** — STAR completa no computador.
- **LAN** — STAR + dispositivos locais.
- **ONLINE** — recursos externos opcionais.

**Internet amplia a STAR; não constitui a STAR.**

# Regra de execução
Cada geração segue especificação, arquitetura, implementação incremental,
testes/diagnóstico, documentação, release e freeze.

# Próximo marco
**V3.0 KNOWLEDGE → concluir validações locais de conteúdo, TV e voz; depois freeze.**
