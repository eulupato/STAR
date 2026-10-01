# STAR Watch — Cosmic Crystal Visual System

## Objetivo

Esta camada transforma a identidade visual aprovada do STAR Watch em telas funcionais do simulador no PC sem alterar o Core, voz, memória, providers ou comandos existentes.

Arquitetura:

```text
clients/star_watch_app.py
        ↓
modelo + funções + providers
        ↓
clients/star_watch_visual.py
        ↓
Cosmic Crystal UI
```

O renderer visual herda `StarWatchApp`; portanto ele não cria outra STAR e não duplica a lógica funcional.

## Estados visuais ligados ao runtime

- `idle` → **PRONTA** — orb violeta calmo, filamentos lentos e estrela cristalina.
- `listening` → **OUVINDO** — pulsação e filamentos mais ativos.
- `thinking` → **PENSANDO** — órbitas reorganizadas/aceleradas em violeta e lilás.
- `speaking` → **RESPONDENDO** — pulsos fluidos sincronizados com a resposta.
- `error` → **ATENÇÃO** — vermelho/rosa e distorção breve de alerta.

Esses estados são os mesmos utilizados pelo fluxo real de voz/Core da Watch App. Não são telas decorativas desconectadas.

## STAR Ring no PC

- roda do mouse / setas: girar;
- Enter / clique no núcleo: selecionar;
- clique no anel esquerdo/direito: simular rotação;
- Espaço: iniciar/encerrar voz;
- Backspace: voltar;
- Esc: voltar ou fechar quando estiver na Home.

## Modos preservados

A camada visual reutiliza os modos funcionais existentes:

- Voz;
- Busca;
- Saúde;
- GPS;
- Visão;
- People;
- Medir;
- Mídia;
- Clima;
- Configurações.

Funções dependentes de hardware continuam honestamente marcadas como simuladas/indisponíveis quando não existe sensor real.

## Fluidez

A cena estática é reconstruída apenas quando a tela, modo ou conteúdo muda. A animação normal redesenha somente a camada procedural marcada como `dynamic`, em aproximadamente 30 FPS.

O Cosmic Crystal não depende de GIF, vídeo ou asset externo: orb, filamentos, estrela de 8 pontas, partículas e halos são gerados proceduralmente no Canvas em runtime, reduzindo dependências e facilitando a adaptação para diferentes resoluções de smartwatch.

O valor legado `plasma-orbit` permanece no manifesto/testes como identificador de
compatibilidade da V0.4; ele não descreve mais a paleta/aparência atual.

## Inicialização

```powershell
.\INICIAR_WATCH.bat
```

O launcher abre `clients/star_watch_visual.py`, que reutiliza `clients/star_watch_app.py` como base funcional.
