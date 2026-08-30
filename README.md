# ⭐ STAR — V1.9

S.T.A.R. — **System for Thought, Analysis and Response**.

A STAR é um sistema cognitivo modular em desenvolvimento, com identidade, memória, conhecimento, interface, ambientes e ferramentas. O projeto foi estruturado para crescer por módulos sem depender de um único modelo ou serviço.

## Execução no Windows

Use o iniciador:

`INICIAR_STAR.bat`

Ou execute diretamente:

`\.venv\Scripts\python.exe main.py`

Se a `.venv` ainda não existir, execute `CRIAR_AMBIENTE.bat` uma vez.

Para preparar a voz local, execute `INSTALAR_VOZ.bat` uma vez.

Para diagnosticar a voz ponta a ponta:

`DIAGNOSTICO_VOZ.bat`

## Voz V1.9 — arquitetura oficial

A V1.9 remove os serviços externos de voz do fluxo ativo. Não existe mais dependência de ElevenLabs para fala ou reconhecimento.

```text
🎤 Microfone
    ↓
sounddevice / AudioRecorder
    ↓
faster-whisper local (STT em português)
    ↓
📝 Texto
    ↓
STAR Core
    ↓
💬 Resposta
    ↓
Chatterbox Multilingual local
    ↓
WAV
    ↓
soundfile + sounddevice
    ↓
🔊 Alto-falante
```

### TTS

O Chatterbox roda em um ambiente Python separado (`.voice_venv`) porque o projeto foi testado com Python 3.11 para esse componente. Ele recebe um áudio de referência local e gera o WAV. O processo principal da STAR é responsável pela reprodução.

### STT

O reconhecimento usa `faster-whisper` local, com o modelo `base` por padrão, CPU e quantização INT8. O tamanho pode ser alterado pela variável `STAR_STT_MODEL`.

## Referência de voz

Coloque seu áudio autorizado em:

`voice/reference/star_reference.mp3`

O arquivo de referência não é distribuído pelo repositório público. Use somente áudios que você tenha autorização para utilizar na clonagem/síntese de voz.

## Estrutura principal

```text
STAR/
├── core/                  # identidade, cérebro, roteamento e estado
├── database/              # memória persistente
├── gui/                   # interface
├── knowledge/             # Knowledge Packs e conteúdos
├── modules/               # ferramentas e automações
├── voice/                 # voz local
├── tests/                 # testes
├── docs/                  # documentação
├── assets/                # recursos visuais
├── SKINS/                 # aparências da STAR
├── main.py                # entrada principal
├── config.py              # configuração
├── requirements.txt       # dependências da .venv
└── INICIAR_STAR.bat       # inicializador
```

## STAR WORLD

O catálogo de ambientes inclui HUB, Casa, Laboratório, Central de Criação, Biblioteca, Estúdio de Música, Observatório, Jardim, Correio, Cura, Heróis e Idiomas. As ilhas podem existir visualmente antes de receberem conteúdo completo.

## Matemática

A V1.9 possui um motor determinístico separado do processamento de linguagem. Ele interpreta formas naturais como:

- dois mais dois
- três vezes cinco
- vinte dividido por quatro
- raiz quadrada de dezesseis
- metade de vinte
- dobro de quinze

## Controle do computador

Existe uma camada inicial para ações locais, incluindo abertura/pesquisa no navegador, abertura do Spotify e busca de arquivos. A arquitetura foi separada para receber novas skills sem misturar automação com o núcleo cognitivo.

## Segurança e privacidade

Ambientes virtuais, banco local, modelos baixados, cache, áudios temporários e credenciais ficam fora do versionamento. Nunca coloque chaves ou tokens no GitHub.

## CI

O projeto possui uma verificação automática de sintaxe Python e dos manifestos JSON principais.

## Estado da V1.9

Implementado na branch `v1.9-development`:

- arquitetura de voz local unificada;
- Chatterbox persistente em worker separado;
- reprodução de WAV no processo principal;
- STT local com faster-whisper;
- diagnóstico executável da voz;
- matemática em linguagem natural;
- controle inicial do computador;
- pack inicial da Ilha dos Heróis;
- proteção de segredos e dados locais;
- CI de sintaxe/manifestos.

Ainda requer validação física no Windows para microfone, saída de áudio e tempo de geração do Chatterbox no hardware do usuário.
