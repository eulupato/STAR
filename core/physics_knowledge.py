"""Catálogo local de Física da STAR: 50 tópicos x 1.000 variações = 50.000."""
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
    "CERN": "CERN Standard Model",
    "NASA": "NASA Physics of the Cosmos",
}

FAMILIES = (
    "conceito", "formula", "variaveis_unidades", "hipoteses_validade", "derivacao",
    "calculo", "aplicacao", "erros_comuns", "limites", "conexoes",
)
STYLES = ("direto", "intuitivo", "didatico", "tecnico", "vestibular", "graduacao", "laboratorio", "engenharia", "pesquisa", "revisao")
CONTEXTS = ("definicao", "interpretacao", "simbolico", "dimensional", "experimental", "comparativo", "estimativa", "caso_limite", "aplicado", "checagem")
VARIANTS_PER_TOPIC = 1000
TOTAL_VARIANTS = 50000

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

# TSV: id, domínio, nível, título, fórmula, síntese, aliases, fonte.
_ROWS = r"""
dimensional_analysis	matematica_fisica	1	Análise dimensional	[Q]=M^a L^b T^c I^d Θ^e N^f J^g	Checa homogeneidade física e relações de escala.	dimensoes;homogeneidade dimensional;teorema pi	NIST
uncertainty_propagation	matematica_fisica	2	Propagação de incertezas	u_f^2≈Σ_i(∂f/∂x_i)^2u_i^2	Combina pequenas incertezas independentes por derivadas parciais.	incerteza;erro experimental;metrologia	NIST
constant_acceleration	cinematica	1	Cinemática com aceleração constante	v=v0+at; x=x0+v0t+(1/2)at^2	Relaciona posição, velocidade, aceleração e tempo no MRUV.	mruv;equacao horaria;aceleracao constante	MIT_MECH
projectile_motion	cinematica	2	Lançamento oblíquo ideal	R=v0^2 sin(2θ)/g	Alcance para mesma altura, sem arrasto e g uniforme.	projetil;lancamento obliquo;alcance	MIT_MECH
newton_second	dinamica	1	Segunda lei de Newton	ΣF=ma	Força resultante produz aceleração para massa constante.	segunda lei;forca resultante;f ma	MIT_MECH
friction_drag	dinamica	2	Atrito e arrasto	f_s≤μ_sN; f_k=μ_kN; F_D≈(1/2)ρC_DAv^2	Modela forças dissipativas de contato e fluido.	atrito;arrasto;resistencia do ar	OPENSTAX
work_energy	energia_momento	1	Trabalho e energia	W=∫F·dr; K=(1/2)mv^2	Trabalho líquido altera energia cinética.	trabalho;energia cinetica;teorema trabalho energia	MIT_MECH
impulse_momentum	energia_momento	1	Impulso e momento	J=∫Fdt=Δp	Impulso é a variação do momento linear.	impulso;momento linear;quantidade de movimento	MIT_MECH
torque	rotacao	2	Torque	τ=r×F	Mede tendência de uma força causar rotação.	torque;momento de uma forca;alavanca	MIT_MECH
angular_momentum	rotacao	2	Momento angular	L=r×p; L≈Iω	Conserva-se se o torque externo resultante for nulo.	momento angular;I omega;conservacao angular	MIT_MECH
newton_gravity	gravitacao	1	Gravitação universal	F=Gm1m2/r^2; U=-GMm/r	Lei do inverso do quadrado e potencial gravitacional newtoniano.	gravidade;lei da gravitacao;potencial gravitacional	MIT_MECH
kepler_orbit	gravitacao	2	Órbitas e Kepler	v_c=sqrt(GM/r); T^2=4π^2a^3/(GM)	Conecta órbitas circulares e a terceira lei de Kepler.	orbita;kepler;periodo orbital	MIT_MECH
simple_harmonic	oscilacoes	1	Oscilador harmônico simples	x=A cos(ωt+φ); ω0=sqrt(k/m)	Força restauradora linear gera oscilação harmônica.	mhs;massa mola;movimento harmonico	OPENSTAX
damped_resonance	oscilacoes	3	Amortecimento e ressonância	x≈Ae^{-γt}cos(ω_dt+φ); γ=b/(2m)	Dissipação reduz amplitude e forçamento pode gerar ressonância.	amortecimento;ressonancia;oscilador forcado	OPENSTAX
wave_equation	ondas	2	Ondas e equação de onda	v=fλ; ∂²y/∂t²=v²∂²y/∂x²	Descreve propagação linear e relação entre frequência e comprimento de onda.	onda;comprimento de onda;equacao de onda	OPENSTAX
doppler	ondas	2	Efeito Doppler	f'=f(v±v_o)/(v∓v_s)	Movimento relativo muda a frequência observada.	doppler;som;frequencia observada	OPENSTAX
continuity_fluid	fluidos	2	Continuidade de fluido	A1v1=A2v2	Conservação de massa em fluxo incompressível estacionário.	continuidade;vazao;escoamento	OPENSTAX
bernoulli	fluidos	2	Equação de Bernoulli	p+(1/2)ρv^2+ρgh=constante	Conservação de energia ao longo de linha de corrente ideal.	bernoulli;pressao dinamica;fluido ideal	OPENSTAX
ideal_gas_first_law	termodinamica	2	Gás ideal e primeira lei	PV=nRT; ΔU=Q-W	Equação de estado e conservação de energia térmica.	gas ideal;primeira lei;energia interna	MIT_STAT
entropy_carnot	termodinamica	3	Entropia e Carnot	dS=δQ_rev/T; η_C=1-T_c/T_h	Entropia mede irreversibilidade e Carnot fixa limite reversível.	entropia;carnot;segunda lei	MIT_STAT
boltzmann_entropy	mecanica_estatistica	3	Entropia de Boltzmann	S=k_B lnΩ	Liga entropia macroscópica ao número de microestados.	boltzmann;microestado;macroestado	MIT_STAT
partition_function	mecanica_estatistica	4	Distribuição canônica e partição	p_i=e^{-βE_i}/Z; Z=Σe^{-βE_i}; F=-k_BT lnZ	A função de partição normaliza estados e gera termodinâmica.	ensemble canonico;funcao de particao;energia livre	MIT_STAT
coulomb	eletrostatica	1	Lei de Coulomb	F=(1/(4πε0)) abs(q1q2)/r^2	Força eletrostática pontual segue o inverso do quadrado.	coulomb;forca eletrica;cargas	MIT_EM
gauss_electric	eletrostatica	2	Lei de Gauss elétrica	∮E·dA=Q_enc/ε0	Fluxo elétrico fechado depende da carga encerrada.	gauss;fluxo eletrico;superficie gaussiana	MIT_EM
ohm_power	circuitos	1	Ohm e potência	V=IR; P=VI=I^2R=V^2/R	Relaciona tensão, corrente, resistência e potência.	lei de ohm;potencia eletrica;resistor	MIT_EM
rc_rlc	circuitos	3	Circuitos RC e RLC	τ_RC=RC; ω0=1/sqrt(LC)	RC relaxa exponencialmente e RLC possui frequência natural.	circuito rc;circuito rlc;ressonancia eletrica	MIT_EM
lorentz_force	magnetismo	2	Força de Lorentz	F=q(E+v×B)	Força eletromagnética sobre carga em campos E e B.	forca de lorentz;campo magnetico;particula carregada	MIT_EM
biot_ampere	magnetismo	3	Biot-Savart e Ampère	dB=(μ0/4π)I(dℓ×r_hat)/r^2; ∮B·dℓ=μ0I_enc	Relaciona correntes estacionárias a campos magnéticos.	biot savart;ampere;magnetostatica	MIT_EM
faraday	eletromagnetismo	2	Lei de Faraday-Lenz	ε=-dΦ_B/dt	Fluxo magnético variável induz força eletromotriz.	faraday;lenz;inducao	MIT_EM
maxwell_waves	eletromagnetismo	4	Maxwell e ondas eletromagnéticas	∇·E=ρ/ε0; ∇·B=0; ∇×E=-∂B/∂t; ∇×B=μ0J+μ0ε0∂E/∂t	Unifica eletricidade e magnetismo e prevê ondas EM.	maxwell;onda eletromagnetica;corrente de deslocamento	MIT_EM
snell_lens	optica	1	Refração e lente delgada	n1sinθ1=n2sinθ2; 1/f=1/d_o+1/d_i	Relaciona refração e formação paraxial de imagens.	snell;lente delgada;refracao	OPENSTAX
interference_diffraction	optica	2	Interferência e difração	d sinθ=mλ; a sinθ=mλ (mínimos)	Superposição coerente e abertura finita produzem padrões ondulatórios.	dupla fenda;interferencia;difracao	OPENSTAX
lorentz_transform	relatividade_especial	3	Transformação de Lorentz	γ=1/sqrt(1-v^2/c^2); x'=γ(x-vt); t'=γ(t-vx/c^2)	Relaciona espaço-tempo entre referenciais inerciais.	lorentz;gamma relativistico;tempo proprio	MIT_REL
relativistic_energy	relatividade_especial	3	Energia-momento relativística	E^2=(pc)^2+(mc^2)^2	Invariante relativístico entre energia, momento e massa.	energia momento;E mc2;relatividade	MIT_REL
einstein_field	relatividade_geral	5	Equações de Einstein	G_{μν}+Λg_{μν}=(8πG/c^4)T_{μν}	Curvatura do espaço-tempo responde a energia e momento.	equacao de einstein;curvatura;tensor energia momento	MIT_REL
schwarzschild	relatividade_geral	4	Schwarzschild e horizonte	r_s=2GM/c^2; dτ=dt sqrt(1-r_s/r)	Solução esférica não rotativa introduz horizonte e redshift gravitacional.	schwarzschild;buraco negro;horizonte	MIT_REL
friedmann	cosmologia_relativistica	5	Equação de Friedmann	H^2=(8πG/3)ρ+Λc^2/3-kc^2/a^2	Descreve expansão homogênea e isotrópica do Universo.	friedmann;FLRW;expansao do universo	PDG
schrodinger	quantica	4	Equação de Schrödinger	iħ∂ψ/∂t=Ĥψ	Governa evolução unitária quântica não relativística.	schrodinger;funcao de onda;hamiltoniano	MIT_QM
uncertainty_debroglie	quantica	3	Incerteza e de Broglie	ΔxΔp≥ħ/2; λ=h/p	Liga incompatibilidade quântica e ondas de matéria.	heisenberg;de broglie;onda de materia	MIT_QM
hydrogen_rydberg	atomica_molecular	3	Hidrogênio e Rydberg	E_n≈-13.6eV/n^2; 1/λ=R_H(1/n1^2-1/n2^2)	Níveis discretos produzem linhas espectrais do hidrogênio.	hidrogenio;rydberg;espectro atomico	OPENSTAX
drude_bloch	materia_condensada	4	Drude e Bloch	σ=ne^2τ/m; ψ_{n,k}=e^{ik·r}u_{n,k}(r)	Modela transporte semiclassicamente e estados em redes periódicas.	drude;bloch;bandas cristalinas	OPENSTAX
fermi_semiconductor	materia_condensada	4	Fermi e semicondutores	E_F=ħ^2(3π^2n)^{2/3}/(2m); n_i≈sqrt(N_cN_v)e^{-E_g/(2k_BT)}	Fermi governa elétrons degenerados e o gap controla portadores intrínsecos.	energia de fermi;semicondutor;gap de banda	MIT_STAT
nuclear_binding_decay	nuclear	3	Ligação e decaimento nuclear	E_b=Δmc^2; N=N0e^{-λt}; t_1/2=ln2/λ	Defeito de massa mede ligação e decaimentos independentes geram exponencial.	defeito de massa;meia vida;radioatividade	OPENSTAX
nuclear_q_activity	nuclear	3	Valor Q e atividade	Q=(m_i-m_f)c^2; A=λN	Valor Q mede balanço energético e atividade mede taxa de decaimentos.	valor q;atividade;becquerel	OPENSTAX
standard_model_alpha	particulas	5	Modelo Padrão e estrutura fina	SU(3)_C×SU(2)_L×U(1)_Y; α=e^2/(4πε0ħc)	Teoria de gauge das interações forte e eletrofraca; α mede acoplamento EM.	modelo padrao;estrutura fina;qed	CERN
field_euler_lagrange	qft	5	Euler-Lagrange para campos	∂L/∂φ-∂_μ[∂L/∂(∂_μφ)]=0	Extremização da ação gera equações de movimento de campos.	lagrangiana;teoria quantica de campos;acao	PDG
plasma_debye	plasma	4	Plasma e Debye	ω_pe=sqrt(n_e e^2/(m_eε0)); λ_D=sqrt(ε0k_BT_e/(n_ee^2))	Define oscilação eletrônica coletiva e escala de blindagem eletrostática.	plasma;debye;frequencia de plasma	OPENSTAX
cyclotron_lyapunov	plasma_caos	5	Ciclotron e Lyapunov	ω_c=abs(q)B/m; λ_L=lim(1/t)ln(abs(δx(t))/abs(δx(0)))	Giro magnético e sensibilidade exponencial em sistemas dinâmicos.	ciclotron;lyapunov;caos	MIT_EM
stellar_luminosity	astrofisica	3	Luminosidade estelar	F=L/(4πd^2); L≈4πR^2σT_eff^4	Fluxo cai com d² e corpo negro liga raio, temperatura e luminosidade.	luminosidade estelar;fluxo;stefan boltzmann	NASA
hubble_critical	cosmologia	4	Hubble e densidade crítica	v≈H0d; ρ_c=3H^2/(8πG)	Em baixo redshift a recessão é aproximadamente linear; ρ_c normaliza densidades cosmológicas.	hubble;densidade critica;omega cosmologico	PDG
"""

def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFD", str(text or "").lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"[^a-z0-9_\s]", " ", value)
    return " ".join(value.split())

def _topics() -> tuple[PhysicsTopic, ...]:
    result = []
    for line in _ROWS.strip().splitlines():
        p = line.split("\t")
        if len(p) != 8:
            raise ValueError(f"physics row inválida: {len(p)} campos")
        topic_id, domain, level, title, formula, summary, aliases, source = p
        result.append(PhysicsTopic(topic_id, domain, int(level), title, formula, summary, tuple(a.strip() for a in aliases.split(";") if a.strip()), source))
    if len(result) != 50:
        raise ValueError(f"Esperados 50 tópicos; encontrados {len(result)}")
    return tuple(result)

TOPICS = _topics()

class PhysicsKnowledgeEngine:
    def __init__(self):
        self.topics = TOPICS
        self._search = []
        for topic in self.topics:
            values = (topic.id, topic.domain, topic.title, *topic.aliases)
            self._search.append(tuple(dict.fromkeys(_normalize(v) for v in values if v)))

    def stats(self):
        return {
            "canonical_topics": 50,
            "variants_per_topic": VARIANTS_PER_TOPIC,
            "content_variations": TOTAL_VARIANTS,
            "domains": len({t.domain for t in self.topics}),
            "levels": [1, 2, 3, 4, 5],
            "families": len(FAMILIES),
            "styles": len(STYLES),
            "contexts": len(CONTEXTS),
        }

    @staticmethod
    def content_id(topic_index: int, variant_index: int) -> str:
        if not 0 <= topic_index < 50 or not 0 <= variant_index < 1000:
            raise IndexError("índice fora do catálogo PHYS-00001..PHYS-50000")
        return f"PHYS-{topic_index * 1000 + variant_index + 1:05d}"

    def get_variant(self, content_id: str):
        m = re.fullmatch(r"PHYS-(\d{5})", str(content_id or "").upper())
        if not m:
            return None
        n = int(m.group(1))
        if not 1 <= n <= TOTAL_VARIANTS:
            return None
        topic_index, local = divmod(n - 1, 1000)
        family_i, within = divmod(local, 100)
        style_i, context_i = divmod(within, 10)
        topic = self.topics[topic_index]
        family, style, context = FAMILIES[family_i], STYLES[style_i], CONTEXTS[context_i]
        return {
            "id": f"PHYS-{n:05d}", "topic_id": topic.id, "domain": topic.domain,
            "level": topic.level, "title": topic.title, "family": family,
            "style": style, "context": context,
            "prompt": self._prompt(topic, family, style, context),
            "answer": self._render(topic, family, style, context),
            "source": SOURCES[topic.source],
        }

    def match(self, query: str):
        q = _normalize(query)
        if not q:
            return None
        qt = set(q.split())
        best, best_score = None, 0.0
        for topic, candidates in zip(self.topics, self._search):
            for c in candidates:
                if c == q:
                    score = 1.0
                elif c in q or q in c:
                    score = 0.92
                else:
                    ct = set(c.split())
                    score = len(qt & ct) / max(1, min(len(qt), len(ct)))
                if score > best_score:
                    best, best_score = topic, score
        return best if best_score >= 0.58 else None

    def answer(self, query: str):
        topic = self.match(query)
        if topic is None:
            return None
        q = _normalize(query)
        if any(k in q for k in ("formula", "equacao", "expressao")):
            family = "formula"
        elif any(k in q for k in ("calcule", "calculo", "resolver", "conta", "passo a passo")):
            family = "calculo"
        elif any(k in q for k in ("unidade", "dimensao", "variavel", "simbolo")):
            family = "variaveis_unidades"
        elif any(k in q for k in ("hipotese", "validade", "vale quando", "condicao")):
            family = "hipoteses_validade"
        elif any(k in q for k in ("deriv", "demonstr", "de onde vem")):
            family = "derivacao"
        elif any(k in q for k in ("aplic", "serve para", "uso", "exemplo")):
            family = "aplicacao"
        elif any(k in q for k in ("erro", "pegadinha", "confus", "cuidado")):
            family = "erros_comuns"
        elif any(k in q for k in ("limite", "aproxim", "quando nao", "falha")):
            family = "limites"
        elif any(k in q for k in ("relacao", "conecta", "ligacao", "correlacion")):
            family = "conexoes"
        else:
            family = "conceito"
        digest = hashlib.sha256(q.encode()).digest()
        return self._render(topic, family, STYLES[digest[0] % 10], CONTEXTS[digest[1] % 10])

    @staticmethod
    def _prompt(topic, family, style, context):
        verb = {
            "conceito": "Explique", "formula": "Apresente a fórmula de", "variaveis_unidades": "Detalhe símbolos e unidades de",
            "hipoteses_validade": "Liste hipóteses de", "derivacao": "Dê um roteiro de derivação de", "calculo": "Monte um cálculo com",
            "aplicacao": "Dê aplicações de", "erros_comuns": "Aponte erros comuns em", "limites": "Explique limites de", "conexoes": "Conecte a outras áreas:",
        }[family]
        return f"{verb} {topic.title} — estilo {style}, contexto {context}."

    @staticmethod
    def _render(topic, family, style, context):
        ref = SOURCES[topic.source]
        if family == "formula":
            body = f"Fórmula-base: {topic.formula}. {topic.summary}"
        elif family == "variaveis_unidades":
            body = f"Use {topic.formula}. Identifique cada símbolo, converta dados para unidades coerentes e confirme homogeneidade dimensional."
        elif family == "hipoteses_validade":
            body = f"Antes de usar {topic.formula}, cheque regime físico, aproximações, condições iniciais/contorno e domínio de validade. {topic.summary}"
        elif family == "derivacao":
            body = f"Roteiro: declare hipóteses; escolha leis/simetrias; escreva grandezas; derive simbolicamente; teste dimensões e casos-limite. Resultado de referência: {topic.formula}."
        elif family == "calculo":
            body = f"Cálculo: parta de {topic.formula}; liste dados com unidades; converta para SI; isole a incógnita; substitua; calcule; cheque dimensão, sinal, ordem de grandeza e regime."
        elif family == "aplicacao":
            body = f"{topic.summary} Relação operacional: {topic.formula}."
        elif family == "erros_comuns":
            body = f"Evite aplicar {topic.formula} fora das hipóteses, misturar unidades, perder sinais/vetores, arredondar cedo ou ignorar limites do modelo."
        elif family == "limites":
            body = f"Teste {topic.formula} nos limites relevantes e não extrapole além do modelo em que foi derivada. {topic.summary}"
        elif family == "conexoes":
            body = f"{topic.summary} Compare com conservação, simetrias, escalas, análise dimensional e áreas vizinhas. Fórmula-base: {topic.formula}."
        else:
            body = f"{topic.summary} Relação central: {topic.formula}."
        return f"{topic.title} — nível {topic.level}. {body} [Fonte técnica: {ref}; modo {style}/{context}]"
