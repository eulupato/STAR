# ⭐ STAR WORLD 2D — Expansão funcional da V1.9

## Objetivo

Transformar a interface 2D da Foundation em uma experiência STAR OS coerente e
navegável, reaproveitando o Core Python atual e sem criar uma STAR paralela.

## Princípios

- `main.py` continua inicializando o mesmo `StarCore`;
- a GUI não substitui MIND, memória cognitiva, Knowledge Packs, voz ou Device Gateway;
- estado visual dos ambientes fica em `runtime/star_world_state.json`;
- `core/islands.py` é a fonte única de verdade da topologia do STAR WORLD;
- ambientes visuais podem existir antes de motores futuros, mas o estado precisa
  permanecer honesto (`DISPONÍVEL`, `EXPERIMENTAL`, `EM DESENVOLVIMENTO`, etc.);
- hover e animações atualizam somente componentes locais; não há rebuild completo
  da tela durante movimento do mouse.

## Topologia

```text
STAR WORLD
├── Casa
│   ├── Sala / STAR TV
│   ├── Cozinha
│   └── Quarto
│       └── Closet
├── Laboratório
│   └── Central de Criação
├── Biblioteca
├── Estúdio de Música
├── Ateliê
├── Jardim
│   ├── Jardim / Plantação
│   ├── Natureza
│   ├── Mar
│   └── Observatório
├── Correios
├── Cura
├── Heróis
└── Idiomas
```

## Funções implementadas na camada 2D

### Menu
- arte canônica da STAR;
- botões reais INICIAR / CONFIGURAÇÕES / SAIR;
- olhos acompanham o cursor por atualização localizada;
- piscada leve;
- reações `happy`, `thinking`, `sad` antes da ação;
- saída com tela de despedida.

### Hub
- dez ilhas;
- status lido do registro central;
- hover sem reconstrução completa;
- Chat global.

### Casa
- Sala: STAR TV abre URLs oficiais do YouTube no navegador e guarda favoritos;
- Cozinha: receitas locais + ingredientes + modo passo a passo;
- Quarto: ambiente pessoal;
- Closet: seleção persistente de skins existentes em `SKINS/`.

### Jardim
- Plantação: catálogo inicial e ciclo educacional plantar/regar/colher;
- Natureza: fauna, flora e representações de locais reais claramente rotuladas;
- Mar: espécies por zonas de profundidade;
- Observatório: catálogo inicial com classificação REAL/FICTÍCIO/HIPOTÉTICO/etc.;
- OSHA aparece no contexto do Jardim, sem virar uma ilha separada.

### Laboratório + Central de Criação
- usam a mesma lista persistente de projetos;
- Laboratório registra objetivo, hipótese e observações;
- Central registra planejamento/versão do mesmo projeto;
- o workspace é educacional e não fornece protocolos perigosos.

### Biblioteca
- importa referência local a PDFs sem copiar o arquivo para o Git;
- abre PDF pelo aplicativo padrão do sistema;
- progresso manual persistente;
- mostra estatísticas reais dos Knowledge Packs;
- leitura TTS/extração automática de PDF permanece fora da Foundation e não é
  apresentada como concluída.

### Estúdio
- projetos musicais;
- título, BPM, tonalidade, letra/notas;
- persistência local;
- não finge ser uma DAW profissional.

### Ateliê
- canvas pixel-art 16×16;
- paleta STAR;
- desenho persistente local.

### Cura
- mostra apenas diagnósticos que a aplicação consegue realmente verificar;
- preserva o contrato:
  diagnóstico → identificação → proposta → validação → aplicação autorizada → teste;
- não possui autorreparo irrestrito.

### Correios
- encomendas;
- abrir pacote;
- inventário;
- pista narrativa da OSHA.

### Heróis
- não inventa catálogo;
- exibe `AGUARDANDO KNOWLEDGE PACK` quando a base estruturada não está instalada.

### Idiomas
- cartões locais de estudo iniciais;
- tutoring avançado continua marcado como evolução futura.

## Assets canônicos

A interface procura:

```text
assets/reference/
├── menu_face.webp
├── kitchen.webp
├── laboratory.webp
├── library.webp
├── observatory.webp
├── cura.webp
└── star_turnaround.webp
```

Expressões ficam em `assets/avatar/`.

Os assets são referências visuais; lógica, status e capacidades continuam vindo
do projeto, não da imagem.

## Limites honestos da V1.9

Esta expansão NÃO conclui:

- V2 MIND;
- V3 Knowledge/RAG/embeddings;
- V5 Vision;
- V6 STAR WORLD 3D;
- V7 Guardian completo;
- V9 Ecosystem completo.

Ela melhora a Foundation 2D e prepara a separação entre visual, estado e Core sem
antecipar as gerações do roadmap.
