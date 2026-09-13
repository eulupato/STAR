# Auditoria da referência `mishu006/Filters`

Data da análise: 2026-09-12.

## Repositório lido

- `README.md`
- `main.py`
- `filters.py`
- `geometry.py`
- `hand_tracking.py`
- `requirements.txt`

## Conceito encontrado

O projeto externo cria um quadrilátero entre indicador/polegar de duas mãos, aplica um efeito apenas dentro dele e troca entre filtros quando a largura do portal cruza um limiar com histerese.

Dependências declaradas pela referência: OpenCV, MediaPipe 0.10.14 e NumPy.

O README declara licença MIT. Na auditoria da raiz não havia arquivo `LICENSE` separado listado. Por isso, a STAR não incorpora/vendoriza os arquivos externos: foi feita uma implementação própria baseada no comportamento/conceito observado.

## Limitações que motivaram a reimplementação

- loop de câmera e regras de produto fortemente acoplados;
- apenas 8 filtros;
- sem suavização temporal das quatro âncoras;
- sem rejeição de saltos/áreas degeneradas;
- gesto baseado apenas em largura instantânea + histerese simples;
- sem confirmação por múltiplos frames e cooldown temporal;
- sem adaptação de resolução para preservar FPS;
- sem HUD operacional;
- sem captura integrada, fullscreen ou controles manuais de fallback;
- dependências obrigatórias no app original;
- nenhuma integração com o Core/segurança/dispositivos da STAR.

## Resultado STAR

O STAR Vision Portal V1 mantém apenas a ideia de interação útil e substitui a implementação por componentes próprios: `GestureHysteresis`, `AdaptivePointSmoother`, `GeometryGate`, `PerformanceGovernor`, `FilterEngine`, `PortalRenderer`, `HandPortalTracker` e integração com `StarCore`.
