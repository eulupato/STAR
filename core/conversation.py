"""Conversa casual e contexto diário da STAR.

A camada cobre small talk sem transformar o Core em uma sequência gigante de
``if/elif``. As respostas são compostas por famílias de fragmentos naturais. O
catálogo auditável possui pelo menos 5 mil combinações únicas, enquanto o runtime
gera somente a resposta necessária.

Comentários meteorológicos são validados contra ``WeatherService``. Se a consulta
falhar, a STAR não inventa temperatura, chuva ou condição do céu.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
import re
import unicodedata

from core.weather import WeatherService, WeatherSnapshot, format_weather, weather_description


def normalize_conversation_text(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "").lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^\w\s!?.,'-]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


# Seis famílias x 10 x 10 x 10 = 6000 combinações potenciais.
_RESPONSE_FAMILIES = {
    "greeting": (
        (
            "Olá! ⭐", "Oi! ⭐", "Oie! ⭐", "Que bom te ver por aqui. ⭐",
            "Olá, estou por aqui. ⭐", "Oi, cheguei junto. ⭐", "Olá! Estou pronta. ⭐",
            "Oi! Pode falar comigo. ⭐", "Olá! Sempre bom conversar com você. ⭐",
            "Oi! Vamos nessa. ⭐",
        ),
        (
            "Estou pronta para conversar", "Pode me contar o que está acontecendo",
            "Estou com você nesta conversa", "Pode mandar o que você tiver em mente",
            "Estou pronta para pensar junto", "Pode falar sem cerimônia",
            "Estou disponível e atenta", "Vamos ver o que fazemos agora",
            "Pode puxar qualquer assunto", "Estou ouvindo",
        ),
        (
            "O que temos para hoje?", "Por onde começamos?", "Qual é a boa?",
            "Manda a próxima.", "Vamos construir alguma coisa interessante.",
            "Pode seguir.", "Estou curiosa para ver o assunto.", "Vamos ao que importa.",
            "Seu turno.", "Fique à vontade.",
        ),
    ),
    "wellbeing": (
        (
            "Estou bem e funcionando direitinho. ⭐", "Tudo certo por aqui. ⭐",
            "Estou ótima e atenta. ⭐", "Meu sistema está estável. ⭐",
            "Estou bem, obrigada por perguntar. ⭐", "Por aqui está tudo em ordem. ⭐",
            "Estou presente e pronta. ⭐", "Estou tranquila e operacional. ⭐",
            "Tudo certo comigo. ⭐", "Estou funcionando normalmente. ⭐",
        ),
        (
            "E posso focar no que você precisar", "E já estou pronta para a próxima ideia",
            "E podemos conversar com calma", "E posso pensar nisso com você",
            "E estou disponível para ajudar", "E podemos continuar de onde quiser",
            "E tenho atenção total agora", "E posso acompanhar seu raciocínio",
            "E estou pronta para trabalhar", "E podemos explorar qualquer assunto",
        ),
        (
            "Pode mandar.", "O que está pegando por aí?", "Vamos nessa.",
            "Fique à vontade.", "Qual é o próximo passo?", "Estou ouvindo.",
            "Pode continuar.", "Me conta.", "Vamos resolver.", "Seu turno.",
        ),
    ),
    "thanks": (
        (
            "Por nada! ⭐", "Sempre às ordens. ⭐", "Imagina! ⭐", "Disponha. ⭐",
            "Fico feliz em ajudar. ⭐", "Tamo junto. ⭐", "Com prazer. ⭐",
            "Que bom que ajudou. ⭐", "Valeu você. ⭐", "Pode contar comigo. ⭐",
        ),
        (
            "Se isso resolveu, perfeito", "O importante é ter sido útil",
            "Gosto quando a resposta encaixa no que você precisava",
            "Bom saber que funcionou", "Seguimos melhorando",
            "A ideia é deixar tudo mais simples", "Fico contente que tenha servido",
            "Missão cumprida nessa parte", "Seguimos em frente", "Essa parte está resolvida",
        ),
        (
            "Quando quiser, seguimos.", "Pode mandar a próxima.", "Continuamos daqui.",
            "Vamos para o próximo ponto.", "Estou por aqui.", "Pode seguir.", "Bora.",
            "Sem problema.", "Próxima missão.", "É só chamar.",
        ),
    ),
    "casual": (
        (
            "Entendi. ⭐", "Faz sentido. ⭐", "Boa observação. ⭐",
            "Interessante você notar isso. ⭐", "Sim, peguei a ideia. ⭐",
            "Estou acompanhando. ⭐", "Certo, entendi o clima da conversa. ⭐",
            "Boa. ⭐", "Saquei. ⭐", "Percebi o ponto. ⭐",
        ),
        (
            "Esse tipo de detalhe muda bastante como a gente percebe o dia",
            "Pequenas coisas acabam dando o tom do momento", "O contexto faz diferença",
            "Dá para conversar sobre isso sem pressa",
            "Essas observações são ótimas para manter a conversa natural",
            "O jeito como o dia está influencia mesmo o ritmo",
            "É um bom ponto para puxar assunto", "Esse detalhe ajuda a situar o momento",
            "Dá para explorar isso por vários lados",
            "Esse tipo de comentário deixa a conversa mais humana",
        ),
        (
            "Querendo continuar, eu acompanho.", "Pode desenvolver.", "Estou com você.",
            "Manda mais.", "Seguimos daqui.", "Pode continuar a ideia.", "Vamos nessa.",
            "Estou ouvindo.", "Sem pressa.", "Pode falar.",
        ),
    ),
    "support": (
        (
            "Entendo. ⭐", "Parece um dia puxado. ⭐", "Isso soa cansativo. ⭐",
            "Dá para sentir que pesou. ⭐", "Imagino que tenha sido bastante coisa. ⭐",
            "Esse tipo de dia cobra energia. ⭐", "Faz sentido estar cansado depois disso. ⭐",
            "Parece que o ritmo foi intenso. ⭐", "É muita coisa para administrar de uma vez. ⭐",
            "Entendi o peso do momento. ⭐",
        ),
        (
            "Podemos organizar uma coisa de cada vez", "Posso ajudar a colocar as ideias em ordem",
            "Dá para reduzir isso a próximos passos pequenos",
            "Podemos separar o urgente do que pode esperar",
            "Posso te ajudar a destravar o primeiro passo",
            "Podemos transformar isso em uma lista simples",
            "Dá para escolher só uma prioridade agora", "Posso ajudar a simplificar a situação",
            "Podemos estruturar o que está sob seu controle",
            "Dá para tornar a próxima ação mais clara",
        ),
        (
            "Sem precisar resolver tudo de uma vez.", "Um passo útil já conta.",
            "Vamos pelo que é mais viável.", "Começamos pelo essencial.",
            "O resto pode vir depois.", "De forma prática.", "Sem complicar.",
            "Com foco no próximo passo.", "No seu ritmo.", "De maneira objetiva.",
        ),
    ),
    "farewell": (
        (
            "Até mais! ⭐", "Tchau! ⭐", "Até logo! ⭐", "Falou! ⭐", "Nos vemos depois. ⭐",
            "Até a próxima. ⭐", "Boa continuação por aí. ⭐", "Vou ficando por aqui. ⭐",
            "Até daqui a pouco. ⭐", "Fechou, até mais. ⭐",
        ),
        (
            "Foi bom conversar", "Quando voltar, continuamos",
            "A conversa fica por aqui por enquanto", "Estarei disponível quando precisar",
            "Pode voltar quando quiser", "Seguimos na próxima",
            "Fico pronta para quando você chamar", "Depois a gente retoma",
            "Quando quiser continuar, estou por aqui", "Encerramos essa parte por agora",
        ),
        (
            "Se cuida.", "Até a próxima conversa.", "Bom resto de dia.",
            "Boa noite quando chegar a hora.", "Nos falamos.", "Valeu pela conversa.",
            "Até breve.", "Tudo de bom por aí.", "Pode contar comigo depois.", "Fui. ⭐",
        ),
    ),
}


@lru_cache(maxsize=1)
def conversation_response_examples() -> tuple[str, ...]:
    responses: set[str] = set()
    for prefixes, cores, suffixes in _RESPONSE_FAMILIES.values():
        for prefix in prefixes:
            for core in cores:
                for suffix in suffixes:
                    responses.add(f"{prefix} {core}. {suffix}".replace("..", "."))
    return tuple(sorted(responses))


def conversation_response_count() -> int:
    return len(conversation_response_examples())


def _pick(parts: tuple[str, ...], seed: str, salt: str) -> str:
    digest = sha256(f"{salt}|{seed}".encode("utf-8")).digest()
    return parts[int.from_bytes(digest[:4], "big") % len(parts)]


def _compose(family: str, seed: str) -> str:
    prefixes, cores, suffixes = _RESPONSE_FAMILIES[family]
    return (
        f"{_pick(prefixes, seed, family + ':p')} "
        f"{_pick(cores, seed, family + ':c')}. "
        f"{_pick(suffixes, seed, family + ':s')}"
    ).replace("..", ".")


def _has_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


# Evite gatilhos genéricos como apenas "tempo", "clima" ou "dia está".
# Eles gerariam falsos positivos em frases como "não tenho tempo" ou
# "meu dia está difícil". Os padrões abaixo exigem contexto meteorológico.
WEATHER_HINTS = (
    "como esta o tempo", "como ta o tempo", "tempo hoje", "tempo agora",
    "previsao do tempo", "como esta o clima", "como ta o clima", "qual o clima",
    "clima hoje", "clima agora", "qual a temperatura", "temperatura agora",
    "esta chov", "ta chov", "dia chuv", "dia esta chuv", "dia ta chuv",
    "tempo chuv", "garoa", "chuva hoje",
    "esta frio", "ta frio", "que frio", "frio hoje", "esta gelad", "ta gelad",
    "esta calor", "ta calor", "que calor", "calor hoje", "esta quente", "ta quente",
    "nublad", "ensolarad", "sol hoje", "dia bonito", "dia esta bonito",
    "dia ta bonito", "dia lindo", "dia esta lindo", "dia ta lindo",
    "tempo bonito", "tempo feio",
)

GREETING_PHRASES = (
    "oi", "ola", "oie", "e ai", "bom dia", "boa tarde", "boa noite", "salve",
    "fala star", "hello", "hey",
)
WELLBEING_PHRASES = (
    "tudo bem", "como voce esta", "como voce ta", "como vai",
    "ta tudo bem com voce", "esta bem",
)
THANKS_PHRASES = ("obrigado", "obrigada", "valeu", "agradeco", "brigado", "vlw")
FAREWELL_PHRASES = (
    "tchau", "ate logo", "ate mais", "falou", "boa noite star", "bye", "ate depois",
)
SUPPORT_PHRASES = (
    "estou cansado", "to cansado", "estou cansada", "to cansada", "dia puxado",
    "dia dificil", "dia foi dificil", "muita coisa hoje", "estou sobrecarregado",
    "estou sobrecarregada",
)


class ConversationEngine:
    def __init__(self, weather: WeatherService | None = None):
        self.weather = weather or WeatherService()

    def respond(self, text: str, *, user_name: str | None = None) -> str | None:
        normalized = normalize_conversation_text(text)
        if not normalized:
            return None
        plain = normalized.translate(str.maketrans("", "", "?!,."))

        # Apoio cotidiano precede clima para evitar que "dia difícil" seja
        # interpretado como meteorologia; clima explícito ainda é reconhecido.
        if _has_any(plain, SUPPORT_PHRASES):
            return _compose("support", plain)

        if _has_any(plain, WEATHER_HINTS):
            return self._weather_response(plain)

        if plain in GREETING_PHRASES or any(plain.startswith(item + " ") for item in GREETING_PHRASES):
            response = _compose("greeting", plain)
            return f"{response} {user_name}, estou por aqui." if user_name else response

        if _has_any(plain, WELLBEING_PHRASES):
            return _compose("wellbeing", plain)
        if _has_any(plain, THANKS_PHRASES):
            return _compose("thanks", plain)
        if plain in FAREWELL_PHRASES or any(plain.startswith(item + " ") for item in FAREWELL_PHRASES):
            return _compose("farewell", plain)

        if any(
            plain.startswith(prefix)
            for prefix in (
                "hoje foi", "meu dia", "que dia", "estou de boa", "to de boa",
                "estou tranquilo", "estou tranquila", "que loucura",
            )
        ):
            return _compose("casual", plain)
        return None

    def _weather_response(self, text: str) -> str:
        snapshot = self.weather.current()
        if snapshot is None:
            return (
                "Eu percebi que você está falando do clima, mas não consegui confirmar "
                "as condições atuais agora. Prefiro não inventar se está frio, quente "
                "ou chovendo. ⭐"
            )

        if _has_any(
            text,
            (
                "como esta o tempo", "como ta o tempo", "qual o clima", "previsao do tempo",
                "tempo agora", "clima agora", "qual a temperatura", "temperatura agora",
            ),
        ):
            return format_weather(snapshot)

        if _has_any(text, ("frio", "gelad")):
            return self._temperature_claim(snapshot, expected="cold")
        if _has_any(text, ("calor", "quente")):
            return self._temperature_claim(snapshot, expected="hot")

        if _has_any(text, ("chov", "chuv", "garoa", "chuva hoje")):
            if snapshot.rainy:
                return (
                    f"Está mesmo com {weather_description(snapshot.weather_code)} em {snapshot.location}: "
                    f"{snapshot.temperature_c:.0f} °C agora e {snapshot.precipitation_mm:.1f} mm "
                    "de precipitação no dado atual. ☔"
                )
            return (
                f"Pelo clima atual em {snapshot.location}, não está chovendo agora: "
                f"{snapshot.temperature_c:.0f} °C e {weather_description(snapshot.weather_code)}. "
                "Então eu não confirmaria que o dia está chuvoso neste momento. ⭐"
            )

        if "nublad" in text:
            if snapshot.cloud_cover_pct >= 70 or snapshot.weather_code == 3:
                return (
                    f"Sim, está bem nublado em {snapshot.location}: cobertura de nuvens em torno de "
                    f"{snapshot.cloud_cover_pct}% e {snapshot.temperature_c:.0f} °C agora."
                )
            return (
                f"Na leitura atual de {snapshot.location}, a cobertura de nuvens está em torno de "
                f"{snapshot.cloud_cover_pct}% e a condição é {weather_description(snapshot.weather_code)}."
            )

        if _has_any(text, ("ensolarad", "sol hoje")):
            if snapshot.clear_or_partly_cloudy and snapshot.cloud_cover_pct < 60:
                return (
                    f"Tem razão: o tempo está {weather_description(snapshot.weather_code)} em "
                    f"{snapshot.location}, com {snapshot.temperature_c:.0f} °C agora. ☀️"
                )
            return (
                f"Por aí o dado atual mostra {weather_description(snapshot.weather_code)}, "
                f"{snapshot.cloud_cover_pct}% de nuvens e {snapshot.temperature_c:.0f} °C. "
                "Então eu teria cuidado em chamar de ensolarado agora."
            )

        if _has_any(
            text,
            (
                "dia bonito", "dia esta bonito", "dia ta bonito", "dia lindo",
                "dia esta lindo", "dia ta lindo", "tempo bonito",
            ),
        ):
            if snapshot.clear_or_partly_cloudy and not snapshot.rainy:
                return (
                    f"Está com cara de dia bonito mesmo: {weather_description(snapshot.weather_code)} "
                    f"em {snapshot.location} e {snapshot.temperature_c:.0f} °C agora. ⭐"
                )
            return (
                f"Entendo a sensação, mas o clima atual em {snapshot.location} está com "
                f"{weather_description(snapshot.weather_code)} e {snapshot.temperature_c:.0f} °C. "
                "Então prefiro descrever o que os dados mostram em vez de fingir que está aberto."
            )

        if "tempo feio" in text:
            return (
                f"Agora em {snapshot.location} está {weather_description(snapshot.weather_code)}, "
                f"com {snapshot.temperature_c:.0f} °C. Se isso é 'feio' ou não é mais gosto pessoal; "
                "a condição objetiva é essa. ⭐"
            )
        return format_weather(snapshot)

    @staticmethod
    def _temperature_claim(snapshot: WeatherSnapshot, *, expected: str) -> str:
        temp = snapshot.temperature_c
        feels = snapshot.feels_like_c
        if expected == "cold":
            if temp <= 15:
                return (
                    f"Está frio mesmo em {snapshot.location}: {temp:.0f} °C, "
                    f"sensação de {feels:.0f} °C e {weather_description(snapshot.weather_code)}. 🧥"
                )
            if temp >= 26:
                return (
                    f"Na verdade, os dados atuais apontam calor em {snapshot.location}: "
                    f"{temp:.0f} °C, sensação de {feels:.0f} °C. Então eu não diria que está frio. ☀️"
                )
            return (
                f"Está mais para ameno/fresco do que frio em {snapshot.location}: "
                f"{temp:.0f} °C e sensação de {feels:.0f} °C."
            )

        if temp >= 26:
            return (
                f"Está quente mesmo em {snapshot.location}: {temp:.0f} °C, "
                f"sensação de {feels:.0f} °C e {weather_description(snapshot.weather_code)}. ☀️"
            )
        if temp <= 15:
            return (
                f"Os dados atuais apontam o contrário em {snapshot.location}: "
                f"{temp:.0f} °C e sensação de {feels:.0f} °C. Então eu não chamaria de calor agora. 🧥"
            )
        return (
            f"Está mais para ameno em {snapshot.location}: {temp:.0f} °C "
            f"e sensação de {feels:.0f} °C."
        )
