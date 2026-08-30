from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from main import create_star
s=create_star()
assert '4' in s.process('quanto é 2+2')
assert s.packs.list()
print('STAR V1.7: testes essenciais OK')
