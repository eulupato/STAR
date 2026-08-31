# Referência de voz da STAR

A referência oficial é **local, privada e não versionada**.

A V1.9 resolve a referência na seguinte ordem:

1. caminho definido por `STAR_VOICE_REFERENCE`, quando existir;
2. caminho padrão definido em `config.py`;
3. qualquer arquivo de áudio compatível dentro de `voice/reference/`.

Formatos reconhecidos pelo gerenciador:

- MP3
- WAV
- FLAC
- OGG
- M4A
- AAC

Isso significa que um arquivo local como `audiostar35s.mp3` pode ser usado sem
precisar ser renomeado para um nome fixo.

O áudio não é distribuído pelo repositório público e deve permanecer somente na
máquina local.

## Importante

Use apenas uma gravação própria ou uma voz para a qual exista autorização de uso.
No modo `official`, a STAR não troca silenciosamente a voz oficial por uma voz
genérica se o Chatterbox falhar.
