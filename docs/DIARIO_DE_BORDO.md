# ⭐ Diário de Bordo — Projeto STAR

Este arquivo é o registro cronológico oficial das decisões, mudanças de direção, implementações, validações e próximos passos do Projeto STAR.

> Regra: registrar o estado real. Funcionalidade planejada, simulada, parcial e pronta devem permanecer claramente separadas.

---

## 11/09/2026 — Início da fase STAR Watch-first

### Decisão principal

A prioridade prática do projeto foi alterada.

A partir desta data, a ordem de desenvolvimento passa a ser:

1. **STAR Watch como produto principal da fase atual**;
2. desenvolvimento e validação da experiência do relógio primeiro em um **simulador no PC**;
3. portabilidade para um smartwatch Android/Wear OS quando a experiência estiver madura;
4. somente depois, construção da nova experiência completa da **STAR para PC**.

O roadmap antigo deixa de determinar a ordem imediata de implementação. Ele não foi apagado e continua servindo como histórico de decisões anteriores, mas a nova direção aprovada nesta data tem prioridade.

A STAR continua sendo uma única arquitetura. O Watch não deve virar uma STAR paralela e não deve duplicar identidade, memória, Core, voz ou sistemas existentes sem necessidade.

### Pesquisa e decisões de hardware

Durante a definição do STAR Watch, foram avaliados diferentes conceitos de interação física e relógios comerciais.

Requisitos inicialmente discutidos:

- relógio circular;
- anel/bisel giratório para navegação;
- idealmente o próprio anel pressionável para confirmação, em uma interação inspirada na lógica de seleção do Omnitrix, mas com identidade própria da STAR;
- câmera integrada de boa qualidade;
- boa bateria;
- Android suficientemente aberto para executar a STAR;
- preço baixo o bastante para prototipagem.

Foi identificado que a combinação exata de **anel principal que gira e também afunda/clica** praticamente não existe em smartwatches comerciais adequados. Coroas laterais clicáveis não atendem ao conceito desejado.

A ideia foi então reformulada:

- o software deve possuir um contrato genérico de entrada chamado **STAR Ring**;
- no PC, a roda do mouse e as setas simulam a rotação;
- Enter ou clique central simulam a pressão/confirmação;
- em um relógio comercial, bezel/coroa física poderá gerar os mesmos eventos quando suportado;
- em hardware próprio futuro, o STAR Ring poderá finalmente combinar rotação e clique físico do próprio anel sem exigir alterações na lógica da interface.

Também foi avaliado o uso de Galaxy Watch Classic por seu bezel físico giratório, porém o custo de modelos mais novos foi considerado alto demais para esta fase. O Watch4 Classic usado apareceu como opção mais racional para uma futura prova de hardware, mas a decisão final foi **não comprar hardware agora e focar no aplicativo**.

### Conceito atual do STAR Watch

O relógio não deve ser apenas um controle remoto com vários aplicativos comuns. A meta é que a STAR seja a experiência principal do dispositivo.

Modos e áreas definidos para a interface:

- **Voz**;
- **Busca**;
- **Saúde**;
- **GPS/Navegação**;
- **Visão**;
- **People**;
- **Medir**;
- **Mídia**;
- **Clima**;
- **Configurações**.

A navegação deve ser compatível com toque, voz e STAR Ring.

A interface deve ser circular, rápida e simples, com o **Plasma Core** como elemento central de identidade visual.

### Search Specialist

Foi reforçada a ideia de que a STAR não terá vários “robôs” independentes escolhidos manualmente pelo usuário.

A arquitetura desejada é uma única STAR com especializações internas acionadas automaticamente pela intenção da fala.

Exemplo futuro para busca:

> “STAR, procura esse perfume mais barato.”

A especialização de busca deverá futuramente conseguir pesquisar ofertas atuais, comparar preço, frete, confiabilidade da loja e custo-benefício, retornando uma resposta compacta adequada ao relógio.

Na V0.4 essa comparação multi-loja completa **ainda não existe**. A busca reutiliza o Core atual e não declara capacidades inexistentes.

### STAR People

Conceito definido como biblioteca pessoal de pessoas/contatos da STAR, com dados fornecidos pelo usuário, como:

- nome;
- foto;
- contexto de relacionamento;
- observações;
- notas pessoais.

A primeira implementação deve ser manual e local. Reconhecimento visual futuro deverá ser tratado como recurso auxiliar, não como autenticação.

Na V0.4 já existe cadastro manual local em:

`runtime/star_watch/people.json`

### STAR Scan / Vision

O conceito de Scan foi mantido como camada de câmera e visão da STAR.

Objetivos futuros:

- captura de imagem;
- associação a pessoas/objetos/contextos;
- leitura de texto;
- interpretação de objetos e ambientes;
- integração com STAR People quando houver suporte adequado.

Na V0.4 é possível selecionar uma imagem no simulador, mas **Vision AI ainda não é anunciada como pronta**.

O cliente Android anterior já possuía câmera, mas ainda utiliza captura simplificada/preview. Captura em resolução total permanece como tarefa posterior do port Android.

### STAR Measure

Foi definida a ideia de medição independente do hardware específico.

O aplicativo deverá consumir um provider de distância. Assim, a interface não precisa saber se o dado veio de:

- laser ToF;
- rangefinder;
- LiDAR;
- sensor externo;
- simulador.

Na V0.4 o provider de distância é explicitamente **simulado**. Nenhum valor simulado é apresentado como medição física real.

O módulo físico de laser, tampa protetora e sensores ópticos permanece como conceito futuro de hardware e não é necessário para evoluir o app agora.

### Mudança arquitetural

Modelo anterior predominante do Watch:

```text
WATCH
  ↓
PC
  ↓
STAR CORE
```

Direção atual:

```text
STAR WATCH SHELL
│
├── Interface
├── Voz
├── STAR Ring
├── Apps/Modos STAR
├── Sensores
├── Estado local
├── Cache local
│
└── STAR Services
    ├── recursos locais
    ├── PC quando necessário
    └── internet quando necessária
```

A intenção é que o Watch deixe de parecer apenas um controle remoto e passe a ser a experiência principal da STAR, mantendo processamento pesado externo somente quando fizer sentido.

---

## Implementação concluída — STAR Watch App V0.4

Foi criada e integrada uma nova versão funcional para simulação do STAR Watch no PC.

### Arquivos principais adicionados/atualizados

- `clients/star_watch_app.py` — simulador circular principal;
- `INICIAR_STAR_WATCH_APP.bat` — launcher do simulador no Windows;
- `docs/STAR_WATCH_APP_V0_4.md` — documentação técnica da V0.4;
- `STAR_MANIFEST.json` — registra a nova fase Watch-first, modos, formato circular e interações;
- testes automatizados relacionados ao Watch, providers, People, manifesto e segurança de comandos remotos.

### Funcionalidades da V0.4

- interface circular no PC;
- HOME com Plasma Core;
- STAR Ring como contrato de entrada independente de hardware;
- roda do mouse/setas para rotação;
- Enter/clique no núcleo para confirmação;
- navegação entre os modos Voz, Busca, Saúde, GPS, Visão, People, Medir, Mídia, Clima e Config;
- reaproveitamento do `StarCore` oficial sob demanda;
- reutilização da infraestrutura de voz existente;
- cadastro local de STAR People;
- providers simulados e claramente identificados para recursos físicos inexistentes no PC;
- preservação do cliente Android anterior como base de transporte para próxima fase.

### Segurança corrigida

Durante a revisão foi corrigido o comportamento de comandos remotos sensíveis.

As seguintes ações deixaram de ser tratadas como seguras por padrão quando originadas remotamente:

- screenshot;
- busca de arquivos;
- Terminal;
- PowerShell.

Essas ações passam a exigir confirmação/localidade adequada até existir um Permission Manager mais completo.

### Estado do Git após integração

PR utilizada para integrar a nova fase:

- **PR #26 — `⌚ STAR Watch App V0.4 — Watch-first Simulator`**

Commit de integração na `main`:

`957ef56c59831764324ecac7b9fe9303b44721b2`

A `main` passou a apontar para esta nova fase Watch-first.

### Validação automatizada

A versão foi validada antes e depois da integração.

Resultado principal da suíte:

- **54 testes passaram**;
- `pip check` sem dependências quebradas;
- compilação Python aprovada;
- higiene do repositório aprovada.

Workflows validados com sucesso:

- STAR CI;
- STAR Quality;
- STAR Security;
- Windows Smoke;
- STAR Watch Android;
- STAR Mobile iOS.

O build Android existente também permaneceu funcional, evitando regressão na base já criada.

### O que ainda NÃO está pronto

A V0.4 não deve ser descrita como produto final. Permanecem pendentes:

- port do shell circular para Android/Wear OS;
- leitura de bezel/coroa física real;
- câmera do smartwatch em resolução total;
- GPS físico integrado ao app novo;
- sensores reais de saúde integrados ao app novo;
- Vision AI;
- reconhecimento visual de pessoas;
- laser/rangefinder físico;
- clima online configurado no shell novo;
- comparador multi-loja completo para Search;
- validação física em smartwatch real.

### Próximo marco

**STAR Watch V0.5 — Android Shell Port**

Objetivos prioritários:

1. portar o HOME circular e a navegação do STAR Ring para Android;
2. detectar eventos físicos de bezel/coroa disponíveis no hardware escolhido;
3. melhorar a captura de câmera para resolução total;
4. substituir providers simulados por providers reais apenas quando o hardware estiver disponível;
5. preservar a mesma experiência e o mesmo contrato de entrada entre PC e relógio.

### Comandos úteis registrados

Atualizar a STAR para a versão mais recente da `main`:

```powershell
cd C:\Development\Projects\STAR
git pull origin main
```

Abrir o simulador do STAR Watch:

```powershell
.\INICIAR_STAR_WATCH_APP.bat
```

Alternativa direta:

```powershell
.\.venv\Scripts\python.exe .\clients\star_watch_app.py
```

---

## Estado ao encerrar este registro

A nova fase **Watch-first está implementada e integrada**.

O projeto não está recomeçando do zero: Core, voz, comandos, runtime, Android e infraestrutura existente continuam sendo reaproveitados.

A prioridade seguinte é tornar o simulador confortável e coerente como produto e, em seguida, levar exatamente essa experiência ao smartwatch real sem duplicar a STAR ou criar uma arquitetura paralela.
