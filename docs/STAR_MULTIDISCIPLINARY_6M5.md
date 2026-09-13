# STAR Multidisciplinary 6.5M

## Escala

A biblioteca adiciona 13 matérias, cada uma com 25 macroáreas × 20 lentes = 500 nós canônicos. Cada nó possui 1.000 variações determinísticas (10 famílias × 10 estilos × 10 contextos), produzindo exatamente 500.000 conteúdos endereçáveis por matéria e 6.500.000 no total.

Os conteúdos são materializados sob demanda. A STAR não cria nem carrega 6,5 milhões de objetos no startup.

## Matérias e IDs

- Geografia: `GEO-000001..GEO-500000`
- História: `HIST-000001..HIST-500000`
- Matemática: `MATH-000001..MATH-500000`
- Biologia: `BIO-000001..BIO-500000`
- Mecânica: `MECH-000001..MECH-500000`
- Engenharia: `ENG-000001..ENG-500000`
- Computação: `COMP-000001..COMP-500000`
- TI: `IT-000001..IT-500000`
- Lógica: `LOGIC-000001..LOGIC-500000`
- Psicologia e Sociologia: `PSYSOC-000001..PSYSOC-500000`
- Decodificação: `DECODE-000001..DECODE-500000`
- Ciências: `SCI-000001..SCI-500000`
- Filosofia: `PHIL-000001..PHIL-500000`

## Organização interna

As 20 lentes canônicas são: conceito, fundamentos, estrutura, processo, modelo, cálculo, métodos, evidências, história do conceito, casos, comparação, aplicações, erros, limites, controvérsias, interdisciplinaridade, cotidiano, curiosidades/detalhes pouco ensinados, avançado/fronteira e revisão.

As 10 famílias de resposta são: explicação, pergunta/resposta, procedimento, exemplo guiado, comparação, checagem, erros/armadilhas, fontes/evidências, conexões e desafio.

Os 10 estilos são direto, intuitivo, didático, técnico, escolar, graduação, profissional, pesquisa, socrático e revisão. Os 10 contextos são definição, interpretação, problema, caso real, histórico, comparativo, interdisciplinar, aplicado, fronteira e checagem.

## Roteamento e colisões

O Executive preserva os domínios científicos já existentes em prioridade: conhecimento interno → Física 150K → Química 500K → biblioteca multidisciplinar → Knowledge Packs. Isso evita que a matéria ampla `Ciências` capture uma consulta que já possui uma resposta mais específica em Física ou Química.

Dentro da biblioteca multidisciplinar, o resolver usa:

1. matéria explicitamente citada;
2. especificidade da macroárea;
3. cobertura de tokens da consulta;
4. pontuação de precisão;
5. pontes interdisciplinares.

Quando duas matérias diferentes ficam praticamente empatadas e o usuário não informou a área, a STAR pede contexto em vez de escolher arbitrariamente. Exemplos de termos potencialmente ambíguos: redes, sistema, memória, evolução, modelo, estrutura e lógica.

As pontes indicam relação sem duplicar propriedade do mesmo conhecimento. Exemplos: Geografia ↔ História/Biologia; Matemática ↔ Lógica/Computação/Mecânica; Mecânica ↔ Engenharia/Física; Computação ↔ TI/Decodificação; Filosofia ↔ Lógica/História/Ciências.

## História além do currículo padrão

A área de História possui uma política própria de evidência. A lente de curiosidades/detalhes pouco ensinados prioriza fontes primárias, acervos de museus, cultura material, arqueologia e historiografia confiável. Hipóteses e interpretações contestadas são rotuladas; não são convertidas em fato.

Além de cronologia e grandes eventos, os ângulos incluem vida cotidiana, alimentação, trabalho, logística, infraestrutura, mulheres e grupos pouco representados, tecnologia, doença, cultura material, correspondência, registros judiciais, mapas, objetos, arqueologia e história ambiental.

Exemplos de ângulos micro-históricos já codificados:

- Roma: grafites, tábuas, diplomas militares, ânforas e resíduos arqueológicos;
- Mesopotâmia: tábuas administrativas sobre rações, trabalho, dívida e comércio;
- Egito antigo: papiros, ostraca e aldeias de trabalhadores;
- Europa medieval: contas domésticas, tribunais, marginalia, dieta e evidência ambiental;
- Guerras mundiais: logística, manutenção, meteorologia, ferrovias, enfermagem, racionamento e trabalho colonial;
- Brasil: alianças indígenas, rotas internas, escravidão urbana, comunidades africanas, fronteiras e cultura material;
- história da ciência: instrumentos, técnicos, artesãos, padrões, tabelas e falhas experimentais.

## Decodificação

O domínio Decodificação é educacional/defensivo. Cobre sistemas de numeração, ASCII, Unicode, UTF-8/16/32, normalização, Base64/Base32/Base16, percent-encoding, MIME, representação binária, endianness, compressão, entropia, Huffman, codificação aritmética, códigos corretores, checksums, CRC, Reed-Solomon, hashes/autenticação, criptografia conceitual e serialização.

Não é um catálogo operacional de quebra de credenciais, bypass de acesso ou exploração maliciosa.

## Psicologia e Sociologia

O conteúdo cobre pesquisa e teoria em cognição, comportamento, desenvolvimento, personalidade, psicometria, teoria social, instituições, cultura, desigualdade, demografia e métodos de pesquisa. A biblioteca não tenta inferir diagnóstico clínico individual a partir de uma pergunta.

## Voz +1M

`core/thematic_voice.py` adiciona exatamente 1.000.000 de variações temáticas endereçáveis: `VOICE-STUDY-0000001..VOICE-STUDY-1000000`.

Modelo: 10 ações × 10 tons × 10 profundidades × 10 formatos × 10 contextos × 10 encerramentos = 1.000.000.

As frases usam tema livre. Exemplos de formato aceito:

- `STAR, me ensine lógica modal do zero`
- `STAR, aprofunde genética molecular no nível de pesquisa`
- `STAR, compare computação distribuída e paralela`
- `STAR, revise comigo cartografia e projeções`
- `STAR, me faça perguntas sobre epistemologia`

O milhão não é materializado em RAM. `thematic_voice_variant(index)` reconstrói qualquer variante deterministicamente.

## Fontes-base pesquisadas

Pesquisa de setembro de 2026 priorizou famílias de fontes institucionais e acadêmicas: USGS, NOAA, NASA Earthdata, Library of Congress, Smithsonian, UNESCO Memory of the World, OpenStax, MIT OpenCourseWare, NIST, NCBI/NIH, ACM, IETF, Unicode Consortium, APA, American Sociological Association, Stanford Encyclopedia of Philosophy, National Academies e Computer History Museum.

A seleção de fontes serve como base de referência e taxonomia; o repositório não baixa silenciosamente coleções gigantes ou conteúdo protegido.

## Transparência

`6.500.000 conteúdos` significa 6,5 milhões de unidades conversacionais/endereço determinístico produzidas de 6.500 nós canônicos. Não significa 6,5 milhões de fatos independentes manualmente pesquisados.

O objetivo é permitir busca, ensino, comparação, revisão, cálculo/procedimento quando cabível, fontes/evidências, curiosidades verificáveis e conexões entre áreas sem inflar RAM ou criar milhões de condicionais.