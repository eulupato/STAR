"""STAR Chemistry canonical topics 426-450 of 500."""

CHEMISTRY_ROWS_18 = r"""\
polymer_monomer	materiais_polimeros_superficies	1	Monômeros e polímeros	grau de polimerização X_n≈M_n/M_0	Relaciona unidade repetitiva a tamanho médio de cadeia.	polimero;monomero;grau polimerizacao	IUPAC
number_average_molar_mass	materiais_polimeros_superficies	3	Massa molar média numérica	M_n=ΣN_iM_i/ΣN_i	Pondera cada cadeia igualmente no número de moléculas.	mn;massa molar polimero;media numerica	IUPAC
weight_average_molar_mass	materiais_polimeros_superficies	3	Massa molar média ponderal	M_w=ΣN_iM_i^2/ΣN_iM_i	Pondera mais fortemente cadeias de alta massa.	mw;massa molar ponderal;polimero	IUPAC
dispersity	materiais_polimeros_superficies	3	Dispersidade	Đ=M_w/M_n	Quantifica largura relativa da distribuição de massas molares.	dispersidade;pdi;mw mn	IUPAC
step_growth_polymerization	materiais_polimeros_superficies	3	Polimerização por etapas	X_n≈1/(1-p) no caso ideal estequiometricamente balanceado	Relaciona conversão funcional a grau de polimerização no modelo de Carothers.	polimerizacao etapas;carothers;conversao	IUPAC
chain_growth_polymerization	materiais_polimeros_superficies	3	Polimerização em cadeia	iniciação→propagação→terminação/transferência	Distingue crescimento por centro ativo de crescimento por etapas.	polimerizacao cadeia;propagacao;radical	IUPAC
copolymer_composition	materiais_polimeros_superficies	4	Composição de copolímeros	F_1 depende de r_1,r_2 e frações instantâneas em modelo Mayo–Lewis	Relaciona razões de reatividade à incorporação de monômeros.	copolimero;mayo lewis;razao reatividade	IUPAC
glass_transition	materiais_polimeros_superficies	3	Transição vítrea	T_g separa regimes vítreo e segmentalmente móvel	Relaciona mobilidade de cadeia e propriedades mecânicas de materiais amorfos.	transicao vitrea;tg;polimero amorfo	IUPAC
polymer_crystallinity	materiais_polimeros_superficies	3	Cristalinidade em polímeros	fração cristalina pode ser estimada por calorimetria ou difração	Conecta ordem parcial a densidade e propriedades térmicas/mecânicas.	cristalinidade;polimero;dsc	IUPAC
rubber_elasticity	materiais_polimeros_superficies	4	Elasticidade da borracha	G≈ν_e RT em rede ideal	Relaciona módulo elástico à densidade de cadeias efetivamente reticuladas.	borracha;elasticidade;reticulacao	IUPAC
surface_tension_chem	materiais_polimeros_superficies	2	Tensão superficial	γ=(∂G/∂A)_{T,P,n}	Define custo de energia livre por área interfacial.	tensao superficial;energia superficie;interface	IUPAC
young_laplace_chem	materiais_polimeros_superficies	3	Pressão de Laplace	ΔP=γ(1/R1+1/R2)	Relaciona curvatura de interface e salto de pressão.	young laplace;curvatura;gota	IUPAC
adsorption_physisorption_chemisorption	materiais_polimeros_superficies	3	Fisissorção e quimissorção	adsorção difere por natureza e força da interação superfície-adsorbato	Distingue ligação fraca/reversível de interação química mais forte.	fisissorcao;quimissorcao;adsorcao	IUPAC
bet_isotherm	materiais_polimeros_superficies	4	Isoterma BET	P/[n(P0-P)] = 1/(n_m C)+(C-1)P/(n_m C P0)	Estima área superficial por adsorção multicamada em faixa adequada.	bet;area superficial;adsorcao multicamada	IUPAC
contact_angle	materiais_polimeros_superficies	3	Ângulo de contato	γ_SV=γ_SL+γ_LV cosθ no modelo de Young	Relaciona molhabilidade a energias interfaciais ideais.	angulo contato;molhabilidade;young	IUPAC
zeta_potential	materiais_polimeros_superficies	4	Potencial zeta	ζ ligado ao potencial eletrocinético na camada de deslizamento	Ajuda a interpretar estabilidade e mobilidade de dispersões coloidais.	potencial zeta;coloide;eletroforese	IUPAC
dlvo_theory	materiais_polimeros_superficies	5	Teoria DLVO	U_total≈U_vdW+U_eletrostática	Modela competição entre atração de van der Waals e repulsão de dupla camada.	dlvo;estabilidade coloidal;dupla camada	IUPAC
nanoparticle_surface_area	materiais_polimeros_superficies	2	Área superficial de nanopartículas	A/V=6/d para esfera	Mostra aumento de superfície específica com redução de tamanho.	nanoparticula;area volume;superficie especifica	PUBCHEM
quantum_confinement	materiais_polimeros_superficies	4	Confinamento quântico em nanomateriais	gap efetivo tende a crescer quando tamanho se aproxima de escalas eletrônicas	Explica dependência de propriedades ópticas com tamanho em pontos quânticos.	confinamento quantico;quantum dot;nanomaterial	MIT_561
semiconductor_bandgap	materiais_polimeros_superficies	3	Band gap de semicondutores	E_g=E_C-E_V	Controla absorção, portadores e comportamento eletrônico.	band gap;semicondutor;ec ev	MIT_5111
intrinsic_carriers	materiais_polimeros_superficies	4	Portadores intrínsecos	n_i≈sqrt(N_CN_V)e^{-E_g/(2kT)}	Relaciona gap e temperatura à densidade de elétrons e lacunas.	portadores intrinsecos;semicondutor;ni	MIT_5111
doping_semiconductors	materiais_polimeros_superficies	3	Dopagem de semicondutores	dopantes deslocam nível de Fermi e densidade de portadores	Cria materiais tipo n ou p por impurezas controladas.	dopagem;tipo n;tipo p	MIT_5111
battery_intercalation_materials	materiais_polimeros_superficies	4	Materiais de intercalação em baterias	x em Host·A_x controla carga redox e composição	Relaciona inserção reversível de íons a armazenamento eletroquímico.	intercalacao;bateria;material eletrodo	PUBCHEM
perovskite_structure	materiais_polimeros_superficies	4	Estrutura perovskita	ABX3 como motivo estrutural idealizado	Relaciona composição e distorções a propriedades funcionais de materiais.	perovskita;abx3;material	MIT_INORG
photopolymerization	materiais_polimeros_superficies	4	Fotopolimerização	fóton inicia ou participa do processo de geração/propagação reativa	Conecta fotoquímica à formação de materiais poliméricos.	fotopolimerizacao;polimero;luz	IUPAC
"""
