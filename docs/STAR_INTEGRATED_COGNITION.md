# STAR — Cognição Integrada

## Objetivo

Esta atualização conecta os sistemas cognitivos já existentes da STAR ao caminho normal de resposta sem criar um segundo Brain, outra memória, outro Planner, outra personalidade ou outro mecanismo de raciocínio.

O princípio é simples:

```text
entrada
→ roteamento cognitivo
→ posição cognitiva
→ expressão
→ resposta
```

O modelo de linguagem, quando futuramente utilizado, continua sendo ferramenta. A identidade, as preferências, as opiniões persistentes, a memória e os limites operacionais pertencem à arquitetura STAR.

## Mapa da arquitetura reutilizada

| Sistema existente | Responsabilidade preservada | Integração nesta atualização |
| --- | --- | --- |
| `StarIdentity` / B12 | identidade, princípios e limites | fornece valores estáveis; não é reescrita |
| `MemoryContinuity` / B13 | memória persistente + working memory bounded | recupera contexto e guarda somente a posição ativa de forma transitória |
| `AttentionSalience` / B14 | seleção relevante | reutilizada pelo Mind Loop |
| `IntegratedInternalModels` / B15 | WORLD/HUMAN/SOCIAL/SELF/SITUATION | reutilizados pelo Mind Loop |
| `SocialCognition` / B16 | contexto social e hipóteses de intenção | confiança social continua separada de permissão |
| `AffectivePersonality` / B17 | afeto, personalidade e preferências persistentes | também guarda opiniões como um tipo explícito de preferência estruturada, preservando histórico |
| `ReasoningSimulation` / B18 | raciocínio e simulação | reutilizado no caminho deliberativo |
| `PlanningDecision` / B19 | alternativas e decisão | continua sem executar ações |
| `Metacognition` / B20 | confiança, fontes, lacunas, pesquisa/pergunta | alimenta a posição cognitiva |
| `LearningEvolution` / B21 | aprendizagem auditável | permanece dependente de experiência observada |
| `KnowledgeIntegration` / B22 | integração de conhecimento | continua sem promoção canônica automática |
| `GlobalCognitiveWorkspace` / B23 | conjunto ativo bounded | evita carregar espaços lógicos inteiros |
| `MindLoop` / B24 | ciclo cognitivo integrado | passa a ser usado em interações deliberativas reais |
| `Router` | roteamento | seleciona FAST ou DELIBERATIVE |
| `Executive` | produção da resposta final | recebe a posição cognitiva antes da expressão |

## FAST PATH

Usado para interações simples, comandos claros e entradas que não exigem deliberação profunda.

Características:

- não executa o Mind Loop completo;
- mantém custo fixo baixo;
- preserva o caminho local-first;
- continua sujeito a identidade, limites e roteamento existentes.

## DELIBERATIVE PATH

Usado para opiniões, decisões, comparação, análise, conflito de posições, ambiguidade e entradas que exigem maior raciocínio.

Reutiliza o `MindLoop.run_cycle()` B24 e portanto combina, de forma bounded:

```text
PERCEBER
→ CONTEXTO
→ WORKING MEMORY
→ SALIÊNCIA
→ MEMÓRIA
→ CONHECIMENTO
→ MODELOS
→ INTERPRETAÇÃO
→ SIMULAÇÃO
→ METACOGNIÇÃO
→ JULGAMENTO
→ DECISÃO
→ AÇÃO (somente elegibilidade)
→ RESULTADO (somente observado)
→ EXPERIÊNCIA (somente auditável)
→ APRENDIZADO
→ ATUALIZAÇÃO
```

Nem todas as etapas produzem conteúdo em toda interação. O ciclo não executa ferramentas e não fabrica resultados para completar a sequência.

## Posição cognitiva

`CognitiveIntegration` produz um artefato transitório `star.cognitive_position.v1` antes da expressão final.

Ele pode conter, somente quando pertinente:

- assunto;
- intenção percebida;
- estado afetivo atual;
- contexto social;
- valores relevantes;
- opinião do usuário;
- opinião persistente da STAR;
- resumo epistêmico;
- confiança;
- incertezas;
- necessidade de pesquisar, perguntar ou revisar;
- discordância;
- decisão comunicativa;
- tom;
- iniciativa possível;
- tempos de processamento.

A posição ativa é armazenada apenas na working memory B13 com `persistent=False`. Não foi criado banco novo.

## Opiniões independentes e revisáveis

Uma afirmação do usuário é classificada como `information_received` e nunca se transforma automaticamente em crença ou opinião da STAR.

Opiniões persistentes são armazenadas por meio do store já utilizado pelo B17, com:

- tema;
- posição;
- intensidade;
- justificativa;
- evidências;
- preferências/valores relacionados;
- confiança;
- origem;
- motivo;
- referência da revisão anterior.

Alterações exigem `source` e `reference`, preservando histórico append-only. Um argumento do usuário pode ser considerado em deliberações futuras, mas não sobrescreve a posição persistente por simples concordância social.

## Identidade, personalidade, estado e permissão continuam separados

A integração preserva explicitamente:

```text
AFETO ≠ IDENTIDADE
PREFERÊNCIA ≠ PERMISSÃO
OPINIÃO ≠ FATO
CONFIANÇA ≠ VERDADE
CONFIANÇA SOCIAL ≠ AUTORIZAÇÃO
DECISÃO ≠ EXECUÇÃO
SIMULAÇÃO ≠ OBSERVAÇÃO
LEMBRAR ≠ PROVAR
INFERIR ≠ SABER
```

## Percepção e avaliações estéticas

A integração não inventa visão. Quando uma avaliação estética depende de imagem/descrição ou ocasião e esses dados não estão presentes, a posição cognitiva registra a lacuna e a resposta pede contexto.

Quando um provider perceptivo real estiver anexado ao B24, o mesmo fluxo poderá consumir observações reais sem mudar a identidade ou a camada de opinião.

## Iniciativa

A posição pode produzir um candidato de iniciativa baseado em relevância/urgência, mas:

- não interrompe automaticamente;
- não cria scheduler paralelo;
- não executa ação;
- depende de evento/sistema operacional apropriado para futura entrega proativa.

## Métricas

A posição registra tempos de:

- seleção FAST/DELIBERATIVE;
- processamento afetivo;
- recuperação de memória;
- Mind Loop;
- construção total da posição;
- expressão;
- geração/resolução da resposta no Executive.

Isso permite medir a evolução cognitiva sem aceitar regressão de fluidez às cegas.

## Testes comportamentais adicionados

`tests/test_cognitive_integration.py` cobre:

1. FAST PATH sem ciclo profundo;
2. DELIBERATIVE para opinião e decisão;
3. usuário não sobrescreve opinião da STAR;
4. discordância independente;
5. argumento novo não causa revisão automática;
6. revisão explícita e auditável preserva histórico;
7. avaliação estética com contexto insuficiente pergunta em vez de inventar percepção;
8. estado afetivo muda tom sem mudar a opinião/fato;
9. Router expõe FAST/DELIBERATIVE sem Brain paralelo;
10. Executive usa posição cognitiva antes do fallback genérico;
11. continuidade de opinião em múltiplas interações;
12. métricas e posição ativa permanecem bounded/transitórias.

## Limites atuais

- Percepção real continua dependente de providers existentes/futuros; esta atualização não simula sensores.
- A iniciativa é apenas candidata; não existe interrupção autônoma por este módulo.
- Opiniões não são fabricadas em massa. Elas surgem quando deliberadas/registradas com origem rastreável.
- O sistema não reivindica consciência.
- Modelos externos continuam opcionais e não possuem autoridade sobre identidade ou permissões.

## Resultado arquitetural

A mudança transforma os blocos cognitivos já existentes em partes do mesmo ciclo operacional:

```text
STAR recebe
→ Router escolhe custo cognitivo
→ sistemas existentes deliberam
→ posição cognitiva é formada
→ Executive expressa a posição
→ nenhuma decisão vira ação sem a fronteira operacional existente
```

A arquitetura converge: um único STAR Core, uma única memória oficial, um único conjunto de modelos internos, um único Planner, uma única metacognição e um único ciclo profundo B24.
