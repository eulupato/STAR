from pathlib import Path

path = Path('core/social_cognition.py')
text = path.read_text(encoding='utf-8')
old = 'SocialCognitionBranch("relationships_context", "relationship_history", "Histórico de relação", _subs("interações;confiança;conflito;cooperação;mudança;memória social"))'
new = 'SocialCognitionBranch("relationships_context", "relationship_history", "Histórico de relações", _subs("relações;interações;confiança;conflito;cooperação;mudança;memória social"))'
if old not in text:
    raise SystemExit('B16 relationship history marker not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
