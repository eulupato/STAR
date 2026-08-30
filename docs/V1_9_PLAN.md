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

Fallbacks:
Chatterbox indisponível → Piper PT-BR → Windows SAPI
```

A voz oficial é preferida quando `.voice_venv` e
`voice/reference/star_reference.mp3` existem na máquina local.
A referência não é distribuída pelo GitHub.

Para priorizar velocidade manualmente:
`STAR_VOICE_MODE=fast`.

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
- voz oficial local com fallback;
- controle inicial do computador;
- CI de sintaxe e smoke tests.

## Fora do escopo da V1.9
Novas arquiteturas de memória, metacognição, Knowledge Graph e cérebro modular
pertencem à V2.0 MIND.

## Regra
Bugs encontrados na fundação após o merge devem ser corrigidos como V1.9.x
sem bloquear a abertura do desenvolvimento V2.0 em branch separada.
