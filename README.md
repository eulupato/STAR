# ⭐ STAR — S.T.A.R.

**S.T.A.R. — System for Thought, Analysis and Response**

A STAR é uma arquitetura **offline-first** composta por identidade, Core, memória,
conhecimento, MIND, ferramentas, voz, interfaces e dispositivos. Um modelo local ou
cloud é somente um recurso utilizado pela STAR; nenhum modelo isolado é a STAR.

## Estado oficial

- **release estável:** STAR V1.9 Foundation;
- **camada cognitiva:** STAR MIND experimental-alpha;
- **Integrated Evolution:** alpha sobre V1.9, sem promover artificialmente V2+;
- **direção de produto:** Watch-first;
- **internet:** opcional e por capacidades/providers declarados;
- **banco cognitivo:** um único `star.db`;
- **branch `main`:** fonte oficial do estado versionado.

## 🧠 Conhecimento

A base factual endereçável anterior continua em **22,15M de variações composicionais**
(Física, Química, Multidisciplinar e Knowledge PLUS). Esse número não representa
22,15M fatos pesquisados individualmente.

A expansão curricular adiciona:

- **56 temas**;
- **956 menções** consolidadas em **885 conceitos canônicos únicos**;
- **71 duplicações** removidas por identidade/alias;
- **941.000.000** de visões curriculares endereçáveis on-demand.

Os 941M são um espaço determinístico de estudo/pesquisa sobre os conceitos canônicos,
e não 941M afirmações factuais independentes.

## 💾 M.drives

**M.drive = Memory + Drive/Pendrive.** É o nome oficial dos antigos **Knowledge Packs**.

Novos módulos ficam em:

```text
knowledge/m_drives/
```

Mídia removível usa preferencialmente:

```text
STAR_KNOWLEDGE/m_drives/
```

Para não quebrar dados existentes, `knowledge/packs` e `STAR_KNOWLEDGE/packs`
continuam legíveis como caminhos **legados**. A migração é explícita e não destrutiva;
nenhum M.drive executa código automaticamente por ser descoberto.

## 🧠 STAR MIND + Integrated Evolution

O MIND alpha mantém 15 capacidades cognitivas: raciocínio, planejamento, memória,
Knowledge Graph, raciocínio científico, matemática, simulação, coding, verificação,
RAG documental, pesquisa, projetos, user model, multiagentes e autoavaliação.

A camada Integrated Evolution acrescenta, sobre os mesmos sistemas:

### Cognitive Runtime

- Working Context limitado em RAM;
- Salience por relevância/novidade/risco/urgência/prioridade;
- Model Router para engines explicitamente registrados;
- sem criar memória persistente paralela.

### Goal Engine

- objetivos e tarefas persistentes;
- dependências;
- checkpoints;
- retomada;
- execução por handlers registrados;
- idempotência em conjunto com Guardian.

### Guardian alpha

- default-deny para ações desconhecidas;
- política e confirmação por ação;
- restrições remotas;
- audit log;
- claims idempotentes;
- redaction básica de segredos.

Ainda **não** existe sandbox de SO ou Secrets Vault criptográfico completo.

### RAG híbrido + OCR

A fonte de verdade continua sendo documentos/chunks no SQLite com FTS5/BM25. A nova
camada adiciona índice semântico derivado:

```text
PDF/texto
→ extração
→ OCR seletivo quando necessário
→ chunks
→ SQLite / FTS5
→ embedding derivado opcional
→ recuperação híbrida
```

- fallback semântico hashing é local/determinístico;
- Sentence Transformers é opcional;
- `sqlite-vec` é opcional;
- PyMuPDF + Tesseract são opcionais para OCR;
- nenhum modelo neural é carregado no boot base.

Dependências opcionais:

```powershell
python -m pip install -r requirements-intelligence.txt
```

Tesseract precisa ser instalado separadamente no sistema quando OCR real for usado.

### Knowledge Graph científico

`core/scientific_graph.py` pode materializar no grafo já existente:

- 56 temas;
- 885 conceitos canônicos;
- domínios;
- relações de pertencimento e co-tema derivadas da taxonomia.

Ele deliberadamente **não inventa relações causais** que não estejam sustentadas pela
fonte/taxonomia.

### Simulation Engine

Além do laboratório anterior, a STAR possui modelos NumPy locais de:

- RK4 vetorial;
- órbita Newtoniana 2D de dois corpos;
- pêndulo não linear amortecido;
- equação do calor 1D;
- equação da onda 1D;
- circuito RC.

Existem verificações como drift de energia, estabilidade explícita e condição CFL.
Isso ainda não substitui CFD/FEA/SPICE/astrodinâmica de alta fidelidade ou relatividade numérica.

### Research Hub

Pesquisa científica estruturada opt-in usa:

- Crossref;
- OpenAlex;
- arXiv;
- PubMed/NCBI.

Resultados são deduplicados por DOI → URL → título. Encontrar um paper não significa
que sua conclusão foi automaticamente validada; avaliação de evidência continua uma
etapa separada.

### Operator e Senses

- File Index persistente **somente leitura**, iniciado apenas por ação explícita;
- contrato unificado para observações de câmera/tela/sensores;
- buffer de fusão temporal;
- `semantic_scene_understanding=false` por enquanto;
- ações sensíveis continuam bloqueadas.

## Comandos alpha explícitos

Exemplos:

```text
status evolução
contexto cognitivo
rotear engine math
m.drives
criar objetivo Estudo: revisar relatividade geral
listar objetivos
pesquisar profundamente gravitational waves
rag semântico decoerência quântica
ocr C:\documentos\paper.pdf
indexar arquivos C:\Development\Projects
indexar grafo científico
simular órbita
simular pêndulo
```

Esses comandos são estreitos de propósito: o router estável da V1.9 continua com
prioridade e a nova camada não sequestra termos genéricos.

## 🌍 Idiomas

A STAR usa uma fonte canônica de conhecimento e camada de apresentação para:

- `pt-BR`;
- `en-US`;
- `en-GB`;
- `es-ES`;
- `it-IT`;
- `fr-FR`.

IDs, números/unidades, URLs, paths, código e matemática são protegidos pela tradução.
Traduções parciais inseguras são rejeitadas em vez de alterar informação.

## 🎙️ Voz e conversa

Arquitetura local:

```text
Microfone
→ faster-whisper
→ STAR Core
→ Chatterbox oficial / Piper / SAPI fallback
→ alto-falante
```

A referência oficial de voz é privada/local e nunca deve ser versionada.

O catálogo contém **27.804 variações auditáveis de comandos operacionais** e
**1.000.000 de variações temáticas de estudo**. A conversa local possui **6.000
combinações auditáveis**.

## 🌦️ Clima

O Core possui clima contextual sob demanda via Open-Meteo. Internet não é ativada
para outras capacidades só porque o clima foi consultado.

Configuração opcional:

```text
STAR_WEATHER_ENABLED=1
STAR_WEATHER_LOCATION=Cidade, Estado
STAR_WEATHER_AUTOLOCATE=0
STAR_WEATHER_CACHE_SECONDS=600
```

## 👁️ STAR Vision

O Vision Portal local possui:

- webcam local;
- MediaPipe HandLandmarker;
- duas mãos;
- tracking/suavização;
- portal AR;
- HUD/captura/fullscreen;
- 12 filtros.

Isso **não é ainda compreensão semântica de cena**. Abertura/fechamento remoto da
câmera do PC permanece bloqueado.

## ⌚ STAR Watch

A prioridade prática continua Watch-first:

```text
1. validar shell/voz/providers no PC;
2. portar Plasma Orbit para a base Android Watch existente;
3. integrar sensores/hardware reais;
4. validar em hardware físico;
5. depois construir a nova experiência principal de PC.
```

### Watch App V0.4

Simulador funcional no PC com **Plasma Orbit**:

```bat
INICIAR_STAR_WATCH_APP.bat
```

Modos atuais:

`VOZ · BUSCA · SAÚDE · GPS · VISÃO · PEOPLE · MEDIR · MÍDIA · CLIMA · IDIOMA · CONFIG`

No simulador, saúde/GPS/distância continuam marcados como **SIMULAÇÃO** quando não há
provider físico real. Não declaramos laser, reconhecimento automático de pessoas ou
sensores que não existem.

### Android Watch V0.3

A base em `clients/star_watch_android/` fornece transporte LAN, texto, áudio PCM/WAV,
STT no Core, resposta falada, câmera, heartbeat e runtime adaptativo. O shell Plasma
Orbit ainda precisa ser levado integralmente ao hardware e validado fisicamente.

## 📱 Mobile / Device Gateway

- cliente iOS: experimental;
- Device Gateway LAN: experimental e desligado por padrão;
- processamento cognitivo permanece no STAR Core;
- ações remotas sensíveis continuam bloqueadas;
- a porta do Gateway não deve ser exposta à internet.

## 🖥️ PC

A interface desktop V1.9 continua preservada:

```bat
INICIAR_STAR.bat
```

ou:

```powershell
.\.venv\Scripts\python.exe main.py
```

O Operator atual ainda é parcial. Volume, mídia, screenshot, busca/abertura limitada e
algumas ações existem; automação geral, escrita destrutiva e controle irrestrito do SO
não são liberados sem a arquitetura completa de permissões.

## Estrutura principal

```text
STAR/
├── clients/                    # Watch, Android, iOS, Vision
├── core/                       # Core, MIND, Evolution, conhecimento e engines
├── database/                   # persistência única
├── gui/                        # interface PC
├── knowledge/
│   ├── m_drives/               # nome oficial
│   └── packs/                  # compatibilidade legada temporária
├── modules/                    # ferramentas
├── voice/                      # STT/TTS
├── tests/
├── docs/
├── STAR_MANIFEST.json
├── STAR_MIND_MANIFEST.json
├── requirements.txt
├── requirements-intelligence.txt
└── main.py
```

## Testes e diagnóstico

Antes de considerar uma atualização concluída:

```powershell
python diagnostico.py
python -m pytest -q tests
```

Dependências opcionais não devem ser necessárias para o boot/teste base. Interfaces,
microfone, câmera, sensores e hardware físico exigem validação real além do CI.

Nunca versione `.env`, tokens, bancos pessoais, referências privadas de voz, modelos,
caches, fotos pessoais ou arquivos temporários.

## O que ainda não está concluído

Mesmo com as fundações novas, continuam futuros/parciais:

- V2 MIND completo e seus critérios de release;
- Model Registry completo e roteamento de modelos reais;
- embeddings neurais/materialização no PC do usuário;
- OCR até Tesseract/PyMuPDF serem instalados e testados localmente;
- Knowledge Graph de todos os fatos/proveniências;
- solvers CFD/FEA/SPICE e simulação científica de alta fidelidade;
- Research Engine full-text/avaliação metodológica automatizada;
- Operator geral e seguro;
- scene/screen/spatial awareness semântico;
- Guardian com sandbox, vault, autenticação, backup e rollback;
- Scheduler/Attention/Agent autonomy ponta-a-ponta;
- sync completo do ecossistema;
- STAR WORLD 3D;
- robótica física.

Consulte `docs/MASTER_ROADMAP.md` e `docs/STAR_INTEGRATED_EVOLUTION_ALPHA.md` para a
separação entre **estável, alpha, parcial e planejado**.
