# ⭐ STAR — V2.0 MIND

S.T.A.R. — **System for Thought, Analysis and Response**.

A STAR V2.0 introduz a **MIND**, uma arquitetura cognitiva local acima da
fundação estável V1.9. A identidade da STAR permanece separada dos modelos que
ela utiliza, e a operação continua offline-first.

> A branch `main` permanece como fundação V1.9 estável enquanto a V2.0 é
> validada em `v2.0-development`.

## MIND V2

Pipeline principal:

`Entrada → Event Bus → Working Memory → Context → Salience → Planner → Executive MIND → capacidades → resposta`

Componentes ativos:

- Event Bus local;
- Working Memory de sessão;
- Context Engine;
- Salience Engine;
- Planner operacional;
- Capability Registry;
- Executive MIND;
- metacognição operacional;
- fallback seguro para a fundação V1.9.

A MIND não depende de LLM para existir e não registra cadeia privada de
raciocínio. Modelos externos continuam opcionais.

## Compatibilidade V1.9

A V2 preserva identidade, conhecimento interno, Router/Executive existentes,
matemática offline, comandos locais, guarda ONLINE/OFFLINE, memória persistente,
Knowledge Packs, interface 2D, HUB/ilhas/Casa/Closet, STT local e o sistema de
voz da V1.9.

Se a MIND falhar, o StarCore mantém um caminho de compatibilidade com a fundação
V1.9 em vez de derrubar a aplicação.

## Execução no Windows

Use:

`INICIAR_STAR.bat`

ou:

`\.venv\Scripts\python.exe main.py`

Diagnóstico geral:

`\.venv\Scripts\python.exe diagnostico.py`

Diagnóstico da voz:

`DIAGNOSTICO_VOZ.bat`

No chat, use **diagnóstico da mente** para ver telemetria operacional resumida.

## Estrutura principal

- `core/mind/` — MIND V2
- `core/` — fundação, identidade, roteamento e conhecimento
- `database/` — persistência
- `gui/` — interface atual / STAR WORLD
- `knowledge/` — Knowledge Packs
- `modules/` — ferramentas e automações
- `voice/` — STT/TTS local
- `tests/` — regressão e testes MIND
- `docs/` — roadmap e documentação

## Estado

**STAR V2.0 MIND FOUNDATION / development**

A fundação cognitiva está implementada. As expansões V2.1, V2.2 e V2.3
continuam separadas para evitar transformar a V2 em um bloco monolítico.

Veja `docs/V2_0_MIND.md` e `docs/MASTER_ROADMAP.md`.
