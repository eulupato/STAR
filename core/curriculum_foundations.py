"""Base factual fundamental do currículo oficial da STAR.

Este módulo não cria outro sistema de conhecimento. Ele fornece conteúdo factual
curado para os 56 temas já definidos em curriculum_taxonomy.py e fatos gerais
básicos que o CurriculumKnowledgeEngine pode reutilizar. Cada registro mantém
proveniência legível e uma resposta curta, própria para conversa local.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from core.curriculum_taxonomy import THEMES


@dataclass(frozen=True)
class SourceRef:
    key: str
    name: str
    url: str


@dataclass(frozen=True)
class ThemeFoundation:
    theme_id: int
    summary: str
    facts: tuple[str, ...]
    source_keys: tuple[str, ...]
@dataclass(frozen=True)
class FactRecord:
    fact_id: str
    aliases: tuple[str, ...]
    answer: str
    theme_ids: tuple[int, ...]
    source_keys: tuple[str, ...]


SOURCE_REGISTRY = {
    "NIST_SI": SourceRef("NIST_SI", "NIST — SI Units", "https://www.nist.gov/pml/owm/metric-si/si-units"),
    "OPENSTAX_MATH": SourceRef("OPENSTAX_MATH", "OpenStax — Mathematics", "https://openstax.org/subjects/math"),
    "OPENSTAX_PHYSICS": SourceRef("OPENSTAX_PHYSICS", "OpenStax — University Physics", "https://openstax.org/details/books/university-physics-volume-1"),
    "NASA_SCIENCE": SourceRef("NASA_SCIENCE", "NASA Science", "https://science.nasa.gov/"),
    "PDG": SourceRef("PDG", "Particle Data Group", "https://pdg.lbl.gov/"),
    "NASA_SE": SourceRef("NASA_SE", "NASA Systems Engineering Handbook", "https://www.nasa.gov/reference/systems-engineering-handbook/"),
    "NIST_ENGINEERING": SourceRef("NIST_ENGINEERING", "NIST Engineering Laboratory", "https://www.nist.gov/el"),
    "IUPAC_GOLD": SourceRef("IUPAC_GOLD", "IUPAC Gold Book", "https://goldbook.iupac.org/"),
    "PUBCHEM": SourceRef("PUBCHEM", "PubChem — NCBI", "https://pubchem.ncbi.nlm.nih.gov/"),
    "OPENSTAX_CHEM": SourceRef("OPENSTAX_CHEM", "OpenStax — Chemistry 2e", "https://openstax.org/details/books/chemistry-2e"),
    "OPENSTAX_BIO": SourceRef("OPENSTAX_BIO", "OpenStax — Biology 2e", "https://openstax.org/details/books/biology-2e"),
    "OPENSTAX_ANATOMY": SourceRef("OPENSTAX_ANATOMY", "OpenStax — Anatomy and Physiology 2e", "https://openstax.org/details/books/anatomy-and-physiology-2e"),
    "NHLBI_HEART": SourceRef("NHLBI_HEART", "NIH/NHLBI — How the Heart Works", "https://www.nhlbi.nih.gov/health/heart"),
    "NHLBI_LUNGS": SourceRef("NHLBI_LUNGS", "NIH/NHLBI — How the Lungs Work", "https://www.nhlbi.nih.gov/health/lungs"),
    "NCBI_BONE": SourceRef("NCBI_BONE", "NCBI Bookshelf — Physiology, Bone", "https://www.ncbi.nlm.nih.gov/books/NBK441968/"),
    "NIST_AI": SourceRef("NIST_AI", "NIST — Artificial Intelligence", "https://www.nist.gov/artificial-intelligence"),
    "OPENSTAX_CS": SourceRef("OPENSTAX_CS", "OpenStax — Introduction to Computer Science", "https://openstax.org/books/introduction-computer-science/pages/1-introduction"),
    "NCBI_NEURO": SourceRef("NCBI_NEURO", "NCBI Bookshelf — Neuroscience", "https://www.ncbi.nlm.nih.gov/books/NBK11154/"),
    "IETF_RFC": SourceRef("IETF_RFC", "IETF — RFCs and Internet Standards", "https://www.ietf.org/standards/rfcs/"),
    "USGS": SourceRef("USGS", "U.S. Geological Survey", "https://www.usgs.gov/"),
    "NOAA": SourceRef("NOAA", "National Oceanic and Atmospheric Administration", "https://www.noaa.gov/"),
    "IPCC": SourceRef("IPCC", "Intergovernmental Panel on Climate Change", "https://www.ipcc.ch/"),
    "EU_FRANCE": SourceRef("EU_FRANCE", "European Union — France", "https://european-union.europa.eu/principles-countries-history/eu-countries/france_en"),
    "UN_CAPITALS": SourceRef("UN_CAPITALS", "UNGEGN — Country Names and Capitals", "https://unstats.un.org/unsd/geoinfo/ungegn/docs/10th-uncsgn-docs/econf/E_Conf.101_97_List%20of%20Country%20Names%20and%20Capitals.pdf"),
    "GRAMMY_MJ": SourceRef("GRAMMY_MJ", "Recording Academy — Michael Jackson", "https://www.grammy.com/artists/michael-jackson/13202"),
    "NHM_DINO": SourceRef("NHM_DINO", "Natural History Museum — When did dinosaurs live?", "https://www.nhm.ac.uk/discover/when-did-dinosaurs-live.html"),
    "NASA_APOLLO11": SourceRef("NASA_APOLLO11", "NASA — Apollo 11 Mission Overview", "https://www.nasa.gov/history/apollo-11-mission-overview/"),
    "UN_HISTORY": SourceRef("UN_HISTORY", "United Nations — History of the United Nations", "https://www.un.org/en/about-us/history-of-the-un"),
    "NOBEL_CURIE": SourceRef("NOBEL_CURIE", "Nobel Prize — Marie Curie", "https://www.nobelprize.org/prizes/physics/1903/marie-curie/facts/"),
}
THEME_FOUNDATION_ROWS = (
    (1, "O método científico organiza perguntas testáveis, hipóteses, observações, medições, análise e revisão. Uma conclusão confiável depende da qualidade da evidência e de incertezas explicitadas.", ("Correlação não demonstra, por si só, causalidade.", "Medições científicas devem registrar unidades, incerteza e método.", "Resultados ganham força quando podem ser reproduzidos ou confirmados independentemente."), ("NIST_SI",)),
    (2, "Matemática fundamental cobre números, operações, álgebra, funções, geometria e trigonometria; é a linguagem quantitativa usada para descrever relações e resolver problemas.", ("Uma equação expressa uma igualdade entre duas expressões.", "Uma função associa entradas a saídas segundo uma regra.", "Trigonometria relaciona ângulos e comprimentos, especialmente em triângulos e fenômenos periódicos."), ("OPENSTAX_MATH",)),
    (3, "Cálculo estuda mudança e acumulação. Derivadas descrevem taxas locais de variação; integrais descrevem acumulação e áreas, e o Teorema Fundamental conecta as duas ideias.", ("A derivada é o limite de uma taxa média de variação quando o intervalo tende a zero.", "A integral definida acumula uma grandeza ao longo de um intervalo.", "Cálculo multivariável estende essas ideias a funções de várias variáveis."), ("OPENSTAX_MATH",)),
    (4, "Álgebra linear estuda vetores, matrizes, transformações lineares e sistemas de equações. É central em computação gráfica, engenharia, física, estatística e IA.", ("Matrizes podem representar transformações lineares.", "Autovetores mantêm sua direção sob uma transformação linear, mudando por um fator associado.", "Sistemas lineares podem ter solução única, infinitas soluções ou nenhuma solução."), ("OPENSTAX_MATH",)),
    (5, "Equações diferenciais relacionam funções às suas derivadas e modelam evolução no tempo ou no espaço, como movimento, difusão, ondas, circuitos e populações.", ("EDOs envolvem derivadas em uma variável independente.", "EDPs envolvem derivadas parciais em mais de uma variável independente.", "Condições iniciais e de contorno são parte essencial da definição de muitos problemas."), ("OPENSTAX_MATH",)),
    (6, "Matemática avançada reúne estruturas e ferramentas como tensores, topologia, análise complexa e funcional, probabilidade, estatística, grafos, otimização, transformadas e métodos numéricos.", ("Transformadas de Fourier decompõem sinais em componentes de frequência.", "Probabilidade modela incerteza; estatística usa dados para estimar, comparar e testar.", "Otimização procura soluções que minimizem ou maximizem um objetivo sujeito ou não a restrições."), ("OPENSTAX_MATH",)),
    (7, "Mecânica clássica descreve movimento e forças em escalas onde efeitos relativísticos e quânticos são desprezíveis, usando leis de Newton e princípios de conservação.", ("A segunda lei de Newton relaciona força resultante e aceleração por F = ma em massa constante.", "Energia, momento linear e momento angular possuem leis de conservação em condições apropriadas.", "Cinemática descreve o movimento; dinâmica relaciona o movimento às suas causas."), ("OPENSTAX_PHYSICS",)),
    (8, "Termodinâmica estuda energia, calor, trabalho, temperatura, equilíbrio e entropia em sistemas macroscópicos.", ("A primeira lei expressa conservação de energia em processos termodinâmicos.", "A segunda lei introduz direção preferencial de processos e crescimento de entropia em sistemas isolados.", "Condução, convecção e radiação são mecanismos de transferência de calor."), ("OPENSTAX_PHYSICS",)),
    (9, "Mecânica dos fluidos estuda líquidos e gases em repouso e movimento, incluindo pressão, viscosidade, escoamento, turbulência e compressibilidade.", ("Pressão é força normal por unidade de área.", "A equação de Bernoulli é válida sob hipóteses específicas e relaciona pressão, velocidade e altura ao longo de uma linha de corrente.", "O número de Reynolds ajuda a caracterizar regimes de escoamento."), ("OPENSTAX_PHYSICS",)),
    (10, "Eletromagnetismo descreve cargas, campos elétricos e magnéticos e sua interação. As equações de Maxwell unificam eletricidade, magnetismo e ondas eletromagnéticas.", ("Cargas elétricas geram campos elétricos.", "Correntes elétricas e campos elétricos variáveis relacionam-se a campos magnéticos.", "Luz é uma onda eletromagnética."), ("OPENSTAX_PHYSICS", "NIST_SI")),
    (11, "Relatividade especial descreve física em referenciais inerciais, preservando as leis físicas e a velocidade da luz no vácuo para todos os observadores inerciais.", ("Transformações de Lorentz substituem as transformações de Galileu em altas velocidades.", "Dilatação do tempo e contração do comprimento são consequências da estrutura relativística.", "Massa e energia relacionam-se por E = mc² para a energia de repouso."), ("OPENSTAX_PHYSICS",)),
    (12, "Relatividade geral descreve gravitação como geometria dinâmica do espaço-tempo, em que matéria e energia influenciam a curvatura e corpos livres seguem geodésicas.", ("A teoria explica a precessão anômala do periélio de Mercúrio e o desvio gravitacional da luz.", "Ondas gravitacionais são perturbações propagantes da geometria do espaço-tempo e foram detectadas por interferômetros.", "Buracos negros aparecem como soluções das equações de Einstein sob condições adequadas."), ("NASA_SCIENCE",)),
    (13, "Mecânica quântica descreve sistemas microscópicos por estados, amplitudes, observáveis e probabilidades, com evolução governada por leis quânticas.", ("A equação de Schrödinger governa a evolução de muitos sistemas quânticos não relativísticos.", "Superposição permite combinar estados possíveis antes da medição.", "O princípio da incerteza estabelece limites fundamentais para pares de observáveis conjugados."), ("OPENSTAX_PHYSICS",)),
    (14, "Física de partículas e teoria quântica de campos descrevem partículas elementares e interações fundamentais em termos de campos quânticos.", ("O Modelo Padrão inclui quarks, léptons e bósons mediadores, além do bóson de Higgs.", "Prótons e nêutrons são compostos por quarks ligados pela interação forte.", "Neutrinos são léptons eletricamente neutros e possuem massa não nula."), ("PDG",)),
    (15, "Astronomia estuda corpos e fenômenos além da Terra: planetas, luas, pequenos corpos, estrelas, nebulosas, galáxias e outros objetos cósmicos.", ("O Sistema Solar possui oito planetas.", "O Sol é uma estrela da Via Láctea.", "Galáxias são sistemas gravitacionalmente ligados de estrelas, gás, poeira e matéria escura."), ("NASA_SCIENCE",)),
    (16, "Astronomia observacional mede a radiação e outras assinaturas de objetos celestes usando telescópios, detectores, espectrógrafos e técnicas de calibração.", ("Fotometria mede brilho; espectroscopia separa a luz por comprimento de onda.", "Astrometria mede posições e movimentos aparentes de objetos no céu.", "Diferentes faixas do espectro eletromagnético revelam propriedades físicas diferentes."), ("NASA_SCIENCE",)),
    (17, "Astrofísica estelar estuda estrutura, formação, evolução e morte das estrelas a partir de gravidade, termodinâmica, transporte de energia e reações nucleares.", ("Estrelas da sequência principal produzem energia principalmente por fusão de hidrogênio.", "Equilíbrio hidrostático equilibra, aproximadamente, pressão interna e gravidade em uma estrela estável.", "Massa inicial é um dos principais fatores que determinam a evolução estelar."), ("NASA_SCIENCE",)),
    (18, "Objetos compactos são remanescentes estelares extremamente densos, como anãs brancas e estrelas de nêutrons; buracos negros possuem uma região da qual nem a luz escapa para o exterior clássico.", ("Anãs brancas são sustentadas principalmente por pressão de degenerescência de elétrons.", "Estrelas de nêutrons concentram massa estelar em um raio de ordem de dezenas de quilômetros.", "O horizonte de eventos é uma fronteira causal, não uma superfície sólida."), ("NASA_SCIENCE",)),
    (19, "Cosmologia estuda a origem, evolução e estrutura em grande escala do Universo usando relatividade, observações astronômicas e física de partículas.", ("O Universo observável está em expansão.", "A radiação cósmica de fundo é uma relíquia térmica do Universo primordial.", "O modelo ΛCDM combina matéria comum, matéria escura, radiação e energia escura em um quadro cosmológico padrão."), ("NASA_SCIENCE",)),
    (20, "Física do espaço-tempo examina causalidade, geometrias relativísticas e propostas teóricas extremas. Wormholes transitáveis e métricas de warp permanecem ideias teóricas, não tecnologias demonstradas.", ("Soluções matemáticas possíveis não implicam viabilidade física ou tecnológica.", "Condições de energia e requisitos de matéria/energia exótica restringem várias geometrias especulativas.", "Não há demonstração de viagem macroscópica mais rápida que a luz por warp ou wormhole."), ("NASA_SCIENCE",)),
    (21, "Engenharia mecânica aplica mecânica, materiais, termodinâmica e fabricação ao projeto e análise de máquinas, estruturas e mecanismos.", ("Tensão relaciona força interna e área; deformação mede mudança relativa de forma ou comprimento.", "Projetos mecânicos consideram carga, rigidez, resistência, fadiga, tolerâncias e segurança.", "Rolamentos, engrenagens, eixos e atuadores são elementos recorrentes de máquinas."), ("NASA_SE", "NIST_ENGINEERING")),
    (22, "CAD cria modelos geométricos; CAE usa modelos computacionais para avaliar comportamento. FEA discretiza estruturas e campos; CFD resolve numericamente escoamentos.", ("Resultados numéricos dependem de hipóteses, propriedades, condições de contorno e qualidade de malha.", "Convergência de malha ajuda a verificar se a solução não depende excessivamente da discretização.", "Verificação pergunta se o modelo foi resolvido corretamente; validação compara o modelo com a realidade adequada ao uso."), ("NASA_SE", "NIST_ENGINEERING")),
    (23, "Engenharia elétrica trata geração, conversão, transmissão, distribuição e uso de energia elétrica, além de circuitos, máquinas, potência e instrumentação.", ("Tensão é diferença de potencial elétrico; corrente é fluxo de carga.", "Potência elétrica instantânea em corrente contínua pode ser expressa por P = VI.", "Transformadores transferem energia entre circuitos por indução eletromagnética em corrente alternada."), ("OPENSTAX_PHYSICS", "NIST_ENGINEERING")),
    (24, "Engenharia eletrônica projeta circuitos e sistemas que processam sinais e energia usando componentes como resistores, capacitores, semicondutores, conversores e processadores.", ("Diodos permitem condução fortemente assimétrica em muitas aplicações.", "Transistores podem atuar como chaves ou amplificadores.", "ADC converte sinais analógicos em representações digitais; DAC realiza o caminho inverso."), ("NIST_ENGINEERING", "IETF_RFC")),
    (25, "Sinais e sistemas estudam representações de sinais, resposta de sistemas, convolução, transformadas, amostragem, filtros e modulação.", ("Convolução descreve a saída de sistemas lineares invariantes no tempo a partir da entrada e da resposta ao impulso.", "A Transformada de Fourier relaciona representações no tempo e na frequência.", "Um sinal limitado em banda precisa ser amostrado com taxa suficiente para evitar aliasing."), ("OPENSTAX_MATH", "NIST_ENGINEERING")),
    (26, "Engenharia de controle usa modelos e realimentação para fazer sistemas seguirem referências, rejeitarem perturbações e permanecerem estáveis.", ("Controle PID combina ações proporcional, integral e derivativa.", "Espaço de estados representa sistemas por variáveis internas e equações de evolução.", "Estabilidade é uma propriedade central e deve ser analisada antes de otimizar desempenho."), ("NASA_SE", "NIST_ENGINEERING")),
    (27, "Robótica integra percepção, modelagem, planejamento e controle para permitir que máquinas atuem no mundo físico.", ("Cinemática direta calcula a pose a partir das juntas; cinemática inversa procura juntas para uma pose desejada.", "Robôs móveis podem combinar localização e mapeamento em SLAM.", "Planejamento sob incerteza precisa considerar erro de sensores, atuadores e ambiente."), ("NASA_SE", "NIST_ENGINEERING")),
    (28, "Mecatrônica integra mecânica, eletrônica, controle e software em sistemas físicos coordenados.", ("Sensores transformam grandezas físicas em sinais mensuráveis.", "Atuadores convertem comandos em ação física.", "Sistemas de tempo real precisam respeitar prazos de resposta além de produzir resultados corretos."), ("NASA_SE", "NIST_ENGINEERING")),
    (29, "Ciência dos materiais relaciona composição, estrutura, processamento e propriedades de metais, cerâmicas, polímeros, compósitos e materiais funcionais.", ("Estrutura cristalina e defeitos influenciam propriedades mecânicas, elétricas e térmicas.", "Fadiga pode causar falha após carregamentos cíclicos abaixo da resistência estática máxima.", "Seleção de materiais depende de propriedades, ambiente, processo, custo e segurança."), ("NIST_ENGINEERING",)),
    (30, "Manufatura transforma matéria-prima em componentes por processos como usinagem, conformação, união e fabricação aditiva, controlando tolerâncias e qualidade.", ("CNC automatiza movimentos de máquinas-ferramenta a partir de instruções programadas.", "Fabricação aditiva constrói peças camada a camada.", "Metrologia dimensional verifica se peças atendem especificações e tolerâncias."), ("NIST_ENGINEERING",)),
    (31, "Engenharia aeroespacial reúne aerodinâmica, estruturas, propulsão, aviônica, controle, navegação, missão e ambiente espacial.", ("Sustentação, arrasto, peso e empuxo são forças fundamentais em voo atmosférico.", "Foguetes funcionam por conservação de momento ao expelir massa em alta velocidade.", "GNC integra orientação, navegação e controle para determinar estado e comandar trajetória."), ("NASA_SE", "NASA_SCIENCE")),
    (32, "Mecânica orbital e astrodinâmica estudam trajetórias governadas por gravidade, manobras e perturbações de veículos e corpos celestes.", ("No problema ideal de dois corpos, órbitas ligadas são seções cônicas, tipicamente elipses.", "Transferência de Hohmann conecta duas órbitas coplanares circulares por duas queimas impulsivas ideais.", "Pontos de Lagrange são posições no problema restrito de três corpos onde forças efetivas permitem configurações relativas especiais."), ("NASA_SCIENCE",)),
    (33, "Óptica estuda propagação e interação da luz com matéria usando modelos geométricos e ondulatórios.", ("Reflexão ideal obedece igualdade entre ângulos de incidência e reflexão.", "Refração muda direção de propagação quando a velocidade da luz muda entre meios.", "Interferência e difração revelam o caráter ondulatório da luz."), ("OPENSTAX_PHYSICS",)),
    (34, "Fotônica estuda geração, controle, transmissão e detecção de luz em dispositivos como lasers, fibras, moduladores e circuitos ópticos.", ("Laser produz luz por emissão estimulada em uma cavidade ou arquitetura equivalente.", "Fibras ópticas guiam luz por sua estrutura de índices e condições de propagação.", "Fotodetectores convertem radiação óptica em sinais mensuráveis."), ("NIST_ENGINEERING",)),
    (35, "Holografia registra e reconstrói informação de frente de onda por interferência; displays avançados tentam reproduzir profundidade, paralaxe ou campos luminosos.", ("Hologramas registram informação de fase indiretamente por padrões de interferência.", "Displays de campo de luz produzem diferentes raios para diferentes direções de observação.", "Realidade aumentada combina informação digital com a visão do ambiente real."), ("NIST_ENGINEERING",)),
    (36, "Química estuda composição, estrutura, propriedades e transformações da matéria, de átomos e moléculas a materiais e sistemas bioquímicos.", ("Elementos químicos são definidos pelo número de prótons no núcleo.", "Reações químicas reorganizam átomos e ligações sem criar ou destruir carga elétrica total.", "A tabela periódica organiza elementos por número atômico e recorrência de propriedades."), ("IUPAC_GOLD", "OPENSTAX_CHEM", "PUBCHEM")),
    (37, "Energia pode ser armazenada, transferida e convertida entre formas. Engenharia energética compara eficiência, densidade, custo, segurança, emissões e disponibilidade.", ("Energia total é conservada em sistemas fechados apropriados, embora possa mudar de forma.", "Baterias armazenam energia eletroquimicamente.", "Fissão divide núcleos pesados; fusão combina núcleos leves e ainda exige sistemas complexos para produção controlada de energia."), ("OPENSTAX_PHYSICS", "NASA_SCIENCE")),
    (38, "Biologia estuda seres vivos em níveis que vão de moléculas e células a organismos, populações e ecossistemas.", ("A célula é a unidade básica de organização dos seres vivos.", "DNA armazena informação genética em organismos celulares.", "Evolução por seleção natural e outros mecanismos altera frequências de características hereditárias em populações ao longo das gerações."), ("OPENSTAX_BIO", "OPENSTAX_ANATOMY")),
    (39, "Neurociência estuda sistema nervoso, neurônios, sinapses, circuitos e bases neurais de percepção, movimento, memória, emoção e cognição.", ("Neurônios transmitem sinais por mudanças elétricas de membrana e comunicação sináptica.", "O sistema nervoso central inclui encéfalo e medula espinal.", "Plasticidade neural descreve mudanças na força ou organização de circuitos com experiência, desenvolvimento ou lesão."), ("OPENSTAX_ANATOMY", "NCBI_NEURO")),
    (40, "Ciência da computação estuda representação e processamento de informação por algoritmos e sistemas computacionais.", ("Algoritmos são procedimentos finitos para resolver classes de problemas.", "Estruturas de dados organizam informação para operações eficientes.", "Sistemas operacionais gerenciam recursos de hardware e oferecem abstrações a programas."), ("OPENSTAX_CS", "IETF_RFC", "NIST_AI")),
    (41, "Inteligência artificial desenvolve sistemas capazes de realizar tarefas como percepção, previsão, linguagem, busca, planejamento e decisão.", ("Machine learning ajusta modelos a partir de dados ou experiência.", "Transformers usam mecanismos de atenção e são uma arquitetura importante em modelos modernos de linguagem e visão.", "Avaliação de IA deve medir desempenho, robustez, incerteza, segurança e limites no contexto de uso."), ("NIST_AI",)),
    (42, "Computação científica usa algoritmos numéricos, software e hardware para resolver modelos matemáticos, analisar dados e reproduzir resultados.", ("Aritmética de ponto flutuante possui erro de arredondamento finito.", "Métodos numéricos precisam de análise de estabilidade, convergência e erro.", "Reprodutibilidade melhora com dados, versões, parâmetros e código registrados."), ("NIST_ENGINEERING", "OPENSTAX_MATH")),
    (43, "Simulação científica representa aspectos de um sistema real ou teórico em um modelo computacional para testar hipóteses, prever comportamentos e comparar cenários.", ("Todo modelo é uma simplificação com domínio de validade.", "Verificação avalia se as equações/modelos foram implementados e resolvidos corretamente.", "Validação compara previsões com observações adequadas ao uso pretendido."), ("NASA_SE", "NIST_ENGINEERING")),
    (44, "Percepção computacional transforma dados de câmeras e outros sensores em estimativas sobre objetos, geometria, movimento e cenas.", ("Segmentação atribui classes ou instâncias a regiões de uma imagem.", "Estimativa de pose busca posição e orientação de objetos ou corpos.", "Reconstrução 3D infere estrutura espacial a partir de uma ou mais observações e modelos."), ("NIST_AI",)),
    (45, "Sensoriamento mede grandezas físicas por transdutores e cadeias de aquisição, sempre sujeito a faixa, resolução, ruído, calibração e incerteza.", ("Calibração relaciona a indicação de um instrumento a referências conhecidas.", "Ruído limita a precisão de medições.", "Fusão sensorial combina observações para obter estimativas mais robustas quando os modelos são adequados."), ("NIST_SI", "NIST_ENGINEERING")),
    (46, "Acústica e áudio estudam geração, propagação, percepção e processamento do som.", ("Som em ar é uma onda mecânica de pressão e precisa de meio material para se propagar.", "Frequência relaciona-se à periodicidade; amplitude relaciona-se à magnitude da variação física.", "Áudio digital representa sinais acústicos amostrados e quantizados."), ("OPENSTAX_PHYSICS",)),
    (47, "Instrumentação científica transforma fenômenos em dados por sensores, condicionamento, aquisição, calibração e análise.", ("Uma cadeia de medição inclui o mensurando, sensor, eletrônica, conversão e processamento.", "Calibração não elimina automaticamente todos os erros; a incerteza precisa ser avaliada.", "Osciloscópios mostram sinais elétricos em função do tempo; espectrômetros separam sinais por frequência, energia ou comprimento de onda."), ("NIST_SI", "NIST_ENGINEERING")),
    (48, "Engenharia de sistemas coordena objetivos, requisitos, arquitetura, interfaces, integração, verificação e validação ao longo do ciclo de vida de sistemas complexos.", ("Requisitos devem ser claros, verificáveis e rastreáveis.", "Interfaces mal definidas são fonte recorrente de falhas de integração.", "Verificação pergunta se o sistema foi construído conforme especificado; validação pergunta se atende ao uso pretendido."), ("NASA_SE",)),
    (49, "Engenharia de confiabilidade estuda probabilidade e modos de falha, manutenção, redundância, diagnóstico e risco ao longo do tempo.", ("MTBF é uma métrica de tempo médio entre falhas em contextos apropriados; não é uma garantia individual de vida útil.", "FMEA analisa modos de falha, efeitos e prioridades de tratamento.", "Redundância pode aumentar tolerância a falhas, mas também adiciona complexidade e modos comuns de falha."), ("NASA_SE", "NIST_ENGINEERING")),
    (50, "Pesquisa científica e literatura envolvem formular buscas, ler criticamente estudos, rastrear referências, comparar resultados e sintetizar evidências.", ("Artigos primários relatam pesquisa original; revisões sintetizam literatura existente.", "Revisões sistemáticas usam critérios explícitos de busca, seleção e síntese.", "Peer review é um filtro de qualidade, não uma garantia de que uma conclusão esteja correta."), ("NIST_SI",)),
    (51, "Gestão do conhecimento organiza conceitos, entidades, relações, metadados e proveniência para tornar informação pesquisável, reutilizável e auditável.", ("Taxonomias organizam categorias; ontologias modelam entidades, relações e restrições de forma mais explícita.", "Grafos de conhecimento representam entidades como nós e relações como arestas.", "Proveniência registra de onde uma afirmação veio e como foi transformada."), ("NIST_AI", "IETF_RFC")),
    (52, "Avaliação da confiabilidade da informação considera fonte, evidência, independência, data, consenso, conflito e grau de incerteza.", ("Uma afirmação forte exige evidência proporcionalmente forte.", "Confirmação independente reduz risco de erro compartilhado entre fontes.", "Informação pode ser correta e ainda estar desatualizada para uma pergunta temporal."), ("NIST_SI",)),
    (53, "Engenharia experimental transforma hipóteses e requisitos em experimentos instrumentados, dados, análise, incerteza e comparação com modelos.", ("Um experimento deve definir variáveis, controles e critérios de análise antes de interpretar o resultado.", "Repetições ajudam a estimar variabilidade.", "Comparar teoria e experimento exige considerar incerteza nos dois lados."), ("NIST_SI", "NASA_SE")),
    (54, "Invenção e desenvolvimento tecnológico avançam de problema e requisitos a alternativas, modelos, protótipos, testes, falhas, correções e documentação.", ("Protótipos reduzem incerteza, mas não equivalem a produto validado.", "Trade studies comparam alternativas por critérios explícitos.", "Níveis de maturidade tecnológica descrevem evidência de maturidade crescente, não qualidade absoluta da ideia."), ("NASA_SE",)),
    (55, "Tecnologias de fronteira misturam pesquisa demonstrada, protótipos e ideias especulativas; cada afirmação deve deixar claro o nível de evidência.", ("Teletransporte quântico transfere estado quântico/informação quântica entre sistemas, não pessoas ou matéria macroscópica.", "Fusão controlada é área experimental ativa; demonstrações científicas não equivalem automaticamente a geração comercial competitiva.", "Warp drives e wormholes transitáveis permanecem conceitos teóricos sem demonstração tecnológica."), ("PDG", "NASA_SCIENCE", "NIST_AI")),
    (56, "Ciências da Terra integram geologia, geofísica, meteorologia, climatologia, oceanografia, hidrologia, geodesia, geografia e ecologia para estudar o planeta.", ("A litosfera é dividida em placas tectônicas que se movem umas em relação às outras.", "A maior parte dos terremotos concentra-se em falhas e limites de placas.", "Clima descreve padrões estatísticos de longo prazo; tempo descreve condições atmosféricas de curto prazo."), ("USGS", "NOAA", "IPCC")),
)
THEME_FOUNDATIONS = {
    row[0]: ThemeFoundation(row[0], row[1], tuple(row[2]), tuple(row[3]))
    for row in THEME_FOUNDATION_ROWS
}

if set(THEME_FOUNDATIONS) != {theme.id for theme in THEMES}:
    raise RuntimeError("A base factual deve cobrir exatamente os 56 temas curriculares.")


COUNTRY_CAPITALS = {
    "franca": ("França", "Paris", ("EU_FRANCE",)),
    "brasil": ("Brasil", "Brasília", ("UN_CAPITALS",)),
    "argentina": ("Argentina", "Buenos Aires", ("UN_CAPITALS",)),
    "chile": ("Chile", "Santiago", ("UN_CAPITALS",)),
    "uruguai": ("Uruguai", "Montevidéu", ("UN_CAPITALS",)),
    "paraguai": ("Paraguai", "Assunção", ("UN_CAPITALS",)),
    "peru": ("Peru", "Lima", ("UN_CAPITALS",)),
    "colombia": ("Colômbia", "Bogotá", ("UN_CAPITALS",)),
    "venezuela": ("Venezuela", "Caracas", ("UN_CAPITALS",)),
    "mexico": ("México", "Cidade do México", ("UN_CAPITALS",)),
    "estados unidos": ("Estados Unidos", "Washington, D.C.", ("UN_CAPITALS",)),
    "eua": ("Estados Unidos", "Washington, D.C.", ("UN_CAPITALS",)),
    "canada": ("Canadá", "Ottawa", ("UN_CAPITALS",)),
    "portugal": ("Portugal", "Lisboa", ("UN_CAPITALS",)),
    "espanha": ("Espanha", "Madri", ("UN_CAPITALS",)),
    "italia": ("Itália", "Roma", ("UN_CAPITALS",)),
    "alemanha": ("Alemanha", "Berlim", ("UN_CAPITALS",)),
    "reino unido": ("Reino Unido", "Londres", ("UN_CAPITALS",)),
    "irlanda": ("Irlanda", "Dublin", ("UN_CAPITALS",)),
    "belgica": ("Bélgica", "Bruxelas", ("UN_CAPITALS",)),
    "austria": ("Áustria", "Viena", ("UN_CAPITALS",)),
    "polonia": ("Polônia", "Varsóvia", ("UN_CAPITALS",)),
    "grecia": ("Grécia", "Atenas", ("UN_CAPITALS",)),
    "turquia": ("Turquia", "Ancara", ("UN_CAPITALS",)),
    "russia": ("Rússia", "Moscou", ("UN_CAPITALS",)),
    "ucrania": ("Ucrânia", "Kyiv", ("UN_CAPITALS",)),
    "china": ("China", "Pequim", ("UN_CAPITALS",)),
    "japao": ("Japão", "Tóquio", ("UN_CAPITALS",)),
    "coreia do sul": ("Coreia do Sul", "Seul", ("UN_CAPITALS",)),
    "india": ("Índia", "Nova Délhi", ("UN_CAPITALS",)),
    "australia": ("Austrália", "Canberra", ("UN_CAPITALS",)),
    "nova zelandia": ("Nova Zelândia", "Wellington", ("UN_CAPITALS",)),
    "egito": ("Egito", "Cairo", ("UN_CAPITALS",)),
    "marrocos": ("Marrocos", "Rabat", ("UN_CAPITALS",)),
    "nigeria": ("Nigéria", "Abuja", ("UN_CAPITALS",)),
    "quenia": ("Quênia", "Nairóbi", ("UN_CAPITALS",)),
    "arabia saudita": ("Arábia Saudita", "Riad", ("UN_CAPITALS",)),
    "emirados arabes unidos": ("Emirados Árabes Unidos", "Abu Dhabi", ("UN_CAPITALS",)),
}

COUNTRY_CAPITALS.update({
    "suecia": ("Suécia", "Estocolmo", ("UN_CAPITALS",)),
    "noruega": ("Noruega", "Oslo", ("UN_CAPITALS",)),
    "dinamarca": ("Dinamarca", "Copenhague", ("UN_CAPITALS",)),
    "finlandia": ("Finlândia", "Helsinque", ("UN_CAPITALS",)),
    "islandia": ("Islândia", "Reykjavík", ("UN_CAPITALS",)),
    "republica tcheca": ("Tchéquia", "Praga", ("UN_CAPITALS",)),
    "tchequia": ("Tchéquia", "Praga", ("UN_CAPITALS",)),
    "hungria": ("Hungria", "Budapeste", ("UN_CAPITALS",)),
    "romenia": ("Romênia", "Bucareste", ("UN_CAPITALS",)),
    "bulgaria": ("Bulgária", "Sófia", ("UN_CAPITALS",)),
    "croacia": ("Croácia", "Zagreb", ("UN_CAPITALS",)),
    "servia": ("Sérvia", "Belgrado", ("UN_CAPITALS",)),
    "eslovenia": ("Eslovênia", "Liubliana", ("UN_CAPITALS",)),
    "eslovaquia": ("Eslováquia", "Bratislava", ("UN_CAPITALS",)),
    "estonia": ("Estônia", "Tallinn", ("UN_CAPITALS",)),
    "letonia": ("Letônia", "Riga", ("UN_CAPITALS",)),
    "lituania": ("Lituânia", "Vilnius", ("UN_CAPITALS",)),
    "tailandia": ("Tailândia", "Bangcoc", ("UN_CAPITALS",)),
    "vietna": ("Vietnã", "Hanói", ("UN_CAPITALS",)),
    "filipinas": ("Filipinas", "Manila", ("UN_CAPITALS",)),
    "singapura": ("Singapura", "Singapura", ("UN_CAPITALS",)),
    "paquistao": ("Paquistão", "Islamabad", ("UN_CAPITALS",)),
    "bangladesh": ("Bangladesh", "Daca", ("UN_CAPITALS",)),
    "nepal": ("Nepal", "Catmandu", ("UN_CAPITALS",)),
    "ira": ("Irã", "Teerã", ("UN_CAPITALS",)),
    "iraque": ("Iraque", "Bagdá", ("UN_CAPITALS",)),
    "jordania": ("Jordânia", "Amã", ("UN_CAPITALS",)),
    "catar": ("Catar", "Doha", ("UN_CAPITALS",)),
    "kuwait": ("Kuwait", "Cidade do Kuwait", ("UN_CAPITALS",)),
    "oma": ("Omã", "Mascate", ("UN_CAPITALS",)),
    "etiopia": ("Etiópia", "Adis Abeba", ("UN_CAPITALS",)),
    "ghana": ("Gana", "Acra", ("UN_CAPITALS",)),
    "senegal": ("Senegal", "Dacar", ("UN_CAPITALS",)),
    "tanzania": ("Tanzânia", "Dodoma", ("UN_CAPITALS",)),
    "angola": ("Angola", "Luanda", ("UN_CAPITALS",)),
    "mocambique": ("Moçambique", "Maputo", ("UN_CAPITALS",)),
    "argelia": ("Argélia", "Argel", ("UN_CAPITALS",)),
    "tunisia": ("Tunísia", "Túnis", ("UN_CAPITALS",)),
})
FACT_ROWS = (
    ("human.bones", ("quantos ossos o corpo humano tem", "quantos ossos tem o corpo humano", "numero de ossos no corpo humano", "número de ossos no corpo humano", "ossos corpo humano"), "O esqueleto humano adulto é tradicionalmente descrito com 206 ossos. Ao nascer há cerca de 270, e parte deles se funde durante o crescimento; o total adulto pode variar um pouco entre pessoas e conforme o critério de contagem.", (38,), ("NCBI_BONE",)),
    ("human.heart.function", ("para que serve o coracao", "qual a funcao do coracao", "o que o coracao faz", "funcao do coracao", "coração serve para que"), "O coração é a bomba muscular do sistema circulatório: impulsiona o sangue para os pulmões e para o restante do corpo, entregando oxigênio e nutrientes e ajudando a transportar dióxido de carbono e outros resíduos.", (38,), ("NHLBI_HEART",)),
    ("human.heart.chambers", ("quantas camaras tem o coracao", "quantas cavidades tem o coracao", "partes principais do coracao"), "O coração humano tem quatro câmaras: dois átrios, que recebem sangue, e dois ventrículos, que o bombeiam para os pulmões e para o corpo.", (38,), ("NHLBI_HEART",)),
    ("human.lungs.function", ("para que serve o pulmao", "para que servem os pulmoes", "qual a funcao do pulmao", "qual a funcao dos pulmoes", "o que os pulmoes fazem"), "Os pulmões realizam a troca gasosa: levam oxigênio do ar para o sangue e removem dióxido de carbono do sangue para ser expirado. Essa troca ocorre principalmente nos alvéolos.", (38,), ("NHLBI_LUNGS",)),
    ("human.brain.function", ("para que serve o cerebro", "qual a funcao do cerebro", "o que o cerebro faz"), "O cérebro integra informações sensoriais, coordena movimentos e funções corporais e participa de linguagem, memória, emoção, planejamento, aprendizagem e tomada de decisão.", (39,), ("OPENSTAX_ANATOMY",)),
    ("human.liver.function", ("para que serve o figado", "qual a funcao do figado", "o que o figado faz"), "O fígado participa do metabolismo de nutrientes, produz bile, sintetiza proteínas importantes do sangue, armazena substâncias e transforma compostos para facilitar sua eliminação.", (38, 36), ("OPENSTAX_ANATOMY",)),
    ("human.kidneys.function", ("para que servem os rins", "qual a funcao dos rins", "o que os rins fazem"), "Os rins filtram o plasma sanguíneo para formar urina e ajudam a regular água, eletrólitos, equilíbrio ácido-base e pressão arterial; também participam de funções hormonais.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.stomach.function", ("para que serve o estomago", "qual a funcao do estomago", "o que o estomago faz"), "O estômago armazena e mistura alimento e inicia etapas importantes da digestão química, usando ácido e enzimas antes de liberar o conteúdo gradualmente ao intestino delgado.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.intestines.function", ("para que serve o intestino", "funcao do intestino", "o que o intestino faz"), "O intestino delgado realiza grande parte da digestão e absorção de nutrientes; o intestino grosso absorve água e eletrólitos e participa da formação das fezes.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.pancreas.function", ("para que serve o pancreas", "qual a funcao do pancreas", "o que o pancreas faz"), "O pâncreas tem funções digestivas e endócrinas: libera enzimas e bicarbonato no intestino e produz hormônios como insulina e glucagon, que ajudam a regular a glicose no sangue.", (38, 36), ("OPENSTAX_ANATOMY",)),
    ("human.skin.function", ("para que serve a pele", "qual a funcao da pele", "o que a pele faz"), "A pele funciona como barreira contra o ambiente, reduz perda de água, participa da regulação térmica e contém receptores sensoriais; também contribui para defesa e síntese de vitamina D.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.organ.systems", ("quantos sistemas tem o corpo humano", "sistemas do corpo humano", "principais sistemas do corpo humano"), "Uma divisão didática comum reconhece 11 sistemas: tegumentar, esquelético, muscular, nervoso, endócrino, cardiovascular, linfático/imunológico, respiratório, digestório, urinário e reprodutor.", (38,), ("OPENSTAX_ANATOMY",)),
    ("culture.michael_jackson", ("quem e michael jackson", "quem foi michael jackson", "michael jackson", "quem era michael jackson"), "Michael Jackson foi um cantor, compositor e dançarino norte-americano, nascido em 1958 e morto em 2009. Começou profissionalmente no Jackson 5 e teve uma carreira solo de enorme influência na música pop; o álbum Thriller, de 1982, tornou-se um marco de sua carreira.", (), ("GRAMMY_MJ",)),
    ("earth.dinosaurs.when", ("quando os dinossauros existiram", "em que epoca os dinossauros existiram", "quando viveram os dinossauros", "era dos dinossauros", "dinossauros existiram quando"), "Os dinossauros não aviários viveram aproximadamente entre 245 e 66 milhões de anos atrás, durante a Era Mesozoica, dividida nos períodos Triássico, Jurássico e Cretáceo.", (56, 38), ("NHM_DINO",)),
    ("geo.continents", ("quantos continentes existem", "quais sao os continentes", "continentes do mundo"), "No modelo de sete continentes, usado amplamente em referências internacionais, eles são África, Antártida, Ásia, Europa, América do Norte, América do Sul e Oceania/Austrália. Outros sistemas educacionais agrupam as Américas ou Europa e Ásia de forma diferente.", (56,), ("UN_CAPITALS",)),
    ("geo.oceans", ("quantos oceanos existem", "quais sao os oceanos", "oceanos do mundo"), "A divisão moderna mais comum reconhece cinco oceanos: Pacífico, Atlântico, Índico, Ártico e Austral.", (56,), ("NOAA",)),
    ("astronomy.solar_system.planets", ("quantos planetas tem o sistema solar", "quais sao os planetas do sistema solar", "planetas do sistema solar"), "O Sistema Solar tem oito planetas: Mercúrio, Vênus, Terra, Marte, Júpiter, Saturno, Urano e Netuno.", (15,), ("NASA_SCIENCE",)),
)

EXTRA_FACT_ROWS = (
    ("human.blood.function", ("para que serve o sangue", "qual a funcao do sangue", "o que o sangue faz"), "O sangue transporta oxigênio, dióxido de carbono, nutrientes, hormônios, calor e resíduos; também participa da defesa imunológica, da coagulação e da manutenção do equilíbrio interno do organismo.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.red_cells", ("o que fazem as hemacias", "funcao das hemacias", "para que servem os globulos vermelhos"), "As hemácias, ou glóbulos vermelhos, contêm hemoglobina e transportam principalmente oxigênio dos pulmões aos tecidos; também carregam parte do dióxido de carbono de volta aos pulmões.", (38,), ("OPENSTAX_ANATOMY", "NHLBI_LUNGS")),
    ("human.white_cells", ("o que fazem os leucocitos", "funcao dos leucocitos", "para que servem os globulos brancos"), "Leucócitos, ou glóbulos brancos, são células do sistema imune que ajudam a reconhecer e combater microrganismos, células alteradas e outros agentes potencialmente nocivos.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.diaphragm", ("para que serve o diafragma", "qual a funcao do diafragma", "o que o diafragma faz"), "O diafragma é o principal músculo da inspiração. Quando se contrai, aumenta o volume da cavidade torácica e ajuda a puxar ar para os pulmões.", (38,), ("OPENSTAX_ANATOMY", "NHLBI_LUNGS")),
    ("human.trachea", ("para que serve a traqueia", "qual a funcao da traqueia", "o que a traqueia faz"), "A traqueia conduz o ar entre a laringe e os brônquios. Sua parede possui anéis cartilaginosos que ajudam a manter a via aérea aberta.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.nervous_system", ("para que serve o sistema nervoso", "funcao do sistema nervoso", "o que faz o sistema nervoso"), "O sistema nervoso recebe informações sensoriais, integra sinais e coordena respostas rápidas, movimentos, funções automáticas e processos cognitivos por meio do encéfalo, medula espinal e nervos.", (38, 39), ("OPENSTAX_ANATOMY",)),
    ("human.endocrine_system", ("para que serve o sistema endocrino", "funcao do sistema endocrino", "o que faz o sistema endocrino"), "O sistema endócrino usa hormônios liberados no sangue para regular processos como crescimento, metabolismo, reprodução, resposta ao estresse e equilíbrio de água e sais.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.muscular_system", ("para que serve o sistema muscular", "funcao dos musculos", "o que os musculos fazem"), "Os músculos produzem força e movimento. Músculos esqueléticos movimentam o corpo e ajudam a manter postura; músculo cardíaco bombeia sangue e músculo liso atua em órgãos internos.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.teeth", ("quantos dentes tem um adulto", "quantos dentes o ser humano adulto tem", "numero de dentes adulto"), "A dentição humana adulta completa costuma ter 32 dentes, incluindo quatro terceiros molares; algumas pessoas têm menos porque sisos podem não se desenvolver ou ser removidos.", (38,), ("OPENSTAX_ANATOMY",)),
    ("biology.cell", ("o que e uma celula", "o que sao celulas", "qual a unidade basica da vida"), "A célula é a unidade estrutural e funcional básica dos organismos vivos. Ela possui membrana, material genético e sistemas químicos que sustentam suas atividades.", (38,), ("OPENSTAX_BIO",)),
    ("biology.dna", ("o que e dna", "para que serve o dna", "qual a funcao do dna"), "DNA é a molécula que armazena a maior parte da informação genética dos organismos celulares. Sua sequência contém instruções usadas na produção de RNAs e, direta ou indiretamente, de proteínas.", (38,), ("OPENSTAX_BIO",)),
    ("biology.gene", ("o que e um gene", "o que sao genes", "para que servem os genes"), "Um gene é uma região de DNA que contribui para a produção de um produto funcional, como um RNA ou proteína. Genes fazem parte do sistema de herança e regulação biológica.", (38,), ("OPENSTAX_BIO",)),
    ("human.chromosomes", ("quantos cromossomos o ser humano tem", "numero de cromossomos humanos", "quantos pares de cromossomos temos"), "A maioria das células somáticas humanas possui 46 cromossomos organizados em 23 pares. Gametas normalmente possuem 23, e algumas células maduras, como hemácias, não possuem núcleo.", (38,), ("OPENSTAX_BIO",)),
    ("biology.mitochondria", ("para que serve a mitocondria", "qual a funcao da mitocondria", "o que a mitocondria faz"), "Mitocôndrias são organelas de células eucarióticas que participam intensamente da respiração celular e da produção de ATP, uma das principais formas de energia química utilizável pela célula.", (38,), ("OPENSTAX_BIO",)),
    ("biology.photosynthesis", ("o que e fotossintese", "como funciona a fotossintese", "para que serve a fotossintese"), "Fotossíntese converte energia luminosa em energia química. Em plantas, algas e cianobactérias, a fotossíntese oxigênica usa água e dióxido de carbono para formar matéria orgânica e libera oxigênio.", (38,), ("OPENSTAX_BIO",)),
    ("biology.evolution", ("o que e evolucao biologica", "como funciona a evolucao", "o que e selecao natural"), "Evolução biológica é a mudança de características hereditárias de populações ao longo das gerações. Seleção natural é um dos mecanismos evolutivos, junto com mutação, deriva genética e fluxo gênico.", (38,), ("OPENSTAX_BIO",)),
    ("biology.bacteria", ("o que sao bacterias", "bacteria e um ser vivo", "bacterias sao celulas"), "Bactérias são organismos celulares procarióticos. Não possuem núcleo delimitado por membrana e apresentam enorme diversidade metabólica e ecológica.", (38,), ("OPENSTAX_BIO",)),
    ("biology.virus", ("o que e um virus", "virus e uma celula", "como virus se reproduz"), "Vírus são agentes infecciosos acelulares formados por material genético envolto por componentes proteicos e, em alguns casos, envelope lipídico. Para se replicar, dependem da maquinaria de células hospedeiras.", (38,), ("OPENSTAX_BIO",)),
    ("chem.water", ("qual a formula da agua", "formula quimica da agua", "do que a agua e feita"), "A fórmula molecular da água é H₂O: cada molécula possui dois átomos de hidrogênio ligados a um átomo de oxigênio.", (36,), ("OPENSTAX_CHEM",)),
    ("chem.atom", ("o que e um atomo", "o que sao atomos", "definicao de atomo"), "Um átomo é a menor unidade que ainda caracteriza um elemento químico. Possui um núcleo com prótons e, na maioria dos átomos, nêutrons, cercado por elétrons.", (36,), ("IUPAC_GOLD",)),
    ("chem.element", ("o que e um elemento quimico", "o que sao elementos quimicos", "definicao de elemento quimico"), "Elemento químico é definido pelo número de prótons no núcleo de seus átomos, chamado número atômico. Átomos do mesmo elemento podem ter diferentes números de nêutrons, formando isótopos.", (36,), ("IUPAC_GOLD",)),
    ("physics.speed_light", ("qual a velocidade da luz", "velocidade da luz no vacuo", "quanto e a velocidade da luz"), "A velocidade da luz no vácuo é exatamente 299 792 458 metros por segundo no Sistema Internacional de Unidades.", (10, 11, 33), ("NIST_SI",)),
    ("physics.gravity", ("o que e gravidade", "como funciona a gravidade", "qual a gravidade da terra"), "Gravidade é a interação associada à atração entre massas e energia. Perto da superfície da Terra, a aceleração gravitacional é aproximadamente 9,8 m/s², variando ligeiramente com latitude e altitude.", (7, 12, 56), ("OPENSTAX_PHYSICS",)),
    ("astronomy.sun", ("o que e o sol", "o sol e uma estrela", "que tipo de objeto e o sol"), "O Sol é a estrela no centro do Sistema Solar. Sua gravidade mantém planetas e muitos outros corpos em órbita, e sua energia é produzida principalmente por fusão nuclear em seu núcleo.", (15, 17), ("NASA_SCIENCE",)),
    ("astronomy.moon", ("o que e a lua", "a lua e satelite de que", "lua e satelite natural"), "A Lua é o satélite natural da Terra. Ela orbita nosso planeta e sua gravidade é a principal responsável pelas marés oceânicas, junto com a influência do Sol.", (15, 32), ("NASA_SCIENCE", "NOAA")),
    ("astronomy.light_year", ("o que e ano luz", "quanto mede um ano luz", "ano luz e tempo ou distancia"), "Ano-luz é uma unidade de distância, não de tempo: é a distância que a luz percorre no vácuo em um ano, aproximadamente 9,46 trilhões de quilômetros.", (15, 16), ("NASA_SCIENCE",)),
    ("earth.rotation", ("quanto tempo a terra leva para girar", "duracao da rotacao da terra", "quanto dura um dia na terra"), "A Terra gira em torno de seu eixo em cerca de 24 horas em relação ao Sol; o período de rotação sideral é de aproximadamente 23 horas e 56 minutos.", (15, 32, 56), ("NASA_SCIENCE",)),
    ("earth.orbit", ("quanto tempo a terra leva para dar volta no sol", "duracao da translacao da terra", "quanto dura um ano terrestre"), "A Terra leva cerca de 365,25 dias para completar uma órbita ao redor do Sol. O calendário usa ajustes, como anos bissextos, para acompanhar essa duração.", (15, 32, 56), ("NASA_SCIENCE",)),
    ("earth.layers", ("quais sao as camadas da terra", "estrutura interna da terra", "camadas internas da terra"), "Em uma divisão composicional básica, a Terra possui crosta, manto e núcleo. O núcleo é subdividido em uma parte externa líquida e uma parte interna sólida.", (56,), ("USGS",)),
    ("earth.plates", ("o que sao placas tectonicas", "como funcionam as placas tectonicas", "tectonica de placas"), "A litosfera terrestre é fragmentada em placas tectônicas que se movem lentamente sobre camadas mais dúcteis do manto superior. Suas interações ajudam a explicar terremotos, vulcanismo e formação de montanhas.", (56,), ("USGS",)),
    ("earth.earthquake", ("o que e um terremoto", "como acontece um terremoto", "por que ocorrem terremotos"), "Terremotos ocorrem quando energia acumulada nas rochas é liberada subitamente, geralmente pelo deslizamento em falhas. As ondas sísmicas propagam essa energia pelo planeta.", (56,), ("USGS",)),
    ("earth.volcano", ("o que e um vulcao", "como funciona um vulcao", "por que vulcoes entram em erupcao"), "Vulcões são estruturas pelas quais magma, gases e fragmentos podem alcançar a superfície. O vulcanismo está ligado à geração e ascensão de magma e é comum em limites de placas e pontos quentes.", (56,), ("USGS",)),
    ("earth.water_cycle", ("o que e ciclo da agua", "como funciona o ciclo da agua", "ciclo hidrologico"), "O ciclo da água descreve a circulação contínua da água entre atmosfera, superfície e subsolo por processos como evaporação, transpiração, condensação, precipitação, infiltração e escoamento.", (56,), ("USGS",)),
    ("geo.equator", ("o que e a linha do equador", "qual a latitude do equador", "linha do equador"), "A Linha do Equador é o paralelo de latitude 0°. Ela divide convencionalmente a Terra nos hemisférios Norte e Sul.", (56,), ("USGS",)),
    ("geo.coordinates", ("o que e latitude e longitude", "para que servem latitude e longitude", "coordenadas geograficas"), "Latitude mede posição norte-sul em relação ao Equador; longitude mede posição leste-oeste em relação ao meridiano de referência. Juntas, permitem localizar pontos na superfície terrestre.", (56,), ("USGS",)),
    ("geo.pacific", ("qual e o maior oceano", "maior oceano do mundo", "qual o maior oceano da terra"), "O Oceano Pacífico é o maior oceano da Terra em área.", (56,), ("NOAA",)),
    ("earth.ocean_cover", ("quanto da terra e coberta por oceanos", "porcentagem da terra coberta por agua", "quanto da superficie terrestre e oceano"), "Os oceanos cobrem cerca de 71% da superfície da Terra e contêm a grande maioria da água do planeta.", (56,), ("NOAA",)),
    ("earth.weather_climate", ("qual a diferenca entre tempo e clima", "tempo e clima sao iguais", "diferenca de clima e tempo"), "Tempo descreve condições atmosféricas de curto prazo em um lugar; clima descreve padrões e estatísticas dessas condições ao longo de períodos longos.", (56,), ("NOAA", "IPCC")),
)

GENERAL_FACT_ROWS_V2_A = (
    ("human.esophagus", ("para que serve o esofago", "qual a funcao do esofago", "o que o esofago faz"), "O esôfago é um tubo muscular que conduz alimento e líquidos da faringe ao estômago, principalmente por movimentos coordenados de peristaltismo.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.gallbladder", ("para que serve a vesicula biliar", "qual a funcao da vesicula biliar", "o que a vesicula faz"), "A vesícula biliar armazena e concentra a bile produzida pelo fígado e a libera no intestino delgado, onde a bile ajuda na digestão e absorção de gorduras.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.spleen", ("para que serve o baco", "qual a funcao do baco", "o que o baco faz"), "O baço filtra o sangue, participa de respostas imunes e ajuda a remover células sanguíneas envelhecidas ou danificadas.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.bladder", ("para que serve a bexiga", "qual a funcao da bexiga", "o que a bexiga faz"), "A bexiga urinária é um órgão muscular que armazena temporariamente a urina produzida pelos rins até a micção.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.thyroid", ("para que serve a tireoide", "qual a funcao da tireoide", "o que a tireoide faz"), "A tireoide produz hormônios que influenciam o metabolismo, o crescimento e o desenvolvimento; também produz calcitonina, envolvida na regulação do cálcio.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.pituitary", ("para que serve a hipofise", "qual a funcao da hipofise", "o que a hipofise faz"), "A hipófise produz ou libera hormônios que participam do crescimento, reprodução, equilíbrio de água e regulação de outras glândulas endócrinas.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.adrenal", ("para que servem as suprarrenais", "qual a funcao das suprarrenais", "glandulas suprarrenais"), "As glândulas suprarrenais produzem hormônios como cortisol, aldosterona e catecolaminas, envolvidos em metabolismo, equilíbrio de sais, pressão arterial e respostas ao estresse.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.bone_marrow", ("para que serve a medula ossea", "qual a funcao da medula ossea", "o que a medula ossea faz"), "A medula óssea vermelha é um dos principais locais de produção de células sanguíneas, incluindo hemácias, leucócitos e plaquetas.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.skeleton", ("para que serve o esqueleto", "qual a funcao do esqueleto", "funcoes do esqueleto"), "O esqueleto sustenta o corpo, protege órgãos, funciona como sistema de alavancas para os músculos, armazena minerais e abriga medula óssea responsável pela formação de muitas células do sangue.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.joints", ("o que sao articulacoes", "para que servem as articulacoes", "funcao das articulacoes"), "Articulações são regiões de união entre ossos ou cartilagens. Dependendo do tipo, fornecem estabilidade e permitem diferentes graus de movimento.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.lymphatic_system", ("para que serve o sistema linfatico", "qual a funcao do sistema linfatico", "o que faz o sistema linfatico"), "O sistema linfático devolve líquido intersticial à circulação, transporta lipídios absorvidos no intestino e abriga estruturas importantes da resposta imune.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.immune_system", ("para que serve o sistema imunologico", "qual a funcao do sistema imune", "como funciona o sistema imunologico"), "O sistema imune reconhece e responde a agentes potencialmente nocivos por mecanismos inatos e adaptativos, usando barreiras, células, anticorpos e sinais químicos.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.uterus", ("para que serve o utero", "qual a funcao do utero", "o que o utero faz"), "O útero é um órgão muscular do sistema reprodutor feminino. Seu endométrio participa do ciclo menstrual e, em uma gestação, o útero abriga e sustenta o desenvolvimento do embrião e do feto.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.ovaries", ("para que servem os ovarios", "qual a funcao dos ovarios", "o que os ovarios fazem"), "Os ovários produzem oócitos e secretam hormônios como estrogênios e progesterona, participando da reprodução e da regulação do ciclo reprodutivo.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.testes", ("para que servem os testiculos", "qual a funcao dos testiculos", "o que os testiculos fazem"), "Os testículos produzem espermatozoides e secretam hormônios sexuais, principalmente testosterona.", (38,), ("OPENSTAX_ANATOMY",)),
    ("human.prostate", ("para que serve a prostata", "qual a funcao da prostata", "o que a prostata faz"), "A próstata é uma glândula do sistema reprodutor masculino que produz parte do fluido que compõe o sêmen.", (38,), ("OPENSTAX_ANATOMY",)),
    ("neuro.neuron", ("o que e um neuronio", "para que serve o neuronio", "o que fazem os neuronios"), "Neurônios são células especializadas em receber, processar e transmitir informação por sinais elétricos e químicos no sistema nervoso.", (39,), ("NCBI_NEURO", "OPENSTAX_ANATOMY")),
    ("neuro.synapse", ("o que e uma sinapse", "como funciona uma sinapse", "para que serve a sinapse"), "Sinapse é a junção funcional pela qual um neurônio influencia outra célula. Muitas sinapses usam neurotransmissores químicos; outras transmitem sinais eletricamente.", (39,), ("NCBI_NEURO",)),
    ("biology.homeostasis", ("o que e homeostase", "para que serve a homeostase", "homeostase significa o que"), "Homeostase é a manutenção de condições internas dentro de faixas compatíveis com o funcionamento do organismo, por mecanismos de regulação e feedback.", (38,), ("OPENSTAX_ANATOMY",)),
    ("biology.rna", ("o que e rna", "para que serve o rna", "qual a funcao do rna"), "RNA é uma família de moléculas de ácido ribonucleico com funções diversas, incluindo levar informação genética, participar da síntese de proteínas e regular a expressão gênica.", (38,), ("OPENSTAX_BIO",)),
    ("biology.protein", ("o que e uma proteina", "o que sao proteinas", "para que servem as proteinas"), "Proteínas são polímeros de aminoácidos que podem atuar como enzimas, estruturas, receptores, transportadores, anticorpos e componentes de sinalização, entre muitas outras funções.", (38,), ("OPENSTAX_BIO",)),
    ("biology.enzyme", ("o que e uma enzima", "para que servem as enzimas", "qual a funcao das enzimas"), "Enzimas são catalisadores biológicos, geralmente proteínas, que aceleram reações químicas ao reduzir a energia de ativação sem serem consumidas permanentemente pela reação.", (38, 36), ("OPENSTAX_BIO", "OPENSTAX_CHEM")),
)

GENERAL_FACT_ROWS_V2_B = (
    ("biology.ecosystem", ("o que e um ecossistema", "o que sao ecossistemas", "definicao de ecossistema"), "Um ecossistema inclui organismos vivos e os componentes físicos do ambiente com os quais eles interagem, incluindo fluxos de energia e ciclos de matéria.", (38, 56), ("OPENSTAX_BIO",)),
    ("biology.species", ("o que e uma especie", "o que significa especie em biologia", "definicao de especie"), "Espécie é uma categoria biológica usada para agrupar organismos relacionados. Existem diferentes conceitos de espécie; no conceito biológico clássico, populações da mesma espécie podem cruzar entre si e são reprodutivamente isoladas de outras.", (38,), ("OPENSTAX_BIO",)),
    ("chem.molecule", ("o que e uma molecula", "o que sao moleculas", "definicao de molecula"), "Uma molécula é uma entidade eletricamente neutra formada por dois ou mais átomos ligados, com composição e estrutura definidas.", (36,), ("IUPAC_GOLD", "OPENSTAX_CHEM")),
    ("chem.ion", ("o que e um ion", "o que sao ions", "definicao de ion"), "Íon é um átomo ou grupo de átomos com carga elétrica líquida porque ganhou ou perdeu elétrons em relação ao estado neutro correspondente.", (36,), ("IUPAC_GOLD", "OPENSTAX_CHEM")),
    ("chem.ph", ("o que e ph", "para que serve o ph", "o que significa ph"), "pH é uma medida logarítmica relacionada à atividade de íons hidrogênio em solução. Em soluções aquosas diluídas, valores menores indicam maior acidez e maiores indicam maior basicidade.", (36,), ("IUPAC_GOLD", "OPENSTAX_CHEM")),
    ("chem.acid_base", ("o que e acido e base", "qual a diferenca entre acido e base", "o que sao acidos e bases"), "Ácidos e bases podem ser definidos por diferentes modelos. No modelo de Brønsted-Lowry, ácidos doam prótons e bases os aceitam; no modelo de Lewis, ácidos aceitam pares de elétrons e bases os doam.", (36,), ("IUPAC_GOLD", "OPENSTAX_CHEM")),
    ("chem.periodic_table", ("o que e a tabela periodica", "para que serve a tabela periodica", "como funciona a tabela periodica"), "A tabela periódica organiza os elementos por número atômico e evidencia recorrências de propriedades químicas relacionadas à estrutura eletrônica.", (36,), ("IUPAC_GOLD", "OPENSTAX_CHEM")),
    ("physics.force", ("o que e forca na fisica", "definicao de forca", "o que significa forca em fisica"), "Força é uma interação capaz de alterar o movimento de um corpo. Em mecânica clássica, a força resultante relaciona-se à aceleração por F = ma quando a massa é constante.", (7,), ("OPENSTAX_PHYSICS",)),
    ("physics.mass_weight", ("qual a diferenca entre massa e peso", "massa e peso sao iguais", "o que e massa e peso"), "Massa mede a inércia de um corpo e é expressa em quilogramas no SI. Peso é a força gravitacional exercida sobre o corpo e depende do campo gravitacional local.", (7, 12), ("OPENSTAX_PHYSICS", "NIST_SI")),
    ("physics.energy", ("o que e energia na fisica", "definicao de energia", "o que significa energia em fisica"), "Energia é uma grandeza física associada à capacidade de produzir mudanças e realizar trabalho. Ela pode ser transferida e convertida entre formas, respeitando leis de conservação em sistemas apropriados.", (7, 8, 37), ("OPENSTAX_PHYSICS",)),
    ("physics.sound", ("o que e som", "como o som se propaga", "som precisa de meio"), "Som é uma perturbação mecânica que se propaga por um meio material. No ar, manifesta-se principalmente como variações de pressão; no vácuo não há meio para propagar som.", (46,), ("OPENSTAX_PHYSICS",)),
    ("physics.light", ("o que e luz", "como a luz se propaga", "luz e onda"), "Luz é radiação eletromagnética. Ela pode ser descrita por propriedades ondulatórias, como comprimento de onda e frequência, e por quantização em fótons em contextos quânticos.", (10, 13, 33), ("OPENSTAX_PHYSICS",)),
    ("computing.algorithm", ("o que e um algoritmo", "o que sao algoritmos", "para que serve um algoritmo"), "Um algoritmo é uma sequência finita e precisa de instruções destinada a resolver uma classe de problemas ou realizar uma computação.", (40,), ("OPENSTAX_CS",)),
    ("computing.cpu", ("o que e cpu", "para que serve a cpu", "o que faz o processador"), "A CPU, ou unidade central de processamento, executa instruções de programas e coordena operações de processamento de dados, trabalhando com memória e outros componentes do computador.", (40,), ("OPENSTAX_CS",)),
    ("computing.ram", ("o que e memoria ram", "para que serve a ram", "qual a funcao da memoria ram"), "RAM é memória de acesso aleatório usada para manter temporariamente dados e instruções que programas e o sistema estão usando; seu conteúdo volátil normalmente se perde sem energia.", (40,), ("OPENSTAX_CS",)),
    ("computing.os", ("o que e sistema operacional", "para que serve o sistema operacional", "o que faz um sistema operacional"), "Sistema operacional é o software que gerencia recursos de hardware, processos, memória, arquivos e dispositivos e oferece serviços básicos aos aplicativos.", (40,), ("OPENSTAX_CS",)),
    ("computing.internet", ("o que e a internet", "como funciona a internet", "internet e o que"), "A Internet é uma rede global de redes que se comunica por uma família de protocolos, principalmente a suíte TCP/IP. Serviços como a Web funcionam sobre essa infraestrutura.", (40,), ("IETF_RFC", "OPENSTAX_CS")),
    ("history.apollo11", ("o que foi a apollo 11", "quem chegou a lua primeiro", "quando o ser humano chegou a lua"), "A Apollo 11 foi a missão da NASA que realizou o primeiro pouso humano na Lua. Neil Armstrong e Buzz Aldrin pousaram em 20 de julho de 1969, enquanto Michael Collins permaneceu em órbita lunar.", (15, 31, 32), ("NASA_APOLLO11",)),
    ("history.un", ("quando a onu foi criada", "o que e a onu", "quando nasceu a onu"), "A Organização das Nações Unidas foi criada em 1945; sua Carta entrou em vigor em 24 de outubro de 1945. A organização reúne Estados para cooperação internacional em temas como paz, segurança, desenvolvimento e direitos humanos.", (), ("UN_HISTORY",)),
    ("culture.marie_curie", ("quem foi marie curie", "quem e marie curie", "marie curie"), "Marie Curie foi uma física e química nascida em 1867, pioneira no estudo da radioatividade. Compartilhou o Nobel de Física de 1903 e recebeu o Nobel de Química de 1911.", (36,), ("NOBEL_CURIE",)),
    ("geo.largest_continent", ("qual e o maior continente", "maior continente do mundo", "qual o maior continente da terra"), "A Ásia é o maior continente da Terra em área.", (56,), ("UN_CAPITALS",)),
    ("earth.atmosphere", ("o que e a atmosfera", "para que serve a atmosfera", "o que compoe a atmosfera"), "A atmosfera é a camada de gases mantida pela gravidade ao redor da Terra. Ela participa do clima, protege a superfície de parte da radiação e possibilita processos essenciais como respiração e ciclo da água.", (56,), ("NOAA",)),
    ("earth.atmosphere_composition", ("qual a composicao da atmosfera", "quanto nitrogenio tem no ar", "quanto oxigenio tem no ar"), "O ar seco da baixa atmosfera terrestre é composto principalmente por cerca de 78% de nitrogênio e 21% de oxigênio, com argônio, dióxido de carbono e outros gases em proporções menores; vapor d'água varia no espaço e no tempo.", (56,), ("NOAA",)),
)

FACTS = tuple(
    FactRecord(row[0], tuple(row[1]), row[2], tuple(row[3]), tuple(row[4]))
    for row in (
        *FACT_ROWS,
        *EXTRA_FACT_ROWS,
        *GENERAL_FACT_ROWS_V2_A,
        *GENERAL_FACT_ROWS_V2_B,
    )
)
def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).casefold()
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def sources_for(keys: tuple[str, ...]) -> tuple[SourceRef, ...]:
    return tuple(SOURCE_REGISTRY[key] for key in keys if key in SOURCE_REGISTRY)


def theme_foundation(theme_id: int) -> ThemeFoundation:
    return THEME_FOUNDATIONS[int(theme_id)]


def render_theme_foundation(theme_id: int, *, include_sources: bool = False) -> str:
    foundation = theme_foundation(theme_id)
    theme = next(theme for theme in THEMES if theme.id == foundation.theme_id)
    facts = " ".join(f"• {fact}" for fact in foundation.facts)
    answer = f"{theme.label}: {foundation.summary} {facts}"
    if include_sources:
        refs = sources_for(foundation.source_keys)
        answer += " Fontes-base: " + "; ".join(f"{ref.name} — {ref.url}" for ref in refs)
    return answer


def _capital_answer(query: str, *, include_sources: bool = False) -> str | None:
    q = _norm(query)
    if "capital" not in q:
        return None
    for key, (country, capital, source_keys) in sorted(COUNTRY_CAPITALS.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{re.escape(key)}\b", q):
            article = {
                "França": "da França",
                "Brasil": "do Brasil",
                "Argentina": "da Argentina",
                "Chile": "do Chile",
                "Uruguai": "do Uruguai",
                "Paraguai": "do Paraguai",
                "Peru": "do Peru",
                "Colômbia": "da Colômbia",
                "Venezuela": "da Venezuela",
                "México": "do México",
                "Estados Unidos": "dos Estados Unidos",
                "Canadá": "do Canadá",
                "Espanha": "da Espanha",
                "Itália": "da Itália",
                "Alemanha": "da Alemanha",
                "Reino Unido": "do Reino Unido",
                "China": "da China",
                "Japão": "do Japão",
                "Coreia do Sul": "da Coreia do Sul",
                "Índia": "da Índia",
                "Austrália": "da Austrália",
                "Rússia": "da Rússia",
                "Ucrânia": "da Ucrânia",
                "Suécia": "da Suécia",
                "Noruega": "da Noruega",
                "Dinamarca": "da Dinamarca",
                "Finlândia": "da Finlândia",
                "Islândia": "da Islândia",
                "Tchéquia": "da Tchéquia",
                "Hungria": "da Hungria",
                "Romênia": "da Romênia",
                "Bulgária": "da Bulgária",
                "Croácia": "da Croácia",
                "Sérvia": "da Sérvia",
                "Eslovênia": "da Eslovênia",
                "Eslováquia": "da Eslováquia",
                "Estônia": "da Estônia",
                "Letônia": "da Letônia",
                "Lituânia": "da Lituânia",
                "Tailândia": "da Tailândia",
                "Vietnã": "do Vietnã",
                "Filipinas": "das Filipinas",
                "Singapura": "de Singapura",
                "Paquistão": "do Paquistão",
                "Bangladesh": "de Bangladesh",
                "Nepal": "do Nepal",
                "Irã": "do Irã",
                "Iraque": "do Iraque",
                "Jordânia": "da Jordânia",
                "Catar": "do Catar",
                "Kuwait": "do Kuwait",
                "Omã": "de Omã",
                "Etiópia": "da Etiópia",
                "Gana": "de Gana",
                "Senegal": "do Senegal",
                "Tanzânia": "da Tanzânia",
                "Angola": "de Angola",
                "Moçambique": "de Moçambique",
                "Argélia": "da Argélia",
                "Tunísia": "da Tunísia",
                "Portugal": "de Portugal",
                "Irlanda": "da Irlanda",
                "Bélgica": "da Bélgica",
                "Áustria": "da Áustria",
                "Polônia": "da Polônia",
                "Grécia": "da Grécia",
                "Turquia": "da Turquia",
                "Nova Zelândia": "da Nova Zelândia",
                "Egito": "do Egito",
                "Marrocos": "do Marrocos",
                "Nigéria": "da Nigéria",
                "Quênia": "do Quênia",
                "Arábia Saudita": "da Arábia Saudita",
                "Emirados Árabes Unidos": "dos Emirados Árabes Unidos",
            }.get(country)
            if article:
                answer = f"A capital {article} é {capital}."
            else:
                answer = f"Em {country}, a capital é {capital}."
            if include_sources:
                refs = sources_for(tuple(source_keys))
                answer += " Fonte: " + "; ".join(f"{ref.name} — {ref.url}" for ref in refs)
            return answer
    return None
def lookup_fact(query: str) -> FactRecord | None:
    q = _norm(query)
    if not q:
        return None

    best: tuple[float, int, FactRecord] | None = None
    q_tokens = set(q.split())
    for record in FACTS:
        for alias in record.aliases:
            a = _norm(alias)
            if not a:
                continue
            a_tokens = set(a.split())
            if q == a:
                score = 10.0
            elif f" {a} " in f" {q} ":
                score = 6.0 + min(len(a_tokens), 10) / 100
            else:
                inter = len(q_tokens & a_tokens)
                if not inter:
                    continue
                coverage = inter / max(1, len(a_tokens))
                precision = inter / max(1, len(q_tokens))
                score = 0.7 * coverage + 0.3 * precision
                if len(a_tokens) >= 2 and a_tokens <= q_tokens:
                    score += 1.0
            candidate = (score, len(a_tokens), record)
            if best is None or candidate[:2] > best[:2]:
                best = candidate

    if best is None or best[0] < 0.82:
        return None
    return best[2]


def answer_foundational_fact(query: str) -> str | None:
    q = _norm(query)
    include_sources = any(token in q.split() for token in ("fonte", "fontes", "referencia", "referencias", "evidencia"))

    capital = _capital_answer(query, include_sources=include_sources)
    if capital:
        return capital

    record = lookup_fact(query)
    if record is None:
        return None
    answer = record.answer
    if include_sources:
        refs = sources_for(record.source_keys)
        if refs:
            answer += " Fontes: " + "; ".join(f"{ref.name} — {ref.url}" for ref in refs)
    return answer


def stats() -> dict:
    return {
        "theme_foundations": len(THEME_FOUNDATIONS),
        "fact_records": len(FACTS),
        "country_capitals": len(COUNTRY_CAPITALS),
        "sources": len(SOURCE_REGISTRY),
    }
