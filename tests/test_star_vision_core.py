from core.star_core import StarCore


class DummyRouter:
    def route(self, request):
        return {"response_type": "local"}


class DummyExecutive:
    def execute(self, request, route):
        return "fallback"


class DummyState:
    data = {}


def make_star():
    return StarCore(DummyRouter(), DummyExecutive(), DummyState())


def test_star_core_routes_vision_status_before_generic_router():
    star = make_star()
    response = star.process("STAR, status do star vision")
    assert "STAR Vision Portal V1" in response
    assert star.last_intent == "vision"


def test_star_core_remote_watch_cannot_start_pc_camera():
    star = make_star()
    response = star.process("STAR, abra o portal visual", allow_actions=False)
    assert "não podem ativar remotamente" in response.lower()
    assert star.last_intent == "vision"


def test_star_core_lists_filters_without_optional_cv_dependencies():
    star = make_star()
    response = star.process("quais filtros do portal")
    assert "12 filtros" in response
    assert "Hologram" in response
