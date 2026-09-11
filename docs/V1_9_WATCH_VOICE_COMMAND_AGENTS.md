# STAR V1.9 — Watch Voice + Command/Agent Foundation

## Escopo

Esta atualização corrige o caminho de áudio do STAR Watch e adiciona uma fundação central de comandos/agentes sem antecipar o Goal Engine da V8.

Princípios preservados:
- uma STAR, um Core;
- Watch continua sendo sensor/interface;
- agentes são capacidades especializadas, não cérebros/personas independentes;
- internet continua opcional;
- ações sensíveis não são executadas remotamente sem Permission Manager;
- capacidades futuras permanecem marcadas como `planned`/`partial`.

## Correção de voz do Watch

Antes:

`MIC -> MediaRecorder -> AAC/M4A 44.1 kHz -> LAN -> faster-whisper`

Problemas do caminho antigo:
- compressão com perdas antes do STT;
- fonte de áudio genérica `MIC`;
- sample rate orientado a mídia, não fala;
- pouco controle sobre o sinal entregue ao Core.

Agora:

`VOICE_RECOGNITION -> AudioRecord -> PCM 16-bit mono -> WAV -> LAN -> STT local`

O Watch tenta, nesta ordem:
1. fonte Android `VOICE_RECOGNITION`;
2. fallback `MIC`;
3. 16 kHz;
4. 22,05 kHz;
5. 44,1 kHz.

O arquivo só é aceito quando há amostra de áudio suficiente. O app anuncia `pcm16_wav` e `voice_commands` no pareamento e envia `audio/wav` ao Gateway existente.

## Comandos de voz

`core/commands.py` virou a fonte central de intents de comandos.

O catálogo não contém milhares de `if/elif`. Ele combina templates, aliases e slots e gera mais de 1.000 frases únicas de teste/uso. A suíte exige `command_count() >= 1000`.

Categorias implementadas na Foundation:
- abrir aplicativos conhecidos;
- reconhecer pedidos de fechamento sem executá-los sem confirmação;
- volume +/−/mudo;
- play/pause, próxima e faixa anterior;
- screenshots;
- hora e data;
- busca nominal de arquivos;
- pesquisa web quando ONLINE;
- busca no Spotify quando ONLINE;
- consulta de status de agentes;
- consulta da quantidade de comandos.

Exemplos:
- `STAR, abra o Spotify`
- `Ei STAR, aumente o volume`
- `STAR, diminua o volume`
- `STAR, mute o som`
- `STAR, próxima música`
- `STAR, tire um print`
- `STAR, que horas são?`
- `STAR, qual a data de hoje?`
- `STAR, encontre o arquivo roadmap`
- `STAR, pesquise física quântica`
- `STAR, procure no Spotify lofi`
- `STAR, quais agentes você tem?`
- `STAR, quantos comandos de voz você tem?`

## Segurança de comandos remotos

O `DeviceGateway` continua chamando `StarCore.process(..., allow_actions=False)`.

A semântica agora é:
- `allow_actions=True`: interface local;
- `allow_actions=False`: endpoint remoto, somente comandos `remote_safe`.

O Core ainda conversa normalmente com o Watch, mas ações sensíveis como fechar aplicativos ou bloquear o PC são reconhecidas e recusadas com uma mensagem de confirmação local pendente.

## Agentes/capacidades registrados

1. `voice_command` — available — interpretação de comandos.
2. `computer` — partial — ações simples; V4 completa Operator.
3. `file` — partial — busca nominal; V4 traz índice/semântica.
4. `research` — partial — pesquisa web autorizada; pesquisa avançada é futura.
5. `knowledge` — partial — conhecimento interno + packs atuais.
6. `memory` — partial — memória básica; V2 traz arquitetura cognitiva de memória.
7. `project` — planned — projetos persistentes/Goal workflow.
8. `music` — partial — Spotify/controles multimídia.
9. `vision` — planned — V5 Senses.
10. `device` — partial — Device Gateway experimental atual.
11. `cure` — partial — diagnóstico básico; V7 Guardian amplia.
12. `security` — planned — Permission Manager/Trust na V7.
13. `personal_assistant` — partial — hora/data; scheduler fica para V8.
14. `web` — partial — navegador/pesquisa mínima.
15. `coding` — partial — ferramentas de desenvolvimento, sem autonomia de edição.
16. `home` — planned — V9 Ecosystem.
17. `body` — planned — V10 Embodied.
18. `creation` — planned — STAR World/expansões criativas.
19. `orchestrator` — planned — V8 Agent, múltiplos objetivos/agentes.

## O que esta atualização NÃO afirma

- Vision Agent não está pronto.
- Home Agent não controla uma casa.
- Body Agent não controla um robô.
- Orchestrator não possui autonomia longa.
- Project Agent ainda não é um sistema persistente de projetos.
- Security Agent ainda não substitui Permission Manager.

Esses nomes já existem no registro para a STAR saber sua Capability Tree e responder honestamente sobre o estágio de cada um.

## Testes

`tests/test_voice_commands.py` valida:
- catálogo único com pelo menos 1.000 comandos;
- normalização de acentos/wake word;
- extração de slots;
- bloqueio de ações remotas sensíveis;
- catálogo com 19 agentes e estados honestos;
- resposta sobre quantidade de comandos.

O workflow `STAR Watch Android` continua responsável por compilar o APK em pull requests que alteram o cliente Watch.
