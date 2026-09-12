"""100 tópicos adicionais para o catálogo de Física da STAR.

Cada linha segue o formato TSV:
id, domínio, nível, título, fórmula, síntese, aliases, fonte.

Este módulo adiciona 100 tópicos canônicos; o PhysicsKnowledgeEngine transforma
cada tópico em 1.000 variações determinísticas, somando +100.000 conteúdos.
"""

EXTENDED_SOURCES = {
    "MIT_ADV": "MIT OpenCourseWare advanced physics references",
    "LIGO": "LIGO Scientific Collaboration gravitational-wave science",
    "IAEA": "IAEA nuclear physics, reactor physics and fusion references",
    "PDG": "Particle Data Group, Review of Particle Physics 2026",
    "CERN": "CERN particle-physics and Standard Model references",
    "NASA": "NASA Physics of the Cosmos",
    "NIST": "NIST/CODATA 2022 Fundamental Physical Constants",
    "OPENSTAX": "OpenStax University Physics Volumes 1-3",
}

EXTENDED_ROWS = r"""
kinematic_vectors	cinematica	1	Vetores cinemáticos	v=dr/dt; a=dv/dt	Velocidade e aceleração são derivadas vetoriais da posição no tempo.	vetor velocidade;vetor aceleracao;movimento vetorial	OPENSTAX
relative_motion	cinematica	2	Movimento relativo	v_A/B=v_A-v_B	Velocidades relativas conectam observadores clássicos em referenciais não relativísticos.	velocidade relativa;referencial;galileu	OPENSTAX
circular_motion	cinematica	2	Movimento circular	v=ωr; a_c=v^2/r=ω^2r	Movimento curvo exige aceleração centrípeta dirigida para o centro de curvatura.	movimento circular;aceleracao centripeta;omega	OPENSTAX
noninertial_frames	dinamica	3	Referenciais não inerciais	F_inercial=-ma_ref	Referenciais acelerados exigem forças inerciais efetivas para preservar a forma newtoniana.	forca ficticia;referencial acelerado;nao inercial	MIT_ADV
coriolis	rotacao	3	Força de Coriolis	F_C=-2m Ω×v_rel	Em referenciais rotativos surge uma força aparente perpendicular à rotação e à velocidade relativa.	coriolis;rotacao terrestre;forca aparente	MIT_ADV
centrifugal	rotacao	3	Força centrífuga	F_cf=-m Ω×(Ω×r)	É a força inercial radial observada em um referencial em rotação uniforme.	centrifuga;referencial rotativo;forca inercial	MIT_ADV
rigid_body_inertia	rotacao	3	Tensor de inércia	L=I·ω; T=(1/2)ω·I·ω	A rotação tridimensional de corpos rígidos é governada pelo tensor de inércia.	tensor de inercia;corpo rigido;eixos principais	MIT_ADV
euler_rigid_body	rotacao	4	Equações de Euler para corpo rígido	I dω/dt+ω×(Iω)=τ	Descrevem a dinâmica rotacional em eixos ligados ao corpo.	equacoes de euler;precessao;corpo rigido	MIT_ADV
gyroscope_precession	rotacao	3	Precessão giroscópica	Ω_p≈τ/L	Torque perpendicular ao momento angular produz precessão do eixo de rotação.	giroscopio;precessao;momento angular	OPENSTAX
lagrangian_mechanics	mecanica_analitica	4	Mecânica Lagrangiana	d/dt(∂L/∂qdot_i)-∂L/∂q_i=0	A dinâmica pode ser escrita por coordenadas generalizadas e princípio de ação estacionária.	lagrangiana;coordenadas generalizadas;acao	MIT_ADV
hamiltonian_mechanics	mecanica_analitica	4	Mecânica Hamiltoniana	qdot_i=∂H/∂p_i; pdot_i=-∂H/∂q_i	Reformula a dinâmica no espaço de fase por pares canônicos posição-momento.	hamiltoniana;espaco de fase;equacoes canonicas	MIT_ADV
poisson_brackets	mecanica_analitica	5	Parênteses de Poisson	{A,B}=Σ_i(∂A/∂q_i ∂B/∂p_i-∂A/∂p_i ∂B/∂q_i)	Codificam a estrutura simplética da mecânica clássica e a evolução de observáveis.	poisson;estrutura simpletica;observaveis	MIT_ADV
noether_theorem	mecanica_analitica	5	Teorema de Noether	δS=0 sob simetria contínua ⇒ corrente conservada	Simetrias contínuas da ação correspondem a leis de conservação.	noether;simetria;conservacao	MIT_ADV
central_force_effective	mecanica_analitica	4	Potencial efetivo central	U_eff(r)=U(r)+L^2/(2mr^2)	Reduz problemas de força central a movimento radial unidimensional com barreira centrífuga.	potencial efetivo;forca central;orbita	MIT_ADV
virial_theorem	mecanica_analitica	4	Teorema do virial	2⟨T⟩=⟨r·∇U⟩	Relaciona médias temporais de energia cinética e potencial em sistemas ligados.	teorema do virial;sistema ligado;energia media	MIT_ADV
escape_velocity	gravitacao	2	Velocidade de escape	v_esc=sqrt(2GM/r)	É a velocidade mínima ideal para alcançar o infinito com energia mecânica final nula.	velocidade de escape;gravidade;energia orbital	OPENSTAX
roche_limit	astrofisica	4	Limite de Roche	d≈2.44 R_M(ρ_M/ρ_m)^(1/3)	Estima a distância em que forças de maré podem superar a autogravidade de um corpo fluido.	limite de roche;forca de mare;satelite	NASA
lagrange_points	gravitacao	4	Pontos de Lagrange	∇U_eff=0 no problema restrito de três corpos	São posições de equilíbrio no referencial rotativo do problema restrito de três corpos.	pontos de lagrange;tres corpos;orbita	NASA
three_body_problem	caos	5	Problema de três corpos	m_i rddot_i=Σ_{j≠i}Gm_im_j(r_j-r_i)/abs(r_j-r_i)^3	Sistemas gravitacionais de três corpos geralmente não têm solução fechada geral e podem ser caóticos.	problema de tres corpos;caos gravitacional;n corpos	MIT_ADV
normal_modes	oscilacoes	3	Modos normais	K a=ω^2 M a	Osciladores acoplados podem ser decompostos em modos coletivos independentes.	modos normais;osciladores acoplados;autovalores	MIT_ADV
fourier_series	ondas	3	Série de Fourier	f(x)=a0/2+Σ_n[a_n cos(nx)+b_n sin(nx)]	Funções periódicas podem ser decompostas em componentes harmônicas.	fourier;harmonicos;serie trigonometrica	MIT_ADV
fourier_transform	ondas	4	Transformada de Fourier	F(k)=∫f(x)e^{-ikx}dx	Conecta representações em espaço real e espaço de frequências ou números de onda.	transformada de fourier;espectro;espaco k	MIT_ADV
group_phase_velocity	ondas	4	Velocidades de fase e grupo	v_p=ω/k; v_g=dω/dk	Dispersão separa velocidade de cristas da velocidade de envelopes de pacotes de onda.	velocidade de grupo;velocidade de fase;dispersao	MIT_ADV
wave_packets	ondas	4	Pacotes de onda	ψ(x,t)=∫A(k)e^{i(kx-ωt)}dk	Superposição de ondas forma pacotes localizados cuja evolução depende da relação de dispersão.	pacote de onda;superposicao;dispersao	MIT_ADV
acoustic_impedance	ondas	3	Impedância acústica	Z=ρc	Liga pressão e velocidade de partícula em ondas acústicas planas e controla reflexão em interfaces.	impedancia acustica;som;reflexao	OPENSTAX
navier_stokes	fluidos	5	Equações de Navier-Stokes	ρ(∂v/∂t+v·∇v)=-∇p+μ∇^2v+f	Descrevem conservação de momento em fluidos newtonianos viscosos.	navier stokes;fluido viscoso;hidrodinamica	MIT_ADV
reynolds_number	fluidos	3	Número de Reynolds	Re=ρvL/μ	Compara efeitos inerciais e viscosos e ajuda a classificar regimes de escoamento.	reynolds;laminar;turbulento	OPENSTAX
poiseuille	fluidos	3	Lei de Poiseuille	Q=πΔP r^4/(8μL)	Descreve vazão laminar de fluido newtoniano em tubo cilíndrico longo.	poiseuille;fluxo laminar;viscosidade	OPENSTAX
surface_tension	fluidos	2	Tensão superficial	ΔP=γ(1/R1+1/R2)	A equação de Young-Laplace relaciona curvatura de interface à diferença de pressão.	tensao superficial;young laplace;capilaridade	OPENSTAX
heat_equation	termodinamica	3	Equação do calor	∂T/∂t=α∇^2T	Modela difusão térmica em meios contínuos sob hipóteses lineares usuais.	equacao do calor;difusao termica;condutividade	MIT_ADV
fourier_heat_law	termodinamica	2	Lei de Fourier da condução	q=-k∇T	O fluxo de calor por condução aponta no sentido de temperatura decrescente.	conducao termica;fluxo de calor;gradiente	OPENSTAX
blackbody_planck	termodinamica_quantica	4	Lei de Planck	B_ν(T)=2hν^3/c^2 /(e^{hν/(k_BT)}-1)	Descreve o espectro de radiação térmica de um corpo negro em equilíbrio.	planck;corpo negro;radiacao termica	NASA
wien_law	termodinamica	2	Lei de deslocamento de Wien	λ_max T=b	O pico espectral de um corpo negro desloca-se inversamente com a temperatura.	wien;temperatura;corpo negro	OPENSTAX
stefan_boltzmann	termodinamica	2	Lei de Stefan-Boltzmann	j*=σT^4	A potência radiada por unidade de área de um corpo negro cresce com a quarta potência da temperatura.	stefan boltzmann;radiacao;potencia termica	OPENSTAX
chemical_potential	mecanica_estatistica	4	Potencial químico	dU=TdS-PdV+μdN	O potencial químico mede a variação energética associada à troca de partículas.	potencial quimico;grande canonico;particulas	MIT_ADV
maxwell_boltzmann	mecanica_estatistica	3	Distribuição de Maxwell-Boltzmann	f(v)∝v^2 exp[-mv^2/(2k_BT)]	Descreve velocidades de partículas clássicas não degeneradas em equilíbrio térmico.	maxwell boltzmann;distribuicao de velocidades;gas	MIT_ADV
bose_einstein	mecanica_estatistica	5	Distribuição de Bose-Einstein	nbar=1/(e^{β(E-μ)}-1)	Ocupa estados bosônicos em equilíbrio e permite condensação quando condições apropriadas são satisfeitas.	bose einstein;bosons;condensado	MIT_ADV
fermi_dirac	mecanica_estatistica	5	Distribuição de Fermi-Dirac	nbar=1/(e^{β(E-μ)}+1)	Férmions obedecem exclusão de Pauli e preenchem estados segundo esta distribuição.	fermi dirac;fermions;pauli	MIT_ADV
phase_transitions	mecanica_estatistica	5	Transições de fase e parâmetro de ordem	ξ∼abs(t)^(-ν); M∼(-t)^β	Perto de pontos críticos surgem leis de escala, comprimentos de correlação e expoentes críticos.	transicao de fase;expoente critico;parametro de ordem	MIT_ADV
ising_model	mecanica_estatistica	5	Modelo de Ising	H=-JΣ_<ij>s_i s_j-hΣ_i s_i	É um modelo fundamental de spins que exibe magnetização coletiva e transições de fase.	ising;spin;ferromagnetismo	MIT_ADV
renormalization_group	mecanica_estatistica	5	Grupo de renormalização	g'=R_b(g)	Estuda como parâmetros efetivos mudam com a escala e explica universalidade crítica.	grupo de renormalizacao;escala;universalidade	MIT_ADV
electric_potential	eletrostatica	2	Potencial elétrico	E=-∇V; V(r)=-∫E·dl	Campos eletrostáticos conservativos podem ser descritos por um potencial escalar.	potencial eletrico;campo eletrico;voltagem	OPENSTAX
poisson_laplace	eletrostatica	4	Equações de Poisson e Laplace	∇^2V=-ρ/ε0; ∇^2V=0	Relacionam potenciais eletrostáticos a distribuições de carga e regiões sem carga.	poisson;laplace;potencial eletrostatico	MIT_ADV
capacitance_energy	circuitos	2	Capacitância e energia elétrica	C=Q/V; U=(1/2)CV^2	Capacitores armazenam carga e energia no campo elétrico.	capacitancia;capacitor;energia eletrica	OPENSTAX
inductance_energy	circuitos	3	Indutância e energia magnética	ε_L=-L dI/dt; U=(1/2)LI^2	Indutores resistem a variações de corrente e armazenam energia no campo magnético.	indutancia;indutor;energia magnetica	OPENSTAX
kirchhoff	circuitos	2	Leis de Kirchhoff	ΣI_nó=0; ΣΔV_malha=0	Conservação de carga e energia fundamenta análise de redes elétricas concentradas.	kirchhoff;lei dos nos;lei das malhas	OPENSTAX
ac_impedance	circuitos	4	Impedância em corrente alternada	Z_R=R; Z_L=iωL; Z_C=1/(iωC)	Fasores transformam equações diferenciais lineares de circuitos AC em relações algébricas complexas.	impedancia;corrente alternada;fasor	MIT_ADV
poynting_vector	eletromagnetismo	4	Vetor de Poynting	S=(1/μ0)E×B	Representa fluxo de energia eletromagnética por unidade de área.	poynting;fluxo de energia;campo eletromagnetico	MIT_ADV
em_momentum	eletromagnetismo	5	Momento eletromagnético	g=S/c^2; p_foton=h/λ	Campos e radiação transportam momento além de energia.	momento da luz;pressao de radiacao;foton	MIT_ADV
waveguides	eletromagnetismo	5	Guias de onda	β^2=k^2-k_c^2	Estruturas condutoras ou dielétricas suportam modos com frequências de corte.	guia de onda;modo TE;modo TM	MIT_ADV
skin_effect	eletromagnetismo	4	Efeito pelicular	δ=sqrt(2/(μσω))	Correntes AC concentram-se perto da superfície de bons condutores em altas frequências.	efeito pelicular;skin depth;condutor	MIT_ADV
polarization	optica	3	Polarização da luz	I=I0 cos^2θ	A lei de Malus descreve intensidade transmitida por polarizadores lineares ideais.	polarizacao;malus;onda transversal	OPENSTAX
brewster_angle	optica	3	Ângulo de Brewster	tanθ_B=n2/n1	Em uma interface dielétrica existe um ângulo em que a reflexão de uma polarização linear se anula idealmente.	brewster;polarizacao;reflexao	OPENSTAX
fresnel_equations	optica	4	Equações de Fresnel	r_s=(n1cosθ_i-n2cosθ_t)/(n1cosθ_i+n2cosθ_t)	Coeficientes de Fresnel quantificam reflexão e transmissão de ondas em interfaces.	fresnel;reflexao;transmissao	MIT_ADV
fourier_optics	optica	5	Óptica de Fourier	U_f(k_x,k_y)∝FT{U_0(x,y)}	Sistemas ópticos paraxiais podem implementar transformadas espaciais e filtragem de frequências.	optica de fourier;difracao fraunhofer;imagem	MIT_ADV
coherence	optica	5	Coerência óptica	γ12(τ)=Γ12(τ)/sqrt(Γ11Γ22)	Funções de coerência quantificam correlação temporal e espacial de campos ópticos.	coerencia;interferencia;correlacao optica	MIT_ADV
laser_physics	optica_quantica	5	Princípio do laser	N2>N1; ganho > perdas	Emissão estimulada, inversão de população e realimentação óptica produzem luz coerente amplificada.	laser;emissao estimulada;inversao de populacao	MIT_ADV
photoelectric_effect	quantica	2	Efeito fotoelétrico	K_max=hν-φ	A energia máxima de fotoelétrons depende linearmente da frequência acima do limiar do material.	efeito fotoeletrico;funcao trabalho;foton	OPENSTAX
compton_scattering	quantica	3	Espalhamento Compton	Δλ=(h/(m_ec))(1-cosθ)	Espalhamento de fótons por elétrons revela transferência relativística de energia e momento.	compton;espalhamento;foton	OPENSTAX
particle_in_box	quantica	3	Partícula em caixa infinita	E_n=n^2π^2ħ^2/(2mL^2)	Confinamento espacial gera níveis discretos de energia.	particula na caixa;poco infinito;quantizacao	MIT_ADV
quantum_tunneling	quantica	4	Tunelamento quântico	T≈e^{-2κa}; κ=sqrt(2m(V-E))/ħ	Funções de onda penetram barreiras classicamente proibidas, permitindo transmissão finita.	tunelamento;barreira;wkb	MIT_ADV
harmonic_quantum	quantica	4	Oscilador harmônico quântico	E_n=ħω(n+1/2)	O oscilador quântico possui níveis igualmente espaçados e energia de ponto zero.	oscilador quantico;energia de ponto zero;ladder operators	MIT_ADV
angular_momentum_quantum	quantica	4	Momento angular quântico	L^2|lm⟩=ħ^2l(l+1)|lm⟩; L_z|lm⟩=ħm|lm⟩	Momento angular orbital é quantizado em magnitude e projeção.	momento angular quantico;l m;harmonicos esfericos	MIT_ADV
spin_half	quantica	4	Spin 1/2	S_i=(ħ/2)σ_i	Sistemas de dois níveis de spin são representados pelas matrizes de Pauli.	spin meio;matrizes de pauli;qubit	MIT_ADV
born_rule	quantica	3	Regra de Born	P(a)=abs(⟨a|ψ⟩)^2	Amplitudes quânticas determinam probabilidades de resultados de medida.	regra de born;probabilidade quantica;medicao	MIT_ADV
commutators	quantica	5	Comutadores e observáveis	[A,B]=AB-BA; ΔAΔB≥(1/2)abs(⟨[A,B]⟩)	Não comutatividade estrutura incompatibilidade de observáveis e relações gerais de incerteza.	comutador;observaveis;incerteza	MIT_ADV
density_matrix	quantica	5	Matriz densidade	ρ=Σ_i p_i|ψ_i⟩⟨ψ_i|; Trρ=1	Representa estados puros e mistos e permite tratar subsistemas por traço parcial.	matriz densidade;estado misto;traco parcial	MIT_ADV
quantum_entanglement	quantica	5	Emaranhamento quântico	|Φ+⟩=(|00⟩+|11⟩)/sqrt(2)	Estados compostos podem exibir correlações não separáveis sem equivalente clássico local.	emaranhamento;bell;estado bipartido	MIT_ADV
bell_inequality	fundamentos_quanticos	5	Desigualdade CHSH	abs(S)≤2 local; mecânica quântica pode atingir 2sqrt(2)	Testes de Bell distinguem teorias locais de variáveis ocultas das previsões quânticas.	bell;chsh;nao localidade	MIT_ADV
quantum_information_entropy	informacao_quantica	5	Entropia de von Neumann	S(ρ)=-Tr(ρ lnρ)	Quantifica mistura e informação quântica de um estado densidade.	entropia de von neumann;informacao quantica;qubit	MIT_ADV
dirac_equation	quantica_relativistica	5	Equação de Dirac	(iħγ^μ∂_μ-mc)ψ=0	Combina mecânica quântica e relatividade especial para férmions de spin 1/2.	dirac;spinor;antimateria	PDG
klein_gordon	quantica_relativistica	5	Equação de Klein-Gordon	(□+(mc/ħ)^2)φ=0	É a equação relativística de campo livre para graus de liberdade escalares.	klein gordon;campo escalar;relativistica	PDG
qed_lagrangian	qft	5	Lagrangiana da QED	L=-1/4 F_{μν}F^{μν}+ψbar(iγ^μD_μ-m)ψ	A eletrodinâmica quântica descreve férmions carregados interagindo com o campo eletromagnético.	qed;lagrangiana;foton	PDG
qcd_lagrangian	qft	5	Cromodinâmica quântica	L_QCD=-1/4 G^a_{μν}G^{aμν}+Σ_q qbar(iγ^μD_μ-m_q)q	QCD é a teoria de gauge SU(3) da interação forte entre quarks e glúons.	qcd;cromodinamica;gluons	PDG
running_coupling	qft	5	Acoplamento corrente e função beta	β(g)=μ dg/dμ	Constantes de acoplamento efetivas dependem da escala de energia por renormalização.	funcao beta;acoplamento corrente;renormalizacao	PDG
feynman_propagator	qft	5	Propagador de Feynman	D_F(p)=i/(p^2-m^2+iε)	Propagadores codificam evolução e correlações de campos livres em teoria perturbativa.	propagador;feynman;campo quantico	PDG
cross_section	particulas	4	Seção de choque	dσ/dΩ=(taxa espalhada)/(fluxo incidente dΩ)	Quantifica probabilidade efetiva de processos de colisão e espalhamento.	secao de choque;espalhamento;colisor	PDG
lorentz_invariant_phase_space	particulas	5	Espaço de fase relativístico	dΦ_n=(2π)^4δ^4(P-Σp_i)Π_i[d^3p_i/((2π)^3 2E_i)]	É a medida invariante usada no cálculo de taxas de decaimento e seções de choque.	espaco de fase;decaimento;invariante lorentz	PDG
higgs_mechanism	particulas	5	Mecanismo de Higgs	V(Φ)=-μ^2Φ†Φ+λ(Φ†Φ)^2	Quebra espontânea eletrofraca gera massas para bósons W e Z e excitações do campo de Higgs.	higgs;quebra espontanea;campo de higgs	CERN
neutrino_oscillation	particulas	5	Oscilação de neutrinos	P(ν_α→ν_β) depende de Δm^2 L/E e da matriz PMNS	Estados de sabor são superposições de estados de massa, produzindo oscilações durante propagação.	neutrino;pmns;oscilacao	PDG
ckm_matrix	particulas	5	Matriz CKM	V_CKM relaciona estados de sabor e massa dos quarks	A mistura de quarks controla transições fracas carregadas e violação de CP no setor quark.	ckm;mistura de quarks;cp	PDG
radioactive_chains	nuclear	4	Cadeias de decaimento	dN_i/dt=produção_i-λ_iN_i	Equações de Bateman descrevem populações em sequências de decaimentos radioativos.	bateman;cadeia radioativa;decaimento	IAEA
nuclear_cross_sections	nuclear	4	Seções de choque nucleares	R=nσΦ	Taxas de reação nuclear dependem de densidade alvo, seção de choque e fluxo incidente.	secao de choque nuclear;fluxo neutronico;reacao	IAEA
neutron_diffusion	nuclear	5	Difusão de nêutrons	-D∇^2φ+Σ_aφ=S	Modelos de difusão aproximam transporte de nêutrons em meios multiplicativos ou absorvedores.	difusao de neutrons;reator;fluxo neutronico	IAEA
reactor_criticality	nuclear	5	Criticalidade de reatores	k_eff=produção de nêutrons/remoção de nêutrons	k_eff igual a 1 indica estado crítico estacionário ideal em cinética de reator.	keff;criticalidade;reator nuclear	IAEA
fission_energy	nuclear	3	Fissão nuclear	Q=(m_inicial-m_final)c^2	A divisão de núcleos pesados libera energia por diferença de massa e pode liberar nêutrons adicionais.	fissao;energia nuclear;uranio	IAEA
fusion_lawson	fusao	5	Critério de Lawson	nTτ_E deve exceder limiar dependente da reação	Fusão energética exige combinação suficiente de densidade, temperatura e tempo de confinamento.	lawson;fusao;confinamento	IAEA
tokamak_safety_factor	plasma_fusao	5	Fator de segurança tokamak	q(r)≈rB_t/(R B_p)	O fator de segurança mede o enrolamento helicoidal das linhas de campo em um tokamak.	tokamak;fator q;confinamento magnetico	IAEA
magnetohydrodynamics	plasma	5	Magnetohidrodinâmica ideal	∂B/∂t=∇×(v×B); ρDv/Dt=J×B-∇p	MHD trata plasma condutor como fluido acoplado ao campo magnético.	mhd;magnetohidrodinamica;plasma	IAEA
alfven_waves	plasma	5	Ondas de Alfvén	v_A=B/sqrt(μ0ρ)	São ondas MHD transversais propagadas pela tensão das linhas de campo magnético.	alfven;onda mhd;plasma magnetizado	IAEA
plasma_beta	plasma	4	Beta de plasma	β=2μ0p/B^2	Compara pressão térmica do plasma com pressão magnética de confinamento.	beta plasma;pressao magnetica;confinamento	IAEA
debye_sphere	plasma	4	Número na esfera de Debye	N_D=(4π/3)nλ_D^3	Plasma coletivo bem definido requer muitas partículas dentro de uma esfera de Debye.	esfera de debye;plasma coletivo;blindagem	IAEA
special_relativity_interval	relatividade_especial	3	Intervalo espaço-temporal	ds^2=-c^2dt^2+dx^2+dy^2+dz^2	O intervalo de Minkowski é invariante sob transformações de Lorentz.	intervalo;minkowski;invariante	MIT_ADV
four_momentum	relatividade_especial	4	Quadrimomento	p^μ=(E/c,p); p_μp^μ=-m^2c^2	Energia e momento formam um quadrivetor com norma relativisticamente invariante.	quadrimomento;quatro vetor;relatividade	MIT_ADV
equivalence_principle	relatividade_geral	4	Princípio da equivalência	massa inercial localmente indistinguível de massa gravitacional	Localmente, queda livre elimina efeitos gravitacionais uniformes e motiva descrição geométrica da gravidade.	principio da equivalencia;queda livre;gravidade	LIGO
geodesic_equation	relatividade_geral	5	Equação geodésica	d^2x^μ/dτ^2+Γ^μ_{αβ}(dx^α/dτ)(dx^β/dτ)=0	Partículas livres seguem geodésicas do espaço-tempo curvo.	geodesica;christoffel;espaco tempo	LIGO
riemann_curvature	relatividade_geral	5	Tensor de Riemann	R^ρ_{σμν}=∂_μΓ^ρ_{νσ}-∂_νΓ^ρ_{μσ}+...	O tensor de Riemann mede curvatura intrínseca e desvio geodésico.	riemann;curvatura;relatividade geral	MIT_ADV
gravitational_redshift	relatividade_geral	4	Redshift gravitacional	ν_obs/ν_emit≈sqrt(g00_emit/g00_obs)	Frequências de relógios e fótons dependem do potencial gravitacional.	redshift gravitacional;relogio;tempo gravitacional	LIGO
gravitational_waves	relatividade_geral	5	Ondas gravitacionais	□h_ij≈0 no vácuo linearizado	Perturbações de curvatura propagantes transportam informação de sistemas massivos acelerados.	onda gravitacional;strain;ligo	LIGO
chirp_mass	astrofisica_relativistica	5	Massa chirp em binárias	M_c=(m1m2)^(3/5)/(m1+m2)^(1/5)	A evolução de frequência de uma binária inspiralante depende fortemente da massa chirp.	massa chirp;binaria;onda gravitacional	LIGO
"""
