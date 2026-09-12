# STAR Watch — Plasma Orbit Visual System

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
Plasma Orbit UI
```

O renderer visual herda `StarWatchApp`; portanto ele não cria outra STAR e não duplica a lógica funcional.

## Estados visuais ligados ao runtime

- `idle` → **PRONTA** — triângulo invertido, plasma calmo, órbitas lentas.
- `listening` → **OUVINDO** — triângulo invertido, ondas laterais, órbitas mais ativas.
- `thinking` → **PENSANDO** — estrela, plasma rosa/violeta, órbitas aceleradas.
- `speaking` → **RESPONDENDO** — estrela, plasma rosa/ciano, movimento fluido.
- `error` → **ATENÇÃO** — vermelho/rosa, arco de alerta e movimento mais intenso.

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

O Plasma Orbit não depende de GIF, vídeo ou asset externo: o núcleo, órbitas, partículas e halos são gerados pelo Canvas em runtime, reduzindo dependências e facilitando a futura adaptação para diferentes resoluções de smartwatch.

## Inicialização

```powershell
.\INICIAR_STAR_WATCH_APP.bat
```

O launcher abre `clients/star_watch_visual.py`, que reutiliza `clients/star_watch_app.py` como base funcional.
