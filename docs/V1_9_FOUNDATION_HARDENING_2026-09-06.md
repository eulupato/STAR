# ⭐ STAR V1.9 — Foundation Hardening · 2026-09-06

Esta nota registra a revisão da Foundation V1.9 feita sobre a branch
`feature/star-world-2d-functional-20260904` / PR #16.

## Princípios preservados

- `main` continua sendo a release estável V1.9 FINAL.
- O PR #16 permanece Draft até validação visual e física em Windows.
- Nenhum Core, MIND, memória ou identidade paralelos foram criados.
- A STAR continua local-first; Internet amplia capacidades, mas não constitui a STAR.
- V2 MIND, V3 KNOWLEDGE/RAG, V5 SENSES, V6 STAR WORLD 3D, V7 GUARDIAN e V9 ECOSYSTEM continuam em seus marcos do roadmap.

## Heróis — causa raiz e correção

O pack `knowledge/packs/heroes/` possuía `manifest.json` e `heroes.json`, porém o
`KnowledgePackManager` V1.9 aceita conteúdo por `knowledge.jsonl`,
`knowledge.json` ou por `content_file` explicitamente declarado. Além disso, o
`heroes.json` antigo era apenas uma lista de nomes e não obedecia ao schema de
entradas consultáveis (`title`, `answer/content`, aliases/keywords e source).

Consequência: a Ilha podia detectar arquivos JSON sem possuir nenhuma entrada
realmente pesquisável pelo Core.

A correção desta revisão:

1. migra o seed para `knowledge.json` estruturado;
2. declara `content_file` no manifest;
3. mantém 12 entradas iniciais do catálogo já aprovado, separando claramente
   HISTÓRICO, MITOLÓGICO e FICTÍCIO;
4. adiciona metadados e estado de asset visual;
5. imagens protegidas não são versionadas em massa — sem asset autorizado, a
   entrada registra `missing_authorized_asset`;
6. o `KnowledgePackManager` passa a expor `list_entries(pack_id)` e busca
   opcionalmente restrita a um pack, sem duplicar parsing na GUI;
7. a Ilha dos Heróis usa o mesmo manager do Core, com roster e busca offline.

**Cobertura desta etapa:** seed local funcional de 12 entradas. Isto não é marcado
como catálogo universal completo. Expansões Marvel/DC permanecem separadas e
devem preservar proveniência, identidade de variantes e política de assets.

## Voz — hardening seguro

O fluxo atual já mantém a referência privada fora do Git e o `VoiceManager`
exporta `STAR_VOICE_REFERENCE` ao worker. O worker foi endurecido para:

- confiar no caminho entregue pelo manager, sem descobrir outra voz;
- tratar env vazia como ausência no modo manual;
- exigir `is_file()` para a referência;
- rejeitar diretórios como áudio;
- reportar causa/remédio explicitamente;
- manter o princípio de não usar fallback genérico silencioso no modo oficial.

A validação física de microfone, alto-falante, Chatterbox e da referência privada
continua obrigatória no Windows real antes de declarar a voz validada.

## Skins e Closet

A revisão confirmou que o renderer Python atual usa thumbnail proporcional quando
`fit=False`, preservando aspect ratio. Converter JPEG para PNG sem remover fundo
não cria transparência e tende a aumentar o repositório; portanto esta revisão não
faz conversão cega de assets.

Quando fontes transparentes/autorizadas forem fornecidas, a migração deve:

- preservar proporção e pixel art;
- validar alpha/bordas;
- evitar recorte ou deformação;
- substituir somente após confirmar referências existentes.

A transformação visual de skin e o rig de olhos em camadas continuam pendentes de
assets/validação visual e não são declarados como concluídos.

## Validação automática esperada

- `python -m py_compile` nos módulos alterados;
- `pytest -q tests`;
- STAR CI;
- STAR quality;
- STAR Windows smoke.

## Validação física ainda pendente

1. iniciar a STAR em Windows real;
2. Menu/HUB/resize visual;
3. Closet com todas as skins locais;
4. microfone/STT;
5. modo de voz oficial com referência privada;
6. modo fast;
7. navegação e pesquisa offline na Ilha dos Heróis.

Até estes itens passarem, o PR #16 deve permanecer **Draft**.
