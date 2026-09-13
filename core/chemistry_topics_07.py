"""STAR Chemistry canonical topics 151-175 of 500."""

CHEMISTRY_ROWS_07 = r"""\
dynamic_equilibrium	equilibrio_quimico	1	Equilíbrio químico dinâmico	v_direta=v_reversa no equilíbrio	Descreve estado macroscópico estacionário com processos microscópicos opostos.	equilibrio dinamico;reacao reversivel	OPENSTAX
equilibrium_constant_kc	equilibrio_quimico	2	Constante de equilíbrio Kc	K_c=Π(c_i/c°)^{ν_i}	Relaciona atividades aproximadas por concentrações em equilíbrios ideais/diluídos.	kc;constante de equilibrio;lei da acao das massas	OPENSTAX
equilibrium_constant_kp	equilibrio_quimico	2	Constante de equilíbrio Kp	K_p=Π(P_i/P°)^{ν_i}	Expressa equilíbrio gasoso com pressões parciais.	kp;equilibrio gasoso;pressao parcial	OPENSTAX
reaction_quotient	equilibrio_quimico	2	Quociente de reação	Q=Πa_i^{ν_i}	Compara composição instantânea com condição de equilíbrio.	quociente de reacao;q;equilibrio	OPENSTAX
q_vs_k	equilibrio_quimico	1	Comparação Q e K	Q<K avança direto; Q>K favorece reverso	Prediz sentido de relaxação sem calcular velocidade.	q e k;sentido reacao;equilibrio	OPENSTAX
delta_g_and_q	equilibrio_quimico	3	Energia livre e quociente de reação	Δ_rG=Δ_rG°+RT ln Q	Relaciona força motriz termodinâmica à composição.	delta g;quociente;forca motriz	MIT_560
delta_g_k	equilibrio_quimico	3	Energia livre padrão e K	Δ_rG°=-RT ln K	Conecta posição de equilíbrio a energia livre padrão.	delta g padrao;constante equilibrio;ln k	OPENSTAX
le_chatelier	equilibrio_quimico	1	Princípio de Le Châtelier	perturbação desloca o estado de equilíbrio conforme resposta do sistema	Organiza efeitos qualitativos de concentração, pressão e temperatura.	le chatelier;deslocamento equilibrio	OPENSTAX
equilibrium_ice_tables	equilibrio_quimico	2	Tabelas ICE	inicial + mudança = equilíbrio	Estrutura cálculos algébricos de composição no equilíbrio.	tabela ice;equilibrio;concentracao	OPENSTAX
equilibrium_approximation	equilibrio_quimico	3	Aproximações em cálculos de equilíbrio	x≪C somente se verificado a posteriori	Simplifica equações quando a mudança é pequena sem abandonar checagem de validade.	aproximacao equilibrio;cinco por cento;ice	OPENSTAX
vant_hoff_equilibrium	equilibrio_quimico	3	Equação de van ’t Hoff	d lnK/dT=ΔH°/(RT^2)	Relaciona dependência térmica da constante de equilíbrio à entalpia.	vant hoff;temperatura;constante equilibrio	MIT_560
pressure_effect_equilibrium	equilibrio_quimico	2	Pressão e equilíbrio gasoso	K não muda com pressão a T fixa; composição pode mudar	Distingue constante termodinâmica de deslocamento composicional.	pressao equilibrio;gas;le chatelier	OPENSTAX
inert_gas_equilibrium	equilibrio_quimico	3	Gás inerte e equilíbrio	a T,V fixos, adicionar inerte não altera P_i dos reagentes ideais	Evita aplicação indevida de Le Châtelier.	gas inerte;equilibrio;pressao parcial	MIT_560
coupled_equilibria	equilibrio_quimico	3	Equilíbrios acoplados	K_global=ΠK_j para combinação de reações	Combina reações e constantes de modo termodinamicamente consistente.	equilibrios acoplados;produto de k;reacoes somadas	OPENSTAX
heterogeneous_equilibrium	equilibrio_quimico	2	Equilíbrio heterogêneo	atividade de fase pura≈1 no estado padrão	Remove fases puras da expressão explícita de K quando apropriado.	equilibrio heterogeneo;solido puro;atividade	OPENSTAX
phase_equilibrium_mu	equilibrio_quimico	4	Equilíbrio de fases e potencial químico	μ_i^α=μ_i^β	Define coexistência pela igualdade de potenciais químicos.	equilibrio de fases;potencial quimico;coexistencia	MIT_560
clapeyron_equation	equilibrio_quimico	4	Equação de Clapeyron	dP/dT=ΔS/ΔV=ΔH/(TΔV)	Dá inclinação de curva de coexistência entre fases.	clapeyron;coexistencia;diagrama fase	MIT_560
binary_phase_lever_rule	equilibrio_quimico	3	Regra da alavanca	fração_α=(z-x_β)/(x_α-x_β)	Obtém frações de fase em regiões bifásicas de diagramas binários.	regra da alavanca;diagrama binario;fracao de fase	OPENSTAX
azeotrope	equilibrio_quimico	4	Azeótropos	x_i=y_i no ponto azeotrópico	Identifica composição onde líquido e vapor têm mesma composição.	azeotropo;destilacao;equilibrio liquido vapor	IUPAC
ideal_solution_gibbs_mix	equilibrio_quimico	4	Mistura ideal e Gibbs de mistura	ΔG_mix=RTΣn_i ln x_i	Quantifica ganho entrópico de mistura ideal.	gibbs mistura;solucao ideal;entropia mistura	MIT_560
regular_solution	equilibrio_quimico	5	Modelo de solução regular	ΔG_mix=RTΣn_i ln x_i + termo entálpico	Introduz não idealidade entálpica preservando entropia combinatória ideal.	solucao regular;parametro interacao;mistura	MIT_560
liquid_liquid_equilibrium	equilibrio_quimico	4	Equilíbrio líquido–líquido	μ_i^α=μ_i^β para todos os componentes	Descreve separação em duas fases líquidas imiscíveis ou parcialmente miscíveis.	equilibrio liquido liquido;l l e;binodal	MIT_560
distribution_coefficient	equilibrio_quimico	3	Coeficiente de distribuição	K_D=c_org/c_aq em regime definido	Quantifica partição de soluto entre fases imiscíveis.	coeficiente distribuicao;particao;extracao	LIBRE_ANALYTICAL
complexation_equilibrium	equilibrio_quimico	3	Equilíbrio de complexação	β_n=[ML_n]/([M][L]^n) em forma aproximada	Relaciona formação de complexos a constantes cumulativas.	complexacao;constante de formacao;beta	OPENSTAX
conditional_equilibrium_constants	equilibrio_quimico	5	Constantes condicionais de equilíbrio	K'=K×fatores de distribuição das formas reativas	Incorpora protonação e reações laterais a cálculos analíticos.	constante condicional;equilibrio analitico;reacoes laterais	LIBRE_ANALYTICAL
"""
