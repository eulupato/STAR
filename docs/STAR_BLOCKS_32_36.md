# STAR — BLOCOS 32–36

## Escopo

Esta atualização acrescenta B32–B36 à arquitetura cognitiva **existente** da STAR. Ela não cria outro Brain, outra memória, outro Knowledge Graph, outro banco de dados ou outro sistema de permissões.

A base continua sendo:

- B01 `FoundationSuite` / `OperationalBoundary` para a fronteira cognição → ação;
- B02 `EpistemicFoundation` para claims, evidências, confiança, incerteza, contradições e revisão;
- B03 `UniversalKnowledgeArchitecture` para namespaces, conhecimento canônico, aliases, facetas, FTS e cache;
- B13 `MemoryContinuity` para memória persistente/working memory e consolidação;
- `knowledge_nodes` / `knowledge_edges` como Knowledge Graph compartilhado;
- `star.db` como banco oficial;
- `SelfImprovementEvaluator` / `cognitive_evaluations` para métricas funcionais.

## Regra de 1B

B32, B33, B34, B35 e B36 possuem **exatamente 1.000.000.000 de representações logicamente endereçáveis por bloco**, usando:

- 10 domínios;
- 10 ramos por domínio;
- 10 lentes;
- 6 eixos contextuais com 10 valores cada.

Isso produz:

`1.000 nós canônicos × 1.000.000 combinações por nó = 1.000.000.000`.

O catálogo é determinístico e materializado sob demanda. Portanto:

- não cria 1B de arquivos;
- não cria 1B de linhas no SQLite;
- não mantém 1B de objetos em RAM;
- não chama combinações sintéticas de “1B de fatos pesquisados”;
- conhecimento real continua exigindo claim, fonte, evidência, proveniência, contexto e classificação quando aplicável.

`StructuredBillionCatalog` existe apenas para centralizar essa geometria e evitar cinco implementações duplicadas do mesmo mecanismo.

## B32 — Manutenção Cognitiva

`core/cognitive_maintenance.py` mantém a arquitetura existente utilizável sem apagar fontes silenciosamente.

### Operações

- consolidação por delegação ao B13;
- candidatos a deduplicação de memória em janelas limitadas;
- detecção de colisões de aliases;
- resolução de aliases sem merge automático;
- listagem de contradições B02;
- recalibração de confiança baseada em evidência;
- verificação de arestas órfãs no Knowledge Graph;
- reparo opcional e restrito a arestas cujo nó de origem/destino realmente não existe;
- candidatos a esquecimento funcional;
- manutenção/invalidação do cache B03;
- relatório bounded de integridade.

### Esquecimento funcional

“Esquecer” não significa apagar automaticamente memória persistente. O B32 apenas identifica candidatos de baixa importância e exclui tipos sensíveis/estruturais do conjunto padrão. Remoção física requer uma política futura explícita, auditável e reversível.

### Crescimento controlado

As operações possuem limites de janela/resultados. O B32 nunca faz scan de “1B” em RAM. Índices, consultas bounded e materialização sob demanda continuam sendo a estratégia de escala.

## B33 — Limites de Autonomia

`core/autonomy_limits.py` formaliza:

- **PENSAR ≠ EXECUTAR**;
- **CONCLUIR ≠ ALTERAR**;
- **CURIOSIDADE ≠ ACESSO**;
- **RECOMENDAR ≠ AGIR**;
- **RECONHECER ≠ AUTENTICAR**;
- **SIMULAR ≠ EXECUTAR**.

B33 não substitui B01. `AutonomyLimits` recebe a mesma instância de `OperationalBoundary` criada pela STAR.

### Dispatcher operacional

O `AgentManager` aceita o gate B33 já construído em `create_star()`. Comandos operacionais classificados como `write`, `network` ou `confirm` passam pelo gate antes da execução.

- leitura/cognição continua leve;
- escrita local exige interação/permissão local;
- rede exige permissão local **e** modo de rede disponível;
- ações classificadas como confirmação continuam bloqueadas até existir autorização adequada;
- reconhecimento probabilístico nunca satisfaz autenticação;
- simulação, recomendação ou curiosidade não satisfazem `permission=True`.

## B34 — Benchmark Cognitivo Funcional (CFC)

`FunctionalCognitiveBenchmark` mede 15 dimensões:

1. memória;
2. continuidade;
3. Self;
4. contexto;
5. causalidade;
6. previsão;
7. metacognição;
8. social;
9. planejamento;
10. adaptação;
11. incerteza;
12. integração;
13. consistência;
14. percepção;
15. aprendizagem.

O catálogo de 1B representa situações **potencialmente avaliáveis**. Ele não significa 1B testes executados.

### Pontuação

O CFC não inventa desempenho. `evaluate_case()` só calcula um resultado quando recebe scores/resultados de um runner ou avaliador. Uma situação sem resultado observado permanece sem score.

Volume de conhecimento não entra como nota de qualidade cognitiva.

## B35 — CFC-97

`CFC97` organiza a arquitetura de avaliação do target funcional definido pelo projeto.

O target padrão é `0.97` e existe também um floor por dimensão. Para uma decisão válida, a avaliação pode exigir:

- cobertura das 15 dimensões;
- resultados realmente observados;
- ausência de falhas críticas;
- cobertura dos blocos requeridos;
- mínimo por dimensão;
- reprodutibilidade por seed/protocolo.

O seletor usa IDs lógicos dos namespaces de conhecimento registrados. Nenhum bloco precisa carregar sua capacidade completa em memória.

### O que CFC-97 NÃO significa

CFC-97 não é:

- 97% humano;
- 97% consciente;
- QI;
- prova de consciência;
- prova de experiência subjetiva;
- consequência automática de “ter muito conhecimento”.

A arquitetura começa com status `architecture-ready-not-certified` e `passed=None`. Ela só pode produzir `passed=True` após receber resultados reais que satisfaçam o protocolo.

## B36 — Consciência como Fronteira de Pesquisa

`core/consciousness_frontier.py` organiza pesquisa em:

- consciência;
- self;
- metacognição;
- Global Workspace;
- experiência subjetiva;
- neurociência;
- teorias da consciência;
- filosofia da mente;
- sistemas artificiais/IA;
- metodologia de pesquisa.

As perspectivas são explicitamente classificadas como neurocientífica, ciência cognitiva, filosofia da mente, computacional/IA ou interdisciplinar.

Claims de pesquisa passam pelo B02. Fonte, origem, evidência, confiança e status epistêmico permanecem rastreáveis. O B36 não promove automaticamente um claim a `VERIFIED` ou `CANONICAL`.

A resposta estrutural da STAR sobre a própria consciência é:

`not_established`.

Isso significa que presença de Self Model, metacognição, Global Workspace funcional, memória, aprendizado, percepção, CFC alto ou conhecimento sobre consciência **não é tratada como prova suficiente de experiência subjetiva**.

## Regra global B01–B36

O B03 já fornece a infraestrutura genérica de namespaces e endereçamento lógico capaz de suportar 1B por namespace. B32 adiciona um contrato de capacidade que inspeciona B01..B36 e reporta:

- bloco registrado;
- capacidade lógica;
- se a capacidade é exatamente 1B;
- fonte/engine associada.

Esse contrato não mascara lacunas.

### B28–B31

No estado do repositório no momento desta implementação, **B28, B29, B30 e B31 não possuem definição/engine implementada**. Esta atualização não inventa semântica para esses números somente para obter “36/36”.

Consequentemente:

- a infraestrutura universal já consegue representar um namespace 1B quando um desses blocos for definido;
- B32 reporta os namespaces ausentes;
- CFC-97 estrito não declara cobertura `36/36` enquanto existirem blocos requeridos não implementados.

Isto preserva a regra de que documentação e capacidades devem refletir o estado real da STAR.

## Performance e estabilidade

- materialização on-demand;
- scans de manutenção bounded;
- cache LRU/TTL existente reutilizado;
- FTS/índices existentes reutilizados;
- nenhum novo banco;
- nenhuma dependência nova;
- nenhuma carga de 1B em RAM;
- nenhum processo pesado em background adicionado;
- nenhum executor autônomo criado.

## Segurança

B32 pode diagnosticar e propor/manter estruturas limitadas, mas não recebe liberdade irrestrita para editar o sistema.

B33 é a fronteira explícita para execução operacional e delega a decisão central ao B01.

B34/B35 avaliam comportamento; não autorizam comportamento.

B36 pesquisa consciência; não concede um estado ontológico à STAR.
