# STAR MIND — Cognitive Suite alpha

A STAR continua oficialmente na release **V1.9 stable**. Este conjunto é uma camada **experimental/alpha** alinhada ao roadmap V2 MIND, V2.1 Memory, V2.2 Knowledge Graph e a componentes antecipados de V3/V3.3.

## Objetivo

Transformar conhecimento armazenado em capacidade operacional: decompor problemas, planejar, lembrar, relacionar entidades, formular/testar hipóteses, calcular, simular, executar pequenos testes de código, recuperar documentos, pesquisar literatura acadêmica, manter projetos e medir a própria qualidade.

A suíte não é um novo cérebro paralelo e não substitui o STAR Core. `StarCore` continua sendo a unidade central. A MIND usa o mesmo `star.db`, o mesmo runtime e só intercepta comandos cognitivos explícitos; perguntas comuns preservam o roteamento existente.

## 15 capacidades

1. Reasoning Engine
2. Planner / Goal decomposition
3. Cognitive Memory
4. Knowledge Graph
5. Scientific Reasoner
6. Math Lab
7. Simulation Lab
8. Code Lab
9. Truth / Confidence Verifier
10. Document RAG
11. Research Agent
12. Project Manager
13. Explicit User Model
14. Multi-Agent Orchestrator
15. Self-Improvement Evaluator

## Catálogo cognitivo de 15M

Cada capacidade possui:

- 20 áreas canônicas;
- 50 lentes operacionais;
- 1.000 nós canônicos;
- 1.000 variações por nó (10 famílias × 10 estilos × 10 contextos);
- **1.000.000 de unidades operacionais endereçáveis por capacidade**.

Total: **15.000.000**.

Essas unidades são variações determinísticas de processos/guias cognitivos. **Não são 15 milhões de fatos pesquisados de forma independente.** São materializadas sob demanda, evitando milhões de objetos em RAM ou milhões de linhas versionadas no Git.

## Raciocínio e planejamento

`ReasoningEngine` produz artefatos auditáveis como objetivo, domínios, restrições, incógnitas, alternativas e verificações. Ele não expõe nem tenta armazenar chain-of-thought privada.

`Planner` gera etapas hierárquicas com dependências e critérios de validação. Ele possui templates leves para software, ciência, engenharia e objetivos gerais.

`MetacognitionEngine` decide entre responder localmente, verificar/calcular, consultar memória/conhecimento ou pesquisar quando a informação precisa ser atual.

## Memória cognitiva

A persistência usa o mesmo SQLite oficial da STAR (`star.db`). Tipos aceitos incluem:

- working;
- episodic;
- semantic;
- conversation;
- project;
- decision;
- error;
- temporal;
- people;
- object;
- preference.

A memória antiga de conversa continua preservada. A camada cognitiva acrescenta tabelas específicas ao mesmo banco em vez de criar `memory_v2.db` ou sistema paralelo.

## Knowledge Graph

O grafo persiste entidades e relações em SQLite. Nós possuem tipo, rótulo, dados, confiança e timestamps; arestas possuem relação, peso e metadados. A implementação inicial evita obrigar um servidor de grafos ou NetworkX no startup. Adaptadores mais sofisticados podem ser adicionados depois sem alterar o modelo persistente.

## Raciocínio científico e verificação

`ScientificReasoner` estrutura:

- hipótese;
- operacionalização;
- previsões;
- controles;
- evidência;
- falsificação;
- incerteza;
- replicação.

`TruthVerifier` exige evidência explícita. Sem evidência retorna `insufficient_evidence`; evidência mista vira `disputed_or_mixed`. O componente não transforma ausência de dados em certeza.

## Math Lab

O Math Lab usa **SymPy** local para:

- simplificação simbólica;
- equações;
- derivadas;
- integrais;
- avaliação numérica.

O `core/math_engine.py` básico continua existindo para aritmética rápida e linguagem natural simples. O Math Lab entra apenas em comandos matemáticos avançados explícitos.

## Simulation Lab

Primeira base funcional:

- lançamento de projéteis;
- crescimento/decaimento exponencial;
- Monte Carlo reproduzível com seed;
- integração de EDO escalar por RK4.

Os resultados carregam hipóteses quando pertinente. Esta camada é extensível e não pretende substituir simuladores científicos especializados.

## Code Lab

O Code Lab executa apenas pequenos snippets Python locais validados por AST. Imports são limitados a uma whitelist de módulos da biblioteca padrão; I/O, rede, imports de SO e introspecção perigosa são bloqueados. A execução usa `python -I -S`, diretório temporário e timeout.

**Isto não é um sandbox de segurança de sistema operacional.** Código não confiável e edição autônoma do repositório permanecem bloqueados até o Guardian/Sandbox do roadmap.

## Document RAG

Pipeline atual:

`arquivo/texto → extração → chunks → hash/deduplicação → SQLite → FTS5/BM25 → recuperação → contexto com origem`

Formatos: TXT, Markdown, CSV, JSON, Python, RST e PDF.

PDF usa `pypdf` para extração textual. **pypdf não é OCR**: PDFs escaneados/compostos apenas por imagens precisam de pipeline OCR futuro.

Se SQLite FTS5 não estiver disponível, a STAR usa busca textual fallback; o diagnóstico sinaliza a degradação.

## Research Agent

A primeira integração online é deliberadamente estreita: pesquisa de metadados acadêmicos via **Crossref REST API**, somente quando o modo de rede estiver autorizado.

O agente retorna título, DOI/URL, data, tipo, publisher, autores e contagem de citações quando disponível e armazena metadados para rastreabilidade. Pesquisa web geral autônoma continua parcial/futura; a existência do Crossref não deve ser anunciada como navegador universal.

## Projetos e User Model

Projetos persistem nome, objetivo, status, metadados e eventos/decisões.

O User Model armazena apenas informações explícitas/auditáveis. A MIND não infere automaticamente atributos sensíveis do usuário.

## Multiagente

`MultiAgentOrchestrator` coordena funções especializadas registradas, inclusive em paralelo, com máximo de workers limitado. Os agentes não são novas STARs nem personalidades independentes; são capacidades chamadas pelo Core.

## Autoavaliação

`SelfImprovementEvaluator` registra métricas, calcula médias e sugere investigações. Ele **não modifica código automaticamente**. Toda mudança do repositório continua sujeita a testes, permissões, revisão e validação.

## Crescimento diário de conhecimento

Existe infraestrutura para ingestão factual por tema, com alvo configurável (inclusive 1M). Porém:

- alvo não é garantia de 1M fatos válidos;
- registro precisa de conteúdo, fonte e tipo de fonte/proveniência;
- duplicatas não contam;
- registros rejeitados não contam;
- variações determinísticas do catálogo cognitivo não contam como fatos novos;
- toda execução registra `accepted`, `duplicates`, `rejected`, fontes e status.

O objetivo é aumentar conhecimento real sem degradar a base com spam, repetição ou afirmações sem origem.

## Comandos iniciais

Exemplos:

- `status mind`
- `planeje criar um software local`
- `raciocine sobre ...`
- `derive x^2 em x`
- `integre 2*x em x`
- `resolva a equação x^2=4`
- `simule lançamento 10 a 45 graus`
- `busque nos documentos energia escura`
- `pesquise artigos sobre quantum gravity` (rede autorizada)
- `crie projeto Nome: objetivo`
- `REASON-0000001` para inspecionar unidade do catálogo cognitivo

## Critério de estabilidade

Esta feature só deve ser promovida além de alpha quando:

- testes da suíte completa passarem;
- diagnóstico Windows passar;
- dependências estiverem consistentes;
- regressões de voz/conversa/conhecimento não aparecerem;
- consumo de startup/RAM continuar aceitável;
- interfaces e documentação refletirem as capacidades reais;
- limites de Code Lab, RAG, Research e autoavaliação estiverem claros.
