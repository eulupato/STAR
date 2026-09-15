class Router:
    """Roteador cognitivo local: identifica intenção e custo cognitivo necessário."""

    def __init__(self, internal_knowledge=None, cognitive_integration=None):
        self.internal_knowledge = internal_knowledge
        self.cognitive_integration = cognitive_integration

    def route(self, request):
        text = str(request.get("input", "")).strip()
        response_type = self.internal_knowledge.detect(text) if self.internal_knowledge else None
        internal = response_type is not None
        nuclei = ["linguistic"]

        if response_type in {"brain", "nuclei", "core", "how_work", "systems", "modules", "decisions"}:
            nuclei.append("executive")
        if response_type in {"memory", "remember_me", "forget", "memory_storage"}:
            nuclei.append("memory")
        if response_type in {"errors", "unknown", "admit_unknown", "autonomy"}:
            nuclei.append("safety")

        if self.cognitive_integration is not None:
            cognitive_path = self.cognitive_integration.select_path(
                text,
                internal_response=internal,
            )
        else:
            cognitive_path = "FAST" if internal or len(text.split()) <= 8 else "DELIBERATIVE"

        if cognitive_path == "DELIBERATIVE":
            nuclei.extend(["memory", "salience", "analytical", "executive"])

        return {
            "nuclei": list(dict.fromkeys(nuclei)),
            "tools": [],
            "model_required": False,
            "internal_response": internal,
            "response_type": response_type,
            "priority": "high" if internal else "normal",
            "depth": "basic" if cognitive_path == "FAST" else "deliberative",
            "cognitive_path": cognitive_path,
        }
