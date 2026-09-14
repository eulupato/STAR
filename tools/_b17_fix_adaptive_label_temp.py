from pathlib import Path
path = Path('core/affective_personality.py')
text = path.read_text(encoding='utf-8')
old = 'PersonalityBranch("adaptive_personality", "adaptive_baselines", "Baselines adaptativos", _subs("baseline;ajuste pequeno;histórico;persistência;rollback"))'
new = 'PersonalityBranch("adaptive_personality", "adaptive_baselines", "Baselines da personalidade adaptativa", _subs("personalidade adaptativa;baseline;ajuste pequeno;histórico;persistência;rollback"))'
if old not in text:
    raise SystemExit('B17 adaptive label marker not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
