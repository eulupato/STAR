"""Taxonomia curricular canônica da STAR.

O catálogo consolida os 56 temas de conhecimento fornecidos para a expansão
curricular. Menções repetidas são deduplicadas no engine por identidade
normalizada/aliases; a taxonomia preserva todas as relações temáticas.

A seção de prioridades e o ciclo de invenção não criam cópias factuais: são
metadados/visões sobre este catálogo.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CurriculumTheme:
    id: int
    label: str
    owner: str
    topics: tuple[str, ...]
    source_families: tuple[str, ...] = ()
    evidence_class: str = "established"


def _topics(raw: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in raw.split(";") if x.strip())


OWNER_SOURCES = {
    "science": ("NIST metrology/GUM", "NASA systems engineering", "National Academies scientific practice"),
    "mathematics": ("NIST DLMF", "MIT OpenCourseWare Mathematics", "OpenStax Mathematics"),
    "physics": ("NIST/CODATA", "Particle Data Group 2026", "NASA Science", "LIGO", "MIT OpenCourseWare Physics"),
    "chemistry": ("IUPAC", "NIST Chemistry WebBook", "PubChem/NCBI", "MIT OpenCourseWare Chemistry"),
    "biology": ("NIH", "NCBI Bookshelf", "NIH BRAIN Initiative", "OpenStax Biology"),
    "engineering": ("NASA Systems Engineering Handbook", "NASA Technical Standards", "NIST Engineering Laboratory", "IEEE/IETF concepts"),
    "computing": ("ACM Computing Classification System", "NIST IT/AI", "IETF RFCs", "MIT OpenCourseWare EECS"),
    "geography": ("USGS", "NOAA", "NASA Earthdata", "IPCC"),
}


THEMES = (
    CurriculumTheme(1, "Método científico e raciocínio", "science", _topics(
        "método científico;epistemologia;lógica;formulação de hipóteses;falseabilidade;desenho experimental;medição;análise de evidências;propagação de erros;análise dimensional;incerteza experimental;correlação e causalidade;estatística experimental;revisão por pares;reprodutibilidade;validação de resultados;classificação do grau de evidência científica;diferenciação entre ciência estabelecida, hipótese, especulação e ficção;inferência bayesiana;pré-registro;meta-análise;seleção de modelos;rastreabilidade metrológica;análise de sensibilidade")),
    CurriculumTheme(2, "Matemática fundamental", "mathematics", _topics(
        "aritmética;álgebra;funções;exponenciais;logaritmos;geometria;trigonometria;números complexos;análise dimensional")),
    CurriculumTheme(3, "Cálculo", "mathematics", _topics(
        "limites;derivadas;integrais;séries;cálculo diferencial;cálculo integral;cálculo multivariável;cálculo vetorial;campos vetoriais;cálculo variacional")),
    CurriculumTheme(4, "Álgebra linear", "mathematics", _topics(
        "vetores;matrizes;sistemas lineares;espaços vetoriais;determinantes;autovalores;autovetores;transformações lineares;decomposições matriciais;álgebra linear numérica")),
    CurriculumTheme(5, "Equações diferenciais", "mathematics", _topics(
        "equações diferenciais ordinárias;equações diferenciais parciais;sistemas dinâmicos;condições iniciais;condições de contorno;equação da onda;equação do calor;métodos numéricos para EDO;métodos numéricos para EDP")),
    CurriculumTheme(6, "Matemática avançada", "mathematics", _topics(
        "cálculo tensorial;geometria diferencial;topologia;teoria de grupos;análise complexa;análise funcional;teoria da medida;probabilidade;estatística;processos estocásticos;matemática discreta;teoria dos grafos;teoria dos jogos;otimização;transformadas de Fourier;transformadas de Laplace;métodos numéricos;otimização convexa;problemas inversos;teoria da informação")),
    CurriculumTheme(7, "Mecânica clássica", "physics", _topics(
        "leis de Newton;cinemática;dinâmica;estática;conservação de energia;conservação do momento;conservação do momento angular;sistemas de partículas;corpos rígidos;gravidade newtoniana;oscilações;vibrações;ondas;mecânica analítica;dinâmica não linear;teoria do caos;mecânica lagrangiana;mecânica hamiltoniana;princípio da ação mínima")),
    CurriculumTheme(8, "Termodinâmica", "physics", _topics(
        "temperatura;calor;trabalho;energia;entropia;equilíbrio termodinâmico;ciclos térmicos;máquinas térmicas;mecânica estatística;transferência de calor;condução;convecção;radiação térmica;potenciais termodinâmicos;transições de fase;termodinâmica fora do equilíbrio")),
    CurriculumTheme(9, "Mecânica dos fluidos", "physics", _topics(
        "hidrostática;hidrodinâmica;aerodinâmica;viscosidade;equação de Bernoulli;equações de Navier-Stokes;fluxo laminar;fluxo turbulento;camada limite;dinâmica dos gases;fluxo compressível;ondas de choque;número de Reynolds;número de Mach;vorticidade;similaridade dinâmica;modelagem de turbulência")),
    CurriculumTheme(10, "Eletromagnetismo", "physics", _topics(
        "carga elétrica;campo elétrico;potencial elétrico;campo magnético;indução eletromagnética;equações de Maxwell;ondas eletromagnéticas;propriedades eletromagnéticas dos materiais;radiofrequência;antenas;micro-ondas;compatibilidade eletromagnética;motores elétricos;geradores;transformadores;vetor de Poynting;condições de contorno eletromagnéticas;linhas de transmissão;guias de onda")),
    CurriculumTheme(11, "Relatividade especial", "physics", _topics(
        "espaço-tempo;referenciais inerciais;transformações de Lorentz;relatividade da simultaneidade;dilatação temporal;contração espacial;equivalência massa-energia;energia e momento relativísticos;causalidade relativística;quatro-vetores;métrica de Minkowski")),
    CurriculumTheme(12, "Relatividade geral e gravitação", "physics", _topics(
        "princípio da equivalência;gravidade como geometria do espaço-tempo;cálculo tensorial aplicado;métricas;geodésicas;curvatura do espaço-tempo;equações de Einstein;solução de Schwarzschild;solução de Kerr;lentes gravitacionais;ondas gravitacionais;cosmologia relativística;causalidade em espaço-tempo curvo;condições de energia;desvio geodésico;relatividade numérica")),
    CurriculumTheme(13, "Mecânica quântica", "physics", _topics(
        "função de onda;equação de Schrödinger;operadores;observáveis;estados quânticos;quantização;princípio da incerteza;spin;superposição;tunelamento;emaranhamento;decoerência;teoria da medição;sistemas de múltiplas partículas;informação quântica;computação quântica;teletransporte quântico;matriz densidade;teoria de perturbação;espalhamento quântico;sistemas quânticos abertos")),
    CurriculumTheme(14, "Física de partículas e teoria quântica de campos", "physics", _topics(
        "teoria quântica de campos;Modelo Padrão;partículas elementares;quarks;léptons;bósons;simetrias;campos quânticos;eletrodinâmica quântica;cromodinâmica quântica;mecanismo de Higgs;neutrinos;teorias de gauge;renormalização;cinemática relativística de partículas;física de colisores;detectores de partículas")),
    CurriculumTheme(15, "Astronomia", "physics", _topics(
        "Sistema Solar;planetas;luas;asteroides;cometas;estrelas;nebulosas;aglomerados estelares;galáxias;quasares;pulsares;magnetars;supernovas;buracos negros;exoplanetas;coordenadas celestes;meio interestelar;classificação estelar")),
    CurriculumTheme(16, "Astronomia observacional", "physics", _topics(
        "telescópios;montagem e rastreamento astronômico;câmeras astronômicas;espectrógrafos;fotometria;espectroscopia;identificação de objetos celestes;processamento de imagens astronômicas;análise de dados observacionais;astrometria;calibração fotométrica;radioastronomia;óptica adaptativa")),
    CurriculumTheme(17, "Astrofísica estelar", "physics", _topics(
        "estrutura estelar;massa estelar;luminosidade;temperatura;espectros;equilíbrio hidrostático;fusão nuclear;nucleossíntese;formação estelar;evolução estelar;protoestrelas;gigantes;anãs brancas;estrelas de nêutrons;supernovas;formação de buracos negros;diagrama Hertzsprung-Russell;atmosferas estelares;transporte de energia estelar")),
    CurriculumTheme(18, "Objetos compactos e buracos negros", "physics", _topics(
        "anãs brancas;estrelas de nêutrons;pulsares;magnetars;buracos negros;horizonte de eventos;ergosfera;discos de acreção;singularidades;buracos negros de Schwarzschild;buracos negros de Kerr;radiação Hawking;termodinâmica de buracos negros;paradoxo da informação;equação TOV;jatos relativísticos;acréscimo e acreção;ondas gravitacionais de compactos")),
    CurriculumTheme(19, "Cosmologia", "physics", _topics(
        "Big Bang;expansão do Universo;lei de Hubble;radiação cósmica de fundo;inflação cósmica;matéria escura;energia escura;formação de estruturas;formação de galáxias;geometria do Universo;equações de Friedmann;modelo ΛCDM;oscilações acústicas de bárions;estrutura em grande escala;parâmetros cosmológicos")),
    CurriculumTheme(20, "Física do espaço-tempo", "physics", _topics(
        "geometria relativística;causalidade;buracos de minhoca;curvas temporais fechadas;métricas exóticas;energia negativa;efeito Casimir;condições de energia;engenharia conceitual do espaço-tempo;limites físicos de viagem temporal;limites físicos de atalhos espaciais;proteção cronológica;métricas de warp"), evidence_class="frontier-theoretical"),
    CurriculumTheme(21, "Engenharia mecânica", "engineering", _topics(
        "estática;dinâmica;resistência dos materiais;mecânica dos sólidos;estruturas;vibrações;mecanismos;elementos de máquinas;engrenagens;rolamentos;transmissões;atuadores;motores;projeto mecânico;análise estrutural;dimensionamento de componentes;tolerâncias;confiabilidade mecânica;tribologia;projeto para fadiga;projeto térmico mecânico")),
    CurriculumTheme(22, "CAD, CAE, FEA e CFD", "engineering", _topics(
        "desenho técnico;modelagem CAD;modelagem 3D;projeto de peças;montagem de conjuntos;CAE;análise por elementos finitos;geração de malha;tensões;deformações;modos de falha;CFD;simulação de escoamentos;pressão;arrasto;sustentação;otimização de projeto;convergência de malha;verificação e validação de simulação;otimização topológica")),
    CurriculumTheme(23, "Engenharia elétrica", "engineering", _topics(
        "teoria de circuitos;corrente e tensão;potência elétrica;sistemas elétricos;máquinas elétricas;motores;fontes de alimentação;baterias;conversores;inversores;instrumentação elétrica;armazenamento de energia;controle elétrico;sistemas trifásicos;sistemas de potência;qualidade de energia;redes elétricas")),
    CurriculumTheme(24, "Engenharia eletrônica", "engineering", _topics(
        "eletrônica analógica;eletrônica digital;resistores;capacitores;indutores;diodos;transistores;MOSFETs;amplificadores;semicondutores;ADC;DAC;microcontroladores;FPGA;processadores;PCB;sensores;interfaces eletrônicas;eletrônica de potência;UART;I²C;SPI;CAN;USB;Ethernet;Bluetooth;Wi-Fi;integridade de sinal;EMI e EMC;sistemas embarcados")),
    CurriculumTheme(25, "Sinais e sistemas", "engineering", _topics(
        "sinais contínuos e discretos;sistemas lineares;convolução;transformada de Fourier;transformada de Laplace;amostragem;quantização;filtros;modulação;processamento digital de sinais;análise espectral;série de Fourier;transformada Z;reconstrução de sinais")),
    CurriculumTheme(26, "Engenharia de controle", "engineering", _topics(
        "sistemas dinâmicos;modelagem de sistemas;funções de transferência;espaço de estados;estabilidade;PID;observadores;estimadores;filtro de Kalman;controle ótimo;controle adaptativo;controle robusto;controle não linear;identificação de sistemas;controlabilidade;observabilidade;controle preditivo por modelo")),
    CurriculumTheme(27, "Robótica", "engineering", _topics(
        "cinemática direta;cinemática inversa;dinâmica de robôs;manipuladores;robôs móveis;planejamento de movimento;planejamento de trajetória;localização;mapeamento;SLAM;sensores;atuadores;motores;servoatuadores;controle robótico;visão computacional;interação humano-robô;fusão sensorial robótica;planejamento sob incerteza")),
    CurriculumTheme(28, "Mecatrônica", "engineering", _topics(
        "integração mecânica-eletrônica;sensores;atuadores;microcontroladores;controle embarcado;sistemas eletromecânicos;integração de hardware e software;sistemas de tempo real;hardware-in-the-loop;co-design mecatrônico")),
    CurriculumTheme(29, "Ciência dos materiais", "engineering", _topics(
        "estrutura atômica dos materiais;ligações químicas;cristalografia;propriedades mecânicas;propriedades térmicas;propriedades elétricas;propriedades magnéticas;metais;ligas;polímeros;cerâmicas;compósitos;semicondutores;fadiga;fratura;corrosão;materiais magnéticos;materiais inteligentes;nanomateriais;metamateriais;seleção de materiais;diagramas de fase;defeitos cristalinos;difusão em materiais;caracterização de materiais")),
    CurriculumTheme(30, "Manufatura e fabricação", "engineering", _topics(
        "processos de fabricação;usinagem;fabricação aditiva;impressão 3D;tolerâncias;montagem;prototipagem;seleção de processos;fabricação de componentes;controle de qualidade;CNC;metrologia dimensional;DFM e DFA;capabilidade de processo")),
    CurriculumTheme(31, "Engenharia aeroespacial", "engineering", _topics(
        "aerodinâmica;estruturas aeroespaciais;propulsão;aviônica;navegação;orientação;controle de voo;dinâmica de voo;sistemas espaciais;satélites;engenharia de missões;reentrada atmosférica;controle térmico espacial;GNC;propulsão química;propulsão elétrica")),
    CurriculumTheme(32, "Mecânica orbital e astrodinâmica", "physics", _topics(
        "problema de dois corpos;problema de N corpos;elementos orbitais;determinação de órbita;estabilidade orbital;órbitas terrestres;transferências orbitais;transferência de Hohmann;trajetórias interplanetárias;janelas de lançamento;assistências gravitacionais;reentrada;pontos de Lagrange;navegação espacial;otimização de trajetórias;problema de Lambert;perturbações orbitais;cônicas remendadas;trajetórias de baixo empuxo")),
    CurriculumTheme(33, "Óptica", "physics", _topics(
        "óptica geométrica;reflexão;refração;lentes;óptica ondulatória;interferência;difração;polarização;formação de imagens;aberrações ópticas;difração de Fresnel;difração de Fraunhofer;radiometria e fotometria")),
    CurriculumTheme(34, "Fotônica", "physics", _topics(
        "lasers;fontes de luz;detectores ópticos;fibras ópticas;guias de onda;modulação óptica;óptica integrada;processamento óptico;fotônica de silício;óptica não linear;fotônica quântica;dispositivos optoeletrônicos")),
    CurriculumTheme(35, "Holografia e displays", "engineering", _topics(
        "holografia;óptica de Fourier;holografia computacional;displays volumétricos;displays de campo de luz;projeção;realidade aumentada;sistemas ópticos para AR;metamateriais ópticos;moduladores espaciais de luz;modelagem de frente de onda;computer-generated holography")),
    CurriculumTheme(36, "Química", "chemistry", _topics(
        "química geral;química orgânica;química inorgânica;físico-química;termodinâmica química;cinética química;eletroquímica;química dos materiais;bioquímica;química computacional;química analítica;espectroscopia molecular;catálise;química quântica")),
    CurriculumTheme(37, "Energia", "engineering", _topics(
        "geração de energia;armazenamento de energia;densidade energética;energia solar;energia eólica;energia hidrelétrica;energia geotérmica;baterias;supercapacitores;hidrogênio;células a combustível;fissão nuclear;fusão nuclear;conversão de energia;eficiência energética;armazenamento em rede;reatores nucleares;confinamento magnético de plasma;integração de redes renováveis")),
    CurriculumTheme(38, "Biologia", "biology", _topics(
        "biologia celular;biologia molecular;genética;evolução;microbiologia;biofísica;bioinformática;biotecnologia;biossegurança;genômica;proteômica;biologia de sistemas;biologia do desenvolvimento")),
    CurriculumTheme(39, "Neurociência", "biology", _topics(
        "neurônios;sinapses;circuitos neurais;regiões cerebrais;sistemas cognitivos;memória;percepção;linguagem;aprendizado;emoção;atenção;tomada de decisão;comportamento;consciência;interfaces cérebro-máquina;plasticidade neural;eletrofisiologia;conectômica;neuroimagem;neurociência de sistemas;neurotecnologia;neuroética")),
    CurriculumTheme(40, "Ciência da computação", "computing", _topics(
        "fundamentos da computação;arquitetura de computadores;algoritmos;estruturas de dados;complexidade computacional;sistemas operacionais;compiladores;redes;bancos de dados;computação distribuída;computação paralela;computação em GPU;computação de alto desempenho;segurança computacional;Python;C;C++;Rust;SQL;JavaScript;concorrência;algoritmos distribuídos;métodos formais;engenharia de software")),
    CurriculumTheme(41, "Inteligência artificial", "computing", _topics(
        "busca;planejamento;representação do conhecimento;lógica computacional;raciocínio simbólico;machine learning;deep learning;redes neurais;transformers;modelos de linguagem;modelos multimodais;visão computacional;reconhecimento de voz;processamento de linguagem natural;reinforcement learning;sistemas multiagentes;agentes autônomos;RAG;busca semântica;otimização para IA;embeddings;bancos vetoriais;avaliação de IA;calibração de incerteza em IA;robustez de IA;interpretabilidade;segurança de IA;TEVV de IA;uso de ferramentas por agentes")),
    CurriculumTheme(42, "Computação científica", "computing", _topics(
        "Python científico;álgebra computacional;matemática simbólica;análise numérica;integração numérica;resolução numérica de equações;otimização computacional;métodos de Monte Carlo;análise de dados;visualização científica;computação paralela;computação de alto desempenho;NumPy;SciPy;SymPy;Pandas;matrizes esparsas;análise de erro numérico;computação científica reprodutível")),
    CurriculumTheme(43, "Simulação científica", "science", _topics(
        "construção de modelos matemáticos;formulação de hipóteses computacionais;simulação de sistemas dinâmicos;simulação estrutural;simulação térmica;CFD;FEA;simulação orbital;simulação N-body;simulação de campos;simulação de ondas;simulação de partículas;mecânica quântica numérica;otimização de modelos;validação entre simulação e realidade;verificação de código de simulação;quantificação de incerteza;modelos substitutos;simulação multifísica")),
    CurriculumTheme(44, "Percepção computacional", "computing", _topics(
        "visão computacional;câmeras RGB;visão de profundidade;infravermelho;imagem macro;processamento de imagem;detecção de objetos;reconhecimento;estimativa espacial;segmentação de imagens;fluxo óptico;estimativa de pose;reconstrução 3D")),
    CurriculumTheme(45, "Sensoriamento", "engineering", _topics(
        "temperatura;pressão;umidade;campo magnético;aceleração;orientação;distância;luz;som;fusão de sensores;calibração de sensores;física de sensores;ruído de sensores;amostragem de sensores;incerteza de sensores")),
    CurriculumTheme(46, "Acústica e áudio", "physics", _topics(
        "ondas sonoras;acústica;localização sonora;análise de frequência;análise espectral;ruído;reconhecimento de voz;processamento digital de áudio;afinação;engenharia de áudio;psicoacústica;beamforming;acústica de salas")),
    CurriculumTheme(47, "Instrumentação científica", "science", _topics(
        "microscopia;telescópios;multímetros;osciloscópios;analisadores lógicos;sensores;câmeras científicas;espectrômetros/espectrógrafos;aquisição de dados;calibração;instrumentação de laboratório;integração de instrumentos com computadores;sincronização de instrumentos;amplificação lock-in;orçamento de incerteza;cadeia de medição")),
    CurriculumTheme(48, "Engenharia de sistemas", "engineering", _topics(
        "definição de missão;definição de objetivos;requisitos;restrições;arquitetura de sistemas;decomposição em subsistemas;interfaces;integração de sistemas;modelagem;prototipagem;testes;verificação;validação;confiabilidade;tolerância a falhas;FMEA;análise de riscos;trade studies;gerenciamento de requisitos;MBSE;SysML;controle de configuração;documentos de controle de interface;medidas de efetividade;medidas de desempenho;matriz de verificação de requisitos")),
    CurriculumTheme(49, "Engenharia de confiabilidade", "engineering", _topics(
        "análise de falhas;modos de falha;redundância;tolerância a falhas;diagnóstico;manutenção;confiabilidade;análise de risco;segurança de sistemas;árvore de falhas;distribuição de Weibull;MTBF;MTTF;diagramas de blocos de confiabilidade;manutenção centrada em confiabilidade")),
    CurriculumTheme(50, "Pesquisa científica e literatura", "science", _topics(
        "busca bibliográfica;leitura de artigos científicos;interpretação de papers;comparação entre estudos;avaliação da qualidade de uma fonte;identificação de consenso científico;identificação de controvérsias;rastreamento de referências;revisão de literatura;análise de dados científicos;revisão sistemática;meta-análise;avaliação de viés de publicação;proveniência bibliográfica")),
    CurriculumTheme(51, "Gestão do conhecimento", "computing", _topics(
        "organização de conhecimento;taxonomias;ontologias;grafos de conhecimento;classificação por assunto;metadados;indexação;busca semântica;relações entre conceitos;proveniência de informação;rastreabilidade de fontes;gerenciamento de versões;resolução de entidades;esquemas de metadados;busca vetorial;alinhamento de ontologias")),
    CurriculumTheme(52, "Avaliação de confiabilidade da informação", "science", _topics(
        "qualidade da fonte;nível de evidência;confirmação independente;data da informação;consenso científico;grau de confiança;fato estabelecido;tecnologia existente;pesquisa experimental;tecnologia plausível;hipótese;especulação;ficção;calibração de confiança;proveniência de afirmações;triangulação de evidências")),
    CurriculumTheme(53, "Engenharia experimental", "engineering", _topics(
        "definição de problema;formulação de hipótese;modelagem;cálculo;desenho experimental;instrumentação;coleta de dados;análise dos resultados;comparação teoria × experimento;documentação;repetição;refinamento;planejamento de experimentos;DOE experimental;orçamento de incerteza experimental;validação cruzada teoria-experimento")),
    CurriculumTheme(54, "Processo de invenção e desenvolvimento tecnológico", "engineering", _topics(
        "identificar um problema;decompor o problema;identificar leis físicas relevantes;estabelecer requisitos;gerar hipóteses;realizar cálculos;comparar alternativas;simular;projetar;criar protótipos;testar;analisar falhas;corrigir;validar;documentar;iterar;níveis de maturidade tecnológica;revisões de projeto;gestão de configuração do protótipo;registro de decisões de engenharia")),
    CurriculumTheme(55, "Tecnologias de fronteira", "science", _topics(
        "wormholes;métricas de warp;métricas exóticas;causalidade;energia negativa;efeito Casimir;engenharia conceitual do espaço-tempo;informação quântica;teletransporte quântico;computação quântica;comunicação quântica;fusão nuclear;armazenamento avançado de energia;alta densidade energética;holografia avançada;displays volumétricos;realidade aumentada;fotônica avançada;metamateriais;nanomateriais;materiais inteligentes;robótica avançada;telepresença;sistemas autônomos;interfaces neurais;interfaces cérebro-computador;propulsão espacial avançada;exploração espacial;viagem interestelar"), evidence_class="mixed-frontier"),
    CurriculumTheme(56, "Ciências da Terra", "geography", _topics(
        "geologia;geofísica;meteorologia;climatologia;oceanografia;geografia;ecologia;tectônica de placas;sismologia;dinâmica atmosférica;hidrologia;geodesia; sensoriamento remoto da Terra;modelagem climática;ciclos biogeoquímicos")),
)


# Aliases só unem conceitos que são a mesma entidade/conceito. Relações próximas
# permanecem separadas e são representadas por memberships/cross-links.
CONCEPT_ALIASES = {
    "wormholes": "buracos de minhoca",
    "armazenamento energético": "armazenamento de energia",
    "interfaces cérebro-computador": "interfaces cérebro-máquina",
    "computer-generated holography": "holografia computacional",
    "fea": "análise por elementos finitos",
    "cfd": "dinâmica dos fluidos computacional",
    "gnc": "orientação, navegação e controle aeroespacial",
    "doe experimental": "planejamento de experimentos",
    "emi e emc": "compatibilidade eletromagnética",
}


# Conceitos que o acrônimo/termo curto referencia. Eles são acrescentados uma
# única vez pelo engine e recebem todos os vínculos dos temas onde aparecem.
CANONICAL_ALIAS_TARGETS = {
    "dinâmica dos fluidos computacional": ("CFD",),
    "análise por elementos finitos": ("FEA",),
    "orientação, navegação e controle aeroespacial": ("GNC",),
    "planejamento de experimentos": ("DOE experimental",),
}


PRIORITY_VIEW = (
    "Matemática", "Física", "Ciência da computação", "Engenharia eletrônica",
    "Engenharia mecânica", "Robótica e controle", "Ciência dos materiais",
    "Engenharia aeroespacial", "Astrofísica", "Cosmologia", "Física quântica",
    "Relatividade", "Energia", "Química", "Biologia", "Neurociência",
    "Fabricação/manufatura",
)

LEARNING_CORE_VIEW = (
    "Matemática", "Física", "Computação", "Eletrônica", "Mecânica", "Controle",
    "Robótica", "Materiais", "Fabricação", "Aeroespacial", "Óptica", "Química",
    "Energia", "Astronomia", "Astrofísica", "Cosmologia", "Quântica",
    "Relatividade", "Biologia", "Neurociência", "Simulação",
    "Engenharia de Sistemas", "Método Científico", "Pesquisa Científica",
    "Tecnologias de Fronteira",
)

INVENTION_CYCLE = (
    "problema", "pesquisa", "hipótese", "matemática", "modelo", "simulação",
    "projeto", "protótipo", "experimento", "dados", "análise", "validação",
    "correção", "novo conhecimento",
)
