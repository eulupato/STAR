"""STAR Chemistry canonical topics 101-125 of 500."""

CHEMISTRY_ROWS_05 = r"""\
ideal_gas_law_chem	estados_materia_solucoes	1	Lei dos gases ideais	PV=nRT	Relaciona pressão, volume, temperatura e quantidade de gás ideal.	gas ideal;pv nrt;equacao de estado	OPENSTAX
gas_density_molar_mass	estados_materia_solucoes	2	Densidade de gases	ρ=PM/(RT)	Combina gás ideal e massa molar para densidade.	densidade gas;massa molar gas;pv nrt	OPENSTAX
dalton_partial_pressures	estados_materia_solucoes	2	Lei de Dalton	P_total=ΣP_i; P_i=x_iP_total	Relaciona composição gasosa a pressões parciais ideais.	dalton;pressao parcial;mistura gasosa	OPENSTAX
graham_effusion	estados_materia_solucoes	2	Lei de Graham	r1/r2=sqrt(M2/M1)	Compara taxas de efusão no regime ideal.	graham;efusao;difusao gasosa	OPENSTAX
kinetic_molecular_theory	estados_materia_solucoes	2	Teoria cinético-molecular	<E_trans>=3RT/2 por mol	Conecta propriedades macroscópicas de gases ao movimento molecular.	teoria cinetica;energia translacional;gases	OPENSTAX
rms_speed	estados_materia_solucoes	2	Velocidade quadrática média	u_rms=sqrt(3RT/M)	Relaciona temperatura e massa molar à escala de velocidades moleculares.	velocidade rms;gas;distribuicao molecular	OPENSTAX
maxwell_boltzmann_speed	estados_materia_solucoes	3	Distribuição de velocidades de Maxwell–Boltzmann	f(v)=4π(M/2πRT)^(3/2)v^2e^(-Mv^2/2RT)	Descreve distribuição de velocidades em gás ideal clássico.	maxwell boltzmann;velocidades;gas	MIT_560
van_der_waals	estados_materia_solucoes	3	Equação de van der Waals	(P+a n^2/V^2)(V-nb)=nRT	Corrige gás ideal por atração e volume molecular efetivo.	van der waals;gas real;a b	MIT_560
compressibility_factor	estados_materia_solucoes	3	Fator de compressibilidade	Z=PV/(nRT)	Quantifica desvio de comportamento ideal.	fator compressibilidade;z;gas real	NIST_WEBBOOK
critical_point	estados_materia_solucoes	3	Ponto crítico	(∂P/∂V)_T=(∂²P/∂V²)_T=0 no modelo vdW	Marca término da coexistência líquido–vapor.	ponto critico;temperatura critica;fluido supercritico	NIST_WEBBOOK
intermolecular_liquid_properties	estados_materia_solucoes	2	Forças intermoleculares e propriedades de líquidos	η,γ,T_b dependem das interações	Relaciona coesão molecular a viscosidade, tensão superficial e ebulição.	forcas intermoleculares;liquidos;viscosidade;tensao superficial	NIST_WEBBOOK
vapor_pressure	estados_materia_solucoes	2	Pressão de vapor	equilíbrio quando μ_l=μ_v	Define pressão do vapor em equilíbrio com fase condensada.	pressao de vapor;equilibrio liquido vapor	NIST_WEBBOOK
clausius_clapeyron	estados_materia_solucoes	3	Equação de Clausius–Clapeyron	ln(P2/P1)=-ΔH_vap/R(1/T2-1/T1)	Aproxima dependência da pressão de vapor com temperatura.	clausius clapeyron;entalpia vaporizacao;pressao vapor	MIT_560
phase_diagram	estados_materia_solucoes	2	Diagramas de fase	linhas de coexistência satisfazem equilíbrio químico entre fases	Mapeia estabilidade de fases em função de temperatura e pressão.	diagrama de fase;ponto triplo;coexistencia	OPENSTAX
crystal_lattices	estados_materia_solucoes	2	Retículos cristalinos	estrutura periódica por vetores de rede	Descreve organização de sólidos cristalinos.	reticulo cristalino;celula unitaria;cristal	OPENSTAX
bragg_law	estados_materia_solucoes	3	Lei de Bragg	nλ=2d sinθ	Relaciona difração de raios X a espaçamento cristalino.	bragg;difracao raios x;cristalografia	OPENSTAX
lattice_energy_born_haber	estados_materia_solucoes	3	Energia reticular e ciclo de Born–Haber	ΔH_f = soma das etapas do ciclo	Usa lei de Hess para relacionar formação iônica e energia reticular.	born haber;energia reticular;ciclo termoquimico	OPENSTAX
solution_process	estados_materia_solucoes	1	Dissolução e solvatação	ΔH_sol=ΔH_separar+ΔH_solvatar	Decompõe energeticamente o processo de formar solução.	dissolucao;solvatacao;entalpia de solucao	OPENSTAX
henry_law	estados_materia_solucoes	2	Lei de Henry	c=k_H P	Relaciona solubilidade diluída de gás à pressão parcial.	henry;solubilidade gas;pressao	IUPAC
raoult_law	estados_materia_solucoes	2	Lei de Raoult	P_i=x_iP_i*	Descreve pressão parcial em solução ideal.	raoult;pressao vapor;solucao ideal	OPENSTAX
colligative_boiling	estados_materia_solucoes	2	Elevação ebuliométrica	ΔT_b=iK_bm	Relaciona concentração efetiva de partículas ao aumento da ebulição.	ebulioscopia;elevacao ponto ebulicao;propriedade coligativa	OPENSTAX
colligative_freezing	estados_materia_solucoes	2	Depressão crioscópica	ΔT_f=iK_fm	Relaciona concentração efetiva à queda do ponto de congelamento.	crioscopia;depressao congelamento;propriedade coligativa	OPENSTAX
osmotic_pressure	estados_materia_solucoes	2	Pressão osmótica	Π=iMRT	Relaciona concentração de soluto à pressão osmótica ideal.	pressao osmotica;osmose;vant hoff	OPENSTAX
activity_coeff_solution	estados_materia_solucoes	4	Atividade em soluções reais	a_i=γ_i c_i/c°	Substitui concentração por atividade termodinâmica em sistemas não ideais.	atividade;coeficiente de atividade;solucao real	IUPAC
colloids_stability	estados_materia_solucoes	3	Coloides e estabilidade	escala coloidal ~1 nm–1 μm	Relaciona dispersão, superfície, carga e agregação em sistemas coloidais.	coloide;dispersao;estabilidade coloidal	IUPAC
"""
