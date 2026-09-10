# STAR + Seed-VC

Integração opcional de conversão de voz para a STAR V1.9.

## Decisão arquitetural

O Seed-VC não é incorporado ao código-fonte da STAR. Ele é instalado como um runtime externo local em:

`voice/external/seed-vc/`

Esse diretório é ignorado pelo Git. A STAR contém apenas `voice/seed_vc.py`, uma ponte leve que chama as interfaces públicas do Seed-VC por subprocesso.

Motivos:

- preservar o `voice/` atual como única arquitetura de voz da STAR;
- não duplicar dezenas de módulos e dependências de ML;
- não aumentar o startup nem o `requirements.txt` principal;
- manter Seed-VC substituível;
- separar claramente o componente GPLv3 do código da STAR;
- permitir remover o runtime sem quebrar STT, Chatterbox, SAPI ou Piper.

## O que a STAR passa a expor

`SeedVCBackend.convert_v1(...)`

- voice conversion zero-shot V1;
- referência de voz de 1–30 s conforme suporte upstream;
- configuração de diffusion steps, length adjust e CFG;
- checkpoint/configuração customizados opcionais.

`SeedVCBackend.convert_v1(..., singing=True)`

- singing voice conversion;
- condicionamento F0;
- ajuste automático de F0 opcional;
- deslocamento de semitons.

`SeedVCBackend.convert_v2(...)`

- voice/accent conversion V2;
- controle separado de inteligibilidade e similaridade;
- conversão de estilo/sotaque/emoção;
- modo de anonimização;
- checkpoints AR/CFM opcionais;
- compilação opcional quando o ambiente suportar.

`SeedVCBackend.launch_realtime(...)`

- abre o modo oficial de conversão em tempo real do runtime Seed-VC;
- permanece separado da thread da GUI da STAR;
- deve ser usado preferencialmente com GPU compatível.

`SeedVCBackend.start_finetune_v1(...)` e `start_finetune_v2(...)`

- expõem o fine-tuning upstream de forma explícita;
- nunca iniciam automaticamente;
- datasets e checkpoints permanecem locais.

## Instalação

A instalação é deliberadamente separada do `INSTALAR_VOZ.bat`, porque Seed-VC é opcional e pesado.

Na raiz da STAR:

```powershell
.\.venv\Scripts\python.exe -m voice.seed_vc install
```

A ponte tenta usar Python 3.10 para criar o ambiente local do Seed-VC. O runtime é fixado na revisão upstream analisada pela STAR para garantir reprodutibilidade.

Verificação sem carregar modelos:

```powershell
.\.venv\Scripts\python.exe -m voice.seed_vc status
```

O diagnóstico geral também mostra a disponibilidade:

```powershell
.\.venv\Scripts\python.exe -m voice.diagnostics
```

## Modelos e funcionamento offline

Os scripts upstream podem baixar checkpoints na primeira inferência quando nenhum checkpoint local é informado. Portanto, a primeira preparação pode exigir internet.

Depois de manter runtime e checkpoints localmente, a conversão pode funcionar localmente. A STAR não transmite automaticamente referências, datasets ou saídas para serviços externos.

Para uma instalação totalmente controlada/offline, configure checkpoints locais nos métodos de conversão.

## Referência oficial da STAR

Seed-VC é uma capacidade de transformação, não a identidade da STAR.

A referência oficial continua em `voice/reference/` e não é versionada. Ao converter áudio para a voz da STAR, a camada chamadora deve fornecer essa referência como `target`.

O TTS oficial continua sendo Chatterbox enquanto o roadmap V1.9 não decidir o contrário.

## Licença

O repositório Seed-VC analisado declara GNU GPL v3. O runtime externo deve conservar sua licença e seus avisos. Esta integração evita copiar/modificar o código upstream dentro da STAR, mas qualquer distribuição que inclua Seed-VC deve respeitar as obrigações aplicáveis da GPLv3.

## Limites desta etapa

- Não há carregamento automático de Seed-VC no startup.
- Não há download de checkpoints no repositório STAR.
- Não há novo menu/GUI da STAR para VC ainda.
- O modo realtime inicialmente abre a GUI upstream isolada; incorporar o stream diretamente ao pipeline de áudio da STAR exigirá benchmark e validação de latência em hardware real.
- Seed-VC não substitui STT nem TTS: ele transforma áudio já existente.
