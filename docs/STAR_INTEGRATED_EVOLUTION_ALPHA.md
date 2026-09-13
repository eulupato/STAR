# STAR Integrated Evolution — alpha

Esta evolução aproxima **MIND, KNOWLEDGE, OPERATOR, SENSES, GUARDIAN e AGENT** sem
promover artificialmente o projeto para versões completas do roadmap. A Foundation
pública continua sendo **STAR V1.9 stable**; os sistemas abaixo são fundações alpha
integradas e testáveis.

## Referências de arquitetura estudadas

Foram pesquisadas implementações/documentações atuais antes de adaptar os princípios:

- **LangGraph** — execução durável, checkpoints, memória curta/longa, human-in-the-loop e idempotência de efeitos colaterais;
- **Microsoft GraphRAG** — entidades/relações/claims e recuperação local/global como referência para Knowledge Graph + RAG; não é dependência do Core;
- **Docling** — parsing/document understanding moderno como referência para futura ingestão multimodal; não é dependência obrigatória;
- **sqlite-vec** — vetores locais sobre SQLite; mantido opcional por ainda ser pre-1.0;
- **Sentence Transformers** — semantic search/embeddings locais;
- **PyMuPDF/Tesseract e OCRmyPDF** — OCR local seletivo para PDFs escaneados;
- **NetworkX** — relações explícitas e algoritmos de grafos como referência; o armazenamento oficial continua no SQLite da STAR;
- **NASA F Prime** — componentes, comandos, eventos, telemetria e health monitoring como referência de sistemas confiáveis;
- **Crossref, OpenAlex, arXiv e NCBI/PubMed** — provedores especializados para descoberta bibliográfica;
- **Database of Religious History, Harvard Pluralism Project, Library of Congress, Smithsonian, UNESCO, Sefaria e SuttaCentral** — referências para taxonomia cultural, religião, folclore e história da magia com proveniência e respeito a comunidades vivas.

Nenhum desses projetos foi copiado ou vendorizado. A STAR mantém implementação e
contratos próprios e usa bibliotecas externas somente como adapters quando isso traz
benefício real.

## 1. Runtime cognitivo

`core/cognition_runtime.py`

- Working Context limitado em RAM;
- seleção contextual por importância, relevância e recência;
- Salience Engine com fatores explícitos de relevância, novidade, risco, urgência e prioridade do usuário;
- Model Router com perfis de engines registrados;
- respeita local/network/custo e nunca inventa modelos instalados;
- memória persistente continua no `CognitiveStore`: não existe segundo sistema de memória.

## 2. Goal Engine + Scheduler durável

`core/goal_engine.py`

- objetivos e tarefas persistentes no `star.db`;
- dependências entre tarefas;
- checkpoints;
- retomada de estado;
- agenda persistente com `not_before`, `deadline` e `priority`;
- tarefas futuras não ficam prontas antes da hora;
- tarefas prontas são ordenadas por prioridade;
- execução somente por handlers registrados explicitamente;
- idempotência quando usado com Guardian;
- `background_autonomy=false`: agenda persistente não significa execução autônoma irrestrita.

## 3. Guardian alpha

`core/guardian.py`

- default-deny para ações desconhecidas;
- política por ação;
- confirmação e restrições remotas;
- audit log persistente;
- claims idempotentes para evitar repetição de efeitos colaterais;
- redaction básica de padrões de segredo/token.

Ainda **não** é sandbox de SO, autenticação forte completa ou Secrets Vault criptográfico.

## 4. RAG híbrido semântico

`core/semantic_rag.py`

- preserva documentos/chunks/FTS5/BM25 como fonte de verdade;
- adiciona índice derivado de embeddings por chunk;
- Sentence Transformers é opcional;
- fallback hashing local, determinístico e explicitamente não-neural;
- `sqlite-vec` fica como adapter opcional, não requisito de boot;
- o índice derivado pode ser reconstruído sem perder documentos.

## 5. OCR local seletivo

`core/ocr.py`

- tenta `pypdf` primeiro;
- OCR só é acionado em PDF escaneado/sem texto suficiente ou quando forçado;
- PyMuPDF + Tesseract são opcionais;
- texto OCR entra no `DocumentRAG` já existente, não em um pipeline paralelo.

## 6. Knowledge Graph científico + cultural

`core/scientific_graph.py`

O nome histórico da classe é preservado para compatibilidade, mas o indexador agora
serve o mesmo grafo oficial para currículo e cultura:

- reutiliza `knowledge_nodes` e `knowledge_edges` do mesmo `star.db`;
- pode materializar os **56 temas e 885 conceitos canônicos** do currículo;
- pode indexar **125 assuntos culturais + 40 aspectos**, regiões e famílias de fontes;
- relações são explicitamente derivadas da taxonomia;
- as **5M perspectivas culturais permanecem lazy** e não são despejadas no grafo;
- múltiplas áreas apontam para o mesmo conceito/assunto canônico;
- não infere causalidade científica sem fonte;
- não infere “verdade teológica” a partir de conectividade do grafo;
- materialização é explícita/on-demand para não aumentar o boot.

## 7. Knowledge cultural — religiões e história da magia

`core/religion_magic_taxonomy.py` + `core/religion_magic_knowledge.py`

- 100 tradições/relações religiosas;
- 25 campos de magia/esoterismo/história da magia;
- 40 aspectos por assunto;
- 5.000 nós canônicos;
- 1.000 perspectivas por nó;
- 5.000.000 de visões endereçáveis on-demand.

Política epistemológica:

- autodescrição de praticantes é atribuída à tradição;
- pesquisa histórica/antropológica é separada da autodescrição;
- alegações sobrenaturais não são tratadas como mecanismos físicos estabelecidos;
- diversidade interna é preservada;
- conhecimento indígena/iniciático marcado como fechado não é reconstruído;
- fontes acadêmicas e fontes da própria comunidade são combinadas quando apropriado.

Os 5M são visões de estudo, **não 5M fatos independentes**.

## 8. Simulation Engine científico

`core/scientific_simulation.py`

Complementa o SimulationLab anterior usando NumPy já presente:

- RK4 vetorial genérico;
- órbita Newtoniana 2D de dois corpos + monitor de drift de energia;
- pêndulo não linear amortecido;
- equação do calor 1D com verificação de estabilidade explícita;
- equação da onda 1D com verificação CFL;
- circuito RC.

Os modelos são úteis para ciência/engenharia inicial e testes. Eles **não** substituem
solvers validados de CFD, FEA, SPICE, astrodinâmica de alta fidelidade ou relatividade numérica.

## 9. Research Hub

`core/research_hub.py`

- Crossref;
- OpenAlex;
- arXiv;
- PubMed/NCBI E-utilities;
- deduplicação por DOI, depois URL, depois título normalizado;
- rede desativada por padrão;
- descoberta bibliográfica não é automaticamente tratada como evidência validada;
- full-text arbitrário não é baixado automaticamente.

A taxonomia cultural pode produzir consultas de pesquisa para OpenAlex/Crossref quando
o modo ONLINE é explicitamente autorizado.

## 10. Operator File Index

`core/operator_index.py`

- índice persistente e somente leitura;
- varredura explícita, nunca em background no boot;
- ignora `.git`, `.venv`, caches, `node_modules` e diretórios de IDE;
- busca nominal rápida;
- não escreve, move ou apaga arquivos.

## 11. Senses observation contract

`core/senses.py`

- envelope comum para câmera/tela/sensores;
- timestamp, confiança e proveniência;
- buffer de fusão temporal;
- prepara integração MIND/Device Gateway;
- continua marcando `semantic_scene_understanding=false` e `multimodal_semantic_fusion=false`.

## 12. M.drives

`core/mdrives.py` + `core/m_drive_manager.py`

**M.drive = Memory + Drive/Pendrive.** É o novo nome oficial dos antigos Knowledge Packs.

- diretório atual: `knowledge/m_drives`;
- mídia removível preferida: `STAR_KNOWLEDGE/m_drives`;
- leitura compatível de `knowledge/packs` e `STAR_KNOWLEDGE/packs`;
- o repositório não mantém cópia atual duplicada em `packs`;
- `heroes` foi migrado para formato estruturado carregável;
- o antigo manifesto vazio de matemática básica foi removido porque duplicava o Math Engine;
- M.drive moderno/primeira identidade carregada vence duplicata, e conflitos são registrados;
- um M.drive nunca ganha permissão de executar código só por ser detectado.

## Integração no Core

`core/evolution.py` agrega essas capacidades sobre a instância já existente do MIND e
reutiliza a mesma instância da base cultural entregue ao Executive.

Comandos explícitos atuais incluem:

- `status evolução`;
- `contexto cognitivo`;
- `rotear engine <capacidade>`;
- `m.drives` / `listar m.drives`;
- `criar objetivo NOME: OBJETIVO`;
- `listar objetivos`;
- `pesquisar profundamente ...`;
- `pesquisa cultural ...`;
- `rag semântico ...`;
- `ocr caminho.pdf`;
- `indexar arquivos CAMINHO`;
- `indexar grafo científico`;
- `indexar grafo cultural`;
- `simular órbita`;
- `simular pêndulo`.

Os comandos são deliberadamente estreitos para evitar regressões no router estável.

## Dependências opcionais

`requirements-intelligence.txt` mantém fora do boot mínimo:

- `sentence-transformers`;
- `sqlite-vec`;
- `PyMuPDF`.

Tesseract é uma dependência externa do sistema para OCR. Nenhum modelo neural é
baixado automaticamente na inicialização da STAR.

## Limites honestos

- V2/V3/V4/V5/V7/V8 **não estão concluídos como releases inteiras**;
- o Model Router ainda não é um registry completo de todos os modelos locais/cloud;
- memória ainda precisa de consolidação, temporalidade avançada e esquecimento controlado;
- embeddings neurais dependem de instalação/modelo opcional;
- OCR depende de stack externo quando o PDF não contém texto;
- Research Hub encontra literatura, mas não substitui avaliação metodológica/retrações;
- o Knowledge Graph ainda não contém automaticamente cada claim factual/proveniência;
- Operator continua read-only neste alpha;
- Senses não possui scene understanding multimodal;
- Guardian não possui sandbox de SO nem vault criptográfico;
- Scheduler não executa trabalhos em background e autonomia sensível continua bloqueada;
- hardware real do Watch, GPS, saúde, laser e robótica continua exigindo implementação e validação física.
