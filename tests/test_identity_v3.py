from core.star_identity import StarIdentity


def test_star_identity_contract():
    identity = StarIdentity()

    assert identity.get_name() == "STAR"
    assert identity.get_full_name() == "System for Thought, Analysis and Response"
    assert identity.get_creator() == "Lu"
    assert identity.is_creator("Lu") is True
    assert identity.is_creator("João") is False

    principles = identity.get_principles()
    assert principles
    assert any("Eu sou a STAR" in item for item in principles)
    assert any("modelos" in item.lower() for item in principles)
