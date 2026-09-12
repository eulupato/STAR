# STAR V1.9 — Conversa Natural, Voz e Clima Contextual

## Objetivo

Esta atualização amplia a Foundation sem criar uma segunda STAR nem um sistema
paralelo. O `StarCore` continua sendo o ponto central de processamento e agora
possui três camadas complementares:

1. `core.commands` — intents/slots para comandos estruturados;
2. `core.conversation` — small talk e respostas naturais;
3. `core.weather` — contexto meteorológico online, sob demanda.

## Catálogo de voz

O catálogo é gerado a partir de templates, wake words, sinônimos e variáveis.
Ele não contém milhares de `if/elif`.

Contrato mínimo automatizado:

- pelo menos **4.000 variações distintas**;
- slots livres para pesquisa web, arquivos, Spotify e localização climática;
- alvos enumerados para abrir/fechar aplicações;
- normalização de acentos, pontuação, wake word e `por favor`;
- comandos sensíveis continuam bloqueados remotamente quando exigem confirmação.

A implementação atual gera mais do que o mínimo de 4.000 variações; o valor exato
é obtido em runtime por `core.commands.command_count()`.

## Catálogo conversacional

`core.conversation` compõe respostas a partir de famílias sem carregar um arquivo
com milhares de frases repetidas. O contrato automatizado exige pelo menos
**5.000 respostas únicas** para:

- saudações;
- bem-estar;
- agradecimentos;
- conversa casual;
- apoio cotidiano;
- despedidas.

O runtime escolhe combinações deterministicamente com base na mensagem recebida,
evitando respostas completamente aleatórias a cada chamada.

## Clima contextual

Comentários meteorológicos não são respondidos por palpite.

Exemplos:

- `o dia está bonito`
- `está frio hoje`
- `que calor`
- `o dia está chuvoso`
- `como está o tempo`
- `como está o tempo em Porto Alegre`

Quando a frase depende do clima, a STAR consulta o provider, usa cache em memória
e compara a afirmação do usuário com temperatura, sensação térmica, precipitação,
cobertura de nuvens e código meteorológico.

Assim, uma condição de 30 °C não é descrita como "frio" apenas para concordar com
o usuário.

## Fontes e rede

O provider usa:

- Open-Meteo Geocoding API para resolver cidades;
- Open-Meteo Forecast API para condições atuais;
- ipwho.is somente quando não existe localização configurada e a estimativa
  automática está habilitada.

Não há consulta em background e nenhuma coordenada é persistida em disco por esta
camada.

Variáveis de ambiente:

```text
STAR_WEATHER_ENABLED=1
STAR_WEATHER_LOCATION=Cidade, Estado
STAR_WEATHER_AUTOLOCATE=1
STAR_WEATHER_CACHE_SECONDS=600
```

Para máxima privacidade, configure `STAR_WEATHER_LOCATION` localmente e use
`STAR_WEATHER_AUTOLOCATE=0`.

## Segurança

O acesso meteorológico é uma capacidade online estreita e não habilita o modo web
geral da STAR. Pesquisa arbitrária, browser e Spotify continuam obedecendo ao
controle `network_enabled`.

Ações destrutivas e sensíveis continuam fora desta atualização.

## Validação

```powershell
python diagnostico.py
python -m pytest -q tests/test_voice_commands.py
python -m pytest -q tests/test_conversation_weather.py
python -m pytest -q tests
```

O diagnóstico também diferencia a simples descoberta de manifests de Knowledge
Packs da existência efetiva de entradas carregadas.
