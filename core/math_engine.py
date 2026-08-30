"""Matemática determinística da STAR V1.9."""
import ast, math, operator, re, unicodedata
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.FloorDiv:operator.floordiv,ast.Pow:operator.pow,ast.Mod:operator.mod,ast.USub:operator.neg,ast.UAdd:operator.pos}
ONES={"zero":0,"um":1,"uma":1,"dois":2,"duas":2,"tres":3,"quatro":4,"cinco":5,"seis":6,"sete":7,"oito":8,"nove":9,"dez":10,"onze":11,"doze":12,"treze":13,"quatorze":14,"quinze":15,"dezesseis":16,"dezessete":17,"dezoito":18,"dezenove":19}
TENS={"vinte":20,"trinta":30,"quarenta":40,"cinquenta":50,"sessenta":60,"setenta":70,"oitenta":80,"noventa":90,"cem":100,"cento":100}

def norm(s):
 s=unicodedata.normalize("NFD",str(s).lower()); return "".join(c for c in s if unicodedata.category(c)!="Mn")

def words_number(tokens):
 total=0; found=False
 for t in tokens:
  if t in ONES: total+=ONES[t]; found=True
  elif t in TENS: total+=TENS[t]; found=True
  elif t=="e": continue
  else: return None
 return total if found else None

def spoken_to_expression(text):
 s=norm(text).replace(",",".")
 s=re.sub(r"^(quanto e|calcule|calcula|resolve|resolva|me diga|qual e o resultado de)\s+","",s).strip()
 m=re.search(r"raiz quadrada de\s+(.+)",s)
 if m:
  n=words_number(re.findall(r"[a-z]+",m.group(1))) or m.group(1).strip()
  return f"sqrt({n})"
 m=re.search(r"(metade|dobro|triplo) de\s+(.+)",s)
 if m:
  n=words_number(re.findall(r"[a-z]+",m.group(2))) or m.group(2).strip()
  return {"metade":f"({n})/2","dobro":f"({n})*2","triplo":f"({n})*3"}[m.group(1)]
 parts=re.split(r"\s+(mais|menos|vezes|vez|multiplicado por|dividido por|dividido|sobre)\s+",s)
 if len(parts)>=3:
  out=[]
  for i,p in enumerate(parts):
   if i%2==1: out.append({"mais":"+","menos":"-","vezes":"*","vez":"*","multiplicado por":"*","dividido por":"/","dividido":"/","sobre":"/"}[p])
   else:
    p=p.strip()
    if re.fullmatch(r"\d+(\.\d+)?",p): out.append(p)
    else:
     n=words_number(re.findall(r"[a-z]+",p))
     if n is None:return None
     out.append(str(n))
  return "".join(out)
 m=re.search(r"(-?\d+(?:\.\d+)?(?:\s*[+\-*/%^]\s*-?\d+(?:\.\d+)?)+)",s)
 return m.group(1).replace(" ","") if m else None

def calculate(expr):
 expr=expr.replace("^","**").replace("×","*").replace("÷","/")
 if expr.startswith("sqrt(") and expr.endswith(")"): return math.sqrt(float(expr[5:-1]))
 tree=ast.parse(expr,mode="eval")
 def ev(n):
  if isinstance(n,ast.Expression): return ev(n.body)
  if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return n.value
  if isinstance(n,ast.UnaryOp) and type(n.op) in OPS:return OPS[type(n.op)](ev(n.operand))
  if isinstance(n,ast.BinOp) and type(n.op) in OPS:return OPS[type(n.op)](ev(n.left),ev(n.right))
  raise ValueError("Expressão não permitida")
 return ev(tree)

def solve_text(text):
 expr=spoken_to_expression(text)
 if not expr:return None
 return expr,calculate(expr)
