# STAR — GRUPO 1: CONVERSA, PERCEPÇÃO E PESSOAS

## Objetivo

Integrar conversa natural, percepção real e contexto de pessoas ao mesmo STAR Core sem criar Brain, memória, banco de pessoas ou sistema de permissões paralelo.

## Arquitetura

```text
entrada textual / imagem / tela / áudio
        ↓
providers locais e explícitos
        ↓
B25 MultimodalPerception + Sensor Fusion
        ↓
B23 Global Workspace / B24 Mind Loop
        ↓
B26 PeopleEntities quando há contexto de pessoa
        ↓
NaturalInteraction
        ↓
resposta semântica
        ↓
modelo local opcional apenas para expressão
```

Regras permanentes:

```text
PERCEPÇÃO ≠ FATO CANÔNICO
RECONHECIMENTO ≠ AUTENTICAÇÃO
AUTENTICAÇÃO ≠ PERMISSÃO
MODELO DE IA ≠ STAR
```

## Modelo local plug-and-play

`core/ai_engine.py` consulta o Ollama local apenas quando um recurso realmente precisa dele. O runtime:

- lista modelos já instalados por `/api/tags`;
- prefere o modelo configurado;
- pode selecionar outro modelo já instalado como fallback para expressão textual;
- aceita imagens quando o modelo suporta visão;
- não baixa modelos silenciosamente;
- mantém `pull_model()` somente para uma ação explicitamente solicitada;
- mantém fallback local determinístico quando Ollama/modelo não estão disponíveis.

O modelo continua sem autoridade para decidir identidade, fatos, autenticação, permissões ou execução.

## Visão semântica

`core/perception_runtime.py::SemanticVisionProvider` reutiliza B25.

Sempre disponível quando Pillow/Numpy estão presentes:

- dimensões da imagem;
- orientação;
- luminância aproximada;
- média RGB;
- evento perceptivo rastreável.

Quando OpenCV opcional está instalado:

- detecção visual de rostos por Haar cascade;
- detecção de rosto não implica identidade.

Quando um VLM Ollama compatível está instalado:

- descrição de cena;
- objetos candidatos;
- pessoas descritas sem identificação nominal;
- texto visual candidato;
- incertezas/confiança declaradas pelo provider.

Saídas do VLM são marcadas como saída de modelo/observação e não são promovidas automaticamente a fatos.

## Imagem anexada ao chat

O botão `+` da interface desktop agora seleciona uma imagem local. Ao enviar:

1. a imagem é validada e analisada no worker do chat;
2. as observações entram no B25;
3. a mensagem textual entra na cognição depois da percepção;
4. `NaturalInteraction` pode recuperar a evidência visual disponível;
5. o arquivo original não é transformado em memória canônica automaticamente.

## Pessoas — B26

B26 continua usando B13 + Knowledge Graph. O perfil persistente agora pode registrar:

- nome e aliases;
- perfil declarado;
- preferências;
- eventos relacionados;
- interações;
- relações entre pessoas;
- consentimentos por escopo/finalidade;
- confiança contextual;
- referências de evidência de identidade;
- templates derivados de face/voz somente com consentimento explícito.

`trust` nunca é usado como permissão operacional.

## Reconhecimento de pessoas

A implementação local possui templates derivados para produzir candidatos de identidade. O resultado é sempre:

```text
status = hypothesis
authenticated = false
grants_permission = false
```

O template visual atual é um descritor local leve para correspondência de aparência e deve ser tratado como hipótese de reconhecimento, não como autenticação biométrica forte. O design permite substituir o descritor por um provider local melhor no futuro sem alterar B26.

Nenhuma imagem facial bruta é persistida pelo B26 por padrão.

## Autenticação separada

`core/person_auth.py::LocalPersonAuthenticator` é um verifier local independente do reconhecimento. Ele:

- exige consentimento explícito para cadastro;
- persiste apenas `salt + scrypt digest`;
- nunca persiste PIN/passphrase em texto;
- pode validar um challenge explícito;
- não concede permissão operacional depois de autenticar.

B26 usa esse verifier pela API `authenticate(...)`; a autorização de ações continua em B01/B33.

## Percepção da tela

`ScreenPerceptionProvider` captura a tela somente quando solicitado localmente. A imagem temporária é removida imediatamente após a análise.

Comandos locais suportados incluem variações de:

- `olhe minha tela`;
- `veja minha tela`;
- `analise minha tela`.

Pedidos remotos não podem acionar tela/microfone do PC por esse caminho.

## Áudio ambiente

`AmbientAudioProvider` realiza apenas uma amostra curta sob solicitação local explícita. Extrai:

- RMS;
- pico;
- zero-crossing rate;
- centroide espectral;
- classificação perceptiva grosseira.

Não existe gravação contínua em background e o áudio bruto da amostra não é persistido por esse provider.

## Speaker recognition

`SpeakerRecognitionProvider` deriva fingerprint acústico local e compara com templates consentidos no B26. Isso produz hipótese de speaker identity; nunca autenticação.

O template não contém o áudio bruto. A qualidade do reconhecedor atual é apropriada para similaridade contextual/local e não deve ser tratada como autenticação biométrica de alta segurança.

## Desempenho

- providers são lazy;
- nenhum polling perceptivo contínuo foi adicionado;
- VLM é opcional;
- OpenCV continua dependência opcional de Vision;
- buffers do B25 continuam bounded;
- nenhum novo banco foi criado;
- nenhuma dependência obrigatória nova foi adicionada;
- ausência de hardware/modelo retorna indisponibilidade em vez de observação inventada.
