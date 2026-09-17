# STAR — Grupo 4: CURA, Sandbox, Segurança, Casa e Integrações

## Princípio central

O Grupo 4 amplia capacidades operacionais sem criar uma segunda autoridade. B01/B33 continuam sendo a única fronteira de execução. Pensar, diagnosticar, reconhecer um dispositivo ou possuir credenciais não concede permissão.

## 31. CURA controlada

`core/cure.py` agora classifica categorias de falha, reúne evidências, registra causa provável/confiança e pode validar candidatos no sandbox. A CURA continua proibida de aplicar alterações automaticamente ao repositório.

Fluxo: problema/logs → classe de falha → causa provável → proposta mínima → candidato → sandbox/testes → validação → processo externo autorizado.

## 32. Sandbox real

`ContainerSandbox` usa Docker ou Podman apenas quando o runtime e a imagem já existem localmente. Não há download automático nem fallback silencioso ao host.

Controles: rede desativada, root filesystem read-only, cap-drop ALL, no-new-privileges, limite de memória/CPU/PIDs, timeout e workspace read-only.

O CodeLab antigo continua existindo para pequenos testes confiáveis, mas não é tratado como fronteira de segurança. `run_sandboxed()` é a rota para código não confiável.

## 33. Security Agent

Security Agent é defensivo/read-only:
- varredura bounded de arquivos textuais por padrões de segredo;
- `pip-audit` quando instalado;
- audit log no `star.db`;
- nenhuma remediação automática;
- status do sandbox.

## 34. Home Automation

Provider inicial: Home Assistant por REST API.

Configuração opt-in:
- `STAR_HOME_ASSISTANT_URL`
- `STAR_HOME_ASSISTANT_TOKEN`

Leituras dependem de rede habilitada. Escritas exigem confirmação local e passam por B33. Domínios sensíveis (locks, alarmes, covers e câmeras) também exigem autenticação; sem autenticador contextual a ação permanece bloqueada.

## 35. Integrações pessoais

As credenciais são lidas do ambiente e não são persistidas pela STAR.

E-mail:
- IMAP para leitura;
- SMTP para envio confirmado.

Calendário:
- agenda local já existente;
- CalDAV opcional para gravação confirmada.

Mensagens:
- webhook opt-in para envio confirmado.

Variáveis relevantes:
- `STAR_EMAIL_IMAP_HOST`, `STAR_EMAIL_IMAP_PORT`
- `STAR_EMAIL_SMTP_HOST`, `STAR_EMAIL_SMTP_PORT`
- `STAR_EMAIL_USERNAME`, `STAR_EMAIL_PASSWORD`, `STAR_EMAIL_FROM`
- `STAR_CALDAV_URL`, `STAR_CALDAV_USERNAME`, `STAR_CALDAV_PASSWORD`
- `STAR_MESSAGE_WEBHOOK_URL`, `STAR_MESSAGE_WEBHOOK_TOKEN`

## Limites honestos

- Sem Docker/Podman + imagem local, sandbox real = indisponível.
- Sem Home Assistant configurado, automação residencial = provider indisponível.
- Sem credenciais de e-mail/CalDAV/webhook, essas integrações = indisponíveis.
- A STAR não baixa imagem de container automaticamente.
- Security Agent não corrige achados sozinho.
- CURA não edita a main sozinha.
- Credencial não equivale a permissão operacional.
