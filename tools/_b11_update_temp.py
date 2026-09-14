from __future__ import annotations

import json
from pathlib import Path


BRANCH = "feat/bloco11-mundo-cotidiano-tecnologia"

# ---- STAR Core: surgical insertion only ----
core_path = Path("core/star_core.py")
core = core_path.read_text(encoding="utf-8")

import_line = "from core.everyday_technology import EverydayTechnologyFoundations\n"
if import_line not in core:
    marker = "from core.conversation import ConversationEngine\n"
    if marker not in core:
        raise SystemExit("star_core import marker not found")
    core = core.replace(marker, marker + import_line, 1)

init_marker = "        self.mind.human_contexts = self.human_contexts\n"
init_block = '''        self.mind.human_contexts = self.human_contexts

        # BLOCO 11: mundo cotidiano e tecnológico. Relaciona objetos, sistemas,
        # funções, usos, riscos, estados e contextos sobre B04/B05/B10 e as bases
        # multidisciplinares existentes, sem criar outro motor técnico ou banco.
        self.everyday_technology = EverydayTechnologyFoundations(
            self.knowledge,
            physical_world=self.physical_world,
            scientific_foundations=self.scientific_foundations,
            human_contexts=self.human_contexts,
        )
        self.mind.everyday_technology = self.everyday_technology
'''
if "self.everyday_technology = EverydayTechnologyFoundations(" not in core:
    if init_marker not in core:
        raise SystemExit("star_core B10 init marker not found")
    core = core.replace(init_marker, init_block, 1)

route_marker = '''        human_context_action = self.human_contexts.handle(user_input)
        if human_context_action:
            self.last_intent = "human_contexts"
            return human_context_action
'''
route_block = route_marker + '''
        everyday_technology_action = self.everyday_technology.handle(user_input)
        if everyday_technology_action:
            self.last_intent = "everyday_technology"
            return everyday_technology_action
'''
if "everyday_technology_action = self.everyday_technology.handle(user_input)" not in core:
    if route_marker not in core:
        raise SystemExit("star_core B10 route marker not found")
    core = core.replace(route_marker, route_block, 1)

core_path.write_text(core, encoding="utf-8")

# ---- STAR MIND manifest ----
manifest_path = Path("STAR_MIND_MANIFEST.json")
data = json.loads(manifest_path.read_text(encoding="utf-8"))
data["schema"] = max(int(data.get("schema", 0)), 12)

for principle in (
    "everyday and technical knowledge never implies live state, operational access or authorization by itself",
    "software, hardware, networks and infrastructure preserve platform, version, configuration, current-source and uncertainty context when relevant",
    "BLOCO 11 reuses physical, scientific, human-context and multidisciplinary technical knowledge instead of duplicating computing, IT or engineering engines",
):
    if principle not in data["principles"]:
        data["principles"].append(principle)

capacity = data["block_3_universal_knowledge"]["namespace_capacity"]
if "B11" not in capacity["current_namespaces"]:
    capacity["current_namespaces"].append("B11")
capacity["truthfulness_note"] = (
    "each 1B is logical capacity per block namespace, not a billion preloaded rows; "
    "integrated B01-B11 therefore represent 11B logical addresses with only materialized knowledge persisted"
)

block11 = {
    "status": "experimental-integrated",
    "source_of_truth": "core/everyday_technology.py",
    "integration": "core/star_core.py",
    "namespace": "B11",
    "database": "star.db through BLOCO 3 for materialized canonical knowledge",
    "requested_topics": [
        "casas", "edificações", "cidades", "trânsito", "transportes", "navegação",
        "culinária", "rotinas", "ferramentas", "máquinas", "computadores", "hardware",
        "software", "programação", "sistemas operacionais", "redes", "internet",
        "segurança digital", "energia", "infraestrutura", "documentos", "mídia", "objetos cotidianos",
    ],
    "relation_axes": ["objects", "systems", "functions", "uses", "risks", "states", "contexts"],
    "reuse": {
        "canonical_knowledge": "BLOCO 3 UniversalKnowledgeArchitecture",
        "claims_evidence_provenance": "BLOCO 2 epistemic ledger",
        "knowledge_graph": "existing knowledge_nodes/knowledge_edges",
        "physical_world": "BLOCO 4 PhysicalWorldModel",
        "scientific_foundations": "BLOCO 5 ScientificFoundations",
        "human_contexts": "BLOCO 10 HumanContextFoundations",
        "multidisciplinary": "existing engineering, geography, mechanics, computing and IT subjects loaded lazily",
        "parallel_technology_database_created": False,
        "parallel_technology_graph_created": False,
        "parallel_computing_engine_created": False,
    },
    "knowledge_graph_taxonomy": "Mundo Cotidiano e Tecnológico -> domínio -> ramo -> subtema; canonical B11 knowledge is linked to its branch in the same shared graph",
    "canonical_policy": "technical references and situational interpretations are never auto-promoted; persistent B11 knowledge requires the BLOCO 2 CANONICAL fact gate and BLOCO 3 promotion",
    "interpretation_policy": {
        "knowledge_implies_operational_access": False,
        "technical_description_implies_authorization": False,
        "digital_security_knowledge_implies_attack_permission": False,
        "navigation_knowledge_is_live_route_data": False,
        "infrastructure_description_is_live_status": False,
        "software_behavior_is_version_independent": False,
        "hardware_behavior_is_platform_independent": False,
        "unknown_state_may_be_invented": False,
        "live_conditions_require_current_source": True,
        "operational_action_requires_permission_capability_safety": True,
        "rule": "CONHECER UM OBJETO OU SISTEMA NÃO SIGNIFICA POSSUIR ACESSO, CONTROLE, ESTADO AO VIVO OU AUTORIZAÇÃO PARA OPERÁ-LO",
    },
    "variant_matrix": {
        "object": 10,
        "system": 10,
        "function": 10,
        "use": 10,
        "risk": 5,
        "state": 4,
        "context": 10,
        "combinations_per_node": 2000000,
    },
    "everyday_technology_catalog": {
        "domains": 13,
        "branches": 50,
        "lenses_per_branch": 10,
        "canonical_nodes": 500,
        "variants_per_node": 2000000,
        "addressable_contents": 1000000000,
        "materialization": "on-demand",
        "prepopulated_knowledge_rows": 0,
        "truthfulness_note": "1B are deterministic addressable representations across objects, systems, functions, uses, risks, states and contexts; not 1B independent technical facts, devices, recipes, programs or files",
    },
}

rebuilt = {}
inserted = False
for key, value in data.items():
    if key == "cognitive_catalog" and not inserted:
        rebuilt["block_11_everyday_technology"] = block11
        inserted = True
    rebuilt[key] = value
if not inserted:
    rebuilt["block_11_everyday_technology"] = block11

rebuilt.setdefault("persistence", {})["everyday_technology_foundations"] = (
    "no new table; canonical B11 knowledge persists through universal_knowledge, taxonomy/relations use the shared Knowledge Graph, "
    "and situational technical interpretation does not imply live state, access or operational authorization"
)
manifest_path.write_text(json.dumps(rebuilt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ---- Official roadmap ----
roadmap_path = Path("docs/MASTER_ROADMAP.md")
roadmap = roadmap_path.read_text(encoding="utf-8")
block_text = r'''
### BLOCO 11 — Mundo Cotidiano e Tecnologia

O BLOCO 11 organiza o conhecimento da STAR sobre o **mundo cotidiano e tecnológico**
como uma camada integradora entre objetos físicos, sistemas técnicos, usos humanos,
infraestrutura e conhecimento computacional. Ele cobre **casas, edificações,
cidades, trânsito, transportes, navegação, culinária, rotinas, ferramentas,
máquinas, computadores, hardware, software, programação, sistemas operacionais,
redes, internet, segurança digital, energia, infraestrutura, documentos, mídia e
objetos cotidianos**.

Implementação central: `core/everyday_technology.py`, integrada em
`core/star_core.py`. O BLOCO 11 não cria um segundo catálogo de Física, Engenharia,
Computação ou TI. Reutiliza:

- BLOCO 2 para proveniência, evidência, confiança, incerteza e validade;
- BLOCO 3 para conhecimento canônico, deduplicação, busca e Knowledge Graph;
- BLOCO 4 para propriedades, estados e riscos do mundo físico;
- BLOCO 5 para fundamentos científicos e energia;
- BLOCO 10 para contexto humano situado;
- `core.multidisciplinary_knowledge.py` para Engenharia, Geografia, Mecânica,
  Computação e TI já existentes, carregadas sob demanda.

A taxonomia B11 inclui 13 domínios e 50 ramos: ambiente construído e sistemas
prediais; cidades, trânsito e transporte público; navegação, mapas, veículos e
logística; culinária, segurança alimentar e rotinas; ferramentas, máquinas,
eletrodomésticos e manutenção; computadores, componentes, periféricos e IoT;
software, programação, dados, aplicações e desenvolvimento; sistemas operacionais,
arquivos, processos, usuários e permissões; redes, internet, protocolos, web e
nuvem; segurança digital, identidade/acesso e higiene digital; energia,
infraestrutura elétrica, água/saneamento e telecomunicações; documentos, mídia e
formatos; objetos domésticos, pessoais, embalagens e armazenamento.

Cada ramo é observado por 10 lentes: **conceito, estrutura/componentes, função,
operação, uso, estado, risco, falha/manutenção, contexto e relações**. As relações
canônicas e taxonômicas usam o mesmo Knowledge Graph oficial.

Regras permanentes:

```text
CONHECIMENTO TÉCNICO ≠ ACESSO OPERACIONAL
DESCRIÇÃO DE SISTEMA ≠ AUTORIZAÇÃO PARA OPERÁ-LO
SEGURANÇA DIGITAL ≠ PERMISSÃO PARA ATACAR OU ALTERAR SISTEMAS
CONHECIMENTO DE NAVEGAÇÃO ≠ ROTA/CONDIÇÃO AO VIVO
DESCRIÇÃO DE INFRAESTRUTURA ≠ ESTADO ATUAL DA INFRAESTRUTURA
SOFTWARE/HARDWARE → PRESERVAR VERSÃO, PLATAFORMA E CONFIGURAÇÃO
ESTADO NÃO OBSERVADO → PERMANECE DESCONHECIDO
AÇÃO EXTERNA → CONTINUA EXIGINDO CAPACIDADE + PERMISSÃO + SEGURANÇA
```

`contextualize_system(...)` cruza objeto, sistema, função, uso, risco, estado e
contexto, mas retorna uma inferência contextual: não inventa telemetria, não afirma
condições ao vivo sem fonte atual e não concede acesso ou autorização operacional.
Para culinária, segurança alimentar, temperatura, conservação, alergênicos e
contaminação cruzada são preservados quando relevantes. Para tecnologia digital,
versão/plataforma/configuração e limites de segurança permanecem explícitos.

Matriz B11:

```text
OBJETO   10
× SISTEMA  10
× FUNÇÃO   10
× USO      10
× RISCO     5
× ESTADO    4
× CONTEXTO 10
= 2.000.000 variações por nó
```

Escala do BLOCO 11:

- **13 domínios**;
- **50 ramos × 10 lentes = 500 nós canônicos**;
- **2.000.000 variações por nó** usando os sete eixos solicitados;
- **500 × 2.000.000 = 1.000.000.000 de representações endereçáveis em `B11`**;
- IDs `TECH-B11-0000000001` até `TECH-B11-1000000000`;
- materialização sob demanda; zero requisito de 1B de dispositivos, fatos,
  programas, receitas, documentos, arquivos ou linhas pré-carregadas.

Com B11, B01–B11 oferecem **11B de endereços lógicos independentes**. Somente
conhecimento materializado ocupa disco, índices e RAM. O BLOCO 11 amplia o WORLD
MODEL e a base de conhecimento, mas não implementa antecipadamente o V4 OPERATOR,
não concede controle irrestrito do computador, não transforma conhecimento de
segurança em capacidade ofensiva e não marca V2.0, V3.0 ou V4.0 como concluídos.

'''
marker = "\n### V2.1\n"
if "### BLOCO 11 — Mundo Cotidiano e Tecnologia" not in roadmap:
    if marker not in roadmap:
        raise SystemExit("V2.1 roadmap marker not found")
    roadmap = roadmap.replace(marker, "\n" + block_text + "### V2.1\n", 1)
roadmap_path.write_text(roadmap, encoding="utf-8")
