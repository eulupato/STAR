# STAR Languages 500K — idiomas, gírias e tradução offline

## Escopo

A STAR mantém **5 famílias linguísticas**:

1. Português — `pt-BR` — 🇧🇷 — idioma canônico/padrão;
2. Inglês — `en-US` 🇺🇸 e `en-GB` 🇬🇧 — uma família semântica, duas superfícies culturais;
3. Espanhol — `es-ES` — 🇪🇸;
4. Italiano — `it-IT` — 🇮🇹;
5. Francês — `fr-FR` — 🇫🇷.

Isso resulta em **6 perfis selecionáveis**, mas 5 famílias de conteúdo.

## 500.000 conteúdos de expressão

Cada família possui exatamente **100.000 conteúdos semânticos**:

- 50 expressões/equivalências pragmáticas de base;
- 2 modos semânticos (`base`, `intensified`) = 100 conceitos;
- 10 registros × 10 contextos × 10 tons = 1.000 variações por conceito;
- 100 conceitos × 1.000 = **100.000** por família;
- 5 famílias × 100.000 = **500.000** conteúdos.

O inglês mantém os mesmos 100.000 IDs semânticos com duas superfícies. Exemplo:

- pt-BR: `tô liso`;
- en-US: `I'm broke`;
- en-GB: `I'm skint`;
- es: `estoy sin un duro`;
- it: `sono al verde`;
- fr: `je suis fauché`.

Outro exemplo intencionalmente não literal:

- pt-BR: `e aí mano, sereno?`;
- en-US: `yo man, all good?`;
- en-GB: `alright mate, you good?`;
- es: `qué pasa, tío, todo tranqui?`;
- it: `ehi fra, tutto tranquillo?`;
- fr: `wesh mec, ça va tranquille?`.

A política é **equivalência de intenção/registro antes de tradução palavra por palavra**.

## Dicionários offline

Cada família registra no mínimo 5 fontes abertas/redistribuíveis conforme a licença da própria fonte. Os dumps grandes não são commitados no Git porque podem chegar a centenas de MB ou GB.

### Português

- Kaikki / Wiktionary Português;
- Kaikki English Wiktionary — Portuguese;
- FreeDict Portuguese dictionaries;
- Open Multilingual Wordnet — Portuguese;
- Apertium Portuguese lexical data.

### Inglês

- Open English WordNet 2025;
- Kaikki / Wiktionary English;
- FreeDict English dictionaries;
- Open Multilingual Wordnet — English;
- Apertium English lexical data.

### Espanhol

- Kaikki / Wiktionary Español;
- Kaikki English Wiktionary — Spanish;
- FreeDict Spanish dictionaries;
- Open Multilingual Wordnet — Spanish;
- Apertium Spanish lexical data.

### Italiano

- Kaikki / Wiktionary Italiano;
- Kaikki English Wiktionary — Italian;
- FreeDict Italian dictionaries;
- Open Multilingual Wordnet — Italian;
- Apertium Italian lexical data.

### Francês

- Kaikki / Wiktionary Français;
- Kaikki English Wiktionary — French;
- FreeDict French dictionaries;
- Open Multilingual Wordnet — French;
- Apertium French lexical data.

`core/offline_dictionary.py` contém o registro auditável. Há um léxico seed compacto para traduções comuns imediatamente, mesmo sem banco completo.

## Materialização do banco completo

O runtime usa `runtime/language/dictionaries.sqlite3`, que fica fora do Git. O construtor é:

```bash
python scripts/build_offline_dictionaries.py arquivo.jsonl --format jsonl
python scripts/build_offline_dictionaries.py arquivo.tsv --format tsv
python scripts/build_offline_dictionaries.py kaikki.jsonl.gz --format kaikki --source-locale pt-BR
```

Depois de construído, `OfflineDictionaryStore` consulta primeiro o SQLite local e não precisa de internet durante a tradução.

O script deliberadamente **não baixa dumps gigantes em silêncio**. Atualização é uma operação explícita: baixar snapshots abertos, importar, validar e então usar offline.

## Tradução do Core

`StarCore` possui `LanguageManager` antes das demais rotas. A sequência é:

```text
texto/STT
  ↓
comando de idioma/tradução?
  ↓ não
tradução de entrada para pt-BR quando disponível
  ↓
STAR Core / Physics / Conversation / Commands
  ↓
tradução offline da resposta para o idioma selecionado
```

A camada nunca inventa uma palavra ausente do índice: termos não encontrados são preservados, e traduções explícitas inexistentes retornam aviso de ausência.

Com o SQLite completo materializado, a mesma camada traduz respostas geradas por todo o Core, inclusive os conteúdos de Física. Sem o SQLite completo, somente equivalências contextuais e o léxico seed têm cobertura garantida.

## Comandos de voz

Exemplos reconhecidos antes do roteador comum:

```text
STAR, mude para inglês EUA
STAR, mude para inglês UK
STAR, troque para espanhol
STAR, fale em italiano
STAR, fale em francês
switch to British English
habla español
parla italiano
parle français

traduza "tô liso" para inglês UK
translate "tô liso" to French
```

Como a entrada de voz do Watch vira texto antes do Core, esses comandos funcionam também por STT.

## STAR Watch — aba IDIOMA

`clients/star_watch_language.py` estende o Plasma Orbit sem substituir o renderer existente.

Dentro de **IDIOMA**:

- girar para esquerda/direita troca o perfil;
- a bandeira e o nome do idioma ficam no centro;
- vizinhos aparecem nas laterais;
- pressionar confirma e volta;
- ordem: 🇧🇷 `pt-BR` → 🇺🇸 `en-US` → 🇬🇧 `en-GB` → 🇪🇸 `es-ES` → 🇮🇹 `it-IT` → 🇫🇷 `fr-FR`.

O launcher `INICIAR_STAR_WATCH_APP.bat` abre essa camada. Estados, cores, núcleo, anéis e navegação Plasma Orbit continuam herdados do visual V0.4.

## Fontes verificadas em setembro de 2026

- Kaikki/Wiktextract: dados derivados do Wiktionary, atualizados regularmente; snapshots de setembro de 2026 estavam disponíveis para inglês, espanhol, português, italiano e francês.
- Open English WordNet 2025: release em JSON/LMF/RDF/WNDB sob CC-BY 4.0.
- FreeDict: disponibiliza pares bilíngues para várias combinações dessas línguas.
- Open Multilingual Wordnet e Apertium complementam relações semânticas/morfológicas e pares de tradução.

Sempre respeite a licença específica do dump importado e preserve atribuições exigidas pelas fontes.
