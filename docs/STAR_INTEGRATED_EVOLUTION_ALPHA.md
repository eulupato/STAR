# STAR Integrated Evolution — alpha

Esta evolução aproxima MIND, KNOWLEDGE, OPERATOR, SENSES, GUARDIAN e AGENT sem
promover artificialmente o projeto para versões completas do roadmap.

## Referências de arquitetura estudadas
- LangGraph: execução durável, checkpoints, memória curta/longa e human-in-the-loop.
- sqlite-vec: índice vetorial local sobre SQLite; adotado apenas como adaptador opcional por ainda ser pre-1.0.
- Sentence Transformers: semantic search local; modelo neural opcional, nunca requisito de boot.
- PyMuPDF/Tesseract e OCRmyPDF: OCR local e seletivo para PDFs escaneados.
- NetworkX: relações explícitas e algoritmos de grafos como referência; o armazenamento oficial continua no SQLite da STAR.
- NASA F Prime: componentes bem delimitados, comandos/eventos/telemetria e health monitoring como referência de sistemas confiáveis.
- Crossref, OpenAlex, arXiv e NCBI/PubMed: provedores especializados para descoberta bibliográfica.

Nenhum desses projetos foi copiado/vendorizado. Foram reutilizados princípios e APIs públicas.

## Capacidades adicionadas

### Goal Engine durável
`core/goal_engine.py`
- objetivos e tarefas persistentes no `star.db`;
- dependências entre tarefas;
- checkpoints;
- retomada de estado;
- execução por handlers registrados;
- idempotência quando usado com Guardian.

### Guardian alpha
`core/guardian.py`
- default-deny para ações desconhecidas;
- política por ação;
- confirmação e restrições remotas;
- audit log persistente;
- claims idempotentes para evitar repetição de efeitos colaterais;
- redaction básica de segredos em logs.

Ainda NÃO é sandbox de SO nem Secrets Vault criptográfico completo.

### RAG híbrido
`core/semantic_rag.py`
- preserva FTS5/BM25 como fonte de verdade;
- adiciona índice derivado de embeddings por chunk;
- Sentence Transformers opcional;
- fallback hashing local e determinístico quando o backend neural não existe;
- índice pode ser reconstruído sem perder documentos.

### OCR local
`core/ocr.py`
- tenta `pypdf` primeiro;
- só ativa OCR em PDF escaneado/sem texto suficiente;
- PyMuPDF + Tesseract opcionais;
- texto OCR entra no DocumentRAG existente, não em um RAG paralelo.

### Research Hub
`core/research_hub.py`
- Crossref;
- OpenAlex;
- arXiv;
- PubMed/NCBI E-utilities;
- deduplicação por DOI, URL e título;
- rede desativada por padrão;
- descoberta bibliográfica não é tratada automaticamente como evidência validada.

### Operator File Index
`core/operator_index.py`
- índice persistente e somente leitura;
- varredura explícita, nunca em background no boot;
- ignora `.git`, `.venv`, caches e `node_modules`;
- busca nominal rápida;
- não escreve/apaga arquivos.

### Senses observation contract
`core/senses.py`
- envelope comum para câmera/tela/sensores;
- buffer de fusão temporal;
- provenance/confidence;
- não declara compreensão semântica de cena antes de existir.

### M.drives
`core/mdrives.py`
- novo nome oficial de Knowledge Packs: **M.drives (Memory + Drives/Pendrives)**;
- novo diretório `knowledge/m_drives`;
- leitura compatível de `knowledge/packs`;
- M.drive atual vence duplicata legada;
- migração explícita e não destrutiva.

## Integração no Core
`core/evolution.py` agrega as novas capacidades sobre a instância existente do MIND.
Os comandos explícitos são deliberadamente estreitos para evitar regressões no router:
- `status evolução`;
- `m.drives` / `listar m.drives`;
- `criar objetivo NOME: OBJETIVO`;
- `listar objetivos`;
- `pesquisar profundamente ...`;
- `rag semântico ...`;
- `ocr caminho.pdf`;
- `indexar arquivos CAMINHO`.

## Limites honestos
- V2/V3/V4/V5/V7/V8 continuam não concluídos como releases completas;
- embeddings neurais dependem de instalação/modelo opcional;
- `sqlite-vec` permanece adaptador futuro/experimental;
- OCR exige Tesseract externo;
- Research Hub encontra literatura, mas não substitui avaliação metodológica;
- Operator ainda é read-only;
- Senses ainda não possui scene understanding multimodal;
- Guardian ainda não possui sandbox de SO nem vault criptográfico;
- autonomia sensível continua bloqueada.
