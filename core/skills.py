from dataclasses import dataclass, asdict
@dataclass
class Skill:
    name:str; description:str; enabled:bool=True; requires_confirmation:bool=False
class SkillRegistry:
    def __init__(self):
        self.skills={}
        for x in [Skill('conversation','Conversa e identidade local'),Skill('knowledge_lookup','Consulta conhecimento e packs'),Skill('math','Cálculo determinístico offline'),Skill('knowledge_packs','Detecta packs de conhecimento')]: self.register(x)
    def register(self,s): self.skills[s.name]=s
    def list(self): return {k:asdict(v) for k,v in self.skills.items()}
