import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from main import create_star


def test_internal_knowledge_and_routing():
    star=create_star()
    k=star.internal_knowledge
    stats=k.stats()
    assert len(stats)>=40, len(stats)
    # Perguntas continuam variadas, mas respostas não são mais infladas por
    # prefixos/sufixos artificiais. Cada intenção mantém apenas falas autorais.
    assert all(v["questions"]>=20 and v["responses"]>=1 for v in stats.values())

    cases={
        "olá":"greeting",
        "qual o seu nome?":"name",
        "quem criou você?":"creator",
        "o que é seu Core?":"core",
        "como funciona seu cérebro?":"brain",
        "o que é a Cura?":"cure",
        "você funciona offline?":"offline",
        "você é o Qwen?":"model_identity",
        "como você está?":"wellbeing",
    }
    for text,expected in cases.items():
        route=star.router.route({"input":text})
        assert route["response_type"]==expected,(text,route)
        answer=star.process(text)
        assert answer,(text,answer)

    samples={k.answer("olá") for _ in range(30)}
    assert len(samples)>=2


def test_short_conversation_cues_do_not_trigger_unrelated_explanations():
    from core.internal_knowledge import StarInternalKnowledge

    knowledge = StarInternalKnowledge()
    expected = {
        "hum": "acknowledgement",
        "hmm": "acknowledgement",
        "star": "attention",
        "lu": "creator_reference",
        "quem é lu?": "creator_identity",
    }
    for text, intent in expected.items():
        assert knowledge.detect(text) == intent

    banned = (
        "Olha:", "Resumindo,", "De forma simples,",
        "Posso explicar assim:", "Sendo bem direta,",
        "Hehe.", "Haha.", "pelo menos por enquanto",
    )
    for data in knowledge.intents.values():
        for response in data["responses"]:
            assert not any(marker in response for marker in banned)



def test_example_dialogue_stays_short_contextual_and_without_tics():
    star = create_star()
    exchanges = (
        ("ola", ("Olha:", "Resumindo,", "De forma simples,", "Sendo bem direta,")),
        ("o que voce pode fazer?", ("Hehe", "pelo menos por enquanto")),
        ("quem e voce?", ("Olha:", "Resumindo,")),
        ("star", ("Eu sou a STAR", "Meu funcionamento")),
        ("hum", ("Meu funcionamento", "entidade sintética")),
        ("quem criou voce?", ("pelo menos por enquanto",)),
        ("quem e lu?", ("Fui criada",)),
        ("lu", ("Fui criada",)),
    )
    for text, banned in exchanges:
        answer = str(star.process(text))
        assert answer
        assert not any(marker in answer for marker in banned), (text, answer)

    assert "STAR" in str(star.process("qual o seu nome?"))
    meaning = str(star.process("o isso significa?"))
    assert "System for Thought, Analysis and Response" in meaning or "sigla" in meaning
