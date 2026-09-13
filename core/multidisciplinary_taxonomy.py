"""Taxonomia multidisciplinar da STAR.

13 matérias × 25 macroáreas × 20 lentes = 6.500 nós canônicos.
Cada nó gera 1.000 variações sob demanda no engine multidisciplinar.
"""
from __future__ import annotations

LENSES = (
    ("conceito", "conceito e definição", "defina o núcleo conceitual e a terminologia"),
    ("fundamentos", "fundamentos e pré-requisitos", "mostre ideias necessárias antes de avançar"),
    ("estrutura", "estrutura, componentes e classificação", "organize partes, categorias e relações internas"),
    ("processo", "processos, mecanismos e dinâmica", "explique como mudanças ou operações acontecem"),
    ("modelo", "modelos, relações e formalização", "apresente modelos, relações quantitativas ou estruturas causais quando existirem"),
    ("calculo", "cálculo, problema e procedimento", "mostre método de resolução, dados, etapas e verificações quando a área permitir"),
    ("metodos", "métodos, ferramentas e técnicas", "descreva como o conhecimento é produzido, medido ou analisado"),
    ("evidencias", "evidências e fontes", "separe evidência direta, indireta, fontes e grau de confiança"),
    ("historia", "história do conceito e desenvolvimento", "mostre origem, mudanças de interpretação e contexto"),
    ("casos", "casos, exemplos e estudos", "use casos representativos e compare contextos"),
    ("comparacao", "comparações e contrastes", "diferencie conceitos próximos sem colidir domínios"),
    ("aplicacoes", "aplicações e usos", "conecte o conteúdo a problemas e práticas reais"),
    ("erros", "erros comuns e equívocos", "aponte confusões frequentes e como corrigi-las"),
    ("limites", "limites, hipóteses e incertezas", "declare condições de validade, limitações e incerteza"),
    ("controversias", "debates e controvérsias", "distinga consenso, escolas, disputas e evidência disponível"),
    ("interdisciplinar", "conexões interdisciplinares", "aponte pontes sem duplicar o domínio vizinho"),
    ("cotidiano", "cotidiano, experiência e impactos", "relacione o tema a experiências, instituições ou vida material"),
    ("curiosidades", "detalhes pouco ensinados e curiosidades", "priorize fatos verificáveis, fontes primárias e detalhes menos conhecidos"),
    ("avancado", "nível avançado e fronteira", "apresente formulações avançadas, problemas abertos e linguagem técnica"),
    ("revisao", "revisão, perguntas e síntese", "gere síntese, perguntas de checagem e relações-chave"),
)


def _areas(raw: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in raw.split(";") if x.strip())


SUBJECTS = {
    "geography": {
        "prefix": "GEO", "label": "Geografia",
        "aliases": ("geografia", "geografico", "cartografia", "territorio", "paisagem", "sig", "gis"),
        "focus": "espaço, território, paisagem, ambiente, população, redes e métodos geoespaciais",
        "sources": ("USGS", "NOAA", "NASA Earthdata", "IPCC", "OGC/OpenStreetMap concepts"),
        "areas": _areas("Cartografia e projeções;Sistemas de coordenadas e geodesia;Sensoriamento remoto;SIG e análise espacial;Geomorfologia;Climatologia;Meteorologia geográfica;Hidrografia;Oceanografia geográfica;Biogeografia;Solos e pedologia;Geografia urbana;Geografia rural e agrária;Geografia econômica;Geografia da população;Migrações;Geografia política;Geopolítica histórica;Transportes e redes;Globalização e fluxos;Riscos e desastres;Recursos naturais;Mudanças ambientais;Paisagem e território;Geografia regional comparada"),
    },
    "history": {
        "prefix": "HIST", "label": "História",
        "aliases": ("historia", "historico", "arqueologia", "passado", "cronologia", "historiografia"),
        "focus": "cronologia, fontes primárias, arqueologia, vida cotidiana, cultura material e historiografia",
        "sources": ("Library of Congress", "Smithsonian collections", "UNESCO Memory of the World", "National Archives", "The Met Heilbrunn Timeline"),
        "areas": _areas("Pré-história e arqueologia;Mesopotâmia e Crescente Fértil;Egito antigo e nordeste africano;Mediterrâneo antigo;Grécia antiga;Roma e mundo romano;África pré-colonial;Sul e Sudeste Asiático históricos;China e Leste Asiático históricos;Povos indígenas das Américas;Américas pré-colombianas;Europa medieval;Mundo islâmico medieval;Impérios e rotas euro-asiáticas;Renascimentos e reformas;Expansões marítimas e contatos;Colonização e escravidão atlântica;Revoluções dos séculos XVII-XIX;Industrialização e trabalho;Imperialismos do século XIX;Guerras mundiais;Guerra Fria e descolonização;História do Brasil;História da ciência e tecnologia;História social, cotidiana e material"),
    },
    "mathematics": {
        "prefix": "MATH", "label": "Matemática",
        "aliases": ("matematica", "algebra", "calculo", "geometria", "probabilidade", "estatistica"),
        "focus": "definições, teoremas, provas, cálculos, exemplos, contraexemplos e aplicações",
        "sources": ("OpenStax Mathematics", "MIT OpenCourseWare Mathematics", "NIST DLMF", "Encyclopedia of Mathematics", "OEIS"),
        "areas": _areas("Aritmética e sistemas numéricos;Álgebra elementar;Equações e inequações;Funções;Geometria euclidiana;Geometria analítica;Trigonometria;Combinatória;Probabilidade;Estatística;Cálculo diferencial;Cálculo integral;Cálculo multivariável;Equações diferenciais;Álgebra linear;Teoria dos números;Matemática discreta;Teoria dos grafos;Análise real;Análise complexa;Topologia;Álgebra abstrata;Otimização;Métodos numéricos;Teoria da medida e probabilidade avançada"),
    },
    "biology": {
        "prefix": "BIO", "label": "Biologia",
        "aliases": ("biologia", "genetica", "celula", "ecologia", "evolucao", "organismo", "genomica"),
        "focus": "vida da escala molecular à biosfera, com evolução como eixo integrador e evidência experimental",
        "sources": ("OpenStax Biology 2e", "NCBI Bookshelf", "NIH", "CDC foundational biology", "IUCN/GBIF"),
        "areas": _areas("Bioquímica celular;Biologia celular;Membranas e transporte;Metabolismo;Genética mendeliana;Genética molecular;Genômica;Epigenética;Evolução;Genética de populações;Microbiologia;Virologia;Botânica;Zoologia;Fisiologia animal;Fisiologia vegetal;Neurobiologia;Imunologia;Biologia do desenvolvimento;Ecologia de populações;Ecologia de comunidades;Ecossistemas;Biogeografia e conservação;Sistemática e filogenia;Biotecnologia"),
    },
    "mechanics": {
        "prefix": "MECH", "label": "Mecânica",
        "aliases": ("mecanica", "estatica", "dinamica", "cinematica", "vibracao", "tribologia", "mecanismos"),
        "focus": "movimento, forças, estruturas, fluidos, vibrações e sistemas mecânicos com relações quantitativas",
        "sources": ("MIT OpenCourseWare Mechanics", "OpenStax University Physics", "NASA technical references", "NIST engineering data", "ASME terminology"),
        "areas": _areas("Grandezas vetoriais;Cinemática;Dinâmica newtoniana;Estática;Trabalho e energia;Impulso e momento;Movimento rotacional;Corpos rígidos;Centro de massa;Atrito;Oscilações;Vibrações;Mecânica dos fluidos;Hidrostática;Escoamento interno;Aerodinâmica básica;Resistência dos materiais;Tensão e deformação;Flexão de vigas;Torção;Mecanismos e máquinas;Engrenagens e transmissões;Tribologia;Dinâmica veicular;Mecânica computacional"),
    },
    "engineering": {
        "prefix": "ENG", "label": "Engenharia",
        "aliases": ("engenharia", "projeto", "sistemas", "mecatronica", "robotica", "estrutural", "manufatura"),
        "focus": "projeto, requisitos, análise, verificação, confiabilidade, manufatura e sistemas de engenharia",
        "sources": ("NASA Systems Engineering Handbook", "NIST Engineering Laboratory", "MIT OpenCourseWare Engineering", "INCOSE concepts", "OpenStax engineering-adjacent references"),
        "areas": _areas("Projeto de engenharia;Engenharia de sistemas;Engenharia mecânica;Engenharia elétrica;Engenharia eletrônica;Engenharia civil;Engenharia estrutural;Engenharia de materiais;Engenharia química;Engenharia de produção;Engenharia de controle;Mecatrônica;Robótica;Engenharia aeroespacial;Engenharia biomédica;Engenharia ambiental;Engenharia de energia;Manufatura;CAD e CAE;Confiabilidade;Segurança de sistemas;Metrologia;Otimização de projeto;Gestão de requisitos;Verificação e validação"),
    },
    "computing": {
        "prefix": "COMP", "label": "Computação",
        "aliases": ("computacao", "algoritmo", "estrutura de dados", "complexidade", "compilador", "sistema operacional", "programacao"),
        "focus": "fundamentos teóricos e práticos de algoritmos, software, hardware, sistemas e inteligência computacional",
        "sources": ("ACM Computing Classification System", "NIST Computer Science/IT", "IETF RFCs", "Computer History Museum", "MIT OpenCourseWare EECS"),
        "areas": _areas("Fundamentos de computação;Algoritmos;Estruturas de dados;Complexidade computacional;Arquitetura de computadores;Sistemas operacionais;Compiladores;Linguagens de programação;Paradigmas de programação;Banco de dados;Redes de computadores;Computação distribuída;Computação paralela;Computação gráfica;Interação humano-computador;Inteligência artificial;Aprendizado de máquina;Visão computacional;Processamento de linguagem natural;Robótica computacional;Teoria da computação;Criptografia computacional;Engenharia de software;Computação quântica;História da computação"),
    },
    "it": {
        "prefix": "IT", "label": "TI",
        "aliases": ("ti", "tecnologia da informacao", "infraestrutura", "devops", "cloud", "nuvem", "administracao de sistemas"),
        "focus": "operação, infraestrutura, serviços, redes, cloud, governança, segurança e confiabilidade de TI",
        "sources": ("NIST IT/Cybersecurity", "IETF RFCs", "CISA guidance", "Linux documentation", "Microsoft Learn conceptual docs"),
        "areas": _areas("Hardware e suporte;Sistemas Windows;Sistemas Linux;Administração de sistemas;Virtualização;Computação em nuvem;Redes corporativas;DNS e endereçamento;Serviços web;Armazenamento;Backup e recuperação;Bancos de dados operacionais;Observabilidade e logs;Automação de TI;DevOps;CI/CD;Gestão de configuração;Gestão de serviços de TI;Governança de TI;Gestão de identidade e acesso;Segurança de endpoints;Segurança de redes;Continuidade de negócios;Arquitetura de soluções;FinOps e capacidade"),
    },
    "logic": {
        "prefix": "LOGIC", "label": "Lógica",
        "aliases": ("logica", "silogismo", "deducao", "proposicao", "predicado", "falacia", "inferência", "inferencia"),
        "focus": "validade, inferência, sistemas formais, semântica, provas, falácias e aplicações computacionais",
        "sources": ("Stanford Encyclopedia of Philosophy", "Open Logic Project", "MIT logic materials", "Encyclopedia of Mathematics", "classical logic literature"),
        "areas": _areas("Lógica proposicional;Lógica de predicados;Tabelas-verdade;Dedução natural;Sistemas axiomáticos;Teoria da prova;Teoria de modelos;Completude e correção;Lógica modal;Lógica temporal;Lógica deôntica;Lógica epistêmica;Lógica intuicionista;Lógica paraconsistente;Lógica multivalorada;Lógica fuzzy;Lógica booleana;Silogística;Falácias formais;Falácias informais;Raciocínio indutivo;Raciocínio abdutivo;Argumentação;Lógica matemática;Aplicações em computação"),
    },
    "psychology_sociology": {
        "prefix": "PSYSOC", "label": "Psicologia e Sociologia",
        "aliases": ("psicologia", "sociologia", "cognicao", "sociedade", "comportamento", "cultura", "psicometria", "teoria social"),
        "focus": "comportamento, cognição e estruturas sociais com pesquisa empírica, contexto cultural e limites de inferência",
        "sources": ("APA", "OpenStax Psychology 2e", "OpenStax Introduction to Sociology 3e", "American Sociological Association", "WHO social/behavioral references"),
        "areas": _areas("Psicologia cognitiva;Psicologia social;Psicologia do desenvolvimento;Psicologia da personalidade;Aprendizagem e comportamento;Percepção;Memória;Linguagem e cognição;Motivação;Emoção;Psicometria;Métodos de pesquisa psicológica;Neuropsicologia;Sociologia clássica;Teoria social contemporânea;Estratificação social;Instituições sociais;Família e parentesco;Educação e sociedade;Trabalho e organizações;Cultura e identidade;Desigualdade;Demografia social;Movimentos sociais;Métodos de pesquisa social"),
    },
    "decoding": {
        "prefix": "DECODE", "label": "Decodificação",
        "aliases": ("decodificacao", "codificacao", "unicode", "utf-8", "base64", "compressao", "codigo corretor", "codec"),
        "focus": "representação, codificação, compressão, correção de erros e criptografia conceitual/defensiva",
        "sources": ("Unicode Standard 18.0", "IETF RFCs", "NIST Cryptographic Standards", "Shannon information theory", "W3C encoding concepts"),
        "areas": _areas("Sistemas de numeração;ASCII;Unicode;UTF-8;UTF-16 e UTF-32;Normalização Unicode;Base64;Base32 e Base16;Percent-encoding e URLs;MIME e codificações de transferência;Representação binária;Endianness;Códigos de caracteres históricos;Compressão sem perdas;Compressão com perdas;Entropia da informação;Códigos de Huffman;Codificação aritmética;Códigos corretores de erro;Paridade e checksums;CRC;Códigos Reed-Solomon;Hashes e autenticação;Criptografia simétrica e assimétrica;Protocolos e formatos de serialização"),
    },
    "science": {
        "prefix": "SCI", "label": "Ciências",
        "aliases": ("ciencia", "metodo cientifico", "experimento", "reprodutibilidade", "hipotese", "medicao cientifica"),
        "focus": "método, evidência, medição, modelagem, reprodutibilidade, ética e funcionamento da prática científica",
        "sources": ("National Academies", "NIST measurement science", "NASA", "NOAA", "USGS"),
        "areas": _areas("Método científico;Formulação de hipóteses;Desenho experimental;Medição;Unidades e padrões;Incerteza;Análise de dados;Estatística científica;Reprodutibilidade;Repetibilidade;Revisão por pares;Falsificabilidade;Modelagem científica;Simulação;Causalidade;Correlação;Escalas e ordens de grandeza;Instrumentação;Laboratórios e cadernos;Ética científica;Comunicação científica;História da ciência;Ciência aberta;Interdisciplinaridade;Fronteiras e limites do conhecimento"),
    },
    "philosophy": {
        "prefix": "PHIL", "label": "Filosofia",
        "aliases": ("filosofia", "epistemologia", "metafisica", "etica", "fenomenologia", "existencialismo", "estetica"),
        "focus": "problemas, argumentos, tradições, conceitos e debates filosóficos, distinguindo posições e evidências",
        "sources": ("Stanford Encyclopedia of Philosophy", "Internet Encyclopedia of Philosophy", "Perseus classical texts", "PhilPapers taxonomy", "public-domain primary texts"),
        "areas": _areas("Filosofia antiga;Filosofia medieval;Filosofia moderna;Filosofia contemporânea;Epistemologia;Metafísica;Ética;Filosofia política;Filosofia da mente;Filosofia da linguagem;Filosofia da ciência;Filosofia da matemática;Filosofia da lógica;Estética;Fenomenologia;Existencialismo;Pragmatismo;Empirismo;Racionalismo;Idealismo;Materialismo;Filosofia analítica;Filosofia continental;Filosofias não ocidentais;Argumentação e método filosófico"),
    },
}

SUBJECT_ORDER = tuple(SUBJECTS)
SUBJECT_COUNT = len(SUBJECT_ORDER)
AREAS_PER_SUBJECT = 25
LENSES_PER_AREA = 20
NODES_PER_SUBJECT = AREAS_PER_SUBJECT * LENSES_PER_AREA
VARIANTS_PER_NODE = 1000
CONTENTS_PER_SUBJECT = NODES_PER_SUBJECT * VARIANTS_PER_NODE
TOTAL_CONTENTS = SUBJECT_COUNT * CONTENTS_PER_SUBJECT

CROSS_DOMAIN_BRIDGES = {
    "geography": ("history", "biology", "science"),
    "history": ("geography", "philosophy", "psychology_sociology", "science"),
    "mathematics": ("logic", "computing", "mechanics", "engineering", "science"),
    "biology": ("geography", "psychology_sociology", "science"),
    "mechanics": ("mathematics", "engineering", "science", "physics"),
    "engineering": ("mechanics", "mathematics", "computing", "it", "science", "physics", "chemistry"),
    "computing": ("mathematics", "logic", "it", "decoding"),
    "it": ("computing", "decoding"),
    "logic": ("mathematics", "computing", "philosophy"),
    "psychology_sociology": ("biology", "history", "philosophy", "science"),
    "decoding": ("computing", "it", "mathematics", "logic"),
    "science": ("mathematics", "biology", "geography", "history", "philosophy", "physics", "chemistry"),
    "philosophy": ("logic", "history", "psychology_sociology", "science"),
}

HISTORY_EVIDENCE_POLICY = (
    "Curiosidades e detalhes pouco ensinados só devem ser tratados como fatos quando sustentados por "
    "fonte primária, coleção museológica ou historiografia confiável; hipóteses e disputas devem ser rotuladas."
)
DECODING_SAFETY_POLICY = (
    "Decodificação cobre representação, codecs, compressão, teoria da informação, códigos corretores e "
    "criptografia conceitual/defensiva; não é catálogo de bypass, quebra de credenciais ou exploração."
)
PSYCHOLOGY_POLICY = (
    "Psicologia e Sociologia fornecem conteúdo educacional e pesquisa; não produzem diagnóstico clínico individual."
)

if SUBJECT_COUNT != 13:
    raise ValueError(f"Esperadas 13 matérias; encontradas {SUBJECT_COUNT}")
for key, spec in SUBJECTS.items():
    if len(spec["areas"]) != AREAS_PER_SUBJECT:
        raise ValueError(f"{key}: esperadas 25 macroáreas; encontradas {len(spec['areas'])}")
if len(LENSES) != LENSES_PER_AREA:
    raise ValueError("Esperadas 20 lentes")
if CONTENTS_PER_SUBJECT != 500000 or TOTAL_CONTENTS != 6500000:
    raise ValueError("Contagem multidisciplinar inválida")
