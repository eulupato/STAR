from pathlib import Path

path = Path('core/internal_models.py')
text = path.read_text(encoding='utf-8')
old = '            "self": self_snapshot,\n'
new = '            "self_state": self_snapshot,\n'
if old not in text:
    raise SystemExit('B15 context key marker not found')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
