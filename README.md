# ⭐ STAR — V1.5 Offline Core

Base consolidada do projeto STAR. Esta versão parte da V.0 funcional, preserva o
conhecimento fundamental da identidade e incorpora o Hub/STAR WORLD, memória,
avatar, normalização de linguagem e a camada preparada para voz.

## Execução

- Se já existe `.venv`: `INICIAR_STAR.bat`
- Sem ambiente criado: execute `CRIAR_AMBIENTE.bat` uma vez e depois `INICIAR_STAR.bat`.
- Terminal: `python main.py`

## Estado

- IA externa/Ollama/Qwen: **desativados no fluxo ativo**.
- Conhecimento próprio: **ativo**.
- Memória persistente SQLite: **ativa**.
- GUI: menu visual, chat, configurações, avatar e HUB.
- Voz: interface preparada, backend definitivo ainda não conectado.
- Knowledge Packs/pendrives: arquitetura preparada; instalação automática ainda não ativa.
- Cura: diagnóstico e validação controlados; nenhuma autoalteração irrestrita do código.

## Arquitetura de conhecimento

`PDF → OCR/parsing → texto estruturado → revisão → Knowledge Pack → ilha → STAR`

As ilhas podem existir no mapa antes de receberem um pacote. O conteúdo é uma
camada separada da representação do STAR WORLD.

## Pacote distribuído

A versão distribuída inclui um `.venv` de referência para Windows/Python 3.13,
preservado da base V.0, além dos arquivos-fonte. Se o ambiente embutido não for
compatível com sua instalação local, `CRIAR_AMBIENTE.bat` recria um ambiente
novo usando `requirements.txt`.
