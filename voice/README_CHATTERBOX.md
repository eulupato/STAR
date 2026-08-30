# STAR Voice Engine — Voz Local

A arquitetura de voz da STAR V1.9 é totalmente local e separada do Core.

- Entrada: `sounddevice` grava o microfone.
- STT: `faster-whisper` local, com idioma fixado em português (`pt`).
- TTS: `Chatterbox Multilingual` em `.voice_venv` com o áudio de referência da STAR.
- Reprodução: `sounddevice` + `soundfile` no `.venv` principal.
- Não existe dependência de ElevenLabs ou outro serviço externo de voz.

## Instalação

1. Execute `CRIAR_AMBIENTE.bat` se a `.venv` ainda não existir.
2. Execute `INSTALAR_VOZ.bat` uma vez. O Chatterbox usa Python 3.11 em `.voice_venv`; a documentação oficial do projeto recomenda Python 3.11. citeturn537072search1
3. Mantenha `voice/reference/star_reference.mp3` no projeto.
4. Execute `TESTAR_VOZ_LOCAL.bat` para testar a geração e reprodução.

## Primeiro uso

O `faster-whisper` baixa o modelo configurado na primeira transcrição. O modelo padrão da STAR é `base`, executando em CPU com `int8`, adequado para uma máquina sem CUDA. O pacote atual declara Python >=3.9. citeturn567520search0

O Chatterbox Multilingual aceita um `audio_prompt_path` para usar uma referência de voz e suporta português (`pt`). A API atual usa `from_pretrained(device=...)` e `generate(..., language_id="pt", audio_prompt_path=...)`; não usamos o argumento legado `t3_model` na versão instalada da STAR. citeturn537072search1turn537072search5

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
Chatterbox
   ↓
WAV
   ↓
sounddevice
   ↓
Alto-falante
```

A reprodução é feita no processo principal da STAR; o ambiente do Chatterbox apenas gera o WAV. O objetivo é evitar conflitos entre ambientes Python e bibliotecas de áudio.
