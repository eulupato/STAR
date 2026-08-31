# STAR V2.0 — MIND FOUNDATION

Data de implementação inicial: 31/08/2026.

## Objetivo

A V2.0 introduz uma camada cognitiva permanente acima da fundação V1.9.
Ela organiza contexto, relevância, planejamento, capacidades e execução sem
transformar o projeto em um arquivo monolítico e sem exigir um modelo externo.

## Pipeline

Entrada → Event Bus → Working Memory → Context → Salience → Planner →
Executive MIND → capacidades existentes → resposta → metacognição operacional.

## Componentes

- Event Bus: eventos locais e observáveis.
- Working Memory: turnos e fatos apenas da sessão.
- Context Engine: continuidade imediata e contexto corrente.
- Salience Engine: prioridade determinística.
- Planner: plano operacional, não cadeia privada de raciocínio.
- Capability Registry: mapa explícito do que a STAR pode usar.
- Executive MIND: executa etapas até obter uma resposta válida.
- Metacognição operacional: telemetria de roteamento, latência e erros.
- Cognitive Loop: coordena todos os componentes.
- Fallback V1.9: mantém a fundação utilizável se a MIND falhar.

## Garantias da fundação

- offline-first;
- IA externa continua opcional e desligada por padrão;
- ações ONLINE continuam bloqueadas quando o modo ONLINE está desligado;
- matemática e ações locais continuam determinísticas;
- nenhuma capacidade de autocorreção irrestrita foi adicionada;
- a MIND não registra cadeia privada de raciocínio;
- a interface e a voz da V1.9 continuam compatíveis.

## Diagnóstico

No chat, a frase "diagnóstico da mente" retorna um resumo operacional da MIND.

O arquivo diagnostico.py também valida imports, Event Bus, Working Memory,
Context Engine, matemática, Knowledge Packs e voz sem carregar o Chatterbox
pesado.

## Próximos passos planejados

V2.1: Memory Architecture.
V2.2: Knowledge Graph base.
V2.3: Model Router e seleção automática de motores.
