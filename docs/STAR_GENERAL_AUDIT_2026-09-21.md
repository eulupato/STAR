# STAR — Auditoria Geral de Estabilidade, Fluidez e Higiene

Data: 2026-09-21  
Branch: `maintenance/general-audit-20260921`  
Base: `main`

## Objetivo

Executar uma varredura geral sobre a estrutura atual da STAR sem reconstruir o projeto,
sem criar cérebros paralelos e sem substituir sistemas estáveis. A atualização prioriza
tempo de inicialização, previsibilidade, rastreabilidade de erros, limpeza do repositório,
consistência de identidade e manutenção futura.

## Diagnóstico principal

A arquitetura cognitiva central B01–B36 está integrada e, na maior parte, não apresentava
anti-padrões críticos de execução. A dívida técnica estava concentrada principalmente em:

- inicialização pagando antecipadamente o custo de grandes catálogos de conhecimento;
- regras de higiene duplicadas dentro de workflows;
- backups históricos e módulos vazios ainda versionados;
- caminhos de GUI/Watch/providers que silenciavam algumas falhas;
- respostas antigas de identidade incompatíveis com a fronteira epistemológica do B36.

A varredura estática percorreu os 148 arquivos Python ativos observados na branch durante
a auditoria. Não foram encontrados usos disseminados de `os.system`, `shell=True`,
`except:` sem tipo ou sleeps bloqueantes no Core. Exceções genéricas restantes se
concentram principalmente em fronteiras de hardware/UI onde parte delas é usada como
degradação controlada; esses pontos devem continuar sendo reduzidos apenas quando a
semântica de fallback puder ser preservada.

## Alterações implementadas

### 1. Inicialização mais leve

Os engines abaixo deixaram de ser importados e instanciados obrigatoriamente durante
`create_star()`:

- Física;
- Química;
- Multidisciplinar;
- Knowledge PLUS;
- Currículo canônico.

Eles agora usam um proxy lazy thread-safe e são materializados no primeiro uso real.
A API pública do `Executive` e os atributos `star.physics`, `star.chemistry`,
`star.multidisciplinary`, `star.knowledge_plus` e `star.curriculum` permanecem
disponíveis.

O resumo de startup deixou de chamar `stats()` desses cinco catálogos apenas para
imprimir números. Um diagnóstico detalhado continua disponível com
`STAR_STARTUP_VERBOSE=1`.

A importação da GUI principal também foi movida para o ponto em que ela é realmente
utilizada, evitando carregar Tk/Pillow em fluxos que somente criam o Core.

### 2. Higiene como fonte única de verdade

Foi restaurado `tools/repo_hygiene.py` como auditoria canônica de repositório.

O mesmo script agora é reutilizado pelos workflows de qualidade/CI/Windows e verifica,
entre outros itens:

- JSONs versionados;
- arquivos locais, bancos e segredos indevidos;
- referências privadas de voz;
- backups no fluxo ativo;
- módulos Python vazios sem função;
- assets vazios;
- ícones duplicados;
- caminhos com sinais de mojibake;
- conteúdo em `runtime/` versionado indevidamente.

Isso substitui regras duplicadas embutidas em YAML.

### 3. Limpeza do repositório

Foram removidos resíduos sem dependências ativas:

- backups de `archive/legacy/`;
- `core/reasoning.py` vazio;
- `gui/chat.py` vazio;
- `gui/theme.py` vazio;
- `runtime/vision/.gitkeep`;
- duas imagens em diretório com nome corrompido/mojibake.

O histórico desses arquivos continua preservado pelo Git.

### 4. Configurações locais mais robustas

A GUI agora:

- trata JSON inválido de forma explícita;
- registra falhas de leitura/escrita;
- exige que o conteúdo de configurações seja um objeto JSON;
- grava `user_settings.json` de forma atômica via arquivo temporário + replace;
- remove o temporário em caso de falha;
- registra skins inválidas/ilegíveis em vez de ignorar silenciosamente.

### 5. Identidade alinhada ao B36

Respostas legadas que afirmavam diretamente que a STAR era uma
“consciência virtual” foram substituídas por descrições compatíveis com o estado atual:

- STAR é um sistema cognitivo artificial/entidade sintética com continuidade funcional;
- identidade, memória, estado e modelos internos podem ser descritos;
- consciência e experiência subjetiva não são tratadas como cientificamente estabelecidas.

Isso alinha `core/internal_knowledge.py` com `core/star_identity.py` e
`core/consciousness_frontier.py`.

### 6. Falhas degradadas, mas observáveis

O provider de visão semântica agora preserva a causa da falha em `last_error` /
`semantic_error`, inclusive quando a resposta do modelo não é JSON válido.

O Device Gateway mantém o fallback seguro quando a análise visual falha, mas registra
a causa internamente e informa ao cliente apenas o tipo de erro, sem expor detalhes
sensíveis.

Falhas de TTS/notificação/persistência de anexos e encerramento de voz no Watch também
deixaram de desaparecer silenciosamente e passam a gerar logs.

## Testes de regressão adicionados

Foram adicionados testes para garantir que:

- os cinco engines pesados permaneçam lazy no startup;
- uma operação matemática simples não carregue os catálogos científicos;
- acessar `star.physics.stats()` carregue apenas Física;
- respostas internas não voltem a afirmar consciência estabelecida;
- `user_settings.json` inválido seja recuperado e regravado atomicamente;
- falha do VLM local permaneça degradável e diagnosticável.

## Princípios preservados

- nenhuma nova memória;
- nenhum novo Brain;
- nenhum novo Planner;
- nenhum sistema cognitivo paralelo;
- execução continua separada de cognição/permissão;
- reconhecimento continua diferente de autenticação;
- internet continua expansão opcional;
- modelos continuam componentes, não identidade;
- B36 continua com consciência da STAR como `not_established`.

## Validação

A validação final desta manutenção deve exigir:

1. `python tools/repo_hygiene.py`;
2. `python -m compileall -q core gui voice modules database tests main.py config.py diagnostico.py`;
3. `pytest -q tests`;
4. `python diagnostico.py`;
5. revisão do diff contra `main`;
6. confirmação dos checks do GitHub Actions.

Resultados de CI não devem ser marcados como aprovados até os workflows concluírem.
