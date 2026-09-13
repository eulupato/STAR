# STAR — Religiões, tradições e história da magia 5M

## Objetivo

Esta base amplia a cultura geral da STAR sem confundir religião, crença, magia,
folclore ou esoterismo com ciência experimental. O objetivo é permitir estudo
histórico, comparativo, antropológico, textual e contemporâneo de tradições do
mundo inteiro, com respeito à autodescrição das comunidades e à diversidade interna.

## Estrutura

A base possui:

- **125 assuntos culturais**;
- **100 tradições/relações religiosas**;
- **25 campos de magia/esoterismo/história da magia**;
- **40 aspectos canônicos por assunto**;
- **5.000 nós canônicos**;
- **1.000 perspectivas por nó** (`10 lentes × 10 profundidades × 10 formatos`);
- **5.000.000 conteúdos/visões endereçáveis**, materializados sob demanda.

Faixa de IDs:

```text
RCM-0001-0001 ... RCM-5000-1000
```

Os 5M são um espaço determinístico de estudo sobre 5.000 nós canônicos. **Não são
cinco milhões de fatos pesquisados individualmente** e não devem ser somados a
contagens factuais como se fossem afirmações independentes.

## Escopo

A taxonomia atravessa tradições cristãs, judaicas, islâmicas, iranianas, sul-asiáticas,
budistas, leste/sudeste-asiáticas, centro-asiáticas, africanas e afro-diaspóricas,
tradições indígenas das Américas e Oceania, religiões históricas do Mediterrâneo,
Europa e Ásia Ocidental, além de história da magia e esoterismo em diferentes épocas.

Os 40 aspectos cobrem origem, história, textos, tradição oral, autoridade, cosmologia,
doutrina, ética, normas, rituais, práticas cotidianas, contemplação, mística, iniciação,
festas, ritos de passagem, morte/pós-vida, peregrinação, símbolos, arte, música,
alimentação, corpo, família/gênero, instituições, diversidade interna, política,
economia, sincretismo, conflito/tolerância, diáspora, modernidade, ciência/filosofia,
demografia e crítica de fontes.

## Política epistemológica

A STAR deve manter quatro camadas separadas:

1. **autodescrição** — o que praticantes/textos internos afirmam;
2. **registro histórico/etnográfico** — o que fontes documentam sobre práticas e comunidades;
3. **interpretação acadêmica** — hipóteses e debates de historiadores, antropólogos, sociólogos etc.;
4. **evidência física/experimental** — quando uma alegação depende de mecanismo verificável.

Assim, uma frase como “a tradição X afirma que...” pode ser registrada como descrição
fiel da tradição sem que a STAR diga que a alegação sobrenatural foi demonstrada
cientificamente.

## Conhecimento sensível e tradições vivas

Para povos indígenas, tradições iniciáticas e comunidades que mantêm conhecimento
fechado, o sistema aplica uma regra adicional:

- usar apenas informação pública;
- priorizar fontes produzidas/validadas pela própria comunidade;
- não reconstruir cerimônias fechadas a partir de fragmentos;
- não transformar nomes, objetos, cantos ou saberes restritos em “receitas”;
- registrar incerteza e controvérsias de representação.

Isso é especialmente importante porque arquivos históricos podem conter descrições
coloniais, exotizantes ou publicadas sem consentimento contemporâneo.

## Fontes-base

A arquitetura foi desenhada para cruzar fontes com papéis diferentes:

- **Database of Religious History (UBC)** — entradas produzidas por especialistas,
  dados históricos padronizados, comentários qualitativos e referências;
- **Harvard Pluralism Project** — diversidade religiosa, encontros entre tradições e
  autodescrição contextual;
- **Pew Research Center** — demografia e surveys contemporâneos (não usado como
  autoridade doutrinária);
- **Library of Congress / American Folklife Center** — religião vernacular, arquivos,
  ritual, folclore, narrativas e materiais históricos sobre bruxaria/magia;
- **Smithsonian Anthropology** — etnologia, arquivos, cultura material e coleções;
- **UNESCO Intangible Cultural Heritage** — tradições vivas, rituais, oralidade,
  festividades e salvaguarda cultural;
- **Sefaria** — textos judaicos estruturados e ligações intertextuais;
- **SuttaCentral** — textos budistas estruturados;
- **OpenAlex/Crossref** — descoberta acadêmica atualizada via Research Hub.

Fontes públicas antigas (grimórios, tratados ocultistas, relatos de viagem ou
etnografias históricas) podem servir como **fontes primárias históricas**, mas não
recebem automaticamente o mesmo peso de pesquisa acadêmica atual ou de fontes da
comunidade descrita.

## Integração com Research Hub e Knowledge Graph

A base local resolve assunto/aspecto e gera consultas de pesquisa. Quando o modo
ONLINE é autorizado, o Research Hub pode localizar literatura recente via
OpenAlex/Crossref. Em etapas posteriores, claims e relações validados podem ser
ligados ao Knowledge Graph com proveniência.

A abordagem segue a ideia útil do GraphRAG de combinar recuperação textual com
entidades/relações, mas a STAR mantém seu próprio SQLite/grafo e não depende do
framework Microsoft GraphRAG para iniciar.

## Copyright

O GitHub da STAR não deve receber cópias integrais de obras protegidas apenas porque
elas estão disponíveis na web. A base versionada contém taxonomia, metadados,
conhecimento derivado/original e referências. Textos integrais só podem ser
materializados localmente quando licença, domínio público ou autorização permitirem.
