"""STAR Chemistry canonical topics 201-225 of 500."""

CHEMISTRY_ROWS_09 = r"""\
reaction_rate	cinetica_quimica	1	Velocidade de reação	v=(1/ν_i)dc_i/dt com sinal estequiométrico	Define taxa de consumo/formação normalizada pela estequiometria.	velocidade de reacao;taxa reacao;dc dt	OPENSTAX
rate_law	cinetica_quimica	2	Lei de velocidade	v=k[A]^m[B]^n	Relaciona velocidade a concentrações por ordens determinadas experimentalmente.	lei de velocidade;ordem reacao;k	OPENSTAX
reaction_order	cinetica_quimica	2	Ordem de reação	ordem global=m+n+...	Caracteriza sensibilidade empírica da velocidade à concentração.	ordem de reacao;ordem global;expoente	OPENSTAX
zero_order_integrated	cinetica_quimica	2	Lei integrada de ordem zero	[A]=[A]_0-kt	Descreve consumo linear para velocidade independente de A.	ordem zero;lei integrada;meia vida	OPENSTAX
first_order_integrated	cinetica_quimica	2	Lei integrada de primeira ordem	ln[A]=ln[A]_0-kt	Descreve decaimento exponencial de primeira ordem.	primeira ordem;lei integrada;decaimento exponencial	OPENSTAX
second_order_integrated	cinetica_quimica	2	Lei integrada de segunda ordem	1/[A]=1/[A]_0+kt	Descreve caso simples de segunda ordem em um reagente.	segunda ordem;lei integrada;1 sobre a	OPENSTAX
half_life_first_order	cinetica_quimica	2	Meia-vida de primeira ordem	t_1/2=ln2/k	Mostra independência da concentração inicial para primeira ordem.	meia vida;primeira ordem;ln2	OPENSTAX
initial_rates_method	cinetica_quimica	2	Método das velocidades iniciais	v_0 razão revela expoentes da lei de velocidade	Determina ordens por comparação de experimentos iniciais.	velocidades iniciais;ordem;metodo inicial	OPENSTAX
pseudo_first_order	cinetica_quimica	3	Cinética de pseudo-primeira ordem	k_obs=k[B]^n quando B≫A	Reduz lei multirreagente mantendo espécie em grande excesso praticamente constante.	pseudo primeira ordem;kobs;excesso	MIT_560
arrhenius_equation	cinetica_quimica	2	Equação de Arrhenius	k=Ae^(-E_a/RT)	Relaciona constante de velocidade à temperatura e energia de ativação.	arrhenius;energia ativacao;constante velocidade	OPENSTAX
arrhenius_two_temperature	cinetica_quimica	2	Arrhenius em duas temperaturas	ln(k2/k1)=-E_a/R(1/T2-1/T1)	Extrai energia de ativação ou projeta variação de k.	arrhenius duas temperaturas;ea;ln k	OPENSTAX
activation_energy	cinetica_quimica	2	Energia de ativação	E_a=-R dlnk/d(1/T)	Caracteriza dependência térmica aparente da velocidade.	energia ativacao;ea;barreira	MIT_560
reaction_coordinate	cinetica_quimica	2	Coordenada de reação	perfil E ao longo do caminho reacional	Representa reagentes, estado de transição, intermediários e produtos.	coordenada reacao;perfil energetico;estado transicao	MIT_5111
elementary_steps_molecularity	cinetica_quimica	2	Etapas elementares e molecularidade	v_elementar segue estequiometria apenas para etapa elementar	Distingue molecularidade mecanística de ordem experimental global.	etapa elementar;molecularidade;mecanismo	OPENSTAX
reaction_mechanism	cinetica_quimica	3	Mecanismos de reação	mecanismo deve reproduzir lei de velocidade e estequiometria global	Conecta sequência de etapas a observáveis cinéticos.	mecanismo reacao;intermediario;etapas	OPENSTAX
steady_state_approximation	cinetica_quimica	4	Aproximação do estado estacionário	d[I]/dt≈0 para intermediário	Deriva leis de velocidade de mecanismos com intermediários de baixa acumulação.	estado estacionario;steady state;intermediario	MIT_560
pre_equilibrium_approximation	cinetica_quimica	4	Aproximação de pré-equilíbrio	etapa rápida K seguida de etapa lenta	Elimina intermediários usando equilíbrio rápido antecedente.	pre equilibrio;etapa rapida;etapa lenta	MIT_560
catalysis_kinetics	cinetica_quimica	2	Catálise e energia de ativação	catalisador altera caminho e k, não K termodinâmico	Distingue aceleração cinética de deslocamento de equilíbrio.	catalise;catalisador;energia ativacao	MIT_5111
enzyme_michaelis_menten	cinetica_quimica	3	Cinética de Michaelis–Menten	v=V_max[S]/(K_M+[S])	Modelo de saturação para mecanismo enzimático simples.	michaelis menten;km;vmax;enzima	OPENSTAX
lineweaver_burk	cinetica_quimica	3	Linearização de Lineweaver–Burk	1/v=(K_M/V_max)(1/[S])+1/V_max	Lineariza Michaelis–Menten, embora amplifique erros em baixas concentrações.	lineweaver burk;enzima;duplo reciproco	LIBRE_ANALYTICAL
collision_theory	cinetica_quimica	2	Teoria das colisões	k∝Z ρ e^(-E_a/RT)	Relaciona frequência, orientação e energia de colisões à reatividade.	teoria colisoes;fator esterico;frequencia colisao	OPENSTAX
transition_state_theory	cinetica_quimica	4	Teoria do estado de transição	k=(k_BT/h)e^(-ΔG‡/RT)	Relaciona constante de velocidade à energia livre de ativação.	estado de transicao;eyring;delta g dagger	MIT_560
eyring_equation	cinetica_quimica	4	Equação de Eyring	ln(k/T)=ln(k_B/h)+ΔS‡/R-ΔH‡/(RT)	Permite obter entalpia e entropia de ativação de dados cinéticos.	eyring;entalpia ativacao;entropia ativacao	MIT_560
diffusion_controlled_reaction	cinetica_quimica	5	Reações limitadas por difusão	k_diff≈4πRDN_A em modelo de Smoluchowski	Estabelece limite de encontro molecular em solução.	difusao;smoluchowski;limite difusional	MIT_560
oscillating_reactions	cinetica_quimica	5	Reações oscilantes e dinâmica não linear	dc/dt=N·v(c) pode admitir ciclos-limite	Mostra como redes longe do equilíbrio geram oscilações químicas.	reacao oscilante;belousov zhabotinsky;dinamica nao linear	MIT_560
"""
