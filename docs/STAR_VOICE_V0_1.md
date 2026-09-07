# 🎙️ STAR Voice V0.1 — Audio Pipeline + VAD

Status: **experimental / opt-in / pré-V0.2**.

Este marco implementa somente a fundação de escuta contínua do STAR Voice Engine.
Ele **não altera a versão global da STAR**, não declara V5 SENSES concluída e não
substitui o fluxo de voz estável da V1.9.

## Escopo

```text
MICROFONE
    ↓
ContinuousAudioInput
    ↓
Silero VAD ONNX
    ↓
SpeechSegmenter
    ↓
Segment
    ↓
Diagnóstico
```

O V0.1 termina no `Segment`. Não existe transcrição automática nesta etapa.

Explicitamente fora do escopo:

- LocalSpeechToText / faster-whisper integration;
- STAR Core;
- TTS / Chatterbox / Piper / SAPI;
- referência oficial de voz;
- GUI;
- streaming STT/TTS;
- barge-in / full duplex;
- Voice Profile e prosódia.

O `AudioRecorder` push-to-talk continua sendo o caminho estável usado pela GUI.

## Componentes

### `voice/audio_input.py`

`ContinuousAudioInput` acrescenta captura contínua experimental sem remover nem
mudar a API do `AudioRecorder` existente.

Formato canônico V0.1:

- 16 kHz;
- mono;
- `float32`;
- 512 amostras por chunk (~32 ms).

A fila é limitada por `input_queue_seconds`. Com o padrão de 2 s, 16 kHz mono
float32 ocupa aproximadamente 125 KiB de PCM; a implementação aloca um número
inteiro de chunks e descarta o chunk mais antigo se o consumidor atrasar. O callback
do dispositivo não espera processamento de VAD.

### `voice/vad.py`

`SileroVAD` é um wrapper local, numpy-only no código STAR, sobre ONNX Runtime.
O runtime:

- recebe somente caminho de arquivo local;
- não contém URL;
- não baixa modelo;
- não usa `requests`/`urllib`;
- mantém o modelo carregado entre chunks;
- mantém estado recorrente e contexto entre inferências;
- falha explicitamente se o modelo estiver ausente ou incompatível.

### `voice/segmenter.py`

`SpeechSegmenter` transforma probabilidade de fala em eventos/segmentos usando:

- threshold + histerese;
- `min_speech_ms`;
- `min_silence_ms`;
- pre-roll;
- post-roll;
- limite máximo de duração.

A responsabilidade de segmentação fica separada do VAD e da captura. Não conhece
STT, TTS, Core ou GUI.

## Configuração

Fonte única: `config.py > VAD_CONFIG`.

Valores iniciais:

```text
sample_rate             16000 Hz
chunk_samples           512
threshold               0.50
neg_threshold_offset    0.15
min_speech_ms           250 ms
min_silence_ms          500 ms
pre_roll_ms             300 ms
post_roll_ms            300 ms
max_segment_duration_ms 30000 ms
input_queue_seconds     2.0 s
```

São valores iniciais para validação, não resultados de benchmark. Ajustes só devem
ser feitos após medição em hardware real.

Um segmento corrente no limite de 30 s contém cerca de 1,92 MB de PCM float32 a
16 kHz mono. A fila de captura é separada e permanece pequena.

## Silero VAD pinado

Componente: Silero VAD, licença MIT.

```text
versão:  v6.2.1
arquivo: voice/models/vad/silero_vad.onnx
SHA-256: 1a153a22f4509e292a94e67d6f9b85e8deb25b4988682b7e174c65279d8788e3
```

O instalador usa uma URL específica da tag `v6.2.1`. O download é feito para um
arquivo temporário, o SHA-256 é validado e somente então o arquivo é movido para o
caminho final.

`voice/models/` já é ignorado pelo `.gitignore`; o binário ONNX não pertence ao
repositório.

## Dependência nova

```text
onnxruntime>=1.23,<2
```

Não são adicionados PyTorch, torchaudio ou o pacote Python `silero-vad` ao runtime
principal. A linha 1.23+ foi escolhida para manter suporte aos ambientes Python 3.13
usados nos workflows atuais do repositório.

## Instalação

O setup explícito continua sendo:

```bat
INSTALAR_VOZ.bat
```

ou, para preparar apenas os modelos tratados pelo instalador Python:

```bat
.venv\Scripts\python.exe -m voice.install_models
```

Internet pode ser usada nessa etapa de setup. Depois que o modelo está instalado,
`voice/vad.py` opera somente com o arquivo local.

## Diagnóstico experimental

O diagnóstico oficial anterior permanece:

```bat
.venv\Scripts\python.exe -m voice.diagnostics
```

O V0.1 adiciona:

```bat
.venv\Scripts\python.exe -m voice.diagnostics vad
```

ou uma execução limitada, por exemplo:

```bat
.venv\Scripts\python.exe -m voice.diagnostics vad 30
```

Saída esperada durante uma fala:

```text
VAD: ONLINE
STATE: LISTENING
SPEECH START
SPEECH ACTIVE
SPEECH END
segment created
STATE: LISTENING
```

O diagnóstico não salva áudio por padrão e não carrega STT/TTS/Core.

## Testes automatizados

A suíte cobre sem microfone/modelo real:

- erro explícito de modelo ausente;
- ausência de rede/download no runtime VAD;
- contrato ONNX 16 kHz / 512 amostras / contexto / estado;
- reset sem recarregar o modelo;
- pre-roll e post-roll;
- descarte de ruído curto;
- pausa natural sem fragmentação prematura;
- duas utterances separadas;
- validação de entrada;
- fila de captura limitada;
- start/stop determinísticos com dispositivo simulado;
- versão/URL/SHA do instalador;
- ausência de PyTorch/torchaudio no `requirements.txt`.

A CI padrão não baixa `silero_vad.onnx` e não depende da presença do modelo.

## Metas para validação física

Estes valores são **metas**, não medições atuais:

| Métrica | Limite inicial | Meta |
| --- | ---: | ---: |
| onset | ≤ 300 ms | ≤ 200 ms |
| EOS | ≤ 700 ms | ≤ 500 ms |
| falsos positivos em 30 s de silêncio | ≤ 1 | 0 |
| CPU do VAD | ≤ 5% | ≤ 2% |
| RAM adicional do VAD | ≤ 100 MB | ≤ 50 MB |

A medição real deve ser feita no PC da STAR. O ambiente de CI não substitui teste de
microfone, drivers, CPU/RAM e comportamento acústico real.

## Critério de validação local

Antes de considerar V0.1 pronto para merge:

1. instalar o modelo pelo setup explícito;
2. executar `python -m voice.diagnostics vad 30`;
3. testar silêncio, fala curta, frase longa e pausa natural;
4. verificar falsos positivos e cortes de início/fim;
5. repetir start/stop;
6. confirmar CPU/RAM aceitáveis;
7. abrir a GUI estável e validar o push-to-talk existente;
8. rodar `pytest -q tests` e `python diagnostico.py` no ambiente local.

## Próximo passo

Somente após validação e revisão deste marco: **VOICE V0.2 — Streaming STT**.
O V0.1 não antecipa essa integração.
