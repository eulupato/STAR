# ⭐ STAR — MASTER DEVELOPMENT ROADMAP

Documento vivo oficial do projeto.

## Regras de versionamento
- Versão inteira (`V2.0`, `V3.0`) = nova geração funcional.
- `.1`, `.2` = expansão importante dentro da geração.
- `.x.x` = correção/hotfix.
- Ideias novas entram primeiro neste roadmap e só depois viram código.

## Arquitetura conceitual
A STAR é organizada em oito domínios:

- **MIND** — raciocínio, contexto, memória, planejamento, identidade.
- **SENSES** — audição, visão, tela e sensores.
- **EXPRESSION** — linguagem, voz, avatar e animação.
- **ACTION** — aplicativos, arquivos, sistema operacional, web, dispositivos e robótica.
- **KNOWLEDGE** — biblioteca, Knowledge Packs, busca, Knowledge Graph e ciência.
- **HEALTH** — diagnóstico, Cura, watchdog, backup e recuperação.
- **TRUST** — permissões, criptografia, auditoria, sandbox e segredos.
- **WORLD** — STAR WORLD, ilhas, 3D, interfaces e presença física.

## V1.9 — FOUNDATION
**Objetivo:** congelar a fundação estável.

Inclui:
- Core e identidade atuais;
- memória básica;
- matemática natural;
- interface 2D;
- HUB/ilhas/Casa/Closet/skins;
- Knowledge Packs atuais;
- STT local;
- voz oficial local + fallbacks;
- controle inicial do computador;
- CI, logs, limpeza e documentação.

Pós-release: bugs entram como V1.9.x.

### Infraestrutura experimental pós-release

A Foundation pode receber **pontes pequenas, opt-in e sem mudança de geração**
quando forem necessárias para validar hardware real, desde que não antecipem os
sistemas completos de versões futuras.

Atualmente:

- **STAR Device Gateway V0.2** — ponte LAN + Adaptive Runtime;
- **STAR Mobile iOS V0** — iPhone como sensor/interface, sem MIND próprio;
- **STAR Watch Android V0.3** — Watch como sensor/interface, áudio PCM/WAV orientado a fala e comandos remotos seguros, sem MIND próprio;
- **STAR Watch App V0.4 + Plasma Orbit** — shell Watch-first validado primeiro no PC, preservando o Core compartilhado;
- **Command/Agent Foundation V0** — registro central de intents + catálogo de capacidades/agentes com estados `available/partial/planned`, sem Goal Engine ou autonomia V8;
- **Voice Command Catalog V1.9** — catálogo gerado por intents/slots com contrato mínimo de 4.000 variações, sem milhares de `if/else`;
- **Conversation Foundation V1.9** — small talk composicional com contrato mínimo de 5.000 respostas auditáveis, sem substituir o futuro Context Engine V2;
- **Contextual Weather Provider V1.9** — clima online sob demanda e de domínio estreito, usado para aterrar respostas meteorológicas sem liberar o modo web geral;
- **Knowledge Packs removíveis** — packs JSON/JSONL em `STAR_KNOWLEDGE/packs`.

O runtime compartilhado centraliza tema, rótulos, feature flags e perfis
`phone/watch` em `STAR_MANIFEST.json`. Isso valida adaptação entre endpoints sem
criar Core, identidade ou memória paralelos.

O catálogo de comandos pertence ao Core e é reutilizado por PC/Watch. Ações
remotas sensíveis permanecem bloqueadas até o Permission Manager. O registro de
agentes não antecipa autonomia: agentes são capacidades especializadas da mesma
STAR e recursos futuros permanecem explicitamente marcados como planejados.

A etapa **Watch-first** é uma ponte de validação de interface/dispositivos dentro da
Foundation: primeiro estabiliza shell, voz, comandos, providers e integração no PC;
depois porta a experiência validada para o Watch real. Ela não substitui nem pula
o V2.0 MIND.

Esses itens não significam que V5 SENSES, V8 AGENT ou V9 ECOSYSTEM estejam
concluídos. O Gateway apenas entrega entradas ao Core atual; visão, Goal Engine,
Device Manager completo, Offline-first Sync e permissões avançadas continuam em
seus marcos originais.

---

## V2.0 — MIND
**Objetivo:** criar a arquitetura cognitiva permanente.

Inclui:
- Brain Architecture;
- Executive;
- Salience;
- Context Engine;
- Working Memory;
- Metacognição operacional;
- Reasoning/Planning;
- Personality/Identity Core;
- memória episódica, semântica, conversa, projetos e preferências;
- Model Router.

### BLOCO 1 — Princípios invioláveis e modelos fundamentais

O BLOCO 1 é a fundação normativa/cognitiva do V2.0. Pode existir como camada
experimental integrada sobre a V1.9, mas **não significa que V2.0 esteja concluída**.

Ciclo oficial:

```text
PERCEBER
→ IDENTIFICAR
→ COMPREENDER
→ CONTEXTUALIZAR
→ RELACIONAR
→ PREVER
→ INTERPRETAR
→ DECIDIR
→ AGIR
→ OBSERVAR
→ APRENDER
```

Modelos fundamentais:

- WORLD MODEL;
- HUMAN MODEL;
- SOCIAL MODEL;
- SELF MODEL;
- SITUATION MODEL.

Distinções invioláveis:

- MODELO ≠ STAR;
- CORPO ≠ STAR;
- IA ≠ STAR;
- PENSAR ≠ AGIR;
- CURIOSIDADE ≠ AUTORIZAÇÃO;
- INFERÊNCIA ≠ FATO;
- AUTONOMIA COGNITIVA ≠ AUTONOMIA OPERACIONAL.

Implementação central: `core/foundations.py`, reutilizada pelo `STAR Core` e
ancorada na identidade oficial já existente em `core/star_identity.py`.

O catálogo fundacional possui **1.000 nós canônicos × 1.000.000 combinações =
1.000.000.000 de representações operacionais endereçáveis**, materializadas sob
demanda. O número representa espaço combinatório de princípios, regras, estados,
limites e contextos; **não representa 1B de fatos independentes pesquisados** e
não cria 1B de arquivos/linhas em RAM ou no repositório.

Regra operacional permanente: cognição, curiosidade, inferência, previsão ou
planejamento nunca concedem sozinhos autorização para uma ação externa. Ação
requer capacidade + segurança + permissão operacional apropriada.

### BLOCO 2 — Fundação epistêmica

O BLOCO 2 define como a STAR sabe **o que sabe, como sabe, de onde veio, quando
aprendeu, qual fonte sustenta, quais evidências existem, quanta confiança e
incerteza existem, se a informação pode estar errada ou desatualizada, se há
versões conflitantes e qual é seu tipo epistêmico**.

A implementação central é `core/epistemics.py`. A persistência é uma extensão
incremental em `database/epistemic_store.py`, sempre sobre o mesmo `star.db` e o
mesmo `CognitiveStore`; não existe banco ou memória epistêmica paralela.

Cada registro epistêmico pode manter:

- conteúdo e ID estável;
- tipo: `fact`, `hypothesis`, `inference`, `opinion`, `fiction`, `simulation`,
  `unknown`, `observation`, `declared_information` ou `memory`;
- origem e referência de proveniência;
- fonte com tipo, título, confiabilidade e fundamento da confiabilidade;
- data de aprendizado;
- confiança e incerteza calibráveis;
- validade inicial/final, prazo de obsolescência e última verificação;
- múltiplas evidências de suporte, refutação ou contexto;
- relações com outros conhecimentos, inclusive contradição e supersessão;
- histórico auditável de revisões e transições.

Estados oficiais:

```text
DISCOVERED
QUARANTINED
VERIFIED
CANONICAL
SUPERSEDED
RETRACTED
```

Esses estados formam uma máquina de estados explícita. `VERIFIED` exige evidência
rastreável. `CANONICAL` não significa verdade absoluta: exige registro `fact` em
estado `VERIFIED`, proveniência explícita, evidência de suporte, confiança mínima,
incerteza aceitável, validade temporal compatível e ausência de contradição aberta.
Um registro canônico continua revisável, pode voltar à quarentena, ser substituído
ou retraído.

Contradições não são apagadas silenciosamente. Conhecimentos incompatíveis podem
ser relacionados por `contradicts`; se já estavam `VERIFIED` ou `CANONICAL`, são
movidos para `QUARANTINED` até revisão. Versões posteriores podem usar
`supersedes`/`superseded_by`, preservando a história anterior.

A ingestão diária existente continua usando os mesmos contadores e regras de
deduplicação. Registros válidos de crescimento passam também a ser registrados de
forma idempotente no ledger epistêmico como `DISCOVERED`, sem serem promovidos
automaticamente a `VERIFIED` ou `CANONICAL`.

O catálogo do BLOCO 2 possui **1.000 nós canônicos × 1.000.000 combinações =
1.000.000.000 de representações epistêmicas endereçáveis**, materializadas sob
demanda. As combinações cobrem área, lente, família cognitiva, estilo, contexto,
tipo epistêmico, faixa de confiabilidade da fonte e faixa de incerteza.

Assim como no BLOCO 1, **1B é capacidade/endereço lógico, não 1B de fatos
pesquisados, arquivos ou linhas pré-carregadas**. Somente conhecimentos realmente
descobertos/materializados ocupam o SQLite e recebem proveniência, evidências,
relações e histórico persistentes.

### BLOCO 3 — Arquitetura Universal do Conhecimento

O BLOCO 3 organiza a camada universal que conecta conhecimento canônico,
claims/evidências, grafo, relações semânticas, índices e cache sem criar sistemas
paralelos. Ele é uma fundação experimental compartilhada entre MIND e KNOWLEDGE e
**não significa que V2.2 ou V3.0 estejam concluídos**.

Pipeline oficial:

```text
CANONICAL KNOWLEDGE
↓
CLAIMS
↓
EVIDENCE
↓
KNOWLEDGE GRAPH
↓
SEMANTIC RELATIONS
↓
INDEXES
↓
CACHE
↓
STAR
```

Fontes de verdade e reutilização:

- `CANONICAL KNOWLEDGE`: `core/universal_knowledge.py`;
- `CLAIMS` e `EVIDENCE`: ledger epistêmico do BLOCO 2;
- `KNOWLEDGE GRAPH` e `SEMANTIC RELATIONS`: tabelas existentes
  `knowledge_nodes`/`knowledge_edges`;
- persistência/indexação adicional: `database/universal_knowledge_store.py` no
  mesmo `star.db`;
- integração com a STAR: `core/star_core.py`;
- cache: memória limitada LRU/TTL, descartável e nunca fonte de verdade.

Um objeto universal só pode entrar como `CANONICAL KNOWLEDGE` se seu claim
principal já estiver em estado `CANONICAL` no BLOCO 2. `DISCOVERED`,
`QUARANTINED` ou `VERIFIED` nunca são promovidos silenciosamente pelo BLOCO 3.

A camada universal organiza:

- conceitos e entidades;
- aliases normalizados e aliases localizados;
- propriedades;
- categorias, subtemas e contextos como facetas indexáveis;
- taxonomias sobre arestas do Knowledge Graph;
- eventos temporais;
- regras e exceções;
- fontes/evidências por referência aos registros do BLOCO 2;
- temporalidade e proveniência;
- claims adicionais com papéis `supporting`, `corroborating`, `contextual`,
  `exception` ou `historical`;
- relações semânticas e cross-links interdomínio.

Deduplicação usa identidade estável composta por **namespace + tipo de conhecimento
+ rótulo canônico normalizado**. Registrar novamente a mesma identidade reutiliza
o objeto existente e liga claims adicionais em vez de gerar duplicação. Claims
retraídos só podem permanecer como histórico explícito.

Consulta e atualização:

- lookup exato por rótulo canônico normalizado;
- lookup indexado por aliases;
- filtros indexados por facetas;
- SQLite FTS5/BM25 quando disponível;
- fallback textual SQLite quando FTS5 não estiver disponível;
- cache LRU/TTL com invalidação em qualquer escrita relevante;
- atualizações de metadados incrementam revisão e geram eventos auditáveis;
- taxonomias/cross-links invalidam o cache e permanecem no grafo compartilhado.

Escala do BLOCO 3:

- **20 áreas × 50 lentes = 1.000 nós canônicos**;
- **1.000.000 combinações por nó**;
- **1.000.000.000 de representações endereçáveis em `B03`**;
- materialização sob demanda; zero requisito de 1B de linhas físicas.

A arquitetura usa namespaces independentes com IDs textuais. `B01`, `B02`, `B03`,
`B04`, `B05`, `B06` e `B07` registram cada um capacidade lógica própria de **1B**;
blocos futuros podem registrar novos namespaces de 1B sem alteração de schema ou
colisão de IDs. Apenas conhecimento efetivamente materializado ocupa disco, RAM,
índices e cache.

Embeddings locais, Biblioteca completa, Knowledge Packs V2 e o restante da busca
universal madura continuam pertencendo ao V3.0; o BLOCO 3 apenas estabelece a
arquitetura central limpa sobre a qual esses sistemas poderão crescer.

### BLOCO 4 — Modelo Físico Fundamental do Mundo

O BLOCO 4 especializa o `WORLD MODEL` para representar matéria, objetos, espaço,
propriedades físicas, interações, permanência de objetos, affordances, causalidade
e previsão. É uma camada experimental integrada sobre os BLOCO 2 e 3; **não
significa que V5 SENSES ou V10 EMBODIED estejam concluídos**.

Implementação central: `core/physical_world.py`, integrada em `core/star_core.py`.
Ela reutiliza `UniversalKnowledgeArchitecture` e, portanto, o mesmo `star.db`, o
mesmo ledger epistêmico e o mesmo Knowledge Graph. Nenhum banco, grafo ou catálogo
científico paralelo é criado.

Os temas centrais cobrem explicitamente matéria, objetos, superfícies, espaço,
volume, massa, peso, densidade, forma, tamanho, distância, posição, direção,
orientação, movimento, velocidade, aceleração, força, equilíbrio, gravidade,
impacto, colisão, atrito, pressão, temperatura, calor, frio, som, luz, sombra,
reflexão, eletricidade, magnetismo, líquidos, gases, sólidos, permanência de
objetos, affordances, materiais, tempo, causalidade e previsão. Para fechar os
modelos causais também há energia, deformação, estabilidade, flutuabilidade,
fluxo, contato, contenção e risco físico.

O bloco separa três camadas:

1. **Conhecimento físico canônico** — só é materializado no namespace `B04` pelo
   BLOCO 3 quando o claim principal já é `CANONICAL` no BLOCO 2.
2. **Estado físico observado** — objetos de cena permanecem em um world model
   transitório; observar algo não o transforma automaticamente em conhecimento
   canônico persistente.
3. **Inferência física** — affordances e previsões causais qualitativas são
   marcadas como `inference`, preservam incerteza, exigem medição/modelo científico
   para previsão quantitativa e nunca concedem autorização operacional.

Permanência de objetos segue regras conservadoras: perder observação não significa
deixar de existir; um objeto ocluído continua representado com confiança de estado
reduzida até evidência explícita de remoção, destruição ou transformação; posição
e estado não observados não são inventados.

A Física científica existente é reutilizada sob demanda por
`core.physics_knowledge_150k.py`. Fórmulas, fontes e tópicos científicos não são
copiados para o BLOCO 4. Isso mantém a base científica como referência e o world
model como camada de interpretação física do ambiente.

Matriz fundamental:

```text
OBJETO
× MATERIAL
× PROPRIEDADE
× ESTADO
× AMBIENTE
× AÇÃO
× CONSEQUÊNCIA
× RISCO
```

Escala do BLOCO 4:

- **50 temas × 10 subtemas = 500 nós canônicos**;
- por nó: **10 objetos × 10 materiais × 10 propriedades × 5 estados × 5 ambientes
  × 5 ações × 4 consequências × 4 riscos = 2.000.000 combinações**;
- **500 × 2.000.000 = 1.000.000.000 de representações endereçáveis em `B04`**;
- materialização sob demanda; zero requisito de 1B de linhas, arquivos ou fatos
  independentes pesquisados.

O namespace B04 é compatível com a arquitetura universal do BLOCO 3. Somados,
B01–B04 oferecem **4B de endereços lógicos independentes**, mas apenas dados
realmente materializados ocupam armazenamento. Sensores futuros do V5 poderão
alimentar observações do world model; robótica futura do V10 poderá consumi-lo,
sem que este bloco antecipe esses sistemas.

### BLOCO 5 — Fundamentos Científicos

O BLOCO 5 estabelece uma camada científica comum para a STAR, cobrindo profundamente
**lógica, matemática, estatística, método científico, física, química, biologia,
geologia, astronomia, climatologia, ecologia, fauna e flora**, com suas vertentes,
subvertentes e conexões interdisciplinares. É uma fundação experimental integrada
entre MIND e KNOWLEDGE e **não significa que o Scientific Engine completo do V3.0
esteja concluído**.

Implementação central: `core/scientific_foundations.py`, integrada em
`core/star_core.py`. O bloco não cria outro banco, outro ledger, outro Knowledge
Graph nem um segundo Scientific Engine. Ele reutiliza:

- BLOCO 2 para proveniência, evidências, confiança, incerteza e estado epistêmico;
- BLOCO 3 para conhecimento canônico, deduplicação, busca, índices e cache;
- `knowledge_nodes`/`knowledge_edges` como único Knowledge Graph;
- `CognitiveSuite.science` como `ScientificReasoner` existente;
- `core.physics_knowledge_150k.py` como referência especializada de Física;
- `core.chemistry_knowledge_500k.py` como referência especializada de Química;
- `core.multidisciplinary_knowledge.py` para lógica, matemática, estatística,
  biologia e domínios terrestres/biológicos compatíveis;
- `core.curriculum_knowledge.py` como referência científica curricular ampla.

Todos esses provedores são carregados sob demanda. Consultar um provedor não
transforma sua resposta em conhecimento canônico. Para persistir como conhecimento
científico oficial no namespace `B05`, o claim precisa seguir o gate do BLOCO 2 e
chegar como `CANONICAL` ao BLOCO 3.

Taxonomia científica:

```text
CIÊNCIA
↓
DOMÍNIO
↓
RAMO
↓
SUBRAMO
↓
CONHECIMENTO CANÔNICO
```

Essa taxonomia é materializada somente quando necessária e usa o mesmo Knowledge
Graph da MIND. Relações científicas, ligações interdisciplinares e conhecimentos
canônicos B05 permanecem no grafo compartilhado; não existe grafo científico
paralelo.

O catálogo B05 possui **50 ramos científicos**. Entre suas subvertentes estão,
sem limitar a expansão futura: lógica formal, teoria da prova/modelos e inferência;
álgebra, geometria, topologia, cálculo, análise, matemática discreta, equações
diferenciais, métodos numéricos e otimização; probabilidade, estatística inferencial,
Bayes, regressão, desenho experimental e causalidade; raciocínio científico,
metrologia, reprodutibilidade e ética; mecânica, termodinâmica, fluidos, ondas,
óptica, eletromagnetismo, relatividade, quântica, nuclear e partículas; química
geral, físico-química, orgânica, inorgânica, analítica, bioquímica, materiais e
ambiental; biologia molecular/celular, genética, evolução, fisiologia, microbiologia,
imunologia e biotecnologia; mineralogia, petrologia, geoquímica, tectônica,
sismologia, vulcanologia, estratigrafia e paleontologia; astronomia planetária,
estelar, galáctica, observacional e cosmologia; sistema climático, paleoclima,
variabilidade e mudança climática; ecologia de populações, comunidades,
ecossistemas, paisagens e conservação; diversidade, anatomia, fisiologia,
comportamento e conservação animal; diversidade, anatomia, fisiologia, reprodução,
evolução, ecologia e conservação vegetal.

Cada ramo é cruzado por 20 lentes científicas:

- conceitos;
- leis;
- teorias;
- fórmulas;
- equações;
- experimentos;
- propriedades;
- unidades;
- constantes;
- relações;
- descobertas;
- métodos;
- evidências;
- exceções;
- aplicações;
- problemas;
- soluções;
- subdisciplinas;
- história científica;
- fronteira científica.

Regras científicas permanentes do bloco:

- fato, hipótese, modelo, teoria, inferência e especulação não são equivalentes;
- teorias/modelos permanecem revisáveis e devem declarar domínio de validade;
- fórmulas/equações quantitativas preservam símbolos, unidades, hipóteses e análise
  dimensional quando aplicável;
- medições preservam incerteza, calibração e rastreabilidade;
- evidências preservam origem, independência, força e possibilidade de refutação;
- resultados de fronteira permanecem separados de consenso estabelecido;
- experimentos preservam variáveis, controles, protocolo, medição e replicação;
- nenhuma referência científica local é promovida automaticamente a `CANONICAL`.

Escala do BLOCO 5:

- **13 domínios solicitados**;
- **50 ramos × 20 lentes = 1.000 nós canônicos**;
- cada nó combina **10 profundidades × 10 contextos de método × 10 modos de
  evidência × 10 representações × 10 contextos de aplicação × 10 verificações =
  1.000.000 de variações**;
- **1.000 × 1.000.000 = 1.000.000.000 de representações científicas
  endereçáveis em `B05`**;
- IDs `SCI-B05-0000000001` até `SCI-B05-1000000000`;
- materialização sob demanda; zero requisito de 1B de fatos independentes,
  arquivos ou linhas pré-carregadas.

Com B05, B01–B05 oferecem **5B de endereços lógicos independentes**, enquanto
somente conhecimento realmente materializado ocupa disco, índices e RAM. A
Biblioteca científica completa, ingestão documental madura, embeddings locais,
busca científica universal e o Scientific Engine expandido continuam pertencendo
ao V3.0.

### BLOCO 6 — Vida, Corpo e Necessidades Humanas

O BLOCO 6 especializa a fundação científica para representar **vida, organização
biológica, corpo humano, sistemas fisiológicos e necessidades humanas**. É uma
camada experimental integrada sobre os BLOCO 2, 3 e 5 e **não cria um Health
Engine, sistema clínico ou diagnóstico médico automático**.

Implementação central: `core/human_life.py`, integrada em `core/star_core.py`. O
BLOCO 6 reutiliza:

- BLOCO 5 como fundação científica, principalmente sua Biologia e referências
  científicas locais carregadas sob demanda;
- BLOCO 2 para proveniência, evidências, confiança, incerteza e estado epistêmico;
- BLOCO 3 para conhecimento canônico, deduplicação, busca, índices e cache;
- `knowledge_nodes`/`knowledge_edges` como único Knowledge Graph;
- o mesmo `star.db`, sem nova tabela específica de saúde ou corpo humano.

A taxonomia oficial é:

```text
VIDA, CORPO E NECESSIDADES HUMANAS
↓
DOMÍNIO
↓
RAMO
↓
SUBTEMA
↓
CONHECIMENTO CANÔNICO GERAL
```

A raiz B06 também é ligada à Biologia do BLOCO 5 no mesmo grafo, preservando a
relação de especialização sem duplicar a ciência de base. O catálogo cobre 13
domínios estruturais e 50 ramos, incluindo profundamente:

- vida, organismos, biomoléculas, genes e níveis de organização;
- células, transporte, sinalização, ciclo celular, tecidos, órgãos e sistemas;
- metabolismo, fluidos, eletrólitos, equilíbrio ácido-base, termorregulação,
  fisiologia, homeostase e feedback;
- evolução humana, variação, adaptação, aclimatação e plasticidade;
- anatomia axial/apendicular, linguagem anatômica, histologia e visualização;
- coração, circulação, vasos, sangue, pulmões, ventilação e trocas gasosas;
- digestão, absorção, fígado, pâncreas, microbioma, macronutrientes,
  micronutrientes e hidratação;
- músculos, contração, ossos, articulações, movimento, postura, biomecânica e pele;
- sistema nervoso, cérebro, medula, nervos, sistema autônomo, visão, audição,
  equilíbrio, somatossensação e dor;
- sistema imunológico, imunidade inata/adaptativa, inflamação, sistema linfático,
  reparo, sistema endócrino, hormônios e regulação hormonal;
- reprodução, gametogênese, gestação, desenvolvimento, puberdade, maturação,
  envelhecimento e senescência;
- sono, ritmos circadianos, fome, sede, saciedade, fadiga, esforço, recuperação e
  necessidades humanas fundamentais;
- higiene pessoal, higiene oral, higiene alimentar/ambiental, prevenção básica de
  transmissão e consciência corporal não diagnóstica.

Cada ramo é cruzado por 20 lentes: conceito, estrutura, função, mecanismo,
metabolismo, regulação, sinalização, medição, variação biológica, desenvolvimento,
evolução/adaptação, entradas/saídas, interação entre sistemas, evidências,
limites/exceções, necessidades humanas, nutrição/hidratação, manutenção/higiene,
relações de Knowledge Graph e fronteira científica.

Regra permanente de segurança:

```text
CONHECIMENTO BIOLÓGICO ≠ DIAGNÓSTICO AUTOMÁTICO
SINAL CORPORAL ≠ DOENÇA
NECESSIDADE FISIOLÓGICA ≠ DIAGNÓSTICO
CONTEXTO GERAL ≠ PERFIL PESSOAL DE SAÚDE
```

Consequentemente:

- dor, fadiga, fome, sede, sono e outros sinais podem ser contextualizados como
  fenômenos fisiológicos gerais, mas não geram automaticamente candidatos de
  doença;
- o BLOCO 6 não escolhe tratamento automaticamente;
- o BLOCO 6 não cria perfil pessoal de saúde por inferência;
- respostas de provedores científicos não são canonizadas automaticamente;
- conhecimento B06 persistente exige um claim `fact` já `CANONICAL` no BLOCO 2 e
  a promoção explícita pelo BLOCO 3;
- dados pessoais de saúde, caso sejam usados no futuro, exigem camada própria,
  permissões, privacidade, auditoria e regras adequadas; isso não é antecipado aqui.

Escala do BLOCO 6:

- **13 domínios**;
- **50 ramos × 20 lentes = 1.000 nós canônicos**;
- cada nó combina **10 profundidades × 10 escalas biológicas × 10 contextos
  fisiológicos × 10 fases da vida × 10 modos de evidência × 10 representações =
  1.000.000 de variações**;
- **1.000 × 1.000.000 = 1.000.000.000 de representações endereçáveis em `B06`**;
- IDs `LIFE-B06-0000000001` até `LIFE-B06-1000000000`;
- materialização sob demanda; zero requisito de 1B de diagnósticos, prontuários,
  fatos médicos independentes, arquivos ou linhas pré-carregadas.

Com B06, B01–B06 oferecem **6B de endereços lógicos independentes**, enquanto
somente conhecimento efetivamente materializado ocupa disco, índices e RAM. O
Scientific Engine completo continua no V3.0; sistemas futuros de saúde, Cura,
permissões e segurança continuam em seus marcos próprios e não são marcados como
concluídos por este bloco.

### BLOCO 7 — Mente Humana e Psicologia

O BLOCO 7 organiza conhecimento psicológico e comportamental geral sobre percepção,
atenção, memória humana, aprendizagem, motivação, emoções, personalidade, cognição,
hábitos, decisões, vieses, trauma, estresse, luto, identidade, autoestima,
comportamento, expressões, intenção, teoria da mente e relações psicológicas. É uma
camada experimental integrada sobre os BLOCO 2, 3 e 6; **não cria diagnóstico
psicológico automático, leitura mental, perfil clínico ou certeza de intenção**.

Implementação central: `core/human_psychology.py`, integrada em
`core/star_core.py`. O BLOCO 7 reutiliza:

- BLOCO 2 para proveniência, evidência, confiança, incerteza e distinção entre
  observação, inferência e fato;
- BLOCO 3 para conhecimento canônico, deduplicação, busca, índices e cache;
- `knowledge_nodes`/`knowledge_edges` como único Knowledge Graph;
- BLOCO 6 como contexto biológico e corporal, sem reduzir fenômenos psicológicos a
  uma única causa biológica;
- `core.multidisciplinary_knowledge.py` como referência educacional já existente de
  Psicologia e Sociologia, carregada sob demanda;
- o mesmo `star.db`, sem tabela específica de perfil psicológico ou prontuário.

Taxonomia oficial:

```text
MENTE HUMANA E PSICOLOGIA
↓
DOMÍNIO
↓
RAMO
↓
SUBTEMA
↓
CONHECIMENTO CANÔNICO GERAL
```

A raiz B07 é ligada à taxonomia de vida/corpo do BLOCO 6 por relações contextuais,
mas permanece uma camada própria. Conhecimento B07 persistente só pode ser
materializado quando seu claim geral já é `CANONICAL` no BLOCO 2 e é promovido
explicitamente pelo BLOCO 3. Observações sobre uma pessoa, expressões faciais,
comportamentos, respostas de provedores ou intenções inferidas nunca são
canonizados automaticamente como fatos pessoais.

Os 13 domínios do bloco organizam 50 ramos sobre:

- percepção sensorial, organização perceptiva, atenção seletiva/sustentada e
  limites da atenção;
- sistemas de memória, codificação/recuperação, aprendizagem e aquisição de
  habilidades;
- motivação, necessidades psicológicas, hábitos, metas e persistência;
- processos emocionais, teorias da emoção, regulação e expressão;
- personalidade, autoconceito, identidade, autoestima e mudança ao longo da vida;
- cognição, julgamento, tomada de decisão, heurísticas, vieses, erros de raciocínio
  e efeitos de enquadramento/contexto;
- estresse, trauma, luto, resiliência, coping e recuperação;
- comportamento observável, expressões não verbais, intenção e limites da
  inferência comportamental;
- teoria da mente, percepção social, empatia, tomada de perspectiva e atribuição;
- apego, relações interpessoais, comunicação, grupos e pertencimento;
- desenvolvimento ao longo da vida, socialização, família, cultura e ambiente;
- métodos de pesquisa psicológica, psicometria, causalidade, replicabilidade e
  limites de interpretação;
- necessidades psicológicas, adaptação, flexibilidade e bem-estar geral.

Cada ramo é cruzado por 20 lentes: conceito, componentes, mecanismo,
desenvolvimento, contexto, cultura, diferenças individuais, evidências, medição,
possibilidades, interpretações alternativas, exceções, vieses, comportamento,
expressões, intenção, relações, aplicações não clínicas, limites e fronteira/debate.

Regra permanente de interpretação:

```text
COMPORTAMENTO ISOLADO ≠ DIAGNÓSTICO
COMPORTAMENTO ISOLADO ≠ TRAÇO ESTÁVEL
EXPRESSÃO ≠ INTENÇÃO
INFERÊNCIA DE INTENÇÃO ≠ CERTEZA
UMA OBSERVAÇÃO ≠ PADRÃO
```

O método `interpret_behavior` produz apenas `inference` com certeza
`underdetermined`, múltiplas possibilidades, interpretações alternativas,
exceções e contexto ausente. Mesmo comportamento repetido exige análise
longitudinal e não vira automaticamente diagnóstico, personalidade ou intenção.
O bloco não cria candidatos automáticos de transtorno, não atribui traço de
personalidade por observação isolada e não cria perfil psicológico pessoal.

Escala do BLOCO 7:

- **13 domínios**;
- **50 ramos × 20 lentes = 1.000 nós canônicos**;
- cada nó combina **10 contextos × 10 perspectivas × 10 modos de evidência ×
  10 escalas temporais × 10 faixas de confiança × 10 representações =
  1.000.000 de variações**;
- **1.000 × 1.000.000 = 1.000.000.000 de representações endereçáveis em `B07`**;
- IDs `PSY-B07-0000000001` até `PSY-B07-1000000000`;
- materialização sob demanda; zero requisito de 1B de diagnósticos, perfis,
  intenções inferidas, arquivos, linhas ou fatos independentes pré-carregados.

Com B07, B01–B07 oferecem **7B de endereços lógicos independentes**. Somente
conhecimento realmente materializado ocupa disco, índices e RAM. O BLOCO 7 amplia
o HUMAN MODEL e a base de conhecimento geral, mas não substitui avaliação clínica,
não antecipa um sistema de saúde mental e não altera os marcos futuros de Cura,
permissões, privacidade ou segurança.

### V2.1
Memory Architecture.

### V2.2
Knowledge Graph base.

### V2.3
Model Router e seleção automática de motores.

---

## V3.0 — KNOWLEDGE
**Objetivo:** transformar a STAR em uma plataforma de conhecimento offline expansível.

Inclui:
- Biblioteca;
- ingestão de PDF/texto;
- metadados e proveniência;
- embeddings locais;
- busca universal;
- Knowledge Packs V2;
- Knowledge Graph expandido;
- Scientific Engine;
- matemática simbólica, estatística, unidades, física, química e simulações.

---

## V4.0 — OPERATOR
**Objetivo:** controlar o computador e aplicativos de forma geral e segura.

Inclui:
- Application Manager;
- skills por aplicativo;
- File Index;
- busca semântica de arquivos;
- controle de janelas e sistema;
- automações;
- clipboard, volume, processos e dispositivos;
- permissões e logs por ação.

Spotify, navegador, VS Code e outros são apenas aplicações dentro desse sistema.

---

## V5.0 — SENSES
**Objetivo:** percepção multimodal.

Inclui:
- wake word opcional;
- VAD;
- interrupção/barge-in;
- voz com streaming;
- visão;
- webcam;
- interpretação de imagens;
- Screen Awareness;
- Spatial Awareness;
- Multimodal Fusion.

---

## V6.0 — STAR WORLD 3D
**Objetivo:** reconstruir toda a experiência visual em 3D.

Princípio:

```text
STAR CORE
   ↕
Event Bus / API
   ↕
STAR WORLD 3D
```

Inclui:
- avatar 3D;
- rig;
- lip sync;
- animação procedural;
- olhar, piscar, gestos e locomoção;
- ilhas tridimensionais;
- Casa;
- Laboratório;
- Central de Criação;
- Biblioteca;
- Estúdio;
- Ateliê;
- Jardim;
- Observatório;
- Cura;
- Closet;
- Correio;
- Heróis;
- Idiomas;
- Digital Twin.

---

## V7.0 — GUARDIAN
**Objetivo:** transformar Cura em saúde, segurança e recuperação.

Inclui:
- Health Supervisor;
- watchdog;
- integridade de arquivos;
- hashes;
- integração com antimalware/antivírus local;
- Permission Manager;
- Secrets Vault;
- Audit Log;
- snapshots;
- backup;
- rollback;
- sandbox;
- diagnóstico inteligente;
- proposta de reparo e aplicação autorizada.

---

## V8.0 — AGENT
**Objetivo:** trabalhar por objetivos, não apenas comandos isolados.

Inclui:
- Goal Engine;
- Planner;
- Task Manager;
- Scheduler;
- Attention Manager;
- Simulation Mode;
- Skill SDK;
- Capability Registry;
- tarefas persistentes;
- verificação de resultado;
- autonomia controlada por permissões.

---

## V9.0 — ECOSYSTEM
**Objetivo:** expandir a STAR para a rede local e outros dispositivos.

Inclui:
- STAR LAN;
- PC;
- celular;
- tablet;
- Watch;
- Device Manager;
- Offline-first Sync;
- automação residencial;
- sensores;
- Mobile STAR;
- Network Awareness.

Princípio permanente: endpoints percebem, transmitem e executam; a fonte central
processa. Os protótipos Device Gateway/Mobile/Watch da Foundation validam esse
princípio, mas não substituem o Device Manager/Sync desta versão.

LOCAL continua funcional sem LAN ou Internet.

---

## V10.0 — EMBODIED
**Objetivo:** presença física sem prender a STAR a um fabricante.

Inclui:
- Robot Abstraction Layer;
- câmera;
- microfone;
- alto-falante;
- display;
- motores;
- sensores;
- bateria;
- telemetria;
- controle motor;
- percepção física;
- navegação segura quando apropriado.

---

## V11.0 — UNIFIED
**Objetivo:** integrar MIND, SENSES, ACTION, KNOWLEDGE, HEALTH, TRUST, WORLD e robótica em uma plataforma coerente.

Inclui:
- Event Bus maduro;
- observabilidade;
- resiliência;
- degradação graciosa;
- Capability Tree;
- Cura global;
- sincronização de estado entre interfaces.

---

## V12+ — EXPANSION
Expansões sobre a arquitetura consolidada:

- Research Engine;
- Maker Engine;
- CAD;
- eletrônica;
- microcontroladores;
- impressão 3D;
- Coding Lab;
- Creative Engine;
- música;
- arte;
- vídeo;
- modelagem 3D;
- Language Engine;
- tradução offline;
- mapas e referência offline;
- novos Knowledge Packs;
- novas skills.

---

# Sistemas transversais
Evoluem em várias gerações:

- Event Bus;
- Resource Governor;
- perfis ECO / NORMAL / MAX;
- Model Registry;
- Sleep Processing;
- Universal Inbox / Correio;
- Backup;
- Audit Trail;
- Capability Registry;
- Local Secrets Vault;
- Crash Recovery;
- Health Supervisor;
- Hardware Abstraction Layer;
- Plugin/Skill SDK;
- Task Scheduler;
- Notification Center;
- Semantic File Index;
- Personal Knowledge Graph.

# Modos oficiais
## LOCAL
STAR completa no computador.

## LAN
STAR + dispositivos locais.

## ONLINE
Recursos externos opcionais.

**Internet amplia a STAR; não constitui a STAR.**

# Regra de execução
Cada geração segue:
1. especificação;
2. arquitetura;
3. implementação incremental;
4. testes e diagnóstico;
5. documentação;
6. release;
7. freeze.

# Próximo marco
**V1.9 FINAL → estabilizar a ponte Watch-first → abrir V2.0 MIND.**