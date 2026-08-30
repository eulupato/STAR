# ⭐ STAR — V1.9

S.T.A.R. — **System for Thought, Analysis and Response**.

A STAR é um sistema cognitivo modular em desenvolvimento, com identidade, memória, conhecimento, interface, ambientes e ferramentas. O projeto é organizado para crescer por módulos, sem ficar preso a um único modelo de IA ou serviço externo.

## Execução no Windows

Use:

`INICIAR_STAR.bat`

Ou:

`\.venv\Scripts\python.exe main.py`

Caso a `.venv` não exista, execute `CRIAR_AMBIENTE.bat` uma vez.

Para preparar a voz local, execute `INSTALAR_VOZ.bat` uma vez.

Para diagnóstico local:

`DIAGNOSTICO_VOZ.bat`

## Voz V1.9 — arquitetura rápida e local

A V1.9 removeu os serviços externos de voz do caminho ativo. A voz principal funciona localmente:

```text
🎤 Microfone
    ↓
sounddevice / AudioRecorder
    ↓
faster-whisper tiny (STT PT-BR)
    ↓
📝 Texto
    ↓
STAR Core
    ↓
💬 Resposta
    ↓
Piper PT-BR (TTS rápido)
    ↓
🔊 sounddevice
    ↓
Alto-falante
```

O STT e o TTS são pré-carregados em segundo plano para retirar o custo de primeira inicialização da interação. O Piper fica carregado no processo principal e sintetiza por chunks, evitando recarregar o modelo para cada frase.

### Voz clonada

O **Chatterbox** permanece preparado separadamente para a futura modalidade de voz clonada da STAR. Nesta máquina, que é CPU-only, ele é muito mais pesado que o Piper e por isso não é usado no caminho rápido padrão.

A referência de voz deve permanecer somente na máquina local em:

`voice/reference/star_reference.mp3`

O arquivo não é distribuído pelo GitHub.

## Dependências de voz

- `faster-whisper` — reconhecimento local de fala, modelo `tiny`, CPU/INT8.
- `piper-tts` — síntese neural local rápida.
- `pyttsx3` — fallback de voz do Windows/SAPI.
- `sounddevice` + `soundfile` — captura e reprodução de áudio.

As vozes Piper são arquivos `.onnx` + `.onnx.json` baixados localmente pelo instalador. O modelo padrão é `pt_BR-faber-medium`.

## Estrutura principal

```text
STAR/
├── core/                  # identidade, cérebro, roteamento, memória e estado
├── database/              # armazenamento persistente
├── gui/                   # interface e STAR WORLD
├── knowledge/             # Knowledge Packs
├── modules/               # ferramentas e automações
├── voice/                 # pipeline de áudio local
├── tests/                 # testes automatizados
├── docs/                  # documentação
├── assets/                # recursos visuais
├── SKINS/                 # aparências da STAR
├── main.py                # entrada principal
├── config.py              # configuração V1.9
├── requirements.txt       # dependências do ambiente principal
└── INICIAR_STAR.bat       # inicializador
```

## STAR WORLD

O catálogo de ambientes inclui HUB, Casa, Laboratório, Central de Criação, Biblioteca, Estúdio, Observatório, Jardim, Correio, Cura, Heróis e Idiomas. As ilhas podem existir visualmente antes de receberem todo o conhecimento.

## Matemática

O motor determinístico interpreta linguagem natural, por exemplo:

- dois mais dois
- três vezes cinco
- vinte dividido por quatro
- raiz quadrada de dezesseis
- metade de vinte
- dobro de quinze

## Controle do computador

Existe uma camada inicial para abrir navegador e aplicativos, pesquisar na web, localizar arquivos e receber novas skills. A automação fica separada do núcleo cognitivo para permitir expansão posterior com segurança.

## Privacidade

Ambientes virtuais, modelos, caches, banco local, arquivos temporários, referências de voz e credenciais não devem ser versionados. Nunca coloque chaves ou tokens no GitHub.

## CI

O GitHub Actions valida a sintaxe Python e os testes de voz que não dependem de hardware. Microfone, alto-falante e desempenho de inferência precisam de validação final no Windows local.

## Estado da V1.9

A branch `v1.9-development` contém:

- pipeline local STT → STAR → TTS;
- faster-whisper tiny pré-carregado;
- Piper PT-BR pré-carregado e com streaming de áudio;
- fallback SAPI do Windows;
- Chatterbox isolado como backend futuro de voz clonada;
- diagnóstico de dispositivos e tempo de voz;
- matemática em linguagem natural;
- controle inicial do computador;
- pack inicial da Ilha dos Heróis;
- Closet/skins;
- proteção de segredos e arquivos de voz pessoais;
- CI de qualidade.
