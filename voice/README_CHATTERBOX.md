# STAR Voice Engine — Voz Local

A arquitetura de voz da STAR V3 é local e separada do Core cognitivo.

- Entrada: `sounddevice` grava o microfone.
- STT: `faster-whisper` local, com idioma configurado como português (`pt`).
- TTS oficial: Chatterbox Multilingual em `.voice_venv`, usando uma referência local autorizada da STAR.
- TTS rápido: Windows SAPI quando disponível; Piper PT-BR como fallback.
- Reprodução: `sounddevice` + `soundfile`.
- Nenhum serviço externo de voz é necessário.

## Instalação

1. Execute `CRIAR_AMBIENTE.bat` se a `.venv` ainda não existir.
2. Execute `INSTALAR_VOZ.bat` para instalar STT/TTS local.
3. Mantenha a referência de voz em `voice/reference/` ou defina `STAR_VOICE_REFERENCE`.
4. Execute `TESTAR_VOZ_LOCAL.bat` para testar geração e reprodução.

O Chatterbox usa um ambiente separado para reduzir conflitos entre dependências
pesadas de voz e a interface principal.

## Reconhecimento de fala

O modelo configurado atualmente é `tiny`, conforme `config.py`:

```text
STT_ENGINE = faster-whisper
STT_MODEL  = tiny
```

O modelo é carregado somente quando necessário. A interface pode iniciar mesmo
quando STT/TTS não estiverem completamente instalados.

## Modos de voz

### official

Usa a voz oficial Chatterbox com referência local. Por padrão, uma falha da voz
oficial é exibida e não troca silenciosamente para uma voz genérica.

### fast

Prioriza Windows SAPI quando disponível. Piper PT-BR é usado como fallback
local do modo rápido.

## Fluxo

```text
Microfone
   ↓
sounddevice
   ↓
WAV temporário
   ↓
faster-whisper (pt)
   ↓
Texto
   ↓
STAR Core
   ↓
Resposta
   ↓
Chatterbox / SAPI / Piper
   ↓
Áudio local
   ↓
Alto-falante
```

O arquivo de referência de voz, modelos baixados e saídas temporárias permanecem
fora do Git por padrão.
