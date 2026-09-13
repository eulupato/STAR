"""STAR Chemistry canonical topics 126-150 of 500."""

CHEMISTRY_ROWS_06 = r"""\
system_surroundings_state	termoquimica_termodinamica	1	Sistema, vizinhança e estado termodinâmico	estado=f(T,P,V,n_i,...)	Define fronteiras e variáveis de estado antes de qualquer balanço energético.	sistema termodinamico;vizinhanca;estado	OPENSTAX
heat_work_signs	termoquimica_termodinamica	1	Calor, trabalho e convenções de sinal	ΔU=q+w (convenção química)	Distingue transferência de energia por calor e trabalho.	calor;trabalho;convencao de sinal	OPENSTAX
first_law_chem	termoquimica_termodinamica	1	Primeira lei da termodinâmica	ΔU=q+w	Expressa conservação de energia para sistemas fechados.	primeira lei;energia interna;q w	OPENSTAX
pressure_volume_work	termoquimica_termodinamica	2	Trabalho pressão-volume	w=-∫P_ext dV	Calcula trabalho de expansão ou compressão sob pressão externa.	trabalho pv;expansao;compressao	MIT_560
enthalpy	termoquimica_termodinamica	1	Entalpia	H=U+PV; q_p=ΔH em condições apropriadas	Conveniente para processos a pressão constante.	entalpia;delta h;pressao constante	OPENSTAX
calorimetry	termoquimica_termodinamica	1	Calorimetria	q=mcΔT; q_rxn=-q_cal	Extrai calor de processo a partir de resposta térmica medida.	calorimetria;calor especifico;capacidade calorifica	OPENSTAX
heat_capacity	termoquimica_termodinamica	2	Capacidade calorífica	C=dq/dT; C_p=(∂H/∂T)_P	Relaciona energia necessária à variação de temperatura.	capacidade calorifica;cp;cv	NIST_WEBBOOK
hess_law	termoquimica_termodinamica	1	Lei de Hess	ΔH_total=ΣΔH_etapas	Explora caráter de função de estado da entalpia.	lei de hess;entalpia de reacao;ciclo	OPENSTAX
standard_enthalpy_formation	termoquimica_termodinamica	2	Entalpia padrão de formação	Δ_rH°=Σν_iΔ_fH_i°	Calcula entalpia de reação a partir de dados de formação.	entalpia formacao;delta hf;termoquimica	NIST_WEBBOOK
bond_enthalpy_estimates	termoquimica_termodinamica	2	Entalpias de ligação e estimativas	ΔH_rxn≈ΣD(quebradas)-ΣD(formadas)	Estima energeticamente reações gasosas a partir de energias médias de ligação.	entalpia de ligacao;energia de dissociacao;estimativa	NIST_WEBBOOK
kirchhoff_law_thermochem	termoquimica_termodinamica	3	Lei de Kirchhoff termoquímica	d(ΔH)/dT=ΔC_p	Corrige entalpias de reação entre temperaturas quando capacidades caloríficas são conhecidas.	lei de kirchhoff;delta cp;entalpia temperatura	MIT_560
entropy	termoquimica_termodinamica	2	Entropia	dS=δq_rev/T	Quantifica dispersão de energia e irreversibilidade por caminhos reversíveis.	entropia;segunda lei;ds	OPENSTAX
second_law	termoquimica_termodinamica	2	Segunda lei da termodinâmica	ΔS_univ≥0	Fornece critério de espontaneidade para processo total.	segunda lei;entropia universo;espontaneidade	OPENSTAX
third_law	termoquimica_termodinamica	3	Terceira lei da termodinâmica	S→0 para cristal perfeito em T→0 K	Estabelece referência para entropias absolutas de substâncias cristalinas ideais.	terceira lei;entropia absoluta;zero kelvin	MIT_560
gibbs_free_energy	termoquimica_termodinamica	2	Energia livre de Gibbs	G=H-TS; ΔG=ΔH-TΔS	Combina entalpia e entropia para processos a T e P constantes.	gibbs;energia livre;delta g	OPENSTAX
helmholtz_free_energy	termoquimica_termodinamica	4	Energia livre de Helmholtz	A=U-TS	Fornece potencial útil a temperatura e volume constantes.	helmholtz;energia livre a;funcao de helmholtz	MIT_560
fundamental_thermo_equation	termoquimica_termodinamica	4	Equação fundamental termodinâmica	dU=TdS-PdV+Σμ_i dn_i	Une calor, trabalho e composição em forma diferencial.	equacao fundamental;du;potencial quimico	MIT_560
chemical_potential	termoquimica_termodinamica	4	Potencial químico	μ_i=(∂G/∂n_i)_{T,P,n_j}	Mede variação de Gibbs com composição e governa equilíbrio material.	potencial quimico;mu;componente	MIT_560
gibbs_duhem	termoquimica_termodinamica	5	Equação de Gibbs–Duhem	Σn_i dμ_i=-S dT+V dP	Impõe dependência entre potenciais químicos de componentes.	gibbs duhem;potenciais quimicos;mistura	MIT_560
maxwell_relations	termoquimica_termodinamica	5	Relações de Maxwell	(∂T/∂V)_S=-(∂P/∂S)_V entre relações equivalentes	Deriva identidades termodinâmicas de diferenciais exatos dos potenciais.	relacoes de maxwell;termodinamica;derivadas parciais	MIT_560
gibbs_helmholtz	termoquimica_termodinamica	4	Equação de Gibbs–Helmholtz	(∂(G/T)/∂T)_P=-H/T^2	Relaciona dependência térmica de Gibbs e entalpia.	gibbs helmholtz;delta g temperatura	MIT_560
phase_rule	termoquimica_termodinamica	3	Regra das fases de Gibbs	F=C-P+2	Conta graus de liberdade intensivos em equilíbrio de fases não reativo.	regra das fases;gibbs;graus de liberdade	IUPAC
fugacity	termoquimica_termodinamica	5	Fugacidade	μ=μ°+RT ln(f/f°)	Generaliza pressão efetiva para gases reais e fases.	fugacidade;gas real;potencial quimico	IUPAC
partial_molar_quantities	termoquimica_termodinamica	4	Grandezas molares parciais	X̄_i=(∂X/∂n_i)_{T,P,n_j}	Descreve contribuição diferencial de cada componente a propriedade extensiva.	volume molar parcial;grandeza molar parcial	MIT_560
excess_properties	termoquimica_termodinamica	5	Propriedades de excesso	X^E=X_real-X_ideal	Quantifica desvio de misturas reais em relação ao estado ideal de referência.	propriedade de excesso;mistura real;nao idealidade	IUPAC
"""
