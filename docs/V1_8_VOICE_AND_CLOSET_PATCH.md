# STAR V1.8 — Correção de Chat, Voz e Closet

## Corrigido
- Botão CHAT do cabeçalho agora retorna à conversa.
- Modo ONLINE/OFFLINE controla os serviços externos de voz.

## Voz
- Saída: ElevenLabs gera a fala e o pygame reproduz no dispositivo padrão.
- Entrada: botão 🎤 inicia a gravação no primeiro clique e para no segundo.
- O áudio é enviado ao Speech-to-Text do ElevenLabs usando `scribe_v2`.
- A transcrição entra no chat e é enviada ao Core.
- Configurações inclui TESTAR VOZ DA STAR.

## Closet
- Novo caminho: ILHAS → CASA → CLOSET.
- Imagens em `SKINS/` são carregadas automaticamente.
- A seleção é salva em `config_skin.json`.
- A skin escolhida aparece na tela principal.
- As imagens de referência em `SKINS/sistema de seleção/` inspiraram o conceito, sem copiar sua interface.

## Dependências
- numpy
- sounddevice
- soundfile

## Testes
- Compilação Python: OK.
- test_star_v16.py: OK.
- test_star_v17.py: OK.
- test_identity.py: OK.
- test_brain_v2.py: OK.

## Observação
O Windows precisa permitir acesso ao microfone para o Python usado pela STAR. A saída usa o dispositivo de áudio padrão do Windows.
