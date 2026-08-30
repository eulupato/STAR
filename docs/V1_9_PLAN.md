# STAR V1.9 — Arquitetura de voz local

## Decisão arquitetural
A V1.9 abandona serviços externos de voz. O subsistema de voz deve funcionar localmente e ser independente do modo ONLINE/OFFLINE da interface.

## Pipeline definitivo

```text
🎤 Microfone
   ↓
sounddevice / AudioRecorder
   ↓
faster-whisper (STT local, português)
   ↓
📝 texto
   ↓
STAR Core
   ↓
💬 resposta
   ↓
Chatterbox Multilingual (.voice_venv)
   ↓
WAV
   ↓
soundfile + sounddevice (.venv principal)
   ↓
🔊 alto-falante
```

O Chatterbox é um mecanismo de TTS/voice cloning; ele não substitui o reconhecimento de fala. Por isso o STT é separado do TTS.

## Chatterbox
O worker mantém o modelo carregado em processo separado para evitar recarregar o modelo a cada resposta. A instalação oficial é compatível com Python 3.11 e o modelo multilíngue aceita um `audio_prompt_path` para usar uma referência de voz.

## STT
A STAR usa faster-whisper local, com modelo `base` por padrão, `device=cpu` e `compute_type=int8`, adequado ao hardware atual sem exigir GPU NVIDIA.

O tamanho do modelo pode ser alterado pela variável `STAR_STT_MODEL`.

## Reprodução
A reprodução fica somente no processo principal usando `sounddevice` + `soundfile`. O Chatterbox não controla o alto-falante.

## Arquivos principais
- `voice/manager.py` — orquestra STT, TTS e playback.
- `voice/chatterbox_worker.py` — processo persistente do Chatterbox.
- `voice/audio_input.py` — captura do microfone.
- `voice/diagnostics.py` — teste real do pipeline de saída.
- `tests/test_voice_contract.py` — testes leves de contrato.

## Instalação
Execute `INSTALAR_VOZ.bat` uma vez. Ele prepara o `.venv` da STAR e o `.voice_venv` do Chatterbox.

## Diagnóstico
Execute `DIAGNOSTICO_VOZ.bat` para verificar microfone/saída, dependências e executar uma fala real.

## Privacidade
Nenhuma chave de serviço externo é necessária para a voz. Áudios de referência, modelos baixados, banco local e ambientes virtuais ficam fora do versionamento.
