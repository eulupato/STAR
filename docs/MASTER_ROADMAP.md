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

**Status em 31/08/2026: MIND FOUNDATION implementada na branch de desenvolvimento.**

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

Expansões ainda planejadas nesta geração:
- memória episódica, semântica, projetos e preferências;
- Personality/Identity Core expandido;
- Reasoning/Planning avançado;
- Model Router com múltiplos motores.

### V2.1
Memory Architecture.

### V2.2
Knowledge Graph base.

### V2.3
Model Router e seleção automática de motores.

---

## V3.0 — KNOWLEDGE
**Objetivo:** transformar a STAR em uma plataforma de conhecimento offline expansível.

Inclui Biblioteca, ingestão de PDF/texto, proveniência, embeddings locais,
busca universal, Knowledge Packs V2, Knowledge Graph, Scientific Engine,
matemática simbólica, estatística, unidades, física, química e simulações.

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
**V2.0 MIND FOUNDATION → validar em hardware real e seguir para V2.1 Memory Architecture.**
