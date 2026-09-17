# STAR — Grupo 3: conhecimento, pesquisa e documentos

Este grupo amplia os sistemas existentes; não cria um segundo RAG, cérebro, memória ou banco de conhecimento.

## 21. Notificações inteligentes por relevância

`IntelligentProactiveScheduler` especializa o scheduler já existente. Cada evento recebe uma avaliação bounded de importância, tipo, urgência, relevância contextual, solicitação explícita do usuário e repetição recente. Eventos pouco relevantes ou duplicados continuam registrados na fila cognitiva, mas podem deixar de gerar notificação. O scheduler continua sem executar ferramentas ou ações físicas.

## 22. Pesquisa web geral com proveniência

`modules/internet.py` implementa pesquisa web opt-in. A STAR usa SearXNG quando configurado (`STAR_SEARXNG_URL`) e possui fallback para DuckDuckGo HTML. URLs privadas/locais são bloqueadas antes da recuperação. Parte dos resultados é recuperada para confirmar proveniência e acessibilidade, e a resposta registra domínio, horário, provider e status. Recuperabilidade/proveniência não é tratada como prova de veracidade.

## 23. Atualização automática e segura de conhecimento

`SafeKnowledgeUpdater` exige rede habilitada e pelo menos duas fontes independentes recuperáveis. Os resultados são adicionados ao `cognitive_facts` existente como `web_research_evidence`, com URL, horário e metadados. A operação é append-only/deduplicada e nunca promove conteúdo web automaticamente a fato canônico nem altera código/configuração.

## 24. Dicionários offline completos

O `OfflineDictionaryMaterializer` reutiliza `core/offline_dictionary.py` e `scripts/build_offline_dictionaries.py`. Dumps Kaikki/normalizados permanecem fora do Git para manter o projeto leve; quando materializados localmente, entram em `runtime/language/dictionaries.sqlite3`. O status registra fontes e total de relações. Nenhum download de gigabytes ocorre silenciosamente durante o startup.

## 25. OCR de imagens e PDFs escaneados

OCR é local e sob demanda. Imagens usam o executável Tesseract (`STAR_TESSERACT` ou PATH). PDFs primeiro tentam `pypdf`; quando o documento não possui texto útil, PyMuPDF opcional rasteriza as páginas e Tesseract executa OCR. Nenhuma imagem é enviada a serviços cloud.

## 26. DOCX, XLSX e PPTX no RAG

`EnhancedDocumentRAG` continua usando `DocumentRAG` e o mesmo `CognitiveStore`. DOCX/XLSX/PPTX são extraídos diretamente do OOXML (ZIP+XML da biblioteca padrão), evitando dependências Office pesadas. Proveniência, formato e método de extração ficam nos metadados do documento.

## 27. Busca semântica de arquivos do computador

`SemanticFileSearch` usa o mesmo `star.db`. A indexação é explícita, incremental e roda em thread daemon para não bloquear a interface. Se um modelo local apontado por `STAR_EMBEDDING_MODEL` e `sentence-transformers` estiver disponível, ele é usado sem download; caso contrário há um vetor textual local determinístico. Nenhuma pasta do computador é varrida automaticamente no startup.

## Comandos explícitos

- `status grupo 3`
- `pesquise na web <consulta>`
- `indexe documento <caminho>`
- `ocr <caminho>`
- `indexe arquivos em <pasta>`
- `status da indexação de arquivos`
- `busque semanticamente nos arquivos <consulta>`
- `status dos dicionários offline`
- `atualize conhecimento <tema MIND> sobre <consulta>`

## Limites e segurança

- Internet continua dependente do modo ONLINE da STAR.
- Pesquisa e OCR não concedem autorização operacional.
- Resultado web não vira fato canônico automaticamente.
- OCR pode estar indisponível sem Tesseract; PDF escaneado requer também PyMuPDF opcional.
- Dicionários grandes são materializados localmente; não são versionados no repositório.
- Busca de arquivos só indexa diretórios solicitados explicitamente e ignora pastas de desenvolvimento comuns (`.git`, `.venv`, `node_modules`, caches).
