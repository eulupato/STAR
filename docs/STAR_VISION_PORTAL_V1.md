# STAR Vision Portal V1

## Objetivo

Transformar o conceito público de `mishu006/Filters` em uma capacidade própria da STAR, mais modular, fluida e segura, sem copiar/colar a implementação original.

O projeto de referência usa OpenCV, MediaPipe e NumPy para formar um portal entre indicador/polegar das duas mãos e alternar filtros por aproximação. A STAR preserva a ideia central, mas reimplementa a arquitetura do zero e adiciona controles, validações, desempenho adaptativo e integração com o Core.

## O que mudou em relação ao conceito de referência

### Tracking mais estável

- suavização EMA adaptativa: mais suave quando a mão está parada e mais responsiva durante movimentos rápidos;
- filtro de geometria para rejeitar polígonos minúsculos, degenerados ou saltos muito grandes entre frames;
- confirmação do gesto por múltiplos frames;
- histerese entre fechar e reabrir;
- cooldown para impedir múltiplas trocas por tremor;
- escala de processamento adaptativa conforme FPS.

### Rendering

O filtro é aplicado somente dentro do quadrilátero formado pelas mãos. A composição usa:

- máscara poligonal;
- feathering da borda para evitar recorte duro;
- glow externo;
- borda animada inspirada no Plasma Orbit;
- pontos de ancoragem luminosos;
- HUD com filtro, FPS, tracking e escala de processamento.

### 12 filtros

1. Hologram — scanlines, glow e ciano Plasma;
2. Neon — duotone responsivo à luminância;
3. Halftone — trama de pontos monocromática;
4. Chromatic — aberração RGB;
5. Thermal — pseudocor térmica;
6. Vintage — sépia, vinheta e grão;
7. Frosted — vidro fosco;
8. Magenta — halftone rosa/magenta;
9. Edges — contornos luminosos;
10. Night — visão noturna com CLAHE;
11. X-Ray — negativo frio com bordas;
12. Cyber — posterização ciano/violeta.

## Integração com a STAR

O controlador fica em `modules/vision.py` e não importa OpenCV/MediaPipe no startup. Portanto, a STAR continua inicializando mesmo que o pacote de visão não esteja instalado.

O cliente visual fica em `clients/star_vision_portal.py` e só carrega as dependências quando é realmente executado.

Dependências opcionais:

```bash
pip install -r requirements-vision.txt
```

Comandos locais reconhecidos incluem:

```text
STAR, abra o portal visual
STAR, ative o portal de visão
STAR, star vision portal
STAR, status do star vision
STAR, quais filtros do portal
STAR, feche o portal visual
```

A entrada pode vir de texto ou STT, porque o tratamento ocorre dentro do StarCore.

## Segurança

Abrir ou encerrar a webcam do PC é uma ação local. Endpoints remotos como Watch/Mobile podem pedir status e lista de filtros, mas não podem iniciar ou encerrar a câmera do computador enquanto não existir o Permission Manager apropriado.

O módulo não envia frames para internet e não depende de API remota.

## Controles durante execução

- aproximar as duas laterais do portal: próximo filtro;
- `A`: filtro anterior;
- `D`: próximo filtro;
- `S`: salvar captura em `runtime/vision/captures`;
- `H`: mostrar/ocultar HUD;
- `F`: tela cheia;
- `Q` ou `Esc`: fechar.

## Performance

`PerformanceGovernor` observa a taxa de quadros. Quando o FPS fica muito abaixo do alvo, a análise das mãos é reduzida progressivamente até 55% da resolução, enquanto o frame final continua sendo renderizado na resolução da câmera. Se houver folga de desempenho, a escala volta a subir.

## Referência externa

O repositório `mishu006/Filters` foi usado como referência de produto/conceito. O README público declara licença MIT, mas a integração da STAR não vende nem copia os arquivos do projeto: trata-se de uma reimplementação própria do comportamento desejado.
