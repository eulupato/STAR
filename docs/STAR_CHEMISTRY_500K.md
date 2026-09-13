# STAR Chemistry 500K

## Contrato

A STAR possui 500 tópicos canônicos de Química. Cada tópico gera 1.000 variações determinísticas: 10 famílias de conteúdo × 10 estilos × 10 contextos. Total exato: **500.000 conteúdos endereçáveis**, `CHEM-000001..CHEM-500000`.

A materialização é sob demanda: a STAR não cria meio milhão de objetos durante o startup. Os 500.000 itens são variações auditáveis de 500 núcleos científicos, e não 500.000 fatos independentes.

## Famílias de conteúdo

`conceito`, `formula`, `variaveis_unidades`, `hipoteses_validade`, `derivacao`, `calculo`, `aplicacao`, `erros_comuns`, `limites`, `conexoes`.

A família `calculo` fornece a rota de resolução, fórmulas, unidades, estequiometria/balanços e verificações. Ela não é apresentada como um solver simbólico/numerário universal de Química.

## 20 domínios — 25 tópicos cada

1. Fundamentos e medição — tópicos 1–25 — `CHEM-000001..CHEM-025000`
2. Estrutura atômica e periodicidade — 26–50 — `CHEM-025001..CHEM-050000`
3. Ligações e estrutura molecular — 51–75 — `CHEM-050001..CHEM-075000`
4. Estequiometria e reações — 76–100 — `CHEM-075001..CHEM-100000`
5. Estados da matéria e soluções — 101–125 — `CHEM-100001..CHEM-125000`
6. Termoquímica e termodinâmica — 126–150 — `CHEM-125001..CHEM-150000`
7. Equilíbrio químico — 151–175 — `CHEM-150001..CHEM-175000`
8. Ácido–base e solubilidade — 176–200 — `CHEM-175001..CHEM-200000`
9. Cinética química — 201–225 — `CHEM-200001..CHEM-225000`
10. Eletroquímica — 226–250 — `CHEM-225001..CHEM-250000`
11. Química analítica — 251–275 — `CHEM-250001..CHEM-275000`
12. Espectroscopia e métodos — 276–300 — `CHEM-275001..CHEM-300000`
13. Orgânica: fundamentos — 301–325 — `CHEM-300001..CHEM-325000`
14. Orgânica: reações e síntese — 326–350 — `CHEM-325001..CHEM-350000`
15. Inorgânica e coordenação — 351–375 — `CHEM-350001..CHEM-375000`
16. Organometálica e catálise — 376–400 — `CHEM-375001..CHEM-400000`
17. Química quântica e computacional — 401–425 — `CHEM-400001..CHEM-425000`
18. Materiais, polímeros e superfícies — 426–450 — `CHEM-425001..CHEM-450000`
19. Bioquímica e química biológica — 451–475 — `CHEM-450001..CHEM-475000`
20. Nuclear, ambiental e aplicada — 476–500 — `CHEM-475001..CHEM-500000`

Os títulos, fórmulas, aliases, níveis e fontes de todos os 500 núcleos estão versionados nos arquivos `core/chemistry_topics_*.py`; cada linha canônica corresponde exatamente a um bloco de 1.000 IDs consecutivos.

## Fontes técnicas

A síntese original do catálogo foi verificada contra IUPAC Gold Book 5ª ed. (2025), OpenStax Chemistry 2e, NIST Chemistry WebBook SRD 69, NIST CCCBDB SRD 101, NIH/NLM PubChem, MIT OpenCourseWare (5.111, 5.60, 5.61, orgânica e inorgânica), Chemistry LibreTexts e referências da IAEA para radioquímica.

## Segurança e escopo

Conteúdo de síntese orgânica, organometálica e nuclear é enciclopédico/conceitual: mecanismos, relações, métricas, termodinâmica e planejamento abstrato. O catálogo não codifica receitas operacionais perigosas, parâmetros de escala ou protocolos para preparação de materiais nocivos.

## STAR Core

`ChemistryKnowledgeEngine` é carregada no `create_star()`, exposta como `star.chemistry` e consultada pelo `Executive` antes do fallback genérico. Como Watch/Mobile usam o mesmo StarCore, respostas de Química ficam disponíveis aos clientes pelo mesmo caminho de texto/voz já existente.
