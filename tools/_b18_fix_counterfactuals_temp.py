from pathlib import Path
p=Path('core/reasoning_simulation.py')
t=p.read_text(encoding='utf-8')
old='("what_if", "Raciocínio e se", "e se;hipótese;alternativa;consequência;incerteza")'
new='("what_if", "Raciocínio e se / contrafactuais", "contrafactuais;e se;hipótese;alternativa;consequência;incerteza")'
if old not in t: raise SystemExit('B18 counterfactual marker missing')
p.write_text(t.replace(old,new,1),encoding='utf-8')
