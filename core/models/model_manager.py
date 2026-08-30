import time

from config import EXTERNAL_AI_ENABLED


class ModelManager:
    """Gerencia modelos sem permitir uso acidental durante o modo offline."""

    def __init__(self, local_model=None, enabled=None):
        self.local_model = local_model
        self.models = {}
        self.enabled = EXTERNAL_AI_ENABLED if enabled is None else bool(enabled)
        if local_model:
            self.register_model(local_model.model_name, local_model)

    def register_model(self, name, model):
        self.models[name] = model

    def get_model(self, name):
        return self.models.get(name)

    def select_model(self, route=None):
        if not self.enabled:
            raise RuntimeError("IA externa está desativada no modo offline.")
        if self.local_model is None:
            raise RuntimeError("Nenhum modelo foi configurado.")
        return self.local_model

    def generate(self, prompt, identity, state=None, route=None):
        if not self.enabled:
            raise RuntimeError("Geração externa bloqueada: STAR está em modo offline.")
        start = time.perf_counter()
        model = self.select_model(route)
        print(f"\n🤖 MODELO SELECIONADO: {model.model_name}")
        print(f"   Seleção: {time.perf_counter() - start:.3f}s")
        generation_start = time.perf_counter()
        result = model.generate(prompt=prompt, identity=identity, state=state, route=route)
        print(f"   Geração: {time.perf_counter() - generation_start:.3f}s")
        return result
