# STAR — Grupo 4: Guardian, segurança, casa e integrações pessoais

## Princípio

O Grupo 4 adiciona execução controlada sem criar outro cérebro, outro sistema de
permissões ou outro banco. B01/B33 continuam sendo a autoridade operacional e
`star.db` continua sendo a fonte persistente compartilhada.

## CURA controlada

`core/cure.py` agora:
- analisa logs, tracebacks, testes falhos e arquivos prováveis;
- cria casos auditáveis no `star.db`;
- valida patches em um Git worktree descartável;
- faz checagem sintática antes de testes;
- só executa testes de patches quando um sandbox de SO está disponível;
- nunca modifica a árvore real durante validação;
- aplicação real exige patch previamente validado, autorização explícita,
  permissão de mutação, segurança e B01/B33;
- nunca cria commit/push automaticamente.

## Sandbox real

`core/os_sandbox.py` detecta backends já instalados:
- Docker;
- Podman;
- bubblewrap.

Docker/Podman usam filesystem read-only, rede desligada por padrão, limite de
RAM/CPU/PIDs, cap-drop ALL, no-new-privileges e tmpfs temporário. A STAR não
instala runtime, não baixa imagem e não habilita rede silenciosamente.

Sem backend/imagem local pronta, `run_sandboxed()` falha fechado. O runner
restrito legado do CodeLab permanece para compatibilidade e scripts confiáveis,
mas não é reclassificado como sandbox de SO.

## Security Agent

`core/security_agent.py` é um auditor read-only:
- procura formatos comuns de segredos versionados;
- produz snapshot SHA-256 de arquivos críticos;
- audita configuração de superfícies sensíveis;
- usa `pip-audit` somente quando já está instalado;
- grava relatórios no `star.db`;
- não corrige arquivos, não revoga credenciais e não concede permissões.

## Home Automation

`core/home_automation.py` usa Home Assistant REST quando
`STAR_HOME_ASSISTANT_URL` e `STAR_HOME_ASSISTANT_TOKEN` estão configurados.

A versão atual permite apenas:
- `light`;
- `switch`;
- `fan`;
- serviços `turn_on` e `turn_off`.

Locks, alarmes e dispositivos de segurança permanecem fora da allowlist.

Toda mutação é:
pedido -> código temporário -> confirmação local -> B01/B33 -> provider -> audit.

Credenciais ficam somente no ambiente e nunca no banco.

## Integrações pessoais

`core/personal_integrations.py` possui adapters opcionais:
- IMAP para cabeçalhos de e-mails recentes;
- SMTP para envio;
- Telegram Bot API para mensagens;
- CalDAV para sincronizar itens da agenda existente.

Variáveis de ambiente:
- `STAR_EMAIL_IMAP_HOST`, `STAR_EMAIL_IMAP_PORT`;
- `STAR_EMAIL_SMTP_HOST`, `STAR_EMAIL_SMTP_PORT`,
  `STAR_EMAIL_SMTP_SECURITY`;
- `STAR_EMAIL_USER`, `STAR_EMAIL_PASSWORD`, `STAR_EMAIL_FROM`;
- `STAR_TELEGRAM_BOT_TOKEN`, `STAR_TELEGRAM_CHAT_ID`;
- `STAR_CALDAV_URL`, `STAR_CALDAV_USER`, `STAR_CALDAV_PASSWORD`.

E-mail/mensagem/sincronização externa sempre nascem como draft no `star.db`.
O envio requer um código de confirmação local com validade curta. Nenhuma
credencial é persistida.

O calendário local continua sendo o `AgendaManager` criado no Grupo 2; CalDAV
é apenas uma expansão externa, não um segundo calendário.

## Limites explícitos

- Security Agent não é antivírus/EDR.
- Home Assistant precisa existir e estar configurado para controlar dispositivos.
- E-mail/Telegram/CalDAV precisam de contas/credenciais fornecidas localmente.
- Docker/Podman/bubblewrap precisam estar instalados previamente para sandbox real.
- CURA não edita/commita/pusha o repositório automaticamente.
- Origem remota não pode confirmar mutações do Grupo 4.
