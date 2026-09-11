# STAR Watch App V0.4 — Watch-first

## Decisão atual

A prioridade do projeto passa a ser o **aplicativo STAR para relógio**. O PC é usado
nesta fase para simular o hardware e acelerar o desenvolvimento visual/funcional.
A versão desktop completa da nova experiência será tratada depois que o app do
relógio estiver sólido.

A decisão não apaga a Foundation nem cria outra STAR: identidade, Core, voz,
conhecimento e capacidades existentes continuam reutilizados.

## Executar agora

No Windows:

```bat
INICIAR_STAR_WATCH_APP.bat
```

ou:

```powershell
.\.venv\Scripts\python.exe clients\star_watch_app.py
```

## Interação simulada

O PC emula o futuro hardware do relógio:

- roda do mouse / setas esquerda-direita = **girar STAR Ring**;
- clique na lateral esquerda/direita do anel = giro físico simulado;
- Enter / clique no núcleo = **pressionar STAR Ring**;
- Backspace = voltar para HOME;
- Espaço = iniciar/encerrar voz;
- Esc = voltar; no HOME encerra.

A interface é circular e não pressupõe mais `rounded_square` como formato final.

## Modos da V0.4

1. **VOZ** — usa `AudioRecorder`, STT local, STAR Core e TTS já existentes;
2. **BUSCA** — envia a intenção ao Core atual; agregação multi-loja/preço ainda
   depende de um provider de pesquisa mais completo;
3. **SAÚDE** — UX funcional com provider simulado explicitamente rotulado;
4. **GPS** — UX funcional com provider simulado explicitamente rotulado;
5. **VISÃO** — permite selecionar imagem e prepara a experiência STAR Scan;
6. **PEOPLE** — cadastro local simples em `runtime/star_watch/people.json`;
7. **MEDIR** — fluxo STAR Measure com `SimulatedDistanceProvider` até existir laser;
8. **MÍDIA** — reaproveita comandos atuais de mídia do Core;
9. **CLIMA** — interface preparada, sem inventar dados meteorológicos;
10. **CONFIG** — controla simulação e resposta falada.

## STAR Ring

O STAR Ring passa a ser um contrato de entrada do produto, independente do hardware.
A V0.4 implementa semanticamente:

```text
ROTATE_LEFT
ROTATE_RIGHT
PRESS
BACK
```

No simulador esses eventos vêm de mouse/teclado. Em hardware comercial poderão vir
de bezel/coroa. Em hardware próprio poderão vir do anel físico STAR.

Isso evita acoplar a interface a um modelo específico de smartwatch.

## STAR People

A V0.4 implementa **somente cadastro local manual**:

- nome;
- observações;
- caminho opcional de imagem fornecida pelo usuário.

Não existe reconhecimento facial automático nesta versão. Os registros ficam em
`runtime/`, fora da base versionada.

## STAR Scan

A V0.4 prepara o fluxo visual sem declarar Vision AI pronta. No simulador é possível
selecionar uma imagem; análise visual continua indisponível até existir provider real.

O cliente Android V0.3 já transporta imagem, porém usa o preview retornado por
`ACTION_IMAGE_CAPTURE`. Captura de resolução total fica para a portabilidade da V0.4.

## STAR Measure

O software não depende de um tipo específico de sensor. A experiência espera um
provider de distância. Hoje o simulador retorna dados marcados como `SIMULAÇÃO`.
Futuramente esse provider poderá receber um rangefinder/ToF/laser real sem mudar a
navegação da interface.

## O que a V0.4 não finge ter

- GPS físico no PC;
- batimentos/SpO2 reais no PC;
- câmera do smartwatch real;
- análise visual inteligente;
- laser físico;
- clima online configurado;
- comparação automática multi-loja completa;
- reconhecimento automático de pessoas;
- bezel físico conectado.

Esses itens aparecem como provider ausente ou **SIMULAÇÃO**.

## Relação com o Android V0.3

`clients/star_watch_android/` continua sendo a prova de transporte Android:
pareamento, áudio PCM/WAV, câmera, TTS e runtime. A V0.4 não duplica esse código.
Depois que a experiência do simulador estiver validada, o shell circular e o contrato
do STAR Ring serão portados para Android sobre essa base.

## Fonte de verdade

`STAR_MANIFEST.json > star_watch_app` registra versão, direção Watch-first,
interações e modos oficiais da V0.4.

## Próximo marco

**V0.5 — Android Shell Port**

- portar HOME circular e STAR Ring para Android;
- suporte a eventos reais de coroa/bezel quando o hardware disponibilizar API;
- câmera em resolução total;
- providers reais de GPS/saúde conforme o dispositivo;
- Search Provider com resultados estruturados;
- validar consumo de bateria, RAM e frame time em hardware real.
