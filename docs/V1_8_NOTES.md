# STAR V1.8 — Voz + Interface

## Implementado
- Interface principal minimalista inspirada na referência enviada.
- Avatar central antes da primeira mensagem.
- Campo central inferior `Pergunte algo à STAR...` com +, microfone visual e envio.
- Conversa abre sem os antigos painéis laterais.
- Status mostra V1.8 e ONLINE/OFFLINE.
- Configurações com seletor visual de modo de funcionamento.
- `Casa` substitui `House — Casa da STAR`.
- ElevenLabs integrado como camada de TTS, usando `key.txt` local e Voice ID configurado.
- Falha de voz não interrompe o chat.
- Inicializador cria o ambiente virtual automaticamente se ele não existir.
- Matemática offline entende símbolos e expressões como `dois menos um`, `vezes`, `dividido`, `metade de` e `raiz quadrada de`.
- Base pessoal expandida para 100 aliases e 100 respostas por intenção, com seleção aleatória.
- Palavras isoladas ambíguas, como `cerebro`, pedem contexto em vez de assumir a intenção.
- Erros comuns de saudação como `ooi` e `oii` são reconhecidos.
- Pequena memória de sessão para nome do usuário e continuidade imediata.

## Segurança
- A chave do ElevenLabs não é exibida pela interface nem registrada em logs.
- `key.txt` deve permanecer privado e fora de repositórios públicos.
