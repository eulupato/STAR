"""STAR Chemistry canonical topics 226-250 of 500."""

CHEMISTRY_ROWS_10 = r"""\
oxidation_reduction	eletroquimica	1	Oxidação e redução	oxidação perde e-; redução ganha e-	Organiza transferência eletrônica por semirreações.	oxidacao;reducao;redox	OPENSTAX
galvanic_cell	eletroquimica	1	Célula galvânica	E_cell=E_cátodo-E_ânodo	Converte reação redox espontânea em trabalho elétrico.	celula galvanica;pilha;anodo catodo	OPENSTAX
electrolytic_cell	eletroquimica	2	Célula eletrolítica	fonte externa força ΔG>0	Usa energia elétrica para dirigir reação não espontânea.	celula eletrolitica;eletrolise;fonte externa	OPENSTAX
cell_notation	eletroquimica	1	Notação de célula eletroquímica	ânodo | solução || solução | cátodo	Representa fases e junções de uma célula.	notacao celula;ponte salina;linha dupla	OPENSTAX
standard_electrode_potential	eletroquimica	2	Potencial padrão de eletrodo	E° definido relativamente ao eletrodo padrão de hidrogênio	Compara tendência redox sob estados padrão.	potencial padrao;eletrodo;seh	OPENSTAX
standard_cell_potential	eletroquimica	2	Potencial padrão de célula	E°_cell=E°_cátodo-E°_ânodo	Combina potenciais de redução sem multiplicá-los por coeficientes.	potencial de celula;ecell;redox	OPENSTAX
nernst_equation	eletroquimica	2	Equação de Nernst	E=E°-(RT/nF)ln Q	Corrige potencial por composição e temperatura.	nernst;potencial;quociente reacao	OPENSTAX
delta_g_electrochem	eletroquimica	2	Energia livre e potencial elétrico	ΔG=-nFE	Liga trabalho elétrico máximo e espontaneidade redox.	delta g;nfe;energia livre eletroquimica	OPENSTAX
equilibrium_cell_potential	eletroquimica	3	Potencial e constante de equilíbrio	lnK=nFE°/(RT)	Relaciona força eletromotriz padrão à posição de equilíbrio.	k equilibrio;potencial padrao;nfe	OPENSTAX
faraday_laws_electrolysis	eletroquimica	2	Leis de Faraday da eletrólise	n_e=Q/F=It/F	Relaciona carga elétrica à quantidade de transformação redox.	faraday;eletrolise;carga corrente tempo	OPENSTAX
electrolysis_mass	eletroquimica	2	Massa depositada por eletrólise	m=ItM/(nF)	Calcula massa ideal de produto eletrolítico pela carga transferida.	massa eletrolise;deposicao;faraday	OPENSTAX
concentration_cell	eletroquimica	3	Célula de concentração	E=(RT/nF)ln(a_alta/a_baixa) em caso simples	Gera potencial a partir de diferença de atividade da mesma espécie.	celula concentracao;gradiente;nernst	OPENSTAX
reference_electrodes	eletroquimica	3	Eletrodos de referência	E_ref estável e conhecido	Fornece escala reprodutível para potenciais de eletrodo.	eletrodo referencia;ag agcl;calomelano	LIBRE_ANALYTICAL
indicator_electrode	eletroquimica	3	Eletrodos indicadores	E responde à atividade do analito	Converte atividade iônica ou redox em sinal potenciométrico.	eletrodo indicador;potenciometria;ion seletivo	LIBRE_ANALYTICAL
ion_selective_electrode	eletroquimica	3	Eletrodo íon-seletivo	E=const+(RT/zF)ln a_i em resposta ideal	Permite determinação potenciométrica seletiva de íons.	ise;eletrodo ion seletivo;potenciometria	LIBRE_ANALYTICAL
conductivity	eletroquimica	2	Condutividade eletrolítica	κ=G K_cell	Relaciona condutância medida à geometria da célula e solução.	condutividade;condutancia;celula condutometrica	LIBRE_ANALYTICAL
molar_conductivity	eletroquimica	3	Condutividade molar	Λ_m=κ/c	Normaliza condutividade pela concentração de eletrólito.	condutividade molar;lambda m;eletrólito	IUPAC
kohlrausch_law	eletroquimica	4	Lei de Kohlrausch	Λ_m≈Λ_m°-K√c para eletrólitos fortes diluídos	Descreve dependência aproximada da condutividade molar em baixa concentração.	kohlrausch;condutividade limite;eletrólito forte	IUPAC
battery_capacity	eletroquimica	2	Capacidade eletroquímica	Q=It; capacidade específica=Q/m	Quantifica carga armazenável por célula ou material ativo.	capacidade bateria;mah;carga especifica	PUBCHEM
fuel_cell_thermo	eletroquimica	3	Termodinâmica de célula a combustível	E_rev=-ΔG/(nF)	Converte energia livre química diretamente em potencial reversível.	celula combustivel;fuel cell;delta g	OPENSTAX
corrosion_electrochem	eletroquimica	3	Corrosão eletroquímica	reações anódica e catódica acopladas fecham balanço eletrônico	Modela degradação metálica como células locais.	corrosao;potencial misto;metal	OPENSTAX
pourbaix_diagram	eletroquimica	4	Diagramas de Pourbaix	fronteiras E-pH derivadas de Nernst	Mapeiam estabilidade termodinâmica de espécies aquosas, sólidos e gases.	pourbaix;eh ph;diagrama potencial ph	IUPAC
butler_volmer	eletroquimica	5	Equação de Butler–Volmer	i=i0[exp(αnFη/RT)-exp(-(1-α)nFη/RT)]	Relaciona sobrepotencial e corrente de transferência de carga.	butler volmer;sobrepotencial;corrente troca	IUPAC
tafel_equation	eletroquimica	4	Equação de Tafel	η=a+b log10|i| em regime de alta polarização	Aproxima cinética de eletrodo em domínio dominado por um termo exponencial.	tafel;sobrepotencial;polarizacao	IUPAC
cyclic_voltammetry	eletroquimica	4	Voltametria cíclica	i_p∝n^{3/2}AD^{1/2}Cν^{1/2} para reversível ideal	Relaciona resposta corrente-potencial a transporte e cinética redox.	voltametria ciclica;cv;randles sevcik	LIBRE_ANALYTICAL
"""
