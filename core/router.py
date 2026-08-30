class Router:
    """Roteador cognitivo local: primeiro identifica intenção conhecida."""
    def __init__(self, internal_knowledge=None): self.internal_knowledge=internal_knowledge
    def route(self, request):
        text=str(request.get("input", "")).strip()
        response_type=self.internal_knowledge.detect(text) if self.internal_knowledge else None
        internal=response_type is not None
        nuclei=["linguistic"]
        normalized=self.internal_knowledge._norm(text) if False else text.lower()
        if response_type in {"brain","nuclei","core","how_work","systems","modules","decisions"}: nuclei.append("executive")
        if response_type in {"memory","remember_me","forget","memory_storage"}: nuclei.append("memory")
        if response_type in {"errors","unknown","admit_unknown","autonomy"}: nuclei.append("safety")
        return {"nuclei":list(dict.fromkeys(nuclei)),"tools":[],"model_required":False,"internal_response":internal,"response_type":response_type,"priority":"high" if internal else "normal","depth":"basic" if internal else "standard"}
