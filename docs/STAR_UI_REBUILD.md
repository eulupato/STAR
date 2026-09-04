# STAR UI — reconstrução local do protótipo visual

Esta implementação reconstrói localmente a interface 2D observada no protótipo
visual da STAR, sem depender do Base44 para executar o projeto.

## Fluxo principal

```text
MENU
  ├─ INICIAR -> HUB / STAR WORLD
  ├─ CONFIGURAÇÕES -> Settings
  └─ SAIR -> encerra a aplicação

HUB
  ├─ ilhas
  └─ CHAT

CHAT
  ├─ configurações
  └─ botão de ilha -> HUB
```

## Estrutura espacial oficial

- **Casa**
  - Cozinha
  - Quarto
    - Closet
- **Laboratório**
  - Central de Criação (anexa, não é ilha independente)
- **Jardim**
  - caminho para Observatório (não é ilha independente)
- Biblioteca
- Estúdio de Música
- Correio
- Cura
- Heróis
- Ateliê
- Idiomas

## Regras visuais

- fundo espacial azul-marinho/quase preto;
- tipografia pixelada nos títulos;
- painéis escuros com bordas discretas;
- azul para ações/estado ativo;
- rosa para identidade e destaques;
- amarelo para capacidades em desenvolvimento;
- STAR permanece a protagonista visual;
- o menu usa reações: Iniciar=feliz, Configurações=pensativa, Sair=triste;
- os olhos acompanham o cursor de forma sutil;
- recursos incompletos aparecem como **EM DESENVOLVIMENTO**, nunca como prontos.

## Assets da reconstrução

Foram adicionados apenas recursos necessários em runtime, para manter o projeto leve:

- `assets/reference/star_menu_face.jpg` — referência principal do rosto no menu;
- `assets/reference/kitchen_reference.jpg` — versão otimizada da referência visual da cozinha;
- `assets/avatar/happy.png`, `thinking.png` e `sad.png` — estados visuais usados nas reações do menu.

As demais imagens de estudo (turnaround, folha completa de expressões e screenshots)
continuam sendo referências de design e não foram duplicadas no repositório sem necessidade.

## Integração preservada

A GUI continua chamando o mesmo Core Python atual. Foram preservados:

- `brain.process(...)`;
- memória SQLite existente;
- STT local;
- TTS local;
- cancelamento de fala;
- Knowledge Packs;
- modos LOCAL/LAN/ONLINE;
- Closet e skins existentes.

A reconstrução troca a experiência visual sem criar uma segunda STAR, sem frontend
paralelo e sem duplicar o Core cognitivo.

## Limites desta etapa

Esta branch reconstrói a interface 2D atual e os ambientes já definidos para a fase
presente. Ela **não antecipa** o STAR WORLD 3D reservado no roadmap. Ambientes ainda
não implementados funcionalmente permanecem como pontos de entrada e modais de estado.
