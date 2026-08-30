"""Ações locais da STAR V1.9: aplicativos, navegador e busca de arquivos."""
from pathlib import Path
import os, subprocess, webbrowser, urllib.parse
APPS={"google":None,"chrome":None,"spotify":None,"explorador":"explorer"}

def open_app(name):
 n=name.lower().strip()
 if n in ("google","chrome"):
  webbrowser.open("https://www.google.com"); return "Abri o Google."
 if n=="spotify":
  try: os.startfile("spotify:"); return "Abri o Spotify."
  except Exception: webbrowser.open("https://open.spotify.com"); return "Abri o Spotify no navegador."
 if n in APPS and APPS[n]: subprocess.Popen(APPS[n]); return f"Abri {name}."
 raise ValueError(f"Ainda não tenho um atalho configurado para {name}.")

def web_search(query):
 webbrowser.open("https://www.google.com/search?q="+urllib.parse.quote_plus(query)); return f"Pesquisando por: {query}."

def spotify_search(query):
 webbrowser.open("https://open.spotify.com/search/"+urllib.parse.quote(query)); return f"Procurei {query} no Spotify."

def find_files(query, root=None, limit=20):
 root=Path(root or Path.home()); q=query.lower(); hits=[]
 try:
  for p in root.rglob("*"):
   if q in p.name.lower(): hits.append(str(p))
   if len(hits)>=limit: break
 except (PermissionError,OSError): pass
 return hits

def parse(text):
 s=text.lower().strip()
 if "spotify" in s:
  q=s.split("spotify",1)[1].strip()
  for prefix in ("e toca","e toque","toca","toque","procura","pesquisa"): q=q.replace(prefix,"",1).strip()
  return spotify_search(q) if q else open_app("spotify")
 if ("abre" in s or "abrir" in s) and ("google" in s or "chrome" in s):
  if "resultado" in s or "pesquisa" in s or "veja" in s:
   q=s
   for x in ("star,","star","abre pra mim o google e veja","abre o google e veja","abre o google e pesquise","abre pra mim o google e pesquise"): q=q.replace(x,"")
   return open_app("google")+" "+web_search(q.strip(" !,."))
  return open_app("google")
 if s.startswith(("pesquise ","pesquisa ","procure ","procura ")):
  return web_search(s.split(" ",1)[1])
 if "procure arquivo" in s or "procurar arquivo" in s:
  q=s.split("arquivo",1)[1].strip(); hits=find_files(q)
  return "Encontrei: "+", ".join(hits) if hits else "Não encontrei arquivos com esse nome."
 return None
