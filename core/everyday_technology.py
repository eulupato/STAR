"""BLOCO 11 — Mundo Cotidiano e Tecnológico da STAR.

Camada integradora para casas, cidades, mobilidade, culinária, rotinas, ferramentas,
máquinas, computação, software, redes, energia, infraestrutura, documentos, mídia
e objetos cotidianos. Reutiliza B04/B05/B10 e as bases multidisciplinares existentes
em vez de criar outro motor de física, engenharia, computação ou TI.

Escala lógica:
- 50 ramos x 10 lentes = 500 nós canônicos;
- OBJETO(10) x SISTEMA(10) x FUNÇÃO(10) x USO(10) x RISCO(5) x ESTADO(4)
  x CONTEXTO(10) = 2.000.000 variações por nó;
- 500 x 2.000.000 = 1.000.000.000 representações endereçáveis em B11.

Tudo é materializado sob demanda. 1B não significa 1B de fatos, dispositivos,
receitas, arquivos, programas ou linhas pré-carregadas.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import prod
import re
import unicodedata
from typing import Any

from core.universal_knowledge import UniversalKnowledgeArchitecture


@dataclass(frozen=True)
class EverydayTechnologyBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(";") if item.strip())


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", _clean(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


EVERYDAY_TECH_DOMAINS = (
    "built_environment",
    "cities_mobility",
    "navigation_logistics",
    "food_routines",
    "tools_machines",
    "computing_hardware",
    "software_programming",
    "operating_systems",
    "networks_internet",
    "digital_security",
    "energy_infrastructure",
    "documents_media",
    "everyday_objects",
)

DOMAIN_LABELS = {
    "built_environment": "Casas, edificações e serviços prediais",
    "cities_mobility": "Cidades, trânsito e mobilidade",
    "navigation_logistics": "Navegação, transportes e logística",
    "food_routines": "Culinária, alimentação e rotinas",
    "tools_machines": "Ferramentas, máquinas e manutenção",
    "computing_hardware": "Computadores e hardware",
    "software_programming": "Software e programação",
    "operating_systems": "Sistemas operacionais",
    "networks_internet": "Redes e internet",
    "digital_security": "Segurança digital",
    "energy_infrastructure": "Energia e infraestrutura",
    "documents_media": "Documentos e mídia",
    "everyday_objects": "Objetos cotidianos",
}

EVERYDAY_TECH_BRANCHES = (
    EverydayTechnologyBranch("built_environment", "homes", "Casas e moradias", _subs("casas;moradias;cômodos;portas;janelas;telhados;pisos;mobiliário;uso doméstico;segurança doméstica")),
    EverydayTechnologyBranch("built_environment", "buildings", "Edificações e estruturas", _subs("edificações;prédios;estruturas;fundações;escadas;elevadores;acessos;fachadas;circulação;ocupação")),
    EverydayTechnologyBranch("built_environment", "building_utilities", "Sistemas prediais", _subs("instalação elétrica;água;esgoto;gás;ventilação;climatização;iluminação;detecção de incêndio;telecomunicações")),
    EverydayTechnologyBranch("built_environment", "building_maintenance", "Manutenção e operação de edificações", _subs("manutenção;inspeção;limpeza;reparos;falhas;desgaste;segurança;eficiência;acessibilidade")),

    EverydayTechnologyBranch("cities_mobility", "cities", "Cidades e espaço urbano", _subs("cidades;bairros;ruas;calçadas;praças;zoneamento;serviços urbanos;mobilidade;densidade;acessibilidade")),
    EverydayTechnologyBranch("cities_mobility", "traffic", "Trânsito e circulação", _subs("trânsito;sinalização;semáforos;cruzamentos;faixas;velocidade;fluxo;pedestres;ciclistas;risco viário")),
    EverydayTechnologyBranch("cities_mobility", "roads_streets", "Vias, ruas e rodovias", _subs("ruas;avenidas;rodovias;pavimento;faixas;interseções;acostamento;drenagem;obras;condições de via")),
    EverydayTechnologyBranch("cities_mobility", "public_transport", "Transporte público", _subs("ônibus;metrô;trem;BRT;estações;paradas;linhas;tarifas;integração;acessibilidade")),

    EverydayTechnologyBranch("navigation_logistics", "navigation", "Navegação e orientação", _subs("navegação;orientação;direção;posição;rota;destino;referências;GPS;bússola;incerteza de localização")),
    EverydayTechnologyBranch("navigation_logistics", "maps_routes", "Mapas e rotas", _subs("mapas;cartografia;rotas;coordenadas;escala;legenda;trajeto;desvios;restrições;mapas digitais")),
    EverydayTechnologyBranch("navigation_logistics", "vehicles_transport", "Veículos e meios de transporte", _subs("carro;moto;bicicleta;ônibus;trem;avião;barco;propulsão;controle;manutenção;segurança")),
    EverydayTechnologyBranch("navigation_logistics", "logistics", "Logística e movimentação", _subs("logística;carga;entrega;armazenagem;embalagem;distribuição;roteirização;estoque;última milha;cadeia de suprimento")),

    EverydayTechnologyBranch("food_routines", "culinary", "Culinária e preparo de alimentos", _subs("culinária;cozinha;ingredientes;receitas;técnicas;calor;corte;mistura;tempo;equipamentos;porções")),
    EverydayTechnologyBranch("food_routines", "food_safety", "Segurança e conservação de alimentos", _subs("higiene;contaminação;armazenamento;refrigeração;cozimento;temperatura;validade;alergênicos;contaminação cruzada")),
    EverydayTechnologyBranch("food_routines", "household_routines", "Rotinas domésticas", _subs("rotinas;limpeza;lavagem;organização;compras;preparo;manutenção doméstica;descarte;checklists")),
    EverydayTechnologyBranch("food_routines", "time_organization", "Organização cotidiana e tempo", _subs("agenda;sequência;prioridade;tempo;hábitos;lembretes;planejamento;repetição;dependências;rotina")),

    EverydayTechnologyBranch("tools_machines", "hand_tools", "Ferramentas manuais", _subs("ferramentas;martelo;chave;alicate;serrote;tesoura;medição;fixação;corte;uso seguro")),
    EverydayTechnologyBranch("tools_machines", "power_tools", "Ferramentas elétricas e motorizadas", _subs("furadeira;parafusadeira;serra;lixadeira;motor;bateria;energia;proteção;manutenção;risco")),
    EverydayTechnologyBranch("tools_machines", "machines", "Máquinas e mecanismos", _subs("máquinas;motores;engrenagens;transmissões;bombas;compressores;atuadores;sensores;controles;falhas")),
    EverydayTechnologyBranch("tools_machines", "appliances", "Eletrodomésticos e aparelhos", _subs("geladeira;fogão;forno;micro-ondas;lavadora;aspirador;ar-condicionado;ventilador;consumo;manutenção")),
    EverydayTechnologyBranch("tools_machines", "maintenance_repairs", "Manutenção, diagnóstico e reparos", _subs("manutenção preventiva;manutenção corretiva;inspeção;diagnóstico;desgaste;lubrificação;substituição;teste;segurança")),

    EverydayTechnologyBranch("computing_hardware", "computers", "Computadores", _subs("computadores;desktop;notebook;servidor;dispositivos móveis;arquitetura;entrada;processamento;armazenamento;saída")),
    EverydayTechnologyBranch("computing_hardware", "computer_components", "Componentes de hardware", _subs("CPU;GPU;RAM;placa-mãe;SSD;HDD;fonte;refrigeração;barramentos;firmware")),
    EverydayTechnologyBranch("computing_hardware", "peripherals", "Periféricos e interfaces", _subs("teclado;mouse;monitor;impressora;câmera;microfone;alto-falante;USB;Bluetooth;drivers")),
    EverydayTechnologyBranch("computing_hardware", "embedded_mobile", "Dispositivos embarcados, móveis e IoT", _subs("smartphone;smartwatch;microcontrolador;sensores;IoT;firmware;bateria;conectividade;telemetria;limites")),

    EverydayTechnologyBranch("software_programming", "software", "Software e aplicações", _subs("software;aplicativos;serviços;interfaces;dados;configuração;versão;dependências;bugs;atualizações")),
    EverydayTechnologyBranch("software_programming", "programming", "Programação", _subs("programação;algoritmos;variáveis;controle de fluxo;funções;tipos;estruturas de dados;erros;testes;depuração")),
    EverydayTechnologyBranch("software_programming", "data_files", "Dados, arquivos e formatos", _subs("dados;arquivos;diretórios;formatos;texto;binário;JSON;CSV;imagem;áudio;codificação")),
    EverydayTechnologyBranch("software_programming", "applications", "Aplicações e fluxos digitais", _subs("aplicações;interface;entrada;saída;estado;preferências;sessões;integrações;automação;acessibilidade")),
    EverydayTechnologyBranch("software_programming", "software_development", "Desenvolvimento de software", _subs("requisitos;design;controle de versão;Git;build;testes;CI/CD;deploy;observabilidade;manutenção")),

    EverydayTechnologyBranch("operating_systems", "os_concepts", "Conceitos de sistemas operacionais", _subs("sistemas operacionais;kernel;drivers;serviços;processos;memória;dispositivos;boot;interface;configuração")),
    EverydayTechnologyBranch("operating_systems", "files_processes", "Arquivos, processos e recursos", _subs("sistema de arquivos;processos;threads;memória;CPU;I/O;logs;serviços;permissões de arquivo;recursos")),
    EverydayTechnologyBranch("operating_systems", "users_permissions", "Usuários, contas e permissões", _subs("usuários;grupos;privilégios;permissões;autenticação;elevação;isolamento;sandbox;controle de acesso")),

    EverydayTechnologyBranch("networks_internet", "networks", "Redes de computadores", _subs("redes;LAN;WAN;Wi-Fi;Ethernet;roteadores;switches;endereços;pacotes;latência;conectividade")),
    EverydayTechnologyBranch("networks_internet", "internet", "Internet", _subs("internet;ISP;roteamento;DNS;endereçamento;backbone;peering;serviços;latência;disponibilidade")),
    EverydayTechnologyBranch("networks_internet", "protocols_services", "Protocolos e serviços de rede", _subs("TCP;UDP;IP;HTTP;HTTPS;DNS;DHCP;TLS;API;cliente-servidor;portas")),
    EverydayTechnologyBranch("networks_internet", "web_cloud", "Web, nuvem e serviços online", _subs("web;navegador;servidor;cloud;SaaS;armazenamento remoto;CDN;contas;sincronização;dependência de rede")),

    EverydayTechnologyBranch("digital_security", "cybersecurity_basics", "Fundamentos de segurança digital", _subs("segurança digital;ameaças;vulnerabilidades;malware;phishing;atualizações;backup;criptografia;segurança por camadas")),
    EverydayTechnologyBranch("digital_security", "identity_access", "Identidade, autenticação e acesso", _subs("identidade digital;senha;MFA;token;sessão;privilégio;autorização;controle de acesso;segredos;revogação")),
    EverydayTechnologyBranch("digital_security", "secure_behavior", "Uso seguro e higiene digital", _subs("links;downloads;anexos;permissões;privacidade;atualizações;backup;engenharia social;dispositivos perdidos;recuperação")),

    EverydayTechnologyBranch("energy_infrastructure", "energy", "Energia no cotidiano e tecnologia", _subs("energia;eletricidade;combustíveis;baterias;rede elétrica;consumo;potência;eficiência;armazenamento;risco")),
    EverydayTechnologyBranch("energy_infrastructure", "electrical_infrastructure", "Infraestrutura elétrica", _subs("geração;transmissão;distribuição;subestações;transformadores;quadros;disjuntores;aterramento;continuidade")),
    EverydayTechnologyBranch("energy_infrastructure", "water_sanitation", "Água, saneamento e serviços urbanos", _subs("água;captação;tratamento;distribuição;esgoto;drenagem;resíduos;bombas;reservatórios;continuidade")),
    EverydayTechnologyBranch("energy_infrastructure", "telecom_critical_infrastructure", "Telecomunicações e infraestrutura crítica", _subs("telecomunicações;fibra;torres;data centers;energia de backup;serviços essenciais;redundância;falhas;resiliência")),

    EverydayTechnologyBranch("documents_media", "documents", "Documentos", _subs("documentos;texto;formulários;contratos;manuais;relatórios;metadados;assinaturas;versões;arquivamento")),
    EverydayTechnologyBranch("documents_media", "media", "Mídia e conteúdos", _subs("mídia;imagem;áudio;vídeo;streaming;publicação;edição;compressão;metadados;distribuição")),
    EverydayTechnologyBranch("documents_media", "formats_workflows", "Formatos e fluxos documentais", _subs("PDF;DOCX;planilha;apresentação;OCR;conversão;exportação;revisão;aprovação;preservação")),

    EverydayTechnologyBranch("everyday_objects", "household_objects", "Objetos domésticos", _subs("objetos cotidianos;utensílios;recipientes;móveis;chaves;fechaduras;lâmpadas;tomadas;cabos;armazenamento")),
    EverydayTechnologyBranch("everyday_objects", "personal_objects", "Objetos pessoais", _subs("carteira;chaves;roupas;bolsa;óculos;garrafa;celular;carregador;documentos pessoais;uso")),
    EverydayTechnologyBranch("everyday_objects", "packaging_storage", "Embalagens, recipientes e armazenamento", _subs("embalagens;caixas;frascos;recipientes;vedação;rótulos;armazenamento;transporte;descarte;reutilização")),
)

EVERYDAY_TECH_LENSES = (
    ("concept", "conceito", "definir o objeto, sistema ou prática e seus limites"),
    ("structure", "estrutura e componentes", "identificar partes, interfaces e dependências"),
    ("function", "função", "explicar finalidade, mecanismo funcional e condições necessárias"),
    ("operation", "operação", "descrever estados, entradas, saídas e sequência de funcionamento"),
    ("use", "uso", "relacionar usos legítimos, ergonomia, eficiência e contexto"),
    ("state", "estado", "representar disponível, ativo, inativo, degradado, falho ou desconhecido conforme aplicável"),
    ("risk", "riscos", "identificar perigos, exposição, consequência e mitigação sem conceder autorização operacional"),
    ("failure_maintenance", "falhas e manutenção", "explicar falhas típicas, diagnóstico, prevenção, recuperação e limites"),
    ("context", "contexto", "situar ambiente, pessoa, plataforma, versão, infraestrutura, tempo e dependências"),
    ("relations", "relações", "conectar objetos, sistemas, funções, usos, estados, riscos e sistemas vizinhos"),
)

OBJECT_AXIS = (
    "objeto_manual", "objeto_domestico", "ferramenta", "maquina", "veiculo",
    "computador_dispositivo", "componente", "documento_midia", "infraestrutura", "objeto_generico",
)
SYSTEM_AXIS = (
    "isolado", "domestico", "predial", "urbano", "transporte", "mecanico",
    "eletrico", "computacional", "rede_internet", "infraestrutura_servico",
)
FUNCTION_AXIS = (
    "suportar", "conter_armazenar", "transformar", "transportar", "medir_detectar",
    "controlar", "processar_computar", "comunicar", "proteger", "organizar_informacao",
)
USE_AXIS = (
    "rotina_pessoal", "casa", "cozinha", "trabalho", "educacao",
    "mobilidade", "manutencao", "comunicacao", "computacao", "servico_publico",
)
RISK_AXIS = ("baixo_ou_nao_especificado", "fisico", "eletrico_termico", "digital_informacional", "sistemico_operacional")
STATE_AXIS = ("normal_disponivel", "ativo_em_uso", "degradado_falha", "desconhecido_nao_observado")
CONTEXT_AXIS = (
    "individual", "domestico", "predial", "urbano", "publico", "profissional",
    "educacional", "industrial", "digital_online", "emergencia_contingencia",
)

VARIANT_AXES = (
    ("object", OBJECT_AXIS),
    ("system", SYSTEM_AXIS),
    ("function", FUNCTION_AXIS),
    ("use", USE_AXIS),
    ("risk", RISK_AXIS),
    ("state", STATE_AXIS),
    ("context", CONTEXT_AXIS),
)

REQUESTED_TOPICS = (
    "casas", "edificações", "cidades", "trânsito", "transportes", "navegação",
    "culinária", "rotinas", "ferramentas", "máquinas", "computadores", "hardware",
    "software", "programação", "sistemas operacionais", "redes", "internet",
    "segurança digital", "energia", "infraestrutura", "documentos", "mídia", "objetos cotidianos",
)

REFERENCE_SUBJECTS = {
    "built_environment": "engenharia",
    "cities_mobility": "geografia",
    "navigation_logistics": "geografia",
    "tools_machines": "mecanica",
    "computing_hardware": "computacao",
    "software_programming": "computacao",
    "operating_systems": "computacao",
    "networks_internet": "ti",
    "digital_security": "ti",
    "energy_infrastructure": "engenharia",
}

INTERPRETATION_POLICY = {
    "knowledge_implies_operational_access": False,
    "technical_description_implies_authorization": False,
    "digital_security_knowledge_implies_attack_permission": False,
    "navigation_knowledge_is_live_route_data": False,
    "infrastructure_description_is_live_status": False,
    "software_behavior_is_version_independent": False,
    "hardware_behavior_is_platform_independent": False,
    "cooking_instruction_ignores_food_safety": False,
    "observed_state_is_canonical_fact_by_default": False,
    "unknown_state_may_be_invented": False,
    "risk_requires_context": True,
    "version_platform_context_required_when_relevant": True,
    "live_conditions_require_current_source": True,
    "operational_action_requires_permission_capability_safety": True,
    "rule": "CONHECER UM OBJETO OU SISTEMA NÃO SIGNIFICA POSSUIR ACESSO, CONTROLE, ESTADO AO VIVO OU AUTORIZAÇÃO PARA OPERÁ-LO",
}

CROSS_DOMAIN_RELATIONS = {
    "built_environment": ("cities_mobility", "energy_infrastructure", "everyday_objects"),
    "cities_mobility": ("navigation_logistics", "energy_infrastructure"),
    "navigation_logistics": ("cities_mobility", "computing_hardware", "networks_internet"),
    "food_routines": ("tools_machines", "everyday_objects", "energy_infrastructure"),
    "tools_machines": ("computing_hardware", "energy_infrastructure"),
    "computing_hardware": ("software_programming", "operating_systems", "networks_internet"),
    "software_programming": ("operating_systems", "networks_internet", "documents_media"),
    "operating_systems": ("computing_hardware", "software_programming", "digital_security"),
    "networks_internet": ("digital_security", "documents_media", "energy_infrastructure"),
    "digital_security": ("networks_internet", "operating_systems", "software_programming"),
    "energy_infrastructure": ("built_environment", "cities_mobility", "networks_internet"),
    "documents_media": ("software_programming", "networks_internet"),
    "everyday_objects": ("built_environment", "food_routines", "tools_machines"),
}

CANONICAL_NODES = len(EVERYDAY_TECH_BRANCHES) * len(EVERYDAY_TECH_LENSES)
VARIANTS_PER_NODE = prod(len(values) for _, values in VARIANT_AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE

if len(EVERYDAY_TECH_DOMAINS) != 13:
    raise RuntimeError("B11 requer exatamente 13 domínios")
if len(EVERYDAY_TECH_BRANCHES) != 50:
    raise RuntimeError(f"B11 requer exatamente 50 ramos; encontrados {len(EVERYDAY_TECH_BRANCHES)}")
if len(EVERYDAY_TECH_LENSES) != 10:
    raise RuntimeError("B11 requer exatamente 10 lentes")
if CANONICAL_NODES != 500:
    raise RuntimeError(f"B11 requer 500 nós canônicos; encontrados {CANONICAL_NODES}")
if VARIANTS_PER_NODE != 2_000_000:
    raise RuntimeError(f"B11 requer 2M variações/nó; encontradas {VARIANTS_PER_NODE}")
if ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError(f"B11 requer 1B endereçáveis; encontrados {ADDRESSABLE_CONTENTS}")


def _decode_axes(index: int) -> dict[str, str]:
    if not 0 <= int(index) < VARIANTS_PER_NODE:
        raise IndexError(index)
    remainder = int(index)
    decoded: dict[str, str] = {}
    for name, values in reversed(VARIANT_AXES):
        remainder, offset = divmod(remainder, len(values))
        decoded[name] = values[offset]
    if remainder:
        raise RuntimeError("falha ao decodificar variante B11")
    return {name: decoded[name] for name, _ in VARIANT_AXES}


class EverydayTechnologyCatalog:
    NAMESPACE = "B11"
    PREFIX = "TECH-B11"

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE,
            "domains": len(EVERYDAY_TECH_DOMAINS),
            "branches": len(EVERYDAY_TECH_BRANCHES),
            "lenses_per_branch": len(EVERYDAY_TECH_LENSES),
            "canonical_nodes": CANONICAL_NODES,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_contents": ADDRESSABLE_CONTENTS,
            "variant_axes": {name: len(values) for name, values in VARIANT_AXES},
            "materialization": "on-demand",
            "prepopulated_knowledge_rows": 0,
            "truthfulness_note": (
                "1B são representações determinísticas endereçáveis de objetos, sistemas, funções, usos, riscos, estados e contextos; "
                "não 1B de fatos técnicos independentes, dispositivos, receitas, softwares ou arquivos pré-carregados"
            ),
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        node_index, variant_index = int(node_index), int(variant_index)
        if not 0 <= node_index < CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= variant_index < VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = node_index * VARIANTS_PER_NODE + variant_index + 1
        return f"TECH-B11-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"TECH-B11-(\d{10})", _clean(identifier).upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, VARIANTS_PER_NODE)
        branch_index, lens_index = divmod(node_index, len(EVERYDAY_TECH_LENSES))
        branch = EVERYDAY_TECH_BRANCHES[branch_index]
        lens_key, lens_label, instruction = EVERYDAY_TECH_LENSES[lens_index]
        axes = _decode_axes(variant_index)
        return {
            "id": f"TECH-B11-{absolute:010d}",
            "namespace": self.NAMESPACE,
            "domain": branch.domain,
            "domain_label": DOMAIN_LABELS[branch.domain],
            "branch": branch.key,
            "branch_label": branch.label,
            "subtopics": branch.subtopics,
            "lens": lens_key,
            "lens_label": lens_label,
            **axes,
            "prompt": (
                f"{DOMAIN_LABELS[branch.domain]} / {branch.label} / {lens_label}: {instruction}. "
                f"Objeto={axes['object']}; sistema={axes['system']}; função={axes['function']}; uso={axes['use']}; "
                f"risco={axes['risk']}; estado={axes['state']}; contexto={axes['context']}. "
                "Distinguir conhecimento geral de estado ao vivo; preservar versão/plataforma, segurança, manutenção e incerteza quando relevantes; "
                "conhecimento técnico não concede acesso nem autorização operacional."
            ),
        }


class EverydayTechnologyFoundations:
    NAMESPACE = "B11"
    TAXONOMY_ROOT_ID = "TECH-TAX-ROOT"

    def __init__(
        self,
        knowledge: UniversalKnowledgeArchitecture,
        *,
        physical_world=None,
        scientific_foundations=None,
        human_contexts=None,
        multidisciplinary=None,
    ):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.physical_world = physical_world
        self.scientific_foundations = scientific_foundations
        self.human_contexts = human_contexts
        self.multidisciplinary = multidisciplinary
        self.catalog = EverydayTechnologyCatalog()
        self._providers: dict[str, Any] = {}
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 11 — MUNDO COTIDIANO E TECNOLÓGICO",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/everyday_technology.py",
            metadata={
                "materialization": "on-demand",
                "canonical_gate": "BLOCO 2 -> BLOCO 3",
                "knowledge_graph": "shared",
                "reuse": ["B04", "B05", "B10", "multidisciplinary:engineering/geography/mechanics/computing/it"],
                "parallel_technology_database": False,
                "parallel_technology_graph": False,
                "technical_knowledge_grants_access": False,
            },
        )

    @staticmethod
    def _domain_key(value: str) -> str:
        normalized = _norm(value)
        aliases = {
            "casa": "built_environment", "casas": "built_environment", "edificacao": "built_environment", "edificacoes": "built_environment",
            "cidade": "cities_mobility", "cidades": "cities_mobility", "transito": "cities_mobility",
            "transporte": "navigation_logistics", "transportes": "navigation_logistics", "navegacao": "navigation_logistics", "logistica": "navigation_logistics",
            "culinaria": "food_routines", "cozinha": "food_routines", "rotinas": "food_routines",
            "ferramenta": "tools_machines", "ferramentas": "tools_machines", "maquina": "tools_machines", "maquinas": "tools_machines",
            "computador": "computing_hardware", "computadores": "computing_hardware", "hardware": "computing_hardware",
            "software": "software_programming", "programacao": "software_programming",
            "sistema_operacional": "operating_systems", "sistemas_operacionais": "operating_systems",
            "rede": "networks_internet", "redes": "networks_internet", "internet": "networks_internet",
            "seguranca_digital": "digital_security", "ciberseguranca": "digital_security",
            "energia": "energy_infrastructure", "infraestrutura": "energy_infrastructure",
            "documento": "documents_media", "documentos": "documents_media", "midia": "documents_media",
            "objetos_cotidianos": "everyday_objects", "objeto_cotidiano": "everyday_objects",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _branch(key: str) -> EverydayTechnologyBranch:
        for branch in EVERYDAY_TECH_BRANCHES:
            if branch.key == key:
                return branch
        raise KeyError(key)

    @staticmethod
    def _domain_node_id(domain: str) -> str:
        return f"TECH-DOM-{domain.upper()}"

    @staticmethod
    def _branch_node_id(branch: str) -> str:
        return f"TECH-BR-{branch.upper()}"

    @staticmethod
    def _subtopic_node_id(branch: str, subtopic: str) -> str:
        return f"TECH-SUB-{branch.upper()}-{_norm(subtopic).upper()[:72]}"

    def taxonomy_snapshot(self, domain: str | None = None) -> dict:
        key = self._domain_key(domain) if domain else None
        if key and key not in EVERYDAY_TECH_DOMAINS:
            raise KeyError(domain)
        selected = [branch for branch in EVERYDAY_TECH_BRANCHES if key is None or branch.domain == key]
        return {
            "root": "Mundo Cotidiano e Tecnológico",
            "domain": key,
            "branches": [
                {"domain": branch.domain, "domain_label": DOMAIN_LABELS[branch.domain], "branch": branch.key, "branch_label": branch.label, "subtopics": list(branch.subtopics)}
                for branch in selected
            ],
            "cross_domain_relations": deepcopy(CROSS_DOMAIN_RELATIONS),
            "interpretation_policy": deepcopy(INTERPRETATION_POLICY),
        }

    def _ensure_taxonomy_path(self, branch: EverydayTechnologyBranch, *, include_subtopics: bool = True) -> dict:
        root = self.graph.add_entity(
            "everyday_technology_taxonomy", "Mundo Cotidiano e Tecnológico",
            node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B11", "source_of_truth": "core/everyday_technology.py"},
        )
        for node_id, node_type, label, block in (
            ("SCI-TAX-ROOT", "science_taxonomy", "Ciência", "B05"),
            ("CTX-TAX-ROOT", "human_context_taxonomy", "Contextos Humanos Específicos", "B10"),
        ):
            self.graph.add_entity(node_type, label, node_id=node_id, data={"block": block})
            self.graph.relate(root, node_id, "related_to", metadata={"block": "B11", "reuses": block})
            self.graph.relate(node_id, root, "related_to", metadata={"block": "B11", "everyday_technology": True})

        domain_id = self._domain_node_id(branch.domain)
        self.graph.add_entity("everyday_technology_domain", DOMAIN_LABELS[branch.domain], node_id=domain_id, data={"block": "B11", "domain": branch.domain})
        self.graph.relate(root, domain_id, "has_part", metadata={"block": "B11", "taxonomy": True})
        self.graph.relate(domain_id, root, "part_of", metadata={"block": "B11", "taxonomy": True})

        branch_id = self._branch_node_id(branch.key)
        self.graph.add_entity("everyday_technology_branch", branch.label, node_id=branch_id, data={"block": "B11", "domain": branch.domain, "branch": branch.key})
        self.graph.relate(domain_id, branch_id, "has_part", metadata={"block": "B11", "taxonomy": True})
        self.graph.relate(branch_id, domain_id, "part_of", metadata={"block": "B11", "taxonomy": True})

        sub_ids = []
        if include_subtopics:
            for subtopic in branch.subtopics:
                sub_id = self._subtopic_node_id(branch.key, subtopic)
                self.graph.add_entity("everyday_technology_subtopic", subtopic, node_id=sub_id, data={"block": "B11", "domain": branch.domain, "branch": branch.key})
                self.graph.relate(branch_id, sub_id, "has_part", metadata={"block": "B11", "taxonomy": True})
                self.graph.relate(sub_id, branch_id, "part_of", metadata={"block": "B11", "taxonomy": True})
                sub_ids.append(sub_id)
        return {"root_id": root, "domain_id": domain_id, "branch_id": branch_id, "subtopic_ids": sub_ids}

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        key = self._domain_key(domain) if domain else None
        if key and key not in EVERYDAY_TECH_DOMAINS:
            raise KeyError(domain)
        selected = [branch for branch in EVERYDAY_TECH_BRANCHES if key is None or branch.domain == key]
        paths = [self._ensure_taxonomy_path(branch) for branch in selected]
        return {"domain": key, "branches_materialized": len(paths), "knowledge_graph": "shared", "parallel_technology_graph_created": False, "paths": paths}

    def contextualize_system(
        self,
        description: str,
        *,
        object_name: str = "",
        system: str = "",
        function: str = "",
        use: str = "",
        risk: str = "",
        state: str = "",
        context: str = "",
        platform_version: str = "",
        observations: tuple[str, ...] | list[str] | None = None,
    ) -> dict:
        description = _clean(description)
        if not description:
            raise ValueError("descrição cotidiana/tecnológica vazia")
        dimensions = {
            "object": _clean(object_name), "system": _clean(system), "function": _clean(function),
            "use": _clean(use), "risk": _clean(risk), "state": _clean(state), "context": _clean(context),
        }
        return {
            "description": description,
            **dimensions,
            "platform_version": _clean(platform_version),
            "observations": [_clean(item) for item in (observations or ()) if _clean(item)],
            "epistemic_kind": "inference",
            "certainty": "context_dependent",
            "live_state_claim": False,
            "operational_access": False,
            "operational_authorization": False,
            "unknown_state_invented": False,
            "context_checks": [
                "identificar objeto/sistema e separar função projetada de comportamento realmente observado",
                "distinguir uso possível de uso seguro, permitido ou recomendado",
                "preservar estado desconhecido quando não houver telemetria ou observação atual",
                "considerar risco físico, elétrico, térmico, digital, informacional e sistêmico conforme o caso",
                "preservar plataforma, versão, configuração e dependências quando alterarem o comportamento",
                "para trânsito, navegação e infraestrutura, exigir fonte atual para condições ao vivo",
                "para culinária, considerar higiene, temperatura, conservação, alergênicos e contaminação cruzada quando relevantes",
                "para segurança digital, conhecimento técnico não autoriza acesso, ataque, alteração ou persistência em sistemas",
                "separar conhecimento e previsão de autorização operacional",
            ],
            "missing_dimensions": [key for key, value in dimensions.items() if not value],
            "policy": deepcopy(INTERPRETATION_POLICY),
        }

    def reference(self, query: str, *, domain: str | None = None) -> dict | None:
        query = _clean(query)
        if not query:
            return None
        domain_key = self._domain_key(domain) if domain else None
        subject = REFERENCE_SUBJECTS.get(domain_key) if domain_key else None
        if not subject:
            return None
        if self.multidisciplinary is not None:
            engine = self.multidisciplinary
        else:
            if "multidisciplinary" not in self._providers:
                from core.multidisciplinary_knowledge import MultidisciplinaryKnowledgeEngine
                self._providers["multidisciplinary"] = MultidisciplinaryKnowledgeEngine()
            engine = self._providers["multidisciplinary"]
        answer = engine.answer(f"{subject} {query}")
        if not answer:
            return None
        return {
            "provider": "core.multidisciplinary_knowledge",
            "subject_hint": subject,
            "answer": answer,
            "block": "B11",
            "canonicalized": False,
            "note": "referência local reutilizada; conhecimento de provedor não vira canônico automaticamente",
        }

    def promote_canonical_technology_knowledge(
        self,
        record_id: str,
        canonical_label: str,
        *,
        domain: str,
        branch: str,
        knowledge_type: str = "concept",
        aliases=None,
        properties=None,
        subtopics=None,
        contexts=None,
        rules=None,
        exceptions=None,
        summary: str = "",
    ) -> dict:
        domain_key = self._domain_key(domain)
        if domain_key not in EVERYDAY_TECH_DOMAINS:
            raise ValueError(f"domínio B11 inválido: {domain}")
        branch_obj = self._branch(branch)
        if branch_obj.domain != domain_key:
            raise ValueError(f"ramo {branch} não pertence a {domain_key}")
        props = dict(properties or {})
        props.update({
            "knowledge_implies_operational_access": False,
            "technical_description_implies_authorization": False,
            "live_state_requires_current_observation": True,
            "version_platform_context_required_when_relevant": True,
            "knowledge_scope": "everyday_and_technology",
        })
        result = self.knowledge.promote_canonical(
            record_id,
            canonical_label,
            knowledge_type=knowledge_type,
            namespace=self.NAMESPACE,
            summary=summary,
            aliases=aliases,
            properties=props,
            categories=["everyday_technology", domain_key, branch_obj.key],
            subtopics=subtopics,
            contexts=contexts,
            rules=rules,
            exceptions=exceptions,
            provenance={"everyday_technology_block": "B11", "domain": domain_key, "branch": branch_obj.key, "source_record_id": record_id},
        )
        taxonomy = self._ensure_taxonomy_path(branch_obj, include_subtopics=False)
        self.graph.relate(result["knowledge_id"], taxonomy["branch_id"], "is_a", metadata={"block": "B11", "technology_taxonomy": True})
        self.graph.relate(taxonomy["branch_id"], result["knowledge_id"], "has_part", metadata={"block": "B11", "technology_taxonomy": True})
        return result

    def relate(self, source_id: str, target_id: str, relation: str, *, weight: float = 1.0) -> dict:
        return self.knowledge.relate(source_id, target_id, relation, weight=weight, metadata={"block": "B11", "everyday_technology": True})

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "domains": [{"key": key, "label": DOMAIN_LABELS[key]} for key in EVERYDAY_TECH_DOMAINS],
            "requested_topics": list(REQUESTED_TOPICS),
            "reference_subjects": deepcopy(REFERENCE_SUBJECTS),
            "reuse": {
                "physical_world": "B04 reused, not duplicated",
                "scientific_foundations": "B05 reused, not duplicated",
                "human_contexts": "B10 reused, not duplicated",
                "multidisciplinary": "engineering/geography/mechanics/computing/it reused lazily",
            },
            "knowledge_graph": "shared knowledge_nodes/knowledge_edges",
            "canonical_knowledge": "BLOCO 2 gate -> BLOCO 3 -> B11",
            "parallel_technology_database": False,
            "parallel_technology_graph": False,
            "interpretation_policy": deepcopy(INTERPRETATION_POLICY),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None
        if low in {"status bloco 11", "status mundo cotidiano", "status mundo tecnologico", "status mundo tecnológico", "bloco 11 tecnologia"}:
            stats = self.catalog.stats()
            return (
                f"🛠️ BLOCO 11 — MUNDO COTIDIANO E TECNOLÓGICO: {stats['addressable_contents']} conteúdos endereçáveis em B11 | "
                f"{stats['domains']} domínios × {stats['branches']} ramos × {stats['lenses_per_branch']} lentes = {stats['canonical_nodes']} nós | "
                f"{stats['variants_per_node']} variações/nó | Knowledge Graph=COMPARTILHADO."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"🛠️ {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        taxonomy = re.match(r"^(?:taxonomia tecnologia|taxonomia mundo cotidiano)(?:\s+(.+))?$", raw, re.I)
        if taxonomy:
            snapshot = self.taxonomy_snapshot(taxonomy.group(1))
            labels = ", ".join(item["branch_label"] for item in snapshot["branches"][:12])
            return f"🛠️ Taxonomia B11: {len(snapshot['branches'])} ramos. {labels}{'…' if len(snapshot['branches']) > 12 else ''}"
        if low in {"limites bloco 11", "limites tecnologia star", "conhecimento tecnico da acesso", "conhecimento técnico dá acesso"}:
            return "🛡️ Conhecimento técnico não significa acesso, controle, estado ao vivo ou autorização operacional. A STAR mantém capacidade, permissão, segurança e evidência atual como gates separados."
        return None
