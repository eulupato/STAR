"""STAR Chemistry canonical topics 176-200 of 500."""

CHEMISTRY_ROWS_08 = r"""\
arrhenius_acid_base	acido_base_solubilidade	1	Ácidos e bases de Arrhenius	ácido aumenta H3O+; base aumenta OH- em água	Introduz definição operacional em solução aquosa.	arrhenius;acido;base	OPENSTAX
bronsted_lowry	acido_base_solubilidade	1	Brønsted–Lowry	ácido doa H+; base aceita H+	Generaliza reações ácido–base por transferência de próton.	bronsted lowry;proton;acido base	IUPAC
lewis_acid_base	acido_base_solubilidade	2	Ácido e base de Lewis	ácido aceita par eletrônico; base doa par	Expande ácido–base para formação de ligações dativas.	lewis;par de eletrons;acido de lewis	IUPAC
conjugate_pairs	acido_base_solubilidade	1	Pares ácido–base conjugados	HA⇌H++A-	Relaciona espécies que diferem por um próton.	par conjugado;acido conjugado;base conjugada	OPENSTAX
water_autoionization	acido_base_solubilidade	1	Autoionização da água	K_w=a_H3O+ a_OH-	Define equilíbrio ácido–base próprio da água.	kw;autoionizacao agua;hidronio hidroxido	OPENSTAX
ph_poh	acido_base_solubilidade	1	pH e pOH	pH=-log10 a_H+; pOH=-log10 a_OH-	Expressa atividade de íons ácido/base em escala logarítmica.	ph;poh;atividade hidrogenio	IUPAC
strong_acid_base	acido_base_solubilidade	1	Ácidos e bases fortes	aproximação: dissociação praticamente completa nas condições usuais	Resolve concentrações dominadas por eletrólitos fortes.	acido forte;base forte;dissociacao	OPENSTAX
weak_acid_ka	acido_base_solubilidade	2	Ácido fraco e Ka	K_a=a_H+a_A-/a_HA	Quantifica dissociação ácida.	ka;acido fraco;dissociacao acida	OPENSTAX
weak_base_kb	acido_base_solubilidade	2	Base fraca e Kb	K_b=a_BH+ a_OH-/a_B	Quantifica protonação de base em água.	kb;base fraca;protonacao	OPENSTAX
ka_kb_relation	acido_base_solubilidade	2	Relação Ka·Kb	K_aK_b=K_w para par conjugado em água	Conecta forças relativas de ácido e base conjugados.	ka kb;par conjugado;kw	OPENSTAX
pka_strength	acido_base_solubilidade	2	pKa e força ácida	pK_a=-log10 K_a	Converte constantes de acidez em escala logarítmica.	pka;forca acida;ka	IUPAC
percent_ionization	acido_base_solubilidade	2	Percentual de ionização	%ion=100 x/C_0	Quantifica fração dissociada de eletrólito fraco.	percentual ionizacao;dissociacao;acido fraco	OPENSTAX
polyprotic_acids	acido_base_solubilidade	3	Ácidos polipróticos	K_a1,K_a2,... geralmente decrescem em etapas	Trata dissociações sequenciais e distribuição de espécies.	acido poliprotico;ka1;ka2	OPENSTAX
amphiprotic_species	acido_base_solubilidade	3	Espécies anfipróticas	podem doar ou aceitar H+	Explica comportamento intermediário de espécies como bicarbonato.	anfiprotico;anfotero;bicarbonato	OPENSTAX
buffer_henderson	acido_base_solubilidade	2	Soluções tampão e Henderson–Hasselbalch	pH=pK_a+log(a_A-/a_HA)	Relaciona pH à razão base/ácido conjugados em tampões adequados.	tampao;henderson hasselbalch;buffer	OPENSTAX
buffer_capacity	acido_base_solubilidade	3	Capacidade tamponante	β=dn_base/dpH≈2.303 C K_a[H+]/(K_a+[H+])^2 em modelo simples	Quantifica resistência do pH à adição de ácido/base.	capacidade tampao;beta;buffer capacity	LIBRE_ANALYTICAL
acid_base_titration_strong	acido_base_solubilidade	2	Titulação ácido forte–base forte	no equivalente: n_H+=n_OH-	Calcula regiões de curva dominadas por excesso, estequiometria e água.	titulacao forte forte;curva titulacao;equivalencia	OPENSTAX
weak_acid_titration	acido_base_solubilidade	3	Titulação de ácido fraco	meia-equivalência: pH≈pK_a	Conecta curva de titulação, tampão e constante de acidez.	titulacao acido fraco;meia equivalencia;pka	OPENSTAX
indicator_equilibrium	acido_base_solubilidade	3	Indicadores ácido–base	HIn⇌H++In-; faixa visual próxima de pK_a±1	Relaciona mudança de cor à distribuição de formas ácido/base.	indicador acido base;faixa viragem;hin	OPENSTAX
solubility_product	acido_base_solubilidade	2	Produto de solubilidade Ksp	K_sp=Πa_i^{ν_i} para dissolução	Quantifica equilíbrio entre sólido pouco solúvel e íons.	ksp;produto solubilidade;solubilidade	OPENSTAX
molar_solubility	acido_base_solubilidade	2	Solubilidade molar	s ligada a K_sp pela estequiometria	Converte constante de solubilidade em concentração dissolvida.	solubilidade molar;s;ksp	OPENSTAX
common_ion_effect	acido_base_solubilidade	2	Efeito do íon comum	atividade comum desloca equilíbrio de dissolução/protonação	Explica supressão de ionização ou solubilidade por espécie compartilhada.	ion comum;solubilidade;tampao	OPENSTAX
selective_precipitation	acido_base_solubilidade	3	Precipitação seletiva	precipita quando Q_sp≥K_sp	Usa diferenças de Ksp e composição para separar íons.	precipitacao seletiva;separacao;produto ionico	LIBRE_ANALYTICAL
speciation_fraction_alpha	acido_base_solubilidade	4	Frações de distribuição ácido–base	α_i=c_i/C_T; Σα_i=1	Expressa distribuição de espécies em função de pH e constantes.	fracao alfa;especiacao;diagrama distribuicao	LIBRE_ANALYTICAL
activity_debye_huckel	acido_base_solubilidade	5	Debye–Hückel limite	log10γ_i=-A z_i^2 sqrt(I)	Corrige atividades iônicas em soluções diluídas pela força iônica.	debye huckel;coeficiente atividade;forca ionica	MIT_560
"""
