"""Knowledge Packs V1.8: packs reais, portáteis e offline."""
from pathlib import Path
import json
class KnowledgePackManager:
    def __init__(self, root):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True); self.packs={}; self.scan()
    def scan(self):
        self.packs={}
        for manifest in self.root.rglob('manifest.json'):
            try:
                data=json.loads(manifest.read_text(encoding='utf-8'))
                name=data.get('id') or data.get('name') or manifest.parent.name
                self.packs[name]={"manifest":data,"path":str(manifest.parent),"available":True}
            except Exception: pass
        return self.packs
    def list(self): return self.packs
