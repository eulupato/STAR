"""Catálogo local de física da STAR.

50 tópicos canônicos x 1.000 variações determinísticas = 50.000 unidades
endereçáveis. O catálogo evita materializar 50 mil objetos no startup: cada
variação é produzida sob demanda a partir de fatos, fórmulas, hipóteses,
aplicações e roteiros de cálculo revisáveis.

As sínteses são originais; as fontes abaixo servem como referências técnicas e
curriculares. Nenhum texto-fonte é copiado integralmente.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
import unicodedata


SOURCES = {
    "MIT_MECH": "MIT OpenCourseWare 8.01SC Classical Mechanics",
    "MIT_EM": "MIT OpenCourseWare 8.022/8.02 Electricity and Magnetism",
    "MIT_QM": "MIT OpenCourseWare 8.04 Quantum Physics I",
    "MIT_STAT": "MIT OpenCourseWare 8.044/8.333 Statistical Physics",
    "MIT_REL": "MIT OpenCourseWare 8.20/8.033 Relativity",
    "OPENSTAX": "OpenStax University Physics Volumes 1-3",
    "NIST": "NIST/CODATA 2022 Fundamental Physical Constants",
    "PDG": "Particle Data Group, Review of Particle Physics 2026",
    "CERN": "CERN Standard Model and particle-physics references",
    "NASA": "NASA Physics of the Cosmos",
}

VARIATION_FAMILIES = (
    "conceito",
    "formula",
    "variaveis_unidades",
    "hipoteses_validade",
    "derivacao_roteiro",
    "calculo_roteiro",
    "aplicacao",
    "erros_comuns",
    "limites_aproximacoes",
    "conexoes",
)

STYLES = (
    "direto",
    "intuitivo",
    "didatico",
    "tecnico",
    "vestibular",
    "graduacao",
    "laboratorio",
    "engenharia",
    "pesquisa",
    "revisao",
)

CONTEXTS = (
    "definicao",
    "interpretacao",
    "simbolico",
    "dimensional",
    "experimental",
    "comparativo",
    "estimativa",
    "caso_limite",
    "aplicado",
    "checagem",
)


@dataclass(frozen=True)
class PhysicsTopic:
    id: str
    domain: str
    level: int
    title: str
    formula: str
    summary: str
    aliases: tuple[str, ...]
    source: str


_ROWS = r"""
dimensional_analysis|matematica_fisica|1|Análise dimensional|[Q] = M^a L^b T^c I^d Θ^e N^f J^g|Representa grandezas por potências das dimensões fundamentais e permite checar homogeneidade de equações e relações de escala.|dimensoes;homogeneidade dimensional;teorema pi|NIST
uncertainty_propagation|matematica_fisica|2|Propagação de incertezas|u_f^2 ≈ Σ_i (∂f/∂x_i)^2 u_i^2|Para variáveis independentes e pequenas incertezas, estima a incerteza combinada de uma função por derivadas parciais.|erro experimental;incerteza combinada;metrologia|NIST
constant_acceleration|cinematica|1|Cinemática com aceleração constante|v=v0+at; x=x0+v0t+(1/2)at^2|Relaciona posição, velocidade, aceleração e tempo quando a aceleração é constante.|mruv;equacao horaria;aceleracao constante|MIT_MECH
projectile_motion|cinematica|2|Lançamento oblíquo ideal|R=v0^2 sin(2θ)/g|Para lançamento e queda na mesma altura, sem arrasto e com g uniforme, fornece o alcance horizontal.|projetil;lancamento obliquo;alcance balistico|MIT_MECH
newton_second|dinamica|1|Segunda lei de Newton|ΣF=ma|Para massa constante, a força resultante é igual ao produto da massa pela aceleração.|segunda lei;forca resultante;f ma|MIT_MECH
friction_drag|dinamica|2|Atrito e arrasto|f_s≤μ_sN; f_k=μ_kN; F_D≈(1/2)ρC_DAv^2|Modelos de forças dissipativas: atrito seco depende da normal; arrasto quadrático é útil em muitos regimes de fluxo.|atrito;resistencia do ar;drag|OPENSTAX
work_energy|energia_momento|1|Trabalho e energia cinética|W=∫F·dr; K=(1/2)mv^2|O trabalho líquido altera a energia cinética; forças conservativas permitem formular energia potencial.|trabalho;energia cinetica;teorema trabalho energia|MIT_MECH
impulse_momentum|energia_momento|1|Impulso e momento linear|J=∫Fdt=Δp|O impulso de uma força é igual à variação do momento linear do sistema.|impulso;quantidade de movimento;momento linear|MIT_MECH
torque|rotacao|2|Torque|τ=r×F|Mede a tendência de uma força produzir rotação em torno de uma origem ou eixo.|momento de uma forca;torque;alavanca|MIT_MECH
angular_momentum|rotacao|2|Momento angular|L=r×p; eixo fixo: L≈Iω|É o análogo rotacional do momento linear e conserva-se quando o torque externo resultante é nulo.|momento angular;I omega;conservacao angular|MIT_MECH
newton_gravity|gravitacao|1|Gravitação universal|F=Gm1m2/r^2; U=-GMm/r|Massas atraem-se pela lei do inverso do quadrado; a energia potencial gravitacional é negativa com zero no infinito.|gravidade newtoniana;lei da gravitacao;potencial gravitacional|MIT_MECH
kepler_orbit|gravitacao|2|Órbitas e terceira lei de Kepler|v_c=sqrt(GM/r); T^2=4π^2a^3/(GM)|Para massa central dominante, conecta velocidade circular, período e semieixo maior de órbitas keplerianas.|orbita circular;kepler;periodo orbital|MIT_MECH
simple_harmonic|oscilacoes|1|Oscilador harmônico simples|x=A cos(ωt+φ); ω0=sqrt(k/m)|Uma força restauradora linear produz oscilação senoidal com frequência natural determinada por rigidez e massa.|mhs;massa mola;movimento harmonico|OPENSTAX
damped_resonance|oscilacoes|3|Oscilação amortecida e ressonância|x≈Ae^{-γt}cos(ω_dt+φ); γ=b/(2m)|Dissipação reduz amplitude e modifica a frequência; forçamento periódico pode produzir ressonância.|amortecimento;ressonancia;oscilador forcado|OPENSTAX
wave_equation|ondas|2|Ondas e equação de onda|v=fλ; ∂²y/∂t²=v²∂²y/∂x²|Ondas periódicas ligam frequência e comprimento de onda; a equação de onda descreve propagação linear ideal.|onda;comprimento de onda;equacao de onda|OPENSTAX
doppler|ondas|2|Efeito Doppler clássico|f'=f(v±v_o)/(v∓v_s)|A frequência observada muda quando fonte e observador têm movimento relativo no meio.|doppler;frequencia observada;som|OPENSTAX
continuity_fluid|fluidos|2|Continuidade de fluido incompressível|A1v1=A2v2|Em escoamento estacionário incompressível, conservação de massa implica vazão volumétrica constante.|vazao;continuidade;escoamento|OPENSTAX
bernoulli|fluidos|2|Equação de Bernoulli|p+(1/2)ρv^2+ρgh=constante|Ao longo de linha de corrente de fluido ideal estacionário, soma termos de pressão, cinético e gravitacional.|bernoulli;pressao dinamica;fluido ideal|OPENSTAX
ideal_gas_first_law|termodinamica|2|Gás ideal e primeira lei|PV=nRT; ΔU=Q-W|A equação de estado do gás ideal liga P,V,n,T; a primeira lei expressa conservação de energia termodinâmica com convenção W feito pelo sistema.|gas ideal;primeira lei;energia interna|MIT_STAT
entropy_carnot|termodinamica|3|Entropia e limite de Carnot|dS=δQ_rev/T; η_C=1-T_c/T_h|Entropia quantifica irreversibilidade; nenhuma máquina entre dois reservatórios supera a eficiência reversível de Carnot.|entropia;carnot;segunda lei|MIT_STAT
boltzmann_entropy|mecanica_estatistica|3|Entropia de Boltzmann|S=k_B lnΩ|Conecta entropia macroscópica ao número de microestados compatíveis com o macroestado.|boltzmann;microestado;macroestado|MIT_STAT
partition_function|mecanica_estatistica|4|Distribuição canônica e função de partição|p_i=e^{-βE_i}/Z; Z=Σe^{-βE_i}; F=-k_BT lnZ|A função de partição normaliza probabilidades canônicas e gera grandezas termodinâmicas.|ensemble canonico;funcao de particao;energia livre|MIT_STAT
coulomb|eletrostatica|1|Lei de Coulomb|F=(1/(4πε0))|q1q2|/r^2|A força entre cargas pontuais varia com o produto das cargas e com o inverso do quadrado da separação.|coulomb;forca eletrica;cargas|MIT_EM
gauss_electric|eletrostatica|2|Lei de Gauss elétrica|∮E·dA=Q_enc/ε0|O fluxo elétrico por superfície fechada é determinado pela carga líquida encerrada.|gauss;fluxo eletrico;superficie gaussiana|MIT_EM
ohm_power|circuitos|1|Lei de Ohm e potência elétrica|V=IR; P=VI=I^2R=V^2/R|Em resistor ôhmico, tensão e corrente são proporcionais; potência mede a taxa de conversão de energia.|lei de ohm;potencia eletrica;resistor|MIT_EM
rc_rlc|circuitos|3|Circuitos RC e RLC|τ_RC=RC; ω0=1/sqrt(LC)|RC apresenta relaxação exponencial; RLC ideal possui frequência natural definida por L e C.|circuito rc;circuito rlc;ressonancia eletrica|MIT_EM
lorentz_force|magnetismo|2|Força de Lorentz|F=q(E+v×B)|A força eletromagnética sobre uma carga combina componentes elétrica e magnética.|forca de lorentz;campo magnetico;particula carregada|MIT_EM
biot_ampere|magnetismo|3|Biot-Savart e Ampère|dB=(μ0/4π)I(dℓ×r_hat)/r^2; ∮B·dℓ=μ0I_enc|Duas formulações centrais da magnetostática relacionam correntes a campos magnéticos.|biot savart;ampere;magnetostatica|MIT_EM
faraday|eletromagnetismo|2|Lei de Faraday-Lenz|ε=-dΦ_B/dt|Variação de fluxo magnético induz força eletromotriz com sinal que se opõe à mudança do fluxo.|faraday;lenz;inducao eletromagnetica|MIT_EM
maxwell_waves|eletromagnetismo|4|Equações de Maxwell e ondas EM|∇·E=ρ/ε0; ∇·B=0; ∇×E=-∂B/∂t; ∇×B=μ0J+μ0ε0∂E/∂t|As quatro equações unificam eletricidade e magnetismo e implicam ondas que no vácuo propagam-se a c=1/sqrt(μ0ε0).|maxwell;onda eletromagnetica;corrente de deslocamento|MIT_EM
snell_lens|optica|1|Refração e lente delgada|n1sinθ1=n2sinθ2; 1/f=1/d_o+1/d_i|Snell descreve refração em interfaces; a equação de lente relaciona foco, objeto e imagem no regime paraxial.|snell;lente delgada;refracao|OPENSTAX
interference_diffraction|optica|2|Interferência e difração|d sinθ=mλ; mínimos de fenda: a sinθ=mλ|Padrões ondulatórios surgem de superposição coerente e abertura finita.|dupla fenda;interferencia;difracao|OPENSTAX
lorentz_transform|relatividade_especial|3|Transformação de Lorentz e dilatação temporal|γ=1/sqrt(1-v^2/c^2); x'=γ(x-vt); t'=γ(t-vx/c^2)|Relaciona coordenadas entre referenciais inerciais e produz dilatação temporal e contração espacial.|lorentz;gamma relativistico;tempo proprio|MIT_REL
relativistic_energy|relatividade_especial|3|Energia e momento relativísticos|E^2=(pc)^2+(mc^2)^2|É a relação invariante entre energia total, momento e massa de repouso; para p=0 resulta E=mc².|energia momento;E mc2;relatividade|MIT_REL
einstein_field|relatividade_geral|5|Equações de campo de Einstein|G_{μν}+Λg_{μν}=(8πG/c^4)T_{μν}|Relacionam curvatura do espaço-tempo a energia e momento da matéria e campos.|equacao de einstein;tensor energia momento;curvatura|MIT_REL
schwarzschild|relatividade_geral|4|Geometria de Schwarzschild|r_s=2GM/c^2; dτ=dt sqrt(1-r_s/r)|A solução esférica não rotativa no vácuo introduz horizonte em r_s e dilatação gravitacional do tempo para observadores estáticos externos.|schwarzschild;buraco negro;horizonte de eventos|MIT_REL
friedmann|cosmologia_relativistica|5|Equação de Friedmann|H^2=(8πG/3)ρ+Λc^2/3-kc^2/a^2|Descreve a expansão de universo homogêneo e isotrópico em termos de densidade, curvatura e constante cosmológica.|friedmann;FLRW;expansao do universo|PDG
schrodinger|quantica|4|Equação de Schrödinger|iħ∂ψ/∂t=Ĥψ|Governa a evolução unitária de estados quânticos não relativísticos sob um Hamiltoniano.|schrodinger;funcao de onda;hamiltoniano|MIT_QM
uncertainty_debroglie|quantica|3|Incerteza e ondas de matéria|ΔxΔp≥ħ/2; λ=h/p|A mecânica quântica liga dispersões incompatíveis e associa comprimento de onda a momento de partículas.|heisenberg;de broglie;onda de materia|MIT_QM
hydrogen_rydberg|atomica_molecular|3|Hidrogênio e fórmula de Rydberg|E_n≈-13.6eV/n^2; 1/λ=R_H(1/n1^2-1/n2^2)|Níveis ligados discretos do hidrogênio produzem linhas espectrais associadas a transições entre estados.|hidrogenio;rydberg;espectro atomico|OPENSTAX
drude_bloch|materia_condensada|4|Drude e Bloch|σ=ne^2τ/m; ψ_{n,k}=e^{ik·r}u_{n,k}(r)|Drude modela transporte semiclassicamente; Bloch descreve estados eletrônicos em potenciais periódicos cristalinos.|drude;bloch;bandas cristalinas|OPENSTAX
fermi_semiconductor|materia_condensada|4|Energia de Fermi e semicondutores|E_F=ħ^2(3π^2n)^{2/3}/(2m); n_i≈sqrt(N_cN_v)e^{-E_g/(2k_BT)}|Estatística de Fermi governa elétrons degenerados; o gap controla fortemente portadores intrínsecos em semicondutores.|energia de fermi;semicondutor;gap de banda|MIT_STAT
nuclear_binding_decay|nuclear|3|Ligação nuclear e decaimento|E_b=Δmc^2; N=N0e^{-λt}; t_1/2=ln2/λ|Defeito de massa mede energia de ligação; decaimentos independentes com taxa constante geram lei exponencial.|defeito de massa;meia vida;radioatividade|OPENSTAX
nuclear_q_activity|nuclear|3|Valor Q e atividade nuclear|Q=(m_i-m_f)c^2; A=λN|O valor Q mede energia liberada ou requerida; atividade é a taxa média de decaimentos.|valor q;atividade;becquerel|OPENSTAX
standard_model_alpha|particulas|5|Modelo Padrão e estrutura fina|SU(3)_C×SU(2)_L×U(1)_Y; α=e^2/(4πε0ħc)|O Modelo Padrão é uma teoria de gauge das interações forte e eletrofraca; α caracteriza o acoplamento eletromagnético em baixas energias.|modelo padrao;estrutura fina;qed|CERN
field_euler_lagrange|qft|5|Euler-Lagrange para campos|∂L/∂φ-∂_μ[∂L/∂(∂_μφ)]=0|A extremização da ação para uma densidade Lagrangiana gera equações de movimento de campos clássicos e fundamenta a formulação de QFT.|lagrangiana;teoria de campos;acao|PDG
plasma_debye|plasma|4|Frequência de plasma e comprimento de Debye|ω_pe=sqrt(n_e e^2/(m_eε0)); λ_D=sqrt(ε0k_BT_e/(n_ee^2))|Oscilações coletivas eletrônicas e blindagem de Debye são escalas fundamentais de um plasma clássico quase neutro.|plasma;debye;frequencia de plasma|OPENSTAX
cyclotron_lyapunov|plasma_caos|5|Ciclotron e expoente de Lyapunov|ω_c=|q|B/m; λ_L=lim(1/t)ln(|δx(t)|/|δx(0)|)|A frequência ciclotrônica descreve giro de cargas em B uniforme; um expoente de Lyapunov positivo caracteriza sensibilidade exponencial em dinâmica caótica.|ciclotron;lyapunov;caos|MIT_EM
stellar_luminosity|astrofisica|3|Fluxo e luminosidade estelar|F=L/(4πd^2); L≈4πR^2σT_eff^4|Emissão isotrópica obedece lei do inverso do quadrado; estrelas podem ser aproximadas por corpo negro para relacionar raio, temperatura e luminosidade.|luminosidade estelar;fluxo;stefan boltzmann|NASA
hubble_critical|cosmologia|4|Hubble-Lemaître e densidade crítica|v≈H0d (baixo z); ρ_c=3H^2/(8πG)|Em baixo redshift a recessão é aproximadamente linear com distância; a densidade crítica normaliza os parâmetros cosmológicos de densidade.|hubble;densidade critica;omega cosmologico|PDG
"""


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFD", str(text or "").lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"[^a-z0-9_\s]", " ", value)
    return " ".join(value.split())


def _build_topics() -> tuple[PhysicsTopic, ...]:
    topics = []
    for raw in _ROWS.strip().splitlines():
        parts = raw.split("|")
        if len(parts) != 8:
            raise ValueError(f"Linha de física inválida ({len(parts)} campos): {raw[:80]}")
        topic_id, domain, level, title, formula, summary, aliases, source = parts
        topics.append(
            PhysicsTopic(
                id=topic_id,
                domain=domain,
                level=int(level),
                title=title,
                formula=formula,
                summary=summary,
                aliases=tuple(item.strip() for item in aliases.split(";") if item.strip()),
                source=source,
            )
        )
    if len(topics) != 50:
        raise ValueError(f"O catálogo canônico deve conter 50 tópicos; recebeu {len(topics)}")
    return tuple(topics)


TOPICS = _build_topics()
TOPIC_VARIATIONS = 1000
TOTAL_VARIATIONS = len(TOPICS) * TOPIC_VARIATIONS


class PhysicsKnowledgeEngine:
    """Resolve física local e expõe exatamente 50.000 conteúdos variáveis."""

    def __init__(self):
        self.topics = TOPICS
        self._index = []
        for topic in self.topics:
            values = [topic.title, topic.domain, topic.id, *topic.aliases]
            self._index.append(tuple(dict.fromkeys(_normalize(value) for value in values if value)))

    def stats(self):
        domains = sorted({topic.domain for topic in self.topics})
        return {
            "canonical_topics": len(self.topics),
            "variants_per_topic": TOPIC_VARIATIONS,
            "content_variations": TOTAL_VARIATIONS,
            "domains": len(domains),
            "levels": sorted({topic.level for topic in self.topics}),
            "families": len(VARIATION_FAMILIES),
            "styles": len(STYLES),
            "contexts": len(CONTEXTS),
        }

    def content_id(self, topic_index: int, variant_index: int) -> str:
        if not 0 <= topic_index < len(self.topics):
            raise IndexError("topic_index fora do catálogo")
        if not 0 <= variant_index < TOPIC_VARIATIONS:
            raise IndexError("variant_index fora de 0..999")
        number = topic_index * TOPIC_VARIATIONS + variant_index + 1
        return f"PHYS-{number:05d}"

    def get_variant(self, content_id: str):
        match = re.fullmatch(r"PHYS-(\d{5})", str(content_id or "").upper())
        if not match:
            return None
        number = int(match.group(1))
        if number < 1 or number > TOTAL_VARIATIONS:
            return None
        zero = number - 1
        topic_index, variant_index = divmod(zero, TOPIC_VARIATIONS)
        family_index, within_family = divmod(variant_index, 100)
        style_index, context_index = divmod(within_family, 10)
        topic = self.topics[topic_index]
        family = VARIATION_FAMILIES[family_index]
        style = STYLES[style_index]
        context = CONTEXTS[context_index]
        return {
            "id": self.content_id(topic_index, variant_index),
            "topic_id": topic.id,
            "domain": topic.domain,
            "level": topic.level,
            "title": topic.title,
            "family": family,
            "style": style,
            "context": context,
            "prompt": self._prompt(topic, family, style, context),
            "answer": self._render(topic, family, style, context),
            "source": SOURCES.get(topic.source, topic.source),
        }

    def answer(self, query: str):
        topic = self.match(query)
        if topic is None:
            return None
        normalized = _normalize(query)
        if any(key in normalized for key in ("formula", "equacao", "expressao", "lei matematica")):
            family = "formula"
        elif any(key in normalized for key in ("calcule", "calculo", "resolver", "conta", "passo a passo")):
            family = "calculo_roteiro"
        elif any(key in normalized for key in ("unidade", "dimensao", "variavel", "simbolo")):
            family = "variaveis_unidades"
        elif any(key in normalized for key in ("hipotese", "vale quando", "validade", "condicao")):
            family = "hipoteses_validade"
        elif any(key in normalized for key in ("deriv", "demonstr", "de onde vem")):
            family = "derivacao_roteiro"
        elif any(key in normalized for key in ("aplic", "serve para", "uso", "exemplo")):
            family = "aplicacao"
        elif any(key in normalized for key in ("erro", "pegadinha", "confus", "cuidado")):
            family = "erros_comuns"
        elif any(key in normalized for key in ("limite", "aproxim", "falha", "quando nao")):
            family = "limites_aproximacoes"
        elif any(key in normalized for key in ("relacao", "conecta", "ligacao", "correlacion")):
            family = "conexoes"
        else:
            family = "conceito"

        digest = hashlib.sha256(normalized.encode("utf-8")).digest()
        style = STYLES[digest[0] % len(STYLES)]
        context = CONTEXTS[digest[1] % len(CONTEXTS)]
        return self._render(topic, family, style, context)

    def match(self, query: str):
        normalized = _normalize(query)
        if not normalized:
            return None
        query_tokens = set(normalized.split())
        best = None
        best_score = 0.0
        for topic, candidates in zip(self.topics, self._index):
            for candidate in candidates:
                if not candidate:
                    continue
                if candidate in normalized or normalized in candidate:
                    score = 1.0 if candidate == normalized else 0.92
                else:
                    tokens = set(candidate.split())
                    common = len(query_tokens & tokens)
                    score = common / max(1, min(len(query_tokens), len(tokens)))
                if score > best_score:
                    best_score = score
                    best = topic
        return best if best_score >= 0.58 else None

    @staticmethod
    def _prompt(topic, family, style, context):
        labels = {
            "conceito": "Explique",
            "formula": "Apresente e interprete a fórmula de",
            "variaveis_unidades": "Descreva símbolos, unidades e dimensões de",
            "hipoteses_validade": "Quais hipóteses e condições de validade existem em",
            "derivacao_roteiro": "Dê um roteiro de derivação para",
            "calculo_roteiro": "Mostre como montar um cálculo usando",
            "aplicacao": "Mostre aplicações físicas de",
            "erros_comuns": "Aponte erros comuns ao usar",
            "limites_aproximacoes": "Explique limites e aproximações de",
            "conexoes": "Conecte este tópico a outras áreas:",
        }
        return f"{labels[family]} {topic.title} — estilo {style}, contexto {context}."

    @staticmethod
    def _render(topic, family, style, context):
        source = SOURCES.get(topic.source, topic.source)
        header = f"{topic.title} — nível {topic.level}."
        if family == "formula":
            body = f"Fórmula-base: {topic.formula}. {topic.summary}"
        elif family == "variaveis_unidades":
            body = (
                f"Relação-base: {topic.formula}. Identifique cada símbolo pelo contexto físico, "
                "converta os dados para unidades coerentes (preferencialmente SI) e confirme que "
                "as dimensões dos dois lados da igualdade são compatíveis."
            )
        elif family == "hipoteses_validade":
            body = (
                f"Modelo-base: {topic.formula}. Antes de aplicar, verifique regime, aproximações, "
                f"condições iniciais/contorno e se o modelo descrito é compatível com o problema. {topic.summary}"
            )
        elif family == "derivacao_roteiro":
            body = (
                f"Roteiro: (1) declare hipóteses; (2) escolha leis/princípios de conservação; "
                f"(3) escreva as grandezas relevantes; (4) faça a álgebra mantendo dimensões; "
                f"(5) teste casos-limite. Resultado de referência: {topic.formula}."
            )
        elif family == "calculo_roteiro":
            body = (
                f"Cálculo: use {topic.formula}. Liste os dados com unidades, converta para SI, "
                "isole a incógnita, substitua apenas depois de reorganizar simbolicamente, calcule "
                "com algarismos significativos adequados e cheque dimensão, ordem de grandeza e regime físico."
            )
        elif family == "aplicacao":
            body = f"Aplicação: {topic.summary} A relação operacional usada como ponto de partida é {topic.formula}."
        elif family == "erros_comuns":
            body = (
                f"Erros comuns: aplicar {topic.formula} fora das hipóteses, misturar unidades, trocar "
                "sinais/vetores por escalares, arredondar cedo demais ou ignorar o domínio físico da aproximação."
            )
        elif family == "limites_aproximacoes":
            body = (
                f"Limites: {topic.formula} deve ser interpretada dentro do modelo em que foi derivada. "
                "Cheque comportamento quando parâmetros tendem a zero, infinito ou ao limite do regime de validade."
            )
        elif family == "conexoes":
            body = (
                f"Conexões: {topic.summary} Relacione conservação, simetrias, escalas, análise dimensional "
                "e o domínio {topic.domain} ao comparar com modelos vizinhos. Fórmula-base: {topic.formula}."
            )
        else:
            body = f"{topic.summary} Fórmula/relação central: {topic.formula}."
        return f"{header} {body} [Referência técnica: {source}; modo {style}/{context}]"
