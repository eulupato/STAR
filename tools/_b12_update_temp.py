from __future__ import annotations

import json
from pathlib import Path


# ---- STAR Core ----
core_path = Path("core/star_core.py")
core = core_path.read_text(encoding="utf-8")

import_line = "from core.self_model import SelfModel\n"
if import_line not in core:
    marker = "from core.scientific_foundations import ScientificFoundations\n"
    if marker not in core:
        raise SystemExit("star_core import marker not found")
    core = core.replace(marker, marker + import_line, 1)

init_marker = "        self.mind.everyday_technology = self.everyday_technology\n"
init_block = '''        self.mind.everyday_technology = self.everyday_technology

        # BLOCO 12: SELF MODEL auditável. Não cria uma segunda identidade, versão
        # ou fonte de estado; representa as fontes oficiais e usa default deny para
        # permissões. Capacidade, disponibilidade, permissão e segurança são separadas.
        self.self_model = SelfModel(
            self.knowledge,
            identity=self.identity,
            state=self.state,
            mind=self.mind,
            tools=self.tools,
            network_enabled_provider=lambda: bool(self.network_enabled),
        )
        self.mind.self_model = self.self_model
'''
if "self.self_model = SelfModel(" not in core:
    if init_marker not in core:
        raise SystemExit("star_core B11 init marker not found")
    core = core.replace(init_marker, init_block, 1)

route_marker = '''        everyday_technology_action = self.everyday_technology.handle(user_input)
        if everyday_technology_action:
            self.last_intent = "everyday_technology"
            return everyday_technology_action
'''
route_block = route_marker + '''
        self_model_action = self.self_model.handle(user_input)
        if self_model_action:
            self.last_intent = "self_model"
            return self_model_action
'''
if "self_model_action = self.self_model.handle(user_input)" not in core:
    if route_marker not in core:
        raise SystemExit("star_core B11 route marker not found")
    core = core.replace(route_marker, route_block, 1)

core_path.write_text(core, encoding="utf-8")

# ---- Manifest ----
manifest_path = Path("STAR_MIND_MANIFEST.json")
data = json.loads(manifest_path.read_text(encoding="utf-8"))
data["schema"] = max(int(data.get("schema", 0)), 13)

for principle in (
    "SELF MODEL describes STAR from official sources but is not an authority to redefine identity or fundamental rules",
    "identity remains sourced from core.star_identity.py and release/version remains sourced from STAR_MANIFEST.json",
    "capability, availability, permission and safety are distinct; operational permissions use default deny unless explicitly represented",
    "self history and experiences require auditable sources and are never fabricated to fill gaps",
    "unknown or unavailable self-state, device, resource and capability information remains explicit instead of being invented",
):
    if principle not in data["principles"]:
        data["principles"].append(principle)

capacity = data["block_3_universal_knowledge"]["namespace_capacity"]
if "B12" not in capacity["current_namespaces"]:
    capacity["current_namespaces"].append("B12")
capacity["truthfulness_note"] = (
    "each 1B is logical capacity per block namespace, not a billion preloaded rows; "
    "integrated B01-B12 therefore represent 12B logical addresses with only materialized knowledge persisted"
)

block12 = {
    "status": "experimental-integrated",
    "source_of_truth": "core/self_model.py for self representation; official identity remains core/star_identity.py",
    "integration": "core/star_core.py",
    "namespace": "B12",
    "database": "star.db through BLOCO 3 for materialized canonical self knowledge; runtime registries remain bounded in memory/views",
    "requested_topics": [
        "quem é", "o que é", "história", "versão", "identidade", "capacidades", "limitações",
        "recursos", "dispositivos", "estado", "permissões", "objetivos", "valores", "conhecimentos",
        "incertezas", "experiências",
    ],
    "components": [
        "Capability Registry", "Limitation Registry", "Permission Registry", "Identity",
        "Self State", "Self History", "Values",
    ],
    "official_sources": {
        "identity": "core.star_identity.StarIdentity",
        "release_version": "STAR_MANIFEST.json via core.release",
        "state": "core.state.StarState when attached",
        "cognitive_capabilities": "core.mind.CognitiveSuite",
        "tools": "core.tools.ToolRegistry when attached",
        "devices": "core.device_gateway.DeviceRegistry when attached",
        "canonical_knowledge": "BLOCO 2 -> BLOCO 3",
        "knowledge_graph": "existing knowledge_nodes/knowledge_edges",
    },
    "permission_policy": {
        "default": "deny",
        "capability_equals_permission": False,
        "permission_grants_capability": False,
        "permission_bypasses_safety": False,
        "self_model_can_grant_itself_external_authority": False,
        "operational_gate": "capability + permission + safety + current availability",
    },
    "history_policy": {
        "fabricate_history": False,
        "fabricate_experiences": False,
        "experience_requires_source_and_reference": True,
        "runtime_history_auto_canonicalized": False,
    },
    "identity_policy": {
        "parallel_identity_created": False,
        "self_model_is_identity_authority": False,
        "self_model_can_modify_identity": False,
        "self_model_can_modify_fundamental_rules": False,
        "self_model_can_modify_architecture_unrestricted": False,
        "scientifically_proven_biological_consciousness": False,
    },
    "knowledge_graph_taxonomy": "SELF MODEL -> domínio -> ramo -> subtema; root explicitly points to official identity, official release source and the conceptual B01 Self Model using the shared Knowledge Graph",
    "canonical_policy": "dynamic self state, permissions, resource snapshots and history are not automatically canonical; persistent B12 self knowledge requires the BLOCO 2 CANONICAL fact gate and BLOCO 3 promotion",
    "variant_matrix": {
        "time_scope": 10,
        "source": 10,
        "status": 10,
        "relation": 10,
        "confidence": 5,
        "context": 4,
        "evolution_stage": 10,
        "combinations_per_node": 2000000,
    },
    "self_model_catalog": {
        "domains": 13,
        "branches": 50,
        "lenses_per_branch": 10,
        "canonical_nodes": 500,
        "variants_per_node": 2000000,
        "addressable_contents": 1000000000,
        "materialization": "on-demand",
        "prepopulated_knowledge_rows": 0,
        "truthfulness_note": "1B are deterministic addressable self representations across time, source, status, relation, confidence, context and evolution; not 1B fabricated memories, experiences, identities or system states",
    },
}

rebuilt = {}
inserted = False
for key, value in data.items():
    if key == "cognitive_catalog" and not inserted:
        rebuilt["block_12_self_model"] = block12
        inserted = True
    rebuilt[key] = value
if not inserted:
    rebuilt["block_12_self_model"] = block12

rebuilt.setdefault("persistence", {})["self_model"] = (
    "no new table; canonical B12 self knowledge persists through universal_knowledge and the shared Knowledge Graph; "
    "runtime Capability/Limitation/Permission registries, Self State views and bounded Self History remain non-canonical unless explicitly promoted through B02/B03"
)
manifest_path.write_text(json.dumps(rebuilt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ---- Roadmap ----
roadmap_path = Path("docs/MASTER_ROADMAP.md")
roadmap = roadmap_path.read_text(encoding="utf-8")
block_text = r'''
### BLOCO 12 — Self Model

O BLOCO 12 transforma o **SELF MODEL conceitual do BLOCO 1** em uma camada
operacional de autorrepresentação auditável. A STAR passa a representar **quem é,
o que é, história, versão, identidade, capacidades, limitações, recursos,
dispositivos, estado, permissões, objetivos, valores, conhecimentos, incertezas e
experiências**, sem criar uma segunda identidade ou inventar fatos sobre si.

Implementação central: `core/self_model.py`, integrada em `core/star_core.py`.
Todos os componentes pedidos ficam no mesmo módulo para evitar fragmentação:

- `CapabilityRegistry` — capacidade com status `available`, `experimental`,
  `planned`, `unavailable` ou `unknown`; capacidade não concede permissão;
- `LimitationRegistry` — limitações técnicas, epistêmicas, operacionais e de
  identidade com fonte explícita;
- `PermissionRegistry` — representação de permissões com **DEFAULT DENY**;
  permissão não cria capacidade nem ignora segurança;
- `Identity` — visão somente leitura sobre `core.star_identity.StarIdentity`;
- `SelfState` — visão sobre `core.state.StarState` e observações runtime explícitas;
- `SelfHistory` — histórico bounded de eventos reais; experiências exigem fonte e
  referência auditável;
- `Values` — visão somente leitura de propósito, princípios, decisão e limites da
  identidade oficial.

Fontes únicas de verdade preservadas:

```text
IDENTIDADE        -> core/star_identity.py
VERSÃO / RELEASE  -> STAR_MANIFEST.json via core/release.py
ESTADO            -> core/state.py quando anexado ao runtime
CAPACIDADES MIND  -> core/mind.py
FERRAMENTAS       -> ToolRegistry quando anexado
DISPOSITIVOS      -> DeviceRegistry quando anexado
CONHECIMENTO      -> BLOCO 2 -> BLOCO 3 -> Knowledge Graph
```

O Self Model **não copia nem substitui** essas fontes. Se um registry, dispositivo,
recurso ou telemetria não estiver disponível, o estado é `unknown`/`unavailable`;
isso não é convertido em uma informação inventada. O `DeviceRegistry` é lido por
registros públicos e o Self Model não expõe hashes/tokens de pareamento.

Regras permanentes:

```text
SELF MODEL ≠ FONTE DA IDENTIDADE
SELF MODEL ≠ AUTORIDADE PARA REDEFINIR A STAR
CAPACIDADE ≠ DISPONIBILIDADE ≠ PERMISSÃO ≠ SEGURANÇA
PLANEJADO ≠ DISPONÍVEL
UNKNOWN ≠ DISPONÍVEL
PERMISSÃO NÃO CRIA CAPACIDADE
PERMISSÃO NÃO IGNORA SEGURANÇA
ESTADO RUNTIME ≠ CONHECIMENTO CANÔNICO AUTOMÁTICO
HISTÓRIA / EXPERIÊNCIA ≠ ALGO QUE PODE SER FABRICADO
AUSÊNCIA DE REGISTRY ≠ PROVA DE AUSÊNCIA DO RECURSO/DISPOSITIVO
```

A política operacional permanece a mesma da Foundation:

```text
AÇÃO EXTERNA = CAPACIDADE + PERMISSÃO + SEGURANÇA + DISPONIBILIDADE ATUAL
```

O `PermissionRegistry` apenas **representa** autorizações conhecidas. Ele não é um
executor e não permite que a STAR conceda a si mesma autoridade operacional. As
permissões de automodificação de identidade, regras fundamentais e arquitetura
permanecem negadas conforme a identidade oficial.

`SelfHistory` não tenta criar uma autobiografia artificial. Eventos precisam de
fonte, e uma entrada marcada como experiência exige também referência auditável.
Snapshots do Self Model mantêm separadas observação, história e conhecimento
canônico. Um fato persistente B12 continua exigindo claim `fact` `CANONICAL` no
BLOCO 2 e promoção explícita pelo BLOCO 3.

Taxonomia oficial:

```text
SELF MODEL
↓
DOMÍNIO
↓
RAMO
↓
SUBTEMA
↓
CONHECIMENTO CANÔNICO SOBRE A STAR
```

São **13 domínios e 50 ramos**, cobrindo identidade/natureza; história/evolução;
versão/release; capacidades; limitações; recursos; dispositivos; estado próprio;
permissões; objetivos; valores; conhecimento/incerteza; experiências/relações.
Cada ramo é cruzado por 10 lentes: definição, estado atual, fonte/proveniência,
capacidade, limitação, permissão, relação, história/mudança, confiança/incerteza e
auditoria/validação.

Matriz B12:

```text
TIME_SCOPE       10
× SOURCE          10
× STATUS          10
× RELATION        10
× CONFIDENCE       5
× CONTEXT          4
× EVOLUTION_STAGE 10
= 2.000.000 variações por nó
```

Escala do BLOCO 12:

- **13 domínios**;
- **50 ramos × 10 lentes = 500 nós canônicos**;
- **2.000.000 variações por nó**;
- **500 × 2.000.000 = 1.000.000.000 de representações endereçáveis em `B12`**;
- IDs `SELF-B12-0000000001` até `SELF-B12-1000000000`;
- materialização sob demanda; zero requisito de 1B de memórias, experiências,
  identidades, estados ou fatos pré-carregados.

Com B12, B01–B12 oferecem **12B de endereços lógicos independentes**. O BLOCO 12
é a fundação operacional do Self Model da futura MIND, mas **não conclui V2.0 por
si só**, não concede autoconsciência biologicamente comprovada, não cria liberdade
irrestrita, não implementa automodificação autônoma e não antecipa Guardian/Agent.

'''
marker = "\n### V2.1\n"
if "### BLOCO 12 — Self Model" not in roadmap:
    if marker not in roadmap:
        raise SystemExit("V2.1 roadmap marker not found")
    roadmap = roadmap.replace(marker, "\n" + block_text + "### V2.1\n", 1)
roadmap_path.write_text(roadmap, encoding="utf-8")
