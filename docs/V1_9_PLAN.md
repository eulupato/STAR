# STAR V1.9 — Plano técnico

## Entregue nesta branch
- Motor matemático natural: mais, menos, vezes, dividido, raiz quadrada, metade, dobro e triplo.
- Controle local inicial: Google/Chrome, Spotify, pesquisa web e busca de arquivos.
- Integração dessas ações diretamente no núcleo.

## Voz
A arquitetura atual já possui Chatterbox e ponte Python principal -> .voice_venv.
O fluxo deve permanecer local e a GUI não deve depender do modo ONLINE para a saída Chatterbox.
Reconhecimento de fala é separado do TTS.

## Próximas etapas
- Adaptar STT local/offline.
- Mensagens e chamadas apenas através de integrações autorizadas e configuradas.
- Melhorar contexto de palavras ambíguas antes de responder.
- Conhecimento inicial da ilha Heróis em packs.
- Remover backups/arquivos legados após confirmação de que não são usados.
