"""Ferramentas locais da STAR V1.8."""
import ast, operator, re, math

class ToolRegistry:
    def __init__(self): self._tools={}
    def register(self,name,func,enabled=True,description=""):
        self._tools[name]={"func":func,"enabled":bool(enabled),"description":description}
    def available(self): return [n for n,v in self._tools.items() if v["enabled"]]
    def call(self,name,*args,**kwargs):
        if name not in self._tools or not self._tools[name]["enabled"]: raise RuntimeError(f"Ferramenta indisponível: {name}")
        return self._tools[name]["func"](*args,**kwargs)

_ALLOWED={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.FloorDiv:operator.floordiv,ast.Pow:operator.pow,ast.USub:operator.neg,ast.UAdd:operator.pos,ast.Mod:operator.mod}
def safe_math(expr):
    expr=str(expr).replace('×','*').replace('÷','/').replace('^','**')
    tree=ast.parse(expr,mode='eval')
    def ev(n):
        if isinstance(n,ast.Expression): return ev(n.body)
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return n.value
        if isinstance(n,ast.BinOp) and type(n.op) in _ALLOWED: return _ALLOWED[type(n.op)](ev(n.left),ev(n.right))
        if isinstance(n,ast.UnaryOp) and type(n.op) in _ALLOWED: return _ALLOWED[type(n.op)](ev(n.operand))
        raise ValueError('Expressão não permitida')
    return ev(tree)

NUM={"zero":0,"um":1,"uma":1,"dois":2,"duas":2,"tres":3,"quatro":4,"cinco":5,"seis":6,"sete":7,"oito":8,"nove":9,"dez":10,"onze":11,"doze":12,"treze":13,"quatorze":14,"quinze":15,"dezesseis":16,"dezessete":17,"dezoito":18,"dezenove":19,"vinte":20,"trinta":30,"quarenta":40,"cinquenta":50,"sessenta":60,"setenta":70,"oitenta":80,"noventa":90,"cem":100,"cento":100}
def _num_phrase(words):
    total=0; current=0; found=False
    for w in words:
        if w in NUM: current+=NUM[w]; found=True
        elif w=="e": continue
        else: return None
    return current if found else None

def extract_math(text):
    raw=str(text).lower().replace(',','.').replace('á','a').replace('ã','a').replace('ç','c').replace('é','e')
    raw=raw.replace('×','*').replace('x','*').replace('÷','/')
    raw=re.sub(r'\bquanto e\b|\bcalcule\b|\bcalcula\b|\bresolve\b|\bresolva\b|\bme diga\b','',raw).strip()
    # raiz quadrada de N
    m=re.search(r'raiz quadrada (?:de|do|da)?\s*(\d+(?:\.\d+)?)',raw)
    if m: return f'sqrt({m.group(1)})'
    # metade de N
    m=re.search(r'metade (?:de|do|da)?\s*(\d+(?:\.\d+)?)',raw)
    if m: return f'({m.group(1)})/2'
    # números escritos simples: "dois menos um", "três vezes quatro"
    tokens=re.findall(r'[a-z]+|\d+(?:\.\d+)?|[+\-*/()^]',raw)
    opmap={"mais":"+","menos":"-","vezes":"*","vez":"*","multiplicado":"*","dividido":"/","sobre":"/"}
    if any(t in opmap for t in tokens):
        out=[]; buf=[]
        for t in tokens+["|"]:
            if t in opmap or t=="|":
                if buf:
                    n=_num_phrase(buf)
                    if n is None:
                        phrase=' '.join(buf)
                        if re.fullmatch(r'\d+(?:\.\d+)?',phrase): n=phrase
                        else: return None
                    out.append(str(n)); buf=[]
                if t!="|": out.append(opmap[t])
            elif re.fullmatch(r'\d+(?:\.\d+)?',t):
                if buf: return None
                buf=[t]
            elif t in NUM or t=="e": buf.append(t)
        expr=''.join(out)
        if re.search(r'\d',expr) and re.search(r'[+*/-]',expr): return expr
    # expressão simbólica explícita
    m=re.search(r'(-?\d+(?:\.\d+)?(?:\s*[+\-*/%^]\s*-?\d+(?:\.\d+)?)+)',raw)
    return m.group(1).replace(' ','') if m else None

def calculate_expression(expr):
    if expr.startswith('sqrt(') and expr.endswith(')'):
        return math.sqrt(float(expr[5:-1]))
    return safe_math(expr)
