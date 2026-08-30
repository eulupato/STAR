# STAR V1.6 — Conversa e identidade virtual

## Implementado
- conhecimento pessoal offline expandido para 48 intenções;
- mínimo de 20 formas de perguntar e 20 respostas por intenção;
- respostas com tom mais humano, curioso e entusiasmado;
- correção do clique do menu: coordenadas do evento agora são locais à imagem;
- navegação não força restauração de janela maximizada;
- IA externa continua desligada;
- arquitetura de Skills e Tools preparada;
- camada de voz separada em STT/TTS, sem dependência pesada instalada;
- testes de regressão V1.6.

## Referências arquiteturais
A V1.6 aproveita ideias de arquitetura modular observadas em projetos locais de assistentes e agentes: separação de entrada/saída de voz, orquestração, registro de skills e ferramentas. O código da STAR não incorpora os projetos completos nem os torna dependências.

## Execução
No Windows, a partir da pasta STAR:
` .\.venv\Scripts\python.exe .\main.py `

Teste:
` .\.venv\Scripts\python.exe .\tests\test_star_v16.py `
