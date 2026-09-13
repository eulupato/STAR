"""STAR Chemistry canonical topics 276-300 of 500."""

CHEMISTRY_ROWS_12 = r"""\
beer_lambert	espectroscopia_metodos	2	Lei de Beer–Lambert	A=εbc	Relaciona absorbância, caminho óptico e concentração em regime linear.	beer lambert;absorbancia;uv vis	LIBRE_ANALYTICAL
transmittance_absorbance	espectroscopia_metodos	1	Transmitância e absorbância	A=-log10 T; T=I/I0	Converte razão de intensidades em escala logarítmica de absorção.	transmitancia;absorbancia;intensidade	LIBRE_ANALYTICAL
uv_vis_electronic_transitions	espectroscopia_metodos	3	Transições eletrônicas UV-Vis	ΔE=hν	Associa absorção de fótons a promoção eletrônica entre estados moleculares.	uv vis;transicao eletronica;espectro	MIT_561
ir_vibrational_spectroscopy	espectroscopia_metodos	2	Espectroscopia infravermelha	ν~(1/2π)sqrt(k/μ)	Relaciona frequências vibracionais à constante de força e massa reduzida.	infravermelho;ir;vibracao;numero de onda	NIST_WEBBOOK
harmonic_oscillator_vibration	espectroscopia_metodos	3	Oscilador harmônico molecular	E_v=ħω(v+1/2)	Modelo de primeira ordem para níveis vibracionais quantizados.	oscilador harmonico;vibracao molecular;nivel vibracional	MIT_561
anharmonicity	espectroscopia_metodos	4	Anarmonicidade vibracional	E_v≈ω_e(v+1/2)-ω_ex_e(v+1/2)^2	Corrige espaçamentos vibracionais e permite sobretons.	anarmonicidade;vibracao;sobretom	MIT_561
raman_spectroscopy	espectroscopia_metodos	3	Espectroscopia Raman	atividade requer mudança de polarizabilidade	Detecta modos vibracionais via espalhamento inelástico de luz.	raman;espalhamento inelastico;polarizabilidade	IUPAC
ir_selection_rule	espectroscopia_metodos	4	Regra de seleção no IR	modo IR ativo se ∂μ/∂Q≠0	Conecta mudança de dipolo ao acoplamento vibracional com campo elétrico.	regra selecao ir;dipolo;modo vibracional	MIT_561
raman_selection_rule	espectroscopia_metodos	4	Regra de seleção Raman	modo Raman ativo se ∂α/∂Q≠0	Conecta variação de polarizabilidade ao espalhamento Raman.	regra selecao raman;polarizabilidade;modo	MIT_561
fluorescence	espectroscopia_metodos	3	Fluorescência	Φ_F=n_fótons emitidos/n_fótons absorvidos	Caracteriza emissão radiativa rápida após excitação eletrônica.	fluorescencia;rendimento quantico;emissao	IUPAC
phosphorescence	espectroscopia_metodos	3	Fosforescência	emissão envolve estado triplete e escala temporal maior	Distingue emissão retardada associada a mudança de multiplicidade.	fosforescencia;triplete;emissao	IUPAC
jablonski_diagram	espectroscopia_metodos	3	Diagrama de Jablonski	taxas radiativas e não radiativas competem	Organiza absorção, conversão interna, cruzamento intersistemas e emissão.	jablonski;fluorescencia;fosforescencia	IUPAC
nmr_larmor	espectroscopia_metodos	3	Frequência de Larmor em RMN	ω0=γB0	Relaciona campo magnético e precessão nuclear.	nmr;rmn;larmor;campo magnetico	MIT_561
nmr_chemical_shift	espectroscopia_metodos	3	Deslocamento químico em RMN	δ=10^6(ν-ν_ref)/ν0 ppm	Compara frequência de ressonância à referência de forma independente do campo.	deslocamento quimico;ppm;nmr	MIT_561
nmr_spin_spin_coupling	espectroscopia_metodos	4	Acoplamento spin–spin	multiplicidade simples ≈ n+1 em sistemas de primeira ordem	Revela conectividade por interação escalar entre núcleos.	acoplamento spin spin;j coupling;multiplicidade	MIT_561
nmr_integration	espectroscopia_metodos	2	Integração em RMN	área do sinal ∝ número de núcleos equivalentes	Relaciona área integrada a proporções relativas de prótons observados.	integracao nmr;area pico;protons	MIT_ORG
mass_spectrometry_mz	espectroscopia_metodos	2	Razão massa/carga em MS	m/z	Separa íons segundo massa por número de cargas.	m z;espectrometria massas;ion	NIST_WEBBOOK
mass_resolution	espectroscopia_metodos	3	Resolução em espectrometria de massas	R=m/Δm	Quantifica capacidade de distinguir picos próximos em massa.	resolucao massa;m delta m;mass spec	IUPAC
isotope_pattern_ms	espectroscopia_metodos	3	Padrões isotópicos em MS	intensidades seguem abundâncias isotópicas e combinatória	Ajuda a inferir composição elementar por envelopes isotópicos.	padrao isotopico;mass spec;isotopos	NIST_WEBBOOK
xps_binding_energy	espectroscopia_metodos	4	Espectroscopia fotoeletrônica de raios X	E_bind=hν-E_kin-φ	Relaciona energia cinética de fotoelétrons a estados eletrônicos do material.	xps;energia ligacao;fotoeletron	IUPAC
xrd_bragg	espectroscopia_metodos	3	Difração de raios X	nλ=2d sinθ	Extrai espaçamentos de rede de picos de difração.	xrd;bragg;difracao	OPENSTAX
aes_atomic_emission	espectroscopia_metodos	3	Espectroscopia de emissão atômica	I_λ depende da população excitada e probabilidade de transição	Identifica e quantifica elementos por linhas de emissão.	emissao atomica;aes;linha espectral	LIBRE_ANALYTICAL
aas_atomic_absorption	espectroscopia_metodos	3	Espectrometria de absorção atômica	A≈εbc no regime linear do analito atomizado	Quantifica elementos por absorção ressonante de átomos livres.	absorção atomica;aas;elementos	LIBRE_ANALYTICAL
icp_ms	espectroscopia_metodos	4	ICP-MS	contagens iônicas calibradas versus concentração e padrão interno	Combina plasma indutivamente acoplado com espectrometria de massas elementar.	icp ms;plasma;analise elementar	LIBRE_ANALYTICAL
ftir_fourier_transform	espectroscopia_metodos	4	FTIR e transformada de Fourier	S(ν)=F{interferograma(t)}	Recupera espectro de frequências a partir de interferograma.	ftir;fourier;interferograma	MIT_EXPERIMENTAL
"""
