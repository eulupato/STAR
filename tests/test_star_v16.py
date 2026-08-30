import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from main import create_star

def run_tests():
    star=create_star(); k=star.internal_knowledge
    stats=k.stats(); assert len(stats)>=40, len(stats)
    assert all(v["questions"]>=20 and v["responses"]>=20 for v in stats.values())
    cases={"olá":"greeting","qual o seu nome?":"name","quem criou você?":"creator","o que é seu Core?":"core","como funciona seu cérebro?":"brain","o que é a Cura?":"cure","você funciona offline?":"offline","você é o Qwen?":"model_identity","como você está?":"wellbeing"}
    for text,expected in cases.items():
        route=star.router.route({"input":text}); assert route["response_type"]==expected,(text,route)
        answer=star.process(text); assert answer and "não tenho esse conhecimento" not in answer,(text,answer)
    # Respostas devem variar ao longo de múltiplas chamadas.
    samples={k.answer("olá") for _ in range(30)}; assert len(samples)>=2
    print(f"OK — {len(stats)} intenções, variações mínimas: 20 perguntas + 20 respostas por intenção.")
if __name__=="__main__": run_tests()
