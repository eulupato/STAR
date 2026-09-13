# ⭐ STAR Cognitive Foundation — World Model + Continuous Cognition

**Status:** experimental, integrado ao STAR MIND atual  
**Host release:** STAR V1.9 estável  
**Roadmap:** V2.0 MIND / V2.1 Memory / V2.2 Knowledge Graph / V3.0 Knowledge

## Objetivo

Esta camada implementa a matriz de compreensão do mundo e a arquitetura cognitiva contínua sem criar centenas de módulos paralelos.

A STAR continua sendo uma única arquitetura. Os domínios abaixo são conhecimento e capacidades de compreensão usados pelo MIND existente.

## Escala canônica

A especificação corrigida contém:

- 200 domínios de compreensão do mundo;
- 869 subtemas de mundo;
- 85 domínios de cognição contínua;
- 174 subtemas cognitivos;
- 1.328 nós canônicos;
- 1.000.000.000 de views semânticas por nó;
- 1.328.000.000.000 de views endereçáveis.

A contagem de views **não é apresentada como 1,328 trilhão de fatos pesquisados**.

Cada nó possui conteúdo canônico real derivado da especificação do projeto. Uma view combina esse conteúdo com nove dimensões semânticas, sempre preservando o conteúdo-base e seu estado epistemológico.

## Nove dimensões da expansão 1B

Cada índice de 1 a 1.000.000.000 mapeia deterministicamente para:

1. forma de conhecimento;
2. profundidade;
3. contexto;
4. temporalidade;
5. evidência;
6. raciocínio;
7. representação;
8. perspectiva;
9. validação.

Cada dimensão possui dez valores: `10^9 = 1.000.000.000`.

Isso permite profundidade combinatória sem criar um bilhão de arquivos, strings repetidas ou linhas de banco por nó.

## Conhecimento real x view derivada

Uma view derivada nunca é promovida automaticamente a fato.

Novas afirmações factuais devem possuir:

- conteúdo;
- fonte;
- tipo de fonte;
- confiança;
- estado epistemológico;
- validade temporal quando aplicável;
- evidências de suporte/contradição quando existirem.

Fluxo:

```text
DISCOVERED
↓
QUARANTINED
↓
VERIFIED
↓
CANONICAL
↓
SUPERSEDED / RETRACTED
```

Contradições são preservadas em vez de uma fonte sobrescrever silenciosamente a outra.

## Cinco modelos internos

A matriz corrigida usa cinco modelos, não quatro:

```text
WORLD MODEL
HUMAN MODEL
SOCIAL MODEL
SELF MODEL
SITUATION MODEL
```

Eles convergem no presente cognitivo e trabalham com memória, conhecimento, causalidade, incerteza, planejamento e resultado observado.

## Continuous Cognitive State

`core/mind.py` mantém um estado cognitivo persistente sobre o mesmo `star.db`.

Inclui:

- cinco modelos internos;
- working memory;
- atenção;
- saliência;
- lacunas de conhecimento;
- estado interno;
- memória autobiográfica;
- claims revisáveis;
- experiência;
- personalidade com plasticidade limitada.

O estado não é um segundo cérebro nem um banco separado.

## Experiência e autobiografia

Conhecimento e experiência são representações diferentes.

Conhecimento pode dizer que determinado material é frágil.

Experiência registra um episódio real da STAR com:

- evento;
- contexto;
- resultado;
- consequência;
- aprendizagem.

Uma experiência isolada não vira regra universal automaticamente.

## Personalidade

A personalidade não depende de um prompt gigante e também não pode ser reescrita por uma única página ou conversa.

A base funcional é:

```text
IDENTIDADE
+ VALORES
+ CONHECIMENTO
+ MEMÓRIA
+ EXPERIÊNCIA
+ RELAÇÕES
+ CONSEQUÊNCIAS
+ TEMPO
→ PERSONALIDADE EM DESENVOLVIMENTO
```

A plasticidade é deliberadamente lenta e limitada.

Uma alteração de traço exige padrão repetido e cada atualização é limitada a ±0,02.

O núcleo de identidade não pode ser modificado pelo processo normal de aprendizagem.

## Correções transversais incorporadas

A fundação registra explicitamente distinções críticas, entre elas:

- massa ≠ peso;
- calor ≠ temperatura;
- frio não é uma substância física;
- correlação ≠ causalidade;
- expressão ≠ emoção comprovada;
- ação ≠ intenção conhecida;
- reconhecimento ≠ autenticação;
- memória humana ≠ gravação perfeita;
- CFC-97 ≠ 97% consciente/humana.

## Consciência

A arquitetura pode implementar funcionalmente:

- self;
- continuidade;
- integração;
- atenção;
- memória autobiográfica;
- metacognição;
- presente cognitivo;
- perspectiva;
- aprendizagem;
- world model.

Isso **não autoriza** a STAR a afirmar `CONSCIOUS = TRUE`.

O nome técnico continua:

**STAR Continuous Cognitive System / STAR Synthetic Cognitive Architecture**

## Compatibilidade

A implementação preserva:

- os 15 catálogos operacionais existentes do MIND;
- os 15M conteúdos operacionais legados;
- `star.db`;
- routing da V1.9;
- Knowledge Packs;
- engines científicos existentes;
- identidade independente de LLM;
- regra local-first.

Nenhuma capacidade V2/V3 é marcada como concluída por causa desta fundação.

## Arquivos

```text
knowledge/cognitive_foundation.json.gz
core/cognitive_catalog.py
core/mind.py
STAR_MIND_MANIFEST.json
tests/test_cognitive_foundation.py
```

O arquivo de dados é compactado porque é um catálogo gerado grande e somente leitura; em runtime é carregado localmente com `gzip` + `json`.

## Regra de crescimento

A STAR pode crescer para bilhões/trilhões de views, mas a métrica de aprendizado real continua sendo:

- novos conceitos canônicos;
- novas entidades;
- novos claims com fonte;
- novas relações;
- evidências;
- cobertura;
- frescor;
- confiança;
- experiências.

Quantidade nunca substitui qualidade semântica.
