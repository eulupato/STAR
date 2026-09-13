"""STAR Chemistry canonical topics 251-275 of 500."""

CHEMISTRY_ROWS_11 = r"""\
analytical_process	quimica_analitica	1	Processo analítico	amostragem→preparo→medição→calibração→inferência	Organiza etapas que conectam amostra real a resultado reportável.	processo analitico;amostragem;medicao	LIBRE_ANALYTICAL
sampling_error	quimica_analitica	2	Erro de amostragem	s_total^2≈s_sampling^2+s_analysis^2	Separa variabilidade introduzida antes e durante a medição.	erro amostragem;representatividade;variancia	LIBRE_ANALYTICAL
calibration_curve	quimica_analitica	2	Curva de calibração	y=a+bx	Relaciona sinal instrumental a concentração por modelo calibrado.	curva calibracao;reta;concentracao sinal	LIBRE_ANALYTICAL
linear_regression	quimica_analitica	3	Regressão linear em calibração	b=Σ(x-x̄)(y-ȳ)/Σ(x-x̄)^2	Estima sensibilidade e intercepto a partir de pares padrão-sinal.	regressao linear;coeficiente angular;calibracao	LIBRE_ANALYTICAL
standard_addition	quimica_analitica	3	Adição de padrão	sinal cresce com adições conhecidas ao mesmo matriz	Compensa efeitos de matriz por extrapolação.	adicao padrao;efeito matriz;calibracao	LIBRE_ANALYTICAL
internal_standard	quimica_analitica	3	Padrão interno	R=S_analito/S_padrão	Normaliza flutuações de injeção, preparo ou resposta instrumental.	padrao interno;razao sinal;calibracao	LIBRE_ANALYTICAL
limit_detection	quimica_analitica	3	Limite de detecção	LOD≈3σ_blank/m em convenção comum	Estima menor nível distinguível do ruído sob hipótese estatística.	limite deteccao;lod;ruido	IUPAC
limit_quantification	quimica_analitica	3	Limite de quantificação	LOQ≈10σ_blank/m em convenção comum	Define nível baixo com desempenho quantitativo aceitável.	limite quantificacao;loq;sensibilidade	IUPAC
sensitivity_selectivity	quimica_analitica	2	Sensibilidade e seletividade	sensibilidade≈dS/dc	Distingue mudança de sinal por concentração da capacidade de discriminar interferentes.	sensibilidade;seletividade;interferente	IUPAC
precision_repeatability	quimica_analitica	2	Repetibilidade e precisão	RSD=100 s/x̄	Resume dispersão relativa de replicatas sob condições definidas.	rsd;desvio padrao relativo;repetibilidade	IUPAC
confidence_interval_mean	quimica_analitica	3	Intervalo de confiança da média	x̄±t s/√n	Quantifica incerteza estatística da média com distribuição t.	intervalo confianca;t student;media	LIBRE_ANALYTICAL
grubbs_outlier	quimica_analitica	4	Detecção de valor discrepante	G=max|x_i-x̄|/s	Testa um outlier candidato sob hipóteses específicas; não substitui investigação causal.	grubbs;outlier;valor discrepante	LIBRE_ANALYTICAL
propagation_uncertainty_analytical	quimica_analitica	3	Propagação de incerteza analítica	u_f^2≈Σ(∂f/∂x_i)^2u_i^2+covariâncias	Combina contribuições de entrada ao resultado calculado.	propagacao incerteza;incerteza combinada;covariancia	IUPAC
titration_equivalence_endpoint	quimica_analitica	2	Ponto de equivalência e ponto final	erro de titulação = V_final-V_equiv	Distingue condição estequiométrica do evento experimental detectado.	equivalencia;ponto final;erro titulacao	LIBRE_ANALYTICAL
gravimetric_analysis	quimica_analitica	2	Análise gravimétrica	m_analito=m_precipitado×fator gravimétrico	Determina quantidade por conversão a forma de massa conhecida.	gravimetria;fator gravimetrico;precipitado	LIBRE_ANALYTICAL
complexometric_titration	quimica_analitica	3	Titulação complexométrica	M+Y⇌MY; K_f e K_f' governam equilíbrio	Quantifica metais usando ligantes complexantes e constantes condicionais.	complexometria;edta;titulacao metal	LIBRE_ANALYTICAL
redox_titration	quimica_analitica	3	Titulação redox	equivalência por balanço de elétrons	Determina analito a partir de reação de transferência eletrônica estequiométrica.	titulacao redox;permanganato;iodometria	LIBRE_ANALYTICAL
precipitation_titration	quimica_analitica	3	Titulação por precipitação	Q_sp≈K_sp no limiar de precipitação	Usa formação de sólido pouco solúvel para quantificação.	titulacao precipitacao;argentometria;ksp	LIBRE_ANALYTICAL
solvent_extraction	quimica_analitica	3	Extração líquido–líquido	D=C_org/C_aq; fração extraída depende de D e volumes	Separa analitos por partição entre fases imiscíveis.	extracao liquido liquido;coeficiente distribuicao;particao	LIBRE_ANALYTICAL
multiple_extractions	quimica_analitica	3	Extrações múltiplas	fração remanescente=[V_aq/(V_aq+D V_org)]^n	Mostra por que várias extrações menores podem superar uma única de mesmo volume total.	extracoes multiplas;particao;fracao extraida	LIBRE_ANALYTICAL
chromatography_retention	quimica_analitica	2	Retenção cromatográfica	k'=(t_R-t_M)/t_M	Quantifica retenção ajustada ao tempo morto.	cromatografia;fator retencao;k linha	LIBRE_ANALYTICAL
chromatography_resolution	quimica_analitica	3	Resolução cromatográfica	R_s=2(t_R2-t_R1)/(w_1+w_2)	Quantifica separação entre picos adjacentes.	resolucao cromatografica;rs;picos	LIBRE_ANALYTICAL
plate_number_chromatography	quimica_analitica	3	Número de pratos teóricos	N=16(t_R/w)^2 em aproximação gaussiana	Resume eficiência de coluna por alargamento de banda.	pratos teoricos;eficiencia coluna;cromatografia	LIBRE_ANALYTICAL
van_deemter	quimica_analitica	4	Equação de van Deemter	H=A+B/u+Cu	Decompõe altura equivalente a prato em dispersão, difusão longitudinal e transferência de massa.	van deemter;altura prato;velocidade linear	LIBRE_ANALYTICAL
mass_spectrometry_quant	quimica_analitica	4	Quantificação por espectrometria de massas	resposta≈f(concentração,ionização,transmissão)	Enfatiza necessidade de calibração e padrão interno para converter intensidade em quantidade.	espectrometria massas;quantificacao;padrao interno	NIST_WEBBOOK
"""
