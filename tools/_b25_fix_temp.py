from pathlib import Path
p=Path('core/multimodal_perception.py')
s=p.read_text(encoding='utf-8')
old='''def _unique(values: Iterable[Any], *, limit: int = 64) -> tuple[str, ...]:\n    out: list[str] = []\n    for value in values:\n'''
new='''def _unique(values: Iterable[Any], *, limit: int = 64) -> tuple[str, ...]:\n    if isinstance(values, (str, bytes)):\n        values = (values,)\n    out: list[str] = []\n    for value in values:\n'''
if old not in s: raise SystemExit('unique marker missing')
s=s.replace(old,new,1)
old='''                "entities": entities,\n                "metadata": deepcopy(fusion),\n            })\n'''
new='''                "entities": entities,\n                "sensor_fusion": True,\n                "metadata": deepcopy(fusion),\n            })\n'''
if old not in s: raise SystemExit('fusion candidate marker missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
