# STAR — INTERAÇÃO NATURAL INTEGRADA

## Objetivo

Esta camada transforma a arquitetura cognitiva já existente em uma experiência de conversa contínua e menos mecânica, sem transformar um modelo de linguagem na STAR.

A STAR continua sendo a arquitetura completa: identidade, Self, memória, conhecimento, personalidade/afeto, cognição social, raciocínio, planejamento, metacognição, percepção, pessoas, limites e ferramentas. Um modelo local opcional pode apenas **verbalizar** uma resposta que esses sistemas já estruturaram.

## Fluxo

```text
ENTRADA
  ↓
contexto conversacional bounded
  ↓
pessoa ativa + memórias relevantes + percepção disponível
  ↓
FAST ou DELIBERATIVE / posição cognitiva existente
  ↓
resposta semântica
  ↓
expressão natural opcional por modelo local
  ↓
continuidade em working memory
  ↓
âncora persistente ocasional e resumida
```

O fluxo não cria outro Router, Brain, banco, memória, personalidade ou Permission Manager.

## Contexto multi-turn

`core/natural_interaction.py` mantém uma janela limitada de turnos em RAM. Ela rastreia:

- tópico ativo;
- referência de follow-up;
- pessoa ativa;
- relação disponível;
- estado afetivo B17;
- memórias sociais/pessoais B13/B26;
- observações B25 disponíveis;
- posição cognitiva produzida pelo pipeline existente.

Referências curtas como `e ele?`, `e a preta?`, `mas e o segundo?` podem carregar o tópico anterior para a cognição. Comandos operacionais conhecidos não são reescritos por esse mecanismo.

O histórico de sessão é bounded e não é salvo integralmente a cada turno. A cada grupo de interações relevantes pode ser gravada uma âncora curta de continuidade no B13; quando existe uma pessoa ativa, essa âncora pode ser associada ao B26.

## Expressão natural

O catálogo conversacional determinístico anterior continua existindo como fallback offline seguro, mas não é mais tratado como a personalidade inteira da STAR.

Quando existe um endpoint Ollama local em loopback, o runtime pode usar um modelo configurável apenas como **surface realizer**. O pacote enviado ao modelo é bounded e contém resposta semântica, contexto social, estado afetivo, posição cognitiva e contexto recente relevante.

O modelo não recebe autoridade para:

- decidir identidade;
- criar fatos;
- transformar inferência em fato;
- criar permissões;
- autenticar pessoas;
- executar ferramentas;
- declarar ações como executadas;
- redefinir personalidade ou valores fundamentais;
- concluir consciência/experiência subjetiva.

Se o modelo local falhar, estiver ausente ou demorar além do limite configurado, a STAR mantém a resposta semântica/fallback em vez de interromper o fluxo.

### Configuração local opcional

- `STAR_NATURAL_DIALOGUE_LOCAL_LLM`: habilita/desabilita a tentativa de expressão local;
- `STAR_LOCAL_LLM_HOST`: endpoint Ollama local, padrão `http://127.0.0.1:11434`;
- `STAR_LOCAL_LLM_MODEL`: modelo, padrão `qwen3:8b`;
- `STAR_NATURAL_DIALOGUE_TIMEOUT`: timeout do verbalizador, padrão `8` segundos e limitado pelo runtime.

A camada natural aceita por padrão somente host loopback. O modelo não é requisito para a STAR iniciar.

## Opiniões

Opiniões persistentes continuam separadas de preferências do usuário e de fatos.

Quando a STAR ainda não possui uma opinião persistente, a interação natural pode expressar uma **posição provisória** somente quando existe base interna suficiente, por exemplo uma preferência B17 ou inferência atual B24/B18 com confiança mínima e sem contexto essencial ausente.

Uma posição provisória:

- não vira fato;
- não é persistida automaticamente como opinião;
- permanece revisável;
- não copia automaticamente a opinião do usuário;
- não é usada para conceder autorização.

Se faltar contexto importante, a STAR continua perguntando em vez de inventar. No exemplo de roupa, ausência de informação visual e/ou ocasião continua sendo explicitamente detectada.

## Pessoas — B26

B26 agora suporta de forma explícita:

- criação/reuso conservador de pessoa declarada;
- aliases;
- perfil declarado persistente;
- interações associadas;
- evidências de identidade referenciadas;
- recuperação de memórias da pessoa por relações do Knowledge Graph;
- pessoa ativa compartilhada com a conversa natural.

`meu nome é ...` pode criar/reutilizar uma entidade persistente B26. Isso **não autentica** a pessoa.

### Foto + perfil

A API B26 pode receber um perfil e referências de evidência visual/voz/multimodal por `ingest_profile()` / `attach_identity_evidence()` e associá-los à mesma entidade persistente.

Isso não significa que qualquer imagem arrastada para qualquer interface da STAR já seja automaticamente ingerida. Para o fluxo completo automático, a interface/provider precisa entregar a imagem ou sua evidência ao B25/B26. A arquitetura de persistência já está pronta para receber essa integração.

Por padrão, B26 não salva biometria bruta. Uma evidência visual é armazenada como referência/proveniência/descritor/confiança, e sempre mantém:

```text
RECONHECIMENTO ≠ AUTENTICAÇÃO
CONFIANÇA ≠ PERMISSÃO
```

## Percepção — B25

O runtime consulta observações já disponíveis no B25. Quando uma observação visual real está no buffer, a cognição pode distinguir `imagem disponível` de `sem evidência visual`.

Isso não inventa câmera, tela, localização ou sensores. O provider físico correspondente precisa existir e estar conectado.

## Fluidez e desempenho

- contexto em RAM limitado;
- recuperação de pessoa/memória bounded;
- nenhuma carga dos espaços lógicos de 1B em RAM;
- nenhuma nova dependência;
- nenhum processo pesado contínuo em background;
- disponibilidade do modelo local é sondada de forma lazy e com cache;
- falha do verbalizador não derruba o Core;
- comandos/fatos críticos permanecem fora da reescrita livre.

## Segurança operacional

A interação natural não substitui B33/B01.

Pensar, concluir, conversar, recomendar, reconhecer e simular continuam separados de executar ou alterar o mundo. O texto produzido por um modelo de expressão nunca se transforma em autorização operacional.

## Estado funcional

Funcional na arquitetura atual:

- contexto conversacional multi-turn bounded;
- referência curta ao tópico anterior;
- estado afetivo e pessoa ativa disponíveis à expressão;
- memória social/pessoal associável;
- perfil B26 e evidência de identidade persistentes;
- conversa generativa quando existe modelo local compatível;
- fallback sem modelo;
- ausência de percepção não é escondida;
- comandos e respostas factuais críticas preservam caminhos estáveis.

Dependências externas/integrações ainda necessárias para alguns comportamentos:

- modelo Ollama instalado e modelo configurado para expressão realmente generativa local;
- provider real de visão para análise automática de fotos/câmera;
- providers reais de localização/saúde/sensores quando desejados;
- evento/scheduler externo para iniciativa proativa fora de um turno iniciado pelo usuário.

Esses limites são reportados como limites reais, e não como funcionalidades concluídas.