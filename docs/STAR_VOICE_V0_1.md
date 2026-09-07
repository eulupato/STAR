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

A partir da validação física inicial, o diagnóstico também mostra aproximadamente
a cada segundo:

```text
INPUT · rms=-31.4 dBFS · peak=-12.8 dBFS · vad_max=0.917
```

No resumo são mostrados:

- dispositivo de entrada efetivamente usado;
- quantidade de chunks recebidos;
- maior probabilidade VAD;
- RMS global e pico de entrada em dBFS;
- amostras próximas de clipping;
- segmentos produzidos;
- chunks descartados;
- CPU aproximada.

Isso permite separar falha de microfone/driver de falha do VAD/segmentador antes de
alterar thresholds.

Para listar todas as entradas de áudio e descobrir o índice real do microfone:

```bat
.venv\Scripts\python.exe -m voice.diagnostics devices
```

Para testar explicitamente um dispositivo, por exemplo o índice 3:

```bat
.venv\Scripts\python.exe -m voice.diagnostics vad 30 3
```

Se o teste produzir `Segmentos: 0`, não se deve baixar o threshold automaticamente.
Primeiro compare `rms`, `peak` e `vad_max`:

- pico abaixo de aproximadamente `-55 dBFS` → entrada praticamente silenciosa;
- sinal de áudio presente, mas `vad_max < threshold` → investigar microfone/nível e comportamento acústico;
- `vad_max >= threshold` sem segmento → investigar `SpeechSegmenter`.

Saída esperada durante uma fala detectada:

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

## Validação física — 07/09/2026

### Rodada 1 — diagnóstico inicial

No PC real da STAR foram confirmados:

- `onnxruntime 1.29.0` instalado no ambiente principal;
- Silero VAD v6.2.1 baixado e validado localmente;
- referência oficial Chatterbox localizada em `voice/reference/`;
- suíte local completa: **41 testes passaram**;
- `diagnostico.py`: **sem falhas críticas**;
- VAD carregado em aproximadamente **670 ms**;
- execução contínua por aproximadamente **30 s**;
- **0 chunks descartados**;
- CPU aproximada observada: **3,8%**;
- fila configurada: aproximadamente **126 KiB**;
- resultado inicial: **0 segmentos detectados**.

Esse primeiro diagnóstico não registrava RMS/pico/probabilidade máxima, então não foi
feito ajuste arbitrário de threshold. A telemetria foi adicionada antes de alterar o
comportamento do VAD.

### Rodada 2 — telemetria + dispositivo explícito

O diagnóstico de dispositivos confirmou como entrada padrão:

```text
[1] Microfone (USB Audio Device)
```

Com `python -m voice.diagnostics vad 30 1`, o pipeline físico produziu:

- **926 chunks processados**;
- **4 segmentos válidos**;
- `vad_max = 1.000`;
- RMS global de aproximadamente **-44,7 dBFS**;
- pico de entrada de aproximadamente **-16,6 dBFS**;
- **0 amostras próximas de clipping**;
- **0 chunks descartados**;
- CPU aproximada de **4,0%**;
- silêncio observado próximo de **-96 dBFS**;
- fala detectada com probabilidades próximas de `1.000`.

O `threshold = 0.50` foi mantido. Os dados não justificam reduzir o threshold.

Também foi observado um `SEGMENT DROPPED` curto por duração abaixo de
`min_speech_ms = 250`, comportamento esperado para rejeitar ruído/evento muito curto.

### Rodada 3 — start/stop repetido

Foram executadas três sessões independentes de 10 s no mesmo microfone, todas
encerrando normalmente e produzindo fala detectável:

| Execução | Chunks | Segmentos | VAD máx. | Pico | CPU | Drops |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 302 | 1 | 1.000 | -22,7 dBFS | 4,9% | 0 |
| 2 | 304 | 2 | 1.000 | -18,0 dBFS | 5,4% | 0 |
| 3 | 304 | 1 | 1.000 | -20,1 dBFS | 4,2% | 0 |

A média aproximada de CPU das três execuções curtas foi **4,8%**. Uma execução de
10 s mediu **5,4%**, ligeiramente acima do limite inicial de 5%; por ser uma amostra
curta e sem perda de áudio, isso fica registrado para otimização futura, sem alterar
a arquitetura funcional do V0.1 agora.

A repetição confirma que o caminho experimental pode abrir, processar, encerrar e
reiniciar a captura sem fila presa, overflow ou falha observada no dispositivo.

### Inicialização da STAR após os testes

`main.py` iniciou normalmente após as três execuções e processou duas rotas locais.
Esse log confirma que a aplicação continua inicializando na branch de Voice V0.1.
O log fornecido, porém, **não identifica de forma inequívoca se essas duas interações
vieram do botão push-to-talk ou de entrada digitada**. Portanto a regressão específica
do push-to-talk permanece como validação manual explícita antes do merge.

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
- ausência de PyTorch/torchaudio no `requirements.txt`;
- presença da telemetria de microfone no diagnóstico;
- conversão dBFS finita inclusive para silêncio digital.

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

## Estado da validação local

Confirmado:

1. modelo instalado por setup explícito;
2. captura contínua física funcional;
3. Silero VAD físico funcional;
4. segmentação física funcional;
5. silêncio e fala distinguíveis;
6. pre-roll/post-roll/hangover operando no fluxo real;
7. start/stop repetido sem falha observada;
8. `0` chunks descartados nos testes físicos;
9. ausência de clipping nos testes fornecidos;
10. suíte local com **41 passed** e `diagnostico.py` sem falhas críticas;
11. aplicação inicia normalmente após os testes.

Ainda pendente antes do merge:

- confirmar manualmente o fluxo **push-to-talk antigo da GUI**;
- RAM nativa adicional do ONNX continua sem medição direta;
- onset/EOS não foram medidos com cronômetro de referência;
- CPU ainda pode ser otimizada futuramente; uma amostra curta chegou a 5,4%.

## Próximo passo

Depois da confirmação explícita do push-to-talk antigo e revisão final do PR:
**VOICE V0.2 — Streaming STT**.

O V0.1 não antecipa essa integração.
