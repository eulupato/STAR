"""BLOCO 9 — Sociedade e Cultura da STAR.

Integra conhecimento social e cultural geral sobre o BLOCO 2, BLOCO 3 e o mesmo
Knowledge Graph. Reutiliza as bases multidisciplinares locais de História,
Geografia, Psicologia/Sociologia e Filosofia sem criar um segundo catálogo para
essas matérias.

Escala: 50 ramos × 20 lentes = 1.000 nós; 1.000.000 variações/nó = 1B
endereçáveis em B09, materializados sob demanda.
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
class SocietyCultureBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in raw.split(";") if x.strip())


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def _clean(text: str) -> str:
    return " ".join(str(text or "").strip().split())


SOCIETY_CULTURE_DOMAINS = (
    "anthropology_culture",
    "sociology_society",
    "history_temporality",
    "geography_regions",
    "politics_governance",
    "economics_money_property",
    "law_institutions",
    "ethics_philosophy",
    "religion_mythology",
    "arts_literature_media",
    "education_work_organizations",
    "relations_family_friendship",
    "stratification_institutions_change",
)

DOMAIN_LABELS = {
    "anthropology_culture": "Antropologia e cultura",
    "sociology_society": "Sociologia e sociedade",
    "history_temporality": "História, memória e temporalidade",
    "geography_regions": "Geografia, regiões e território",
    "politics_governance": "Política, poder e governança",
    "economics_money_property": "Economia, dinheiro e propriedade",
    "law_institutions": "Direito, normas e instituições",
    "ethics_philosophy": "Ética e filosofia social",
    "religion_mythology": "Religião, mitologia e cosmologias",
    "arts_literature_media": "Arte, literatura e mídia",
    "education_work_organizations": "Educação, trabalho e organizações",
    "relations_family_friendship": "Relações, família e amizade",
    "stratification_institutions_change": "Classes, desigualdade e mudança institucional",
}

SOCIETY_CULTURE_BRANCHES = (
    SocietyCultureBranch("anthropology_culture", "cultural_anthropology", "Antropologia cultural", _subs("cultura;significados;práticas;valores;normas;etnografia;comparação cultural")),
    SocietyCultureBranch("anthropology_culture", "social_anthropology", "Antropologia social", _subs("parentesco;organização social;reciprocidade;status;rituais;instituições")),
    SocietyCultureBranch("anthropology_culture", "material_culture", "Cultura material e tecnologia", _subs("objetos;tecnologia;habitação;vestuário;alimentação;produção;consumo")),
    SocietyCultureBranch("anthropology_culture", "ritual_custom_tradition", "Rituais, costumes e tradições", _subs("tradições;costumes;rituais;festas;passagens;memória coletiva;mudança cultural")),

    SocietyCultureBranch("sociology_society", "social_structure", "Estrutura social", _subs("sociedade;papéis;status;normas;redes;ordem social;mudança")),
    SocietyCultureBranch("sociology_society", "institutions_society", "Instituições sociais", _subs("instituições;estado;mercado;família;religião;educação;organizações")),
    SocietyCultureBranch("sociology_society", "socialization_identity", "Socialização e identidade", _subs("socialização;identidade;grupo;pertencimento;normas;agência")),
    SocietyCultureBranch("sociology_society", "collective_action_movements", "Ação coletiva e movimentos sociais", _subs("movimentos sociais;protesto;mobilização;associações;redes;mudança social")),

    SocietyCultureBranch("history_temporality", "historical_periods", "Períodos e processos históricos", _subs("pré-história;antiguidade;medievo;modernidade;contemporaneidade;periodização")),
    SocietyCultureBranch("history_temporality", "historical_change", "Mudança histórica e causalidade", _subs("continuidade;ruptura;causalidade;processos;eventos;longa duração")),
    SocietyCultureBranch("history_temporality", "historiography_memory", "Historiografia, memória e fontes", _subs("fontes;arquivos;arqueologia;memória;historiografia;narrativas;silêncios")),
    SocietyCultureBranch("history_temporality", "global_connected_history", "História global e conectada", _subs("rotas;impérios;diásporas;colonização;trocas;circulação;conexões")),

    SocietyCultureBranch("geography_regions", "human_geography", "Geografia humana", _subs("território;lugar;paisagem;população;redes;mobilidade;urbanização")),
    SocietyCultureBranch("geography_regions", "political_geography", "Geografia política e fronteiras", _subs("fronteiras;território;estado;soberania;geopolítica;escalas")),
    SocietyCultureBranch("geography_regions", "economic_geography", "Geografia econômica", _subs("produção;comércio;cadeias;recursos;desigualdade espacial;infraestrutura")),
    SocietyCultureBranch("geography_regions", "regional_cultural_geography", "Regiões e paisagens culturais", _subs("regiões;paisagens;cultura;patrimônio;identidade territorial;difusão")),

    SocietyCultureBranch("politics_governance", "political_systems", "Sistemas políticos e relações internacionais", _subs("democracia;monarquia;república;autoritarismo;federalismo;diplomacia;cooperação;conflito")),
    SocietyCultureBranch("politics_governance", "state_government", "Estado, governo e administração", _subs("estado;governo;burocracia;administração;poder público;capacidade estatal")),
    SocietyCultureBranch("politics_governance", "power_legitimacy", "Poder, autoridade e legitimidade", _subs("poder;autoridade;legitimidade;dominação;representação;participação")),
    SocietyCultureBranch("politics_governance", "public_policy_citizenship", "Políticas públicas e cidadania", _subs("cidadania;direitos;políticas públicas;participação;serviços;instituições")),

    SocietyCultureBranch("economics_money_property", "economic_systems", "Sistemas econômicos", _subs("mercado;planejamento;economias mistas;produção;distribuição;instituições econômicas")),
    SocietyCultureBranch("economics_money_property", "money_finance", "Dinheiro, moeda e finanças", _subs("dinheiro;moeda;crédito;bancos;preços;inflação;finanças")),
    SocietyCultureBranch("economics_money_property", "property_resources", "Propriedade, recursos e bens comuns", _subs("propriedade;posse;bens comuns;terra;recursos;herança;uso")),
    SocietyCultureBranch("economics_money_property", "labor_economy", "Trabalho, produção e renda", _subs("trabalho;salários;ocupações;produção;renda;desemprego;relações trabalhistas")),

    SocietyCultureBranch("law_institutions", "legal_systems", "Sistemas jurídicos", _subs("direito;sistemas jurídicos;common law;civil law;direito costumeiro;pluralismo jurídico")),
    SocietyCultureBranch("law_institutions", "rights_duties", "Direitos, deveres e cidadania jurídica", _subs("direitos;deveres;cidadania;liberdades;responsabilidade;garantias")),
    SocietyCultureBranch("law_institutions", "courts_procedure", "Instituições jurídicas e procedimentos", _subs("tribunais;procedimentos;provas;precedentes;administração da justiça")),
    SocietyCultureBranch("law_institutions", "norms_customary_law", "Normas, costumes e direito costumeiro", _subs("normas;costumes;direito costumeiro;pluralismo;autoridade;conflitos normativos")),

    SocietyCultureBranch("ethics_philosophy", "ethics_morality", "Ética e moral", _subs("ética;moral;valores;dever;virtude;consequências;responsabilidade")),
    SocietyCultureBranch("ethics_philosophy", "political_philosophy", "Filosofia política e justiça", _subs("justiça;liberdade;igualdade;autoridade;direitos;bem comum")),
    SocietyCultureBranch("ethics_philosophy", "social_philosophy", "Filosofia social", _subs("sociedade;indivíduo;comunidade;alienação;reconhecimento;instituições")),
    SocietyCultureBranch("ethics_philosophy", "knowledge_worldviews", "Filosofia, conhecimento e visões de mundo", _subs("epistemologia;metafísica;razão;experiência;visões de mundo;argumentação")),

    SocietyCultureBranch("religion_mythology", "religious_traditions", "Religiões e tradições religiosas", _subs("religião;tradições;doutrinas;rituais;instituições;textos;comunidades")),
    SocietyCultureBranch("religion_mythology", "religion_society", "Religião e sociedade", _subs("religião;sociedade;política;família;educação;identidade;secularização")),
    SocietyCultureBranch("religion_mythology", "mythology_cosmology", "Mitologia e cosmologias", _subs("mitologia;cosmologia;deuses;heróis;origens;símbolos;narrativas")),
    SocietyCultureBranch("religion_mythology", "ritual_belief_practice", "Crenças, rituais e práticas", _subs("crenças;rituais;orações;festas;tabus;lugares sagrados;experiência religiosa")),

    SocietyCultureBranch("arts_literature_media", "visual_performing_arts", "Artes visuais e performáticas", _subs("arte;pintura;escultura;arquitetura;música;teatro;dança;performance")),
    SocietyCultureBranch("arts_literature_media", "literature_storytelling", "Literatura e tradição narrativa", _subs("literatura;poesia;romance;conto;oralidade;gêneros;cânones")),
    SocietyCultureBranch("arts_literature_media", "media_communication", "Mídia e comunicação social", _subs("mídia;imprensa;rádio;televisão;cinema;internet;plataformas")),
    SocietyCultureBranch("arts_literature_media", "popular_culture", "Cultura popular e indústrias culturais", _subs("cultura popular;entretenimento;celebridades;fandom;indústrias culturais;memes")),

    SocietyCultureBranch("education_work_organizations", "education_systems", "Educação e sistemas educacionais", _subs("educação;escolas;universidades;currículos;alfabetização;credenciais")),
    SocietyCultureBranch("education_work_organizations", "work_occupations", "Trabalho e ocupações", _subs("trabalho;profissões;ofícios;carreiras;divisão do trabalho;identidade ocupacional")),
    SocietyCultureBranch("education_work_organizations", "organizations_bureaucracy", "Organizações e burocracias", _subs("organizações;burocracia;hierarquia;gestão;coordenação;cultura organizacional")),
    SocietyCultureBranch("education_work_organizations", "markets_professions", "Mercados profissionais e instituições do trabalho", _subs("mercado de trabalho;profissões;sindicatos;empresas;setores;regulação")),

    SocietyCultureBranch("relations_family_friendship", "family_kinship", "Família e parentesco", _subs("família;parentesco;casamento;descendência;domicílio;cuidado;herança")),
    SocietyCultureBranch("relations_family_friendship", "friendship_relations", "Amizade e relações sociais", _subs("amizade;confiança;reciprocidade;redes;apoio;conflito;intimidade")),
    SocietyCultureBranch("relations_family_friendship", "community_association", "Comunidade e associações", _subs("comunidade;vizinhança;associações;clubes;redes locais;solidariedade")),

    SocietyCultureBranch("stratification_institutions_change", "class_stratification", "Classes e estratificação", _subs("classes;status;riqueza;renda;mobilidade;desigualdade;hierarquias")),
    SocietyCultureBranch("stratification_institutions_change", "inequality_power", "Desigualdade e relações de poder", _subs("desigualdade;poder;privilégio;exclusão;dominação;acesso;mobilidade")),
    SocietyCultureBranch("stratification_institutions_change", "institutional_change", "Mudança institucional e transformação social", _subs("instituições;reformas;revoluções;modernização;globalização;mudança social")),
)

SOCIETY_CULTURE_LENSES = (
    ("concept", "conceito", "definir o conceito sem tratá-lo como universal fora de contexto"),
    ("origins_history", "origens e história", "situar origens, continuidades, rupturas e controvérsias históricas"),
    ("structure", "estrutura", "descrever componentes, posições e relações estruturais"),
    ("actors_agency", "atores e agência", "distinguir atores, escolhas, restrições e capacidades de ação"),
    ("institutions", "instituições", "examinar regras formais, informais e organizações relevantes"),
    ("norms_values", "normas e valores", "contextualizar valores, normas, sanções e legitimidade"),
    ("practices_customs", "práticas e costumes", "descrever práticas, rotinas, rituais, tradições e variações"),
    ("material_culture", "cultura material", "relacionar objetos, tecnologia, ambiente construído e vida material"),
    ("economy_resources", "economia e recursos", "examinar produção, distribuição, dinheiro, propriedade e recursos"),
    ("power_governance", "poder e governança", "examinar autoridade, poder, participação e governança sem endossar posição política"),
    ("law_rules", "direito e regras", "distinguir sistemas jurídicos, jurisdição, época, normas e aplicação"),
    ("relations_networks", "relações e redes", "examinar parentesco, amizade, cooperação, conflito, troca e redes"),
    ("geography_region", "geografia e região", "situar território, escalas, mobilidade e diversidade regional"),
    ("time_change", "tempo e mudança", "examinar transformação, persistência, difusão e mudança social"),
    ("comparison", "comparação", "comparar sociedades e sistemas sem usar uma cultura como padrão universal"),
    ("evidence_sources", "evidências e fontes", "distinguir fontes, evidência, lacunas, autoria e confiabilidade"),
    ("perspectives_debates", "perspectivas e debates", "apresentar interpretações concorrentes e pontos de disputa"),
    ("inequality_classes", "classes e desigualdades", "examinar hierarquias, classes, acesso, mobilidade e distribuição"),
    ("impacts_experience", "impactos e experiência", "relacionar instituições e estruturas a experiências sociais diversas"),
    ("limits_context", "limites e contexto", "declarar limites, anacronismos, generalizações e contexto ausente"),
)

REQUESTED_TOPICS = (
    "antropologia", "sociologia", "história", "geografia", "política", "economia", "direito",
    "ética", "filosofia", "religião", "mitologia", "arte", "literatura", "mídia", "educação",
    "trabalho", "organizações", "dinheiro", "propriedade", "tradições", "costumes", "relações",
    "família", "amizade", "sociedade", "classes", "instituições",
)

SOCIETY_VARIANTS = (
    "local_community", "city_state", "kingdom_empire", "nation_state", "diaspora_network",
    "indigenous_society", "agrarian_society", "industrial_society", "postindustrial_society", "comparative_multi_society",
)
ERA_VARIANTS = (
    "prehistory", "ancient", "late_antiquity", "medieval", "early_modern",
    "industrial_19th", "early_20th", "postwar_20th", "contemporary", "longue_duree_comparative",
)
REGION_VARIANTS = (
    "africa", "east_asia", "south_southeast_asia", "europe", "middle_east_north_africa",
    "north_america", "latin_america_caribbean", "oceania_pacific", "arctic_circumpolar", "global_transregional",
)
SYSTEM_VARIANTS = (
    "kinship", "political", "economic", "legal", "religious",
    "educational", "labor_organizational", "class_stratification", "media_symbolic", "mixed_institutional",
)
RELATION_VARIANTS = (
    "cooperation", "conflict", "exchange", "authority", "kinship",
    "friendship", "competition", "solidarity", "dependency", "negotiation",
)
PERSPECTIVE_VARIANTS = (
    "emic", "etic", "historical", "comparative", "institutional",
    "material", "symbolic", "economic", "legal_normative", "critical_multi_perspective",
)

VARIANT_AXES = (
    ("society", SOCIETY_VARIANTS),
    ("era", ERA_VARIANTS),
    ("region", REGION_VARIANTS),
    ("system", SYSTEM_VARIANTS),
    ("relation", RELATION_VARIANTS),
    ("perspective", PERSPECTIVE_VARIANTS),
)

INTERPRETATION_POLICY = {
    "culture_is_fixed_or_homogeneous": False,
    "group_membership_determines_individual_trait": False,
    "single_source_proves_social_claim": False,
    "present_values_are_universal_historical_standard": False,
    "political_description_implies_endorsement": False,
    "religious_belief_is_empirical_fact_by_default": False,
    "mythology_is_ranked_against_religion": False,
    "law_is_timeless_or_jurisdiction_free": False,
    "contested_claims_require_multiple_perspectives": True,
    "historical_and_regional_context_required": True,
    "alternative_interpretations_required": True,
    "rule": "SOCIEDADE OU CULTURA ≠ ESSÊNCIA FIXA; CONTEXTO, ÉPOCA, REGIÃO, FONTES E PERSPECTIVAS DEVEM SER PRESERVADOS",
}

CROSS_DOMAIN_RELATIONS = (
    ("anthropology_culture", "sociology_society", "related_to"),
    ("history_temporality", "geography_regions", "related_to"),
    ("politics_governance", "law_institutions", "related_to"),
    ("economics_money_property", "stratification_institutions_change", "related_to"),
    ("religion_mythology", "arts_literature_media", "related_to"),
    ("education_work_organizations", "relations_family_friendship", "related_to"),
    ("ethics_philosophy", "politics_governance", "contextualizes"),
)

REFERENCE_SUBJECTS = {
    "geography_regions": "geography",
    "history_temporality": "history",
    "sociology_society": "psychology_sociology",
    "relations_family_friendship": "psychology_sociology",
    "stratification_institutions_change": "psychology_sociology",
    "education_work_organizations": "psychology_sociology",
    "ethics_philosophy": "philosophy",
}

CANONICAL_NODES = len(SOCIETY_CULTURE_BRANCHES) * len(SOCIETY_CULTURE_LENSES)
VARIANTS_PER_NODE = prod(len(values) for _, values in VARIANT_AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE

if len(SOCIETY_CULTURE_DOMAINS) != 13:
    raise ValueError("B09 exige 13 domínios")
if len(SOCIETY_CULTURE_BRANCHES) != 50:
    raise ValueError(f"B09 exige 50 ramos; encontrados {len(SOCIETY_CULTURE_BRANCHES)}")
if len(SOCIETY_CULTURE_LENSES) != 20:
    raise ValueError("B09 exige 20 lentes")
if CANONICAL_NODES != 1_000 or VARIANTS_PER_NODE != 1_000_000 or ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise ValueError("escala B09 inválida")


def _decode_axes(index: int) -> dict[str, str]:
    if not 0 <= int(index) < VARIANTS_PER_NODE:
        raise IndexError(index)
    remainder = int(index)
    decoded: dict[str, str] = {}
    for name, values in reversed(VARIANT_AXES):
        remainder, offset = divmod(remainder, len(values))
        decoded[name] = values[offset]
    if remainder:
        raise RuntimeError("falha ao decodificar variante B09")
    return {name: decoded[name] for name, _ in VARIANT_AXES}


class SocietyCultureCatalog:
    NAMESPACE = "B09"
    PREFIX = "SOC-B09"

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE,
            "domains": len(SOCIETY_CULTURE_DOMAINS),
            "branches": len(SOCIETY_CULTURE_BRANCHES),
            "lenses_per_branch": len(SOCIETY_CULTURE_LENSES),
            "canonical_nodes": CANONICAL_NODES,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_contents": ADDRESSABLE_CONTENTS,
            "variant_axes": {name: len(values) for name, values in VARIANT_AXES},
            "materialization": "on-demand",
            "prepopulated_knowledge_rows": 0,
            "truthfulness_note": (
                "1B são representações sociais/culturais determinísticas endereçáveis através de sociedade, época, região, sistema, relação e perspectiva; "
                "não 1B de fatos independentes sobre grupos humanos pré-carregados"
            ),
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        node_index = int(node_index)
        variant_index = int(variant_index)
        if not 0 <= node_index < CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= variant_index < VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = node_index * VARIANTS_PER_NODE + variant_index + 1
        return f"SOC-B09-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"SOC-B09-(\d{10})", str(identifier or "").strip().upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, VARIANTS_PER_NODE)
        branch_index, lens_index = divmod(node_index, len(SOCIETY_CULTURE_LENSES))
        branch = SOCIETY_CULTURE_BRANCHES[branch_index]
        lens_key, lens_label, instruction = SOCIETY_CULTURE_LENSES[lens_index]
        axes = _decode_axes(variant_index)
        return {
            "id": f"SOC-B09-{absolute:010d}",
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
                f"Sociedade={axes['society']}; época={axes['era']}; região={axes['region']}; sistema={axes['system']}; "
                f"relação={axes['relation']}; perspectiva={axes['perspective']}. "
                "Preservar contexto histórico/regional, fontes, diversidade interna e perspectivas concorrentes; "
                "não transformar grupos, culturas ou instituições em essências fixas."
            ),
        }


class SocietyCultureFoundations:
    NAMESPACE = "B09"
    TAXONOMY_ROOT_ID = "SOC-TAX-ROOT"

    def __init__(self, knowledge: UniversalKnowledgeArchitecture, *, human_psychology=None, language_communication=None, multidisciplinary=None):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.human_psychology = human_psychology
        self.language_communication = language_communication
        self.multidisciplinary = multidisciplinary
        self.catalog = SocietyCultureCatalog()
        self._providers: dict[str, Any] = {}
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 9 — SOCIEDADE E CULTURA",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/society_culture.py",
            metadata={
                "materialization": "on-demand",
                "canonical_gate": "BLOCO 2 -> BLOCO 3",
                "knowledge_graph": "shared",
                "multidisciplinary_references": list(sorted(set(REFERENCE_SUBJECTS.values()))),
                "parallel_social_database": False,
                "parallel_social_graph": False,
                "essentialist_group_inference": False,
                "political_endorsement": False,
            },
        )

    @staticmethod
    def _domain_key(value: str) -> str:
        normalized = _norm(value)
        aliases = {
            "antropologia": "anthropology_culture", "cultura": "anthropology_culture", "costumes": "anthropology_culture", "tradicoes": "anthropology_culture",
            "sociologia": "sociology_society", "sociedade": "sociology_society",
            "historia": "history_temporality", "memoria": "history_temporality",
            "geografia": "geography_regions", "regioes": "geography_regions", "territorio": "geography_regions",
            "politica": "politics_governance", "governo": "politics_governance", "governanca": "politics_governance",
            "economia": "economics_money_property", "dinheiro": "economics_money_property", "propriedade": "economics_money_property",
            "direito": "law_institutions", "juridico": "law_institutions", "juridica": "law_institutions",
            "etica": "ethics_philosophy", "filosofia": "ethics_philosophy",
            "religiao": "religion_mythology", "mitologia": "religion_mythology",
            "arte": "arts_literature_media", "literatura": "arts_literature_media", "midia": "arts_literature_media",
            "educacao": "education_work_organizations", "trabalho": "education_work_organizations", "organizacoes": "education_work_organizations",
            "relacoes": "relations_family_friendship", "familia": "relations_family_friendship", "amizade": "relations_family_friendship",
            "classes": "stratification_institutions_change", "instituicoes": "stratification_institutions_change", "desigualdade": "stratification_institutions_change",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _branch(key: str) -> SocietyCultureBranch:
        for branch in SOCIETY_CULTURE_BRANCHES:
            if branch.key == key:
                return branch
        raise KeyError(key)

    @staticmethod
    def _domain_node_id(domain: str) -> str:
        return f"SOC-DOM-{domain.upper()}"

    @staticmethod
    def _branch_node_id(branch: str) -> str:
        return f"SOC-BR-{branch.upper()}"

    @staticmethod
    def _subtopic_node_id(branch: str, subtopic: str) -> str:
        return f"SOC-SUB-{branch.upper()}-{_norm(subtopic).upper()[:80]}"

    def taxonomy_snapshot(self, domain: str | None = None) -> dict:
        key = self._domain_key(domain) if domain else None
        if key and key not in SOCIETY_CULTURE_DOMAINS:
            raise KeyError(domain)
        selected = [branch for branch in SOCIETY_CULTURE_BRANCHES if key is None or branch.domain == key]
        return {
            "root": "Sociedade e Cultura",
            "domain": key,
            "branches": [
                {"domain": branch.domain, "domain_label": DOMAIN_LABELS[branch.domain], "branch": branch.key, "branch_label": branch.label, "subtopics": list(branch.subtopics)}
                for branch in selected
            ],
            "cross_domain_relations": deepcopy(CROSS_DOMAIN_RELATIONS),
            "interpretation_policy": deepcopy(INTERPRETATION_POLICY),
        }

    def _ensure_taxonomy_path(self, branch: SocietyCultureBranch, *, include_subtopics: bool = True) -> dict:
        root = self.graph.add_entity(
            "society_culture_taxonomy",
            "Sociedade e Cultura",
            node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B09", "source_of_truth": "core/society_culture.py"},
        )
        psychology_root = "PSY-TAX-ROOT"
        language_root = "LANG-TAX-ROOT"
        self.graph.add_entity("human_psychology_taxonomy", "Mente Humana e Psicologia", node_id=psychology_root, data={"block": "B07"})
        self.graph.add_entity("language_communication_taxonomy", "Linguagem e Comunicação", node_id=language_root, data={"block": "B08"})
        self.graph.relate(root, psychology_root, "related_to", metadata={"block": "B09", "social_psychology_context": True})
        self.graph.relate(root, language_root, "related_to", metadata={"block": "B09", "culture_language_context": True})
        self.graph.relate(psychology_root, root, "related_to", metadata={"block": "B09", "society_context": True})
        self.graph.relate(language_root, root, "related_to", metadata={"block": "B09", "culture_context": True})

        domain_id = self._domain_node_id(branch.domain)
        self.graph.add_entity("society_culture_domain", DOMAIN_LABELS[branch.domain], node_id=domain_id, data={"block": "B09", "domain": branch.domain})
        self.graph.relate(root, domain_id, "has_part", metadata={"block": "B09", "taxonomy": True})
        self.graph.relate(domain_id, root, "part_of", metadata={"block": "B09", "taxonomy": True})

        branch_id = self._branch_node_id(branch.key)
        self.graph.add_entity("society_culture_branch", branch.label, node_id=branch_id, data={"block": "B09", "domain": branch.domain, "branch": branch.key})
        self.graph.relate(domain_id, branch_id, "has_part", metadata={"block": "B09", "taxonomy": True})
        self.graph.relate(branch_id, domain_id, "part_of", metadata={"block": "B09", "taxonomy": True})

        sub_ids = []
        if include_subtopics:
            for subtopic in branch.subtopics:
                sub_id = self._subtopic_node_id(branch.key, subtopic)
                self.graph.add_entity("society_culture_subtopic", subtopic, node_id=sub_id, data={"block": "B09", "domain": branch.domain, "branch": branch.key})
                self.graph.relate(branch_id, sub_id, "has_part", metadata={"block": "B09", "taxonomy": True})
                self.graph.relate(sub_id, branch_id, "part_of", metadata={"block": "B09", "taxonomy": True})
                sub_ids.append(sub_id)
        return {"root_id": root, "domain_id": domain_id, "branch_id": branch_id, "subtopic_ids": sub_ids}

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        key = self._domain_key(domain) if domain else None
        if key and key not in SOCIETY_CULTURE_DOMAINS:
            raise KeyError(domain)
        selected = [branch for branch in SOCIETY_CULTURE_BRANCHES if key is None or branch.domain == key]
        paths = [self._ensure_taxonomy_path(branch) for branch in selected]
        return {"domain": key, "branches_materialized": len(paths), "knowledge_graph": "shared", "parallel_social_graph_created": False, "paths": paths}

    def contextualize_social_statement(
        self,
        statement: str,
        *,
        society: str = "",
        era: str = "",
        region: str = "",
        system: str = "",
        perspective: str = "",
        sources: tuple[str, ...] | list[str] | None = None,
    ) -> dict:
        statement = _clean(statement)
        if not statement:
            raise ValueError("afirmação social/cultural vazia")
        evidence = [_clean(item) for item in (sources or ()) if _clean(item)]
        return {
            "statement": statement,
            "society": _clean(society),
            "era": _clean(era),
            "region": _clean(region),
            "system": _clean(system),
            "perspective": _clean(perspective),
            "sources": evidence,
            "epistemic_kind": "inference",
            "certainty": "context_dependent",
            "universal_claim": False,
            "group_membership_determines_individual_trait": False,
            "political_endorsement": False,
            "alternative_interpretations_required": True,
            "context_checks": [
                "definir sociedade/grupo e evitar tratar fronteiras sociais como fixas",
                "situar época e evitar anacronismo",
                "situar região e escala geográfica",
                "distinguir norma declarada de prática observada",
                "distinguir instituições formais de regras informais",
                "examinar diversidade interna e exceções",
                "comparar fontes, autoria, interesses e silêncios documentais",
                "separar descrição empírica de julgamento normativo ou preferência política",
            ],
            "missing_context": [
                key for key, value in (("society", society), ("era", era), ("region", region), ("system", system), ("perspective", perspective)) if not _clean(value)
            ],
            "policy": deepcopy(INTERPRETATION_POLICY),
        }

    def reference(self, query: str, *, domain: str | None = None) -> dict | None:
        query = _clean(query)
        if not query:
            return None
        key = self._domain_key(domain) if domain else None
        subject = REFERENCE_SUBJECTS.get(key) if key else None
        if self.multidisciplinary is None:
            if "multidisciplinary" not in self._providers:
                from core.multidisciplinary_knowledge import MultidisciplinaryKnowledgeEngine
                self._providers["multidisciplinary"] = MultidisciplinaryKnowledgeEngine()
            engine = self._providers["multidisciplinary"]
        else:
            engine = self.multidisciplinary
        prompt = f"{subject} {query}" if subject else query
        answer = engine.answer(prompt)
        if not answer:
            return None
        return {
            "provider": "core.multidisciplinary_knowledge",
            "subject_hint": subject,
            "answer": answer,
            "block": "B09",
            "canonicalized": False,
            "note": "referência local reutilizada; resposta de provedor não vira conhecimento canônico automaticamente",
        }

    def promote_canonical_social_knowledge(
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
        if domain_key not in SOCIETY_CULTURE_DOMAINS:
            raise ValueError(f"domínio B09 inválido: {domain}")
        branch_obj = self._branch(branch)
        if branch_obj.domain != domain_key:
            raise ValueError(f"ramo {branch} não pertence a {domain_key}")
        props = dict(properties or {})
        props.update({
            "culture_fixed_or_homogeneous": False,
            "group_trait_determinism": False,
            "political_endorsement": False,
            "jurisdiction_and_time_context_required_for_law": True,
            "knowledge_scope": "society_and_culture",
        })
        result = self.knowledge.promote_canonical(
            record_id,
            canonical_label,
            knowledge_type=knowledge_type,
            namespace=self.NAMESPACE,
            summary=summary,
            aliases=aliases,
            properties=props,
            categories=["society", "culture", domain_key, branch_obj.key],
            subtopics=subtopics,
            contexts=contexts,
            rules=rules,
            exceptions=exceptions,
            provenance={
                "society_culture_block": "B09",
                "domain": domain_key,
                "branch": branch_obj.key,
                "source_record_id": record_id,
                "context_required": True,
            },
        )
        taxonomy = self._ensure_taxonomy_path(branch_obj, include_subtopics=False)
        self.graph.relate(result["knowledge_id"], taxonomy["branch_id"], "is_a", metadata={"block": "B09", "society_culture_taxonomy": True})
        self.graph.relate(taxonomy["branch_id"], result["knowledge_id"], "has_part", metadata={"block": "B09", "society_culture_taxonomy": True})
        return result

    def relate(self, source_id: str, target_id: str, relation: str, *, weight: float = 1.0) -> dict:
        return self.knowledge.relate(source_id, target_id, relation, weight=weight, metadata={"block": "B09", "society_culture": True})

    def policy(self) -> dict:
        return deepcopy(INTERPRETATION_POLICY)

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "domains": [{"key": key, "label": DOMAIN_LABELS[key]} for key in SOCIETY_CULTURE_DOMAINS],
            "lenses": [{"key": key, "label": label} for key, label, _ in SOCIETY_CULTURE_LENSES],
            "requested_topics": list(REQUESTED_TOPICS),
            "reference_subjects": dict(REFERENCE_SUBJECTS),
            "knowledge_graph": "shared knowledge_nodes/knowledge_edges",
            "canonical_knowledge": "BLOCO 2 gate -> BLOCO 3 -> B09",
            "multidisciplinary_knowledge": "reused, not duplicated",
            "interpretation_policy": self.policy(),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None
        if low in {
            "status bloco 9", "status sociedade e cultura", "status sociedade", "status cultura",
            "sociedade e cultura", "fundamentos sociais e culturais", "fundamentos socioculturais",
        }:
            stats = self.stats()
            return (
                f"🌍 BLOCO 9 — SOCIEDADE E CULTURA: {stats['catalog']['addressable_contents']} conteúdos endereçáveis em B09 | "
                f"{stats['catalog']['domains']} domínios × {stats['catalog']['branches']} ramos × {stats['catalog']['lenses_per_branch']} lentes = "
                f"{stats['catalog']['canonical_nodes']} nós | Knowledge Graph=COMPARTILHADO | referências multidisciplinares=REUTILIZADAS."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"🌍 {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        taxonomy = re.match(r"^(?:taxonomia sociedade|taxonomia cultura|taxonomia sociedade e cultura)(?:\s+(.+))?$", raw, re.I)
        if taxonomy:
            snapshot = self.taxonomy_snapshot(taxonomy.group(1))
            labels = ", ".join(item["branch_label"] for item in snapshot["branches"][:12])
            return f"🌍 Taxonomia B09: {len(snapshot['branches'])} ramos. {labels}{'…' if len(snapshot['branches']) > 12 else ''}"
        if low in {"limites bloco 9", "limites sociedade e cultura", "generalizacao cultural", "generalização cultural"}:
            return "🛡️ BLOCO 9 não trata culturas, sociedades, classes, religiões ou instituições como essências fixas. Época, região, fontes, diversidade interna e perspectivas concorrentes permanecem obrigatórias."
        return None
