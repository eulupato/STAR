# STAR — Conhecimento Offline Real

A STAR separa três conceitos:

1. **conteúdo lógico/endereço**: combinações de raciocínio e apresentação;
2. **conteúdo físico real**: registros existentes em fontes/dumps locais;
3. **conhecimento canônico**: conteúdo que passou pela política epistêmica da STAR.

Somente registros físicos reais contam para as metas de 1 bilhão por categoria.

## Categorias

A base registra 34 namespaces, todos com meta física de 1.000.000.000:
geografia, história, física, química, biologia, matemática, astronomia, ciências da Terra, ambiente, medicina, neurociência, psicologia, sociologia, filosofia, economia, direito, civismo, ciência da computação, engenharia de software, engenharia, mecânica, eletrônica, robótica, materiais, energia, fauna, flora, linguística, literatura, artes, música, cultura, agricultura e alimentação/nutrição.

A meta não é preenchida artificialmente. Categorias para as quais não existam 1B de registros únicos confiáveis permanecem abaixo da meta.

## Camadas offline

### Fatos estruturados

`cognitive_facts` no `star.db` possui busca FTS5 quando SQLite oferece FTS5. Novos fatos são indexados durante a ingestão e consultados pelo Executive antes dos matchers científicos/temáticos legados.

O arquivo `knowledge/offline_core_facts.jsonl` contém apenas um seed pequeno e rastreável para garantir uma base factual inicial. Ele não representa a base completa.

### Enciclopédia local

A cobertura ampla usa arquivos ZIM do ecossistema Kiwix/OpenZIM.

Backend preferencial:
- `python-libzim`, leitura e busca diretamente pelo processo Python.

Fallback:
- `kiwix-serve` ligado somente em `127.0.0.1`.

Diretório padrão:
`runtime/knowledge/zim`

O runtime não precisa de internet depois que o ZIM está local.

## Instalação explícita

Leitor ZIM:

```powershell
.\.venv\Scripts\python.exe scripts\setup_offline_knowledge.py install-reader
```

Base compacta:

```powershell
.\.venv\Scripts\python.exe scripts\setup_offline_knowledge.py download-wikipedia compact
```

Base ampla sem imagens:

```powershell
.\.venv\Scripts\python.exe scripts\setup_offline_knowledge.py download-wikipedia standard
```

Base completa com imagens:

```powershell
.\.venv\Scripts\python.exe scripts\setup_offline_knowledge.py download-wikipedia full
```

O downloader resolve o ZIM português mais recente no índice oficial Kiwix, permite retomada parcial e verifica o SHA-256 oficial quando publicado.

Nenhum download grande acontece no startup.

## Fontes especializadas

As categorias são mapeadas a fontes apropriadas. Entre as famílias registradas:

- Wikidata / DBpedia — conhecimento estruturado geral;
- Kiwix/Wikipedia — cobertura enciclopédica;
- NIST — física, matemática e química;
- PubChem — química;
- NCBI GenBank / PubMed — biologia e biomedicina;
- GBIF / Catalogue of Life — fauna, flora e taxonomia;
- NASA — astronomia;
- USGS / NOAA — geociências e ambiente;
- WHO — saúde;
- World Bank — economia;
- UNESCO UIS — educação/ciência/cultura;
- FAOSTAT — agricultura/alimentação;
- MusicBrainz — metadados musicais;
- OpenAlex / Crossref — literatura científica e proveniência bibliográfica.

Metadados bibliográficos não são tratados automaticamente como fatos científicos.

## Importação de fatos normalizados

JSONL esperado:

```json
{"theme":"geography","content":"A capital do Brasil é Brasília.","source":"...","source_type":"...","confidence":0.98,"metadata":{}}
```

Importação:

```powershell
.\.venv\Scripts\python.exe scripts\setup_offline_knowledge.py import-facts D:\dados\fatos.jsonl
```

## Verificação

```powershell
.\.venv\Scripts\python.exe scripts\setup_offline_knowledge.py status
```

O status diferencia explicitamente:
- fatos indexados;
- namespaces;
- contagem física;
- quantidade restante até 1B;
- disponibilidade do leitor ZIM.

## Limites

- 1B é meta por categoria, não alegação automática.
- O mesmo dump não conta duas vezes no mesmo namespace.
- Conteúdo sintético/variações não contam.
- Fontes grandes permanecem fora do Git.
- Wikipedia é uma camada enciclopédica, não substitui fontes primárias especializadas.
- Dados materializados não recebem status CANONICAL automaticamente.
