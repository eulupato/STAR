# STAR V1.9 FINAL — Fundação estável

## Objetivo
A V1.9 é a fundação congelada da STAR antes da abertura da geração V2.0 MIND.

## Pipeline de voz definitivo da V1.9

```text
Microfone
  ↓
sounddevice / AudioRecorder
  ↓
faster-whisper tiny (local, PT-BR, CPU INT8)
  ↓
STAR Core
  ↓
Chatterbox Multilingual + referência local da STAR
  ↓
sounddevice
  ↓
alto-falante
```

A voz oficial é preferida quando `.voice_venv` e uma referência autorizada em
`voice/reference/` existem na máquina local. A referência não é distribuída
pelo GitHub.

No modo `official`, uma falha do Chatterbox é visível e não troca a identidade
da STAR silenciosamente. Fallback automático só ocorre quando explicitamente
habilitado. O modo `fast` usa Windows SAPI quando disponível e Piper PT-BR como
fallback local.

Para priorizar velocidade manualmente:
`STAR_VOICE_MODE=fast`.

## Conversão de voz opcional

A V1.9 também pode usar Seed-VC como backend local opcional de transformação de
áudio, sem substituir STT ou TTS e sem entrar no startup da STAR.

```text
Áudio existente
  ↓
STAR voice/seed_vc.py
  ↓
runtime Seed-VC externo/local
  ├── Voice Conversion V1
  ├── Singing Voice Conversion V1
  ├── Voice/Accent/Style Conversion V2
  ├── Anonymization V2
  ├── Real-time VC
  └── Fine-tuning V1/V2
```

O runtime upstream permanece em `voice/external/seed-vc/`, ignorado pelo Git,
com ambiente e dependências próprios. Sua ausência não impede a STAR de iniciar,
ouvir ou falar. Consulte `voice/README_SEED_VC.md`.

## Estabilidade de fala
A V1.9 FINAL cancela fala anterior quando uma nova interação começa.
Isso evita respostas antigas aparecendo depois de uma nova pergunta.

## Componentes congelados
- identidade independente dos modelos;
- roteamento e Executive atuais;
- memória persistente básica;
- matemática natural;
- Knowledge Packs atuais;
- interface 2D atual;
- HUB, ilhas, Casa, Closet e skins;
- STT local;
- voz oficial local;
- modo rápido local;
- conversão de voz opcional e desacoplada;
- controle inicial do computador;
- CI de sintaxe e smoke tests.

## Fora do escopo da V1.9
Novas arquiteturas de memória, metacognição, Knowledge Graph e cérebro modular
pertencem à V2.0 MIND.

## Regra
Bugs encontrados na fundação após o merge devem ser corrigidos como V1.9.x
sem bloquear a abertura do desenvolvimento V2.0 em branch separada.