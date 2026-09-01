import random
from datetime import datetime

from core.conversation import ConversationVariationEngine


def test_greeting_and_status_have_more_than_1000_combinations():
    engine = ConversationVariationEngine(rng=random.Random(7))
    assert engine.variation_space("greeting") >= 1000
    assert engine.variation_space("greeting", "morning") >= 1000
    assert engine.variation_space("status") >= 1000


def test_equivalent_greetings_are_recognized():
    engine = ConversationVariationEngine(rng=random.Random(2))
    for text in ("olá", "oi", "eai", "e aí", "opa", "bom dia", "boa tarde", "boa noite"):
        response = engine.generate(text, now=datetime(2026, 8, 31, 9, 0))
        assert isinstance(response, str)
        assert response.strip()


def test_status_variants_are_recognized():
    engine = ConversationVariationEngine(rng=random.Random(3))
    for text in ("tudo bem?", "como vai?", "como está?", "tudo certo?", "beleza?"):
        assert engine.generate(text)


def test_recent_responses_are_not_repeated_immediately():
    engine = ConversationVariationEngine(rng=random.Random(11), recent_limit=30)
    responses = [
        engine.generate("oi", now=datetime(2026, 8, 31, 9, 0))
        for _ in range(15)
    ]
    assert len(set(responses)) == len(responses)


def test_wrong_daypart_does_not_force_incoherent_opening():
    engine = ConversationVariationEngine(rng=random.Random(1))
    response = engine.generate("boa noite", now=datetime(2026, 8, 31, 9, 0))
    assert not response.lower().startswith("boa noite")
