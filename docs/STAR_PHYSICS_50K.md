# STAR Physics 50K — catálogo local

A STAR V1.9 passa a ter um catálogo local de Física com **50 tópicos canônicos** e **1.000 variações determinísticas por tópico**, totalizando **exatamente 50.000 conteúdos endereçáveis** (`PHYS-00001` a `PHYS-50000`).

As 1.000 variações de cada tópico são o produto de 10 famílias × 10 estilos × 10 contextos:

- famílias: conceito, fórmula, variáveis/unidades, hipóteses/validade, derivação, cálculo, aplicação, erros comuns, limites e conexões;
- estilos: direto, intuitivo, didático, técnico, vestibular, graduação, laboratório, engenharia, pesquisa e revisão;
- contextos: definição, interpretação, simbólico, dimensional, experimental, comparativo, estimativa, caso-limite, aplicado e checagem.

As variações são materializadas sob demanda para não carregar 50 mil objetos no startup. Cada unidade possui ID, tópico, domínio, nível, família, estilo, contexto, prompt, resposta e referência técnica.

## Tópicos adicionados

1. Análise dimensional — matemática física — nível 1
2. Propagação de incertezas — matemática física — nível 2
3. Cinemática com aceleração constante — cinemática — nível 1
4. Lançamento oblíquo ideal — cinemática — nível 2
5. Segunda lei de Newton — dinâmica — nível 1
6. Atrito e arrasto — dinâmica — nível 2
7. Trabalho e energia — energia/momento — nível 1
8. Impulso e momento — energia/momento — nível 1
9. Torque — rotação — nível 2
10. Momento angular — rotação — nível 2
11. Gravitação universal — gravitação — nível 1
12. Órbitas e Kepler — gravitação — nível 2
13. Oscilador harmônico simples — oscilações — nível 1
14. Amortecimento e ressonância — oscilações — nível 3
15. Ondas e equação de onda — ondas — nível 2
16. Efeito Doppler — ondas — nível 2
17. Continuidade de fluido — fluidos — nível 2
18. Equação de Bernoulli — fluidos — nível 2
19. Gás ideal e primeira lei — termodinâmica — nível 2
20. Entropia e Carnot — termodinâmica — nível 3
21. Entropia de Boltzmann — mecânica estatística — nível 3
22. Distribuição canônica e função de partição — mecânica estatística — nível 4
23. Lei de Coulomb — eletrostática — nível 1
24. Lei de Gauss elétrica — eletrostática — nível 2
25. Lei de Ohm e potência — circuitos — nível 1
26. Circuitos RC e RLC — circuitos — nível 3
27. Força de Lorentz — magnetismo — nível 2
28. Biot-Savart e Ampère — magnetismo — nível 3
29. Lei de Faraday-Lenz — eletromagnetismo — nível 2
30. Equações de Maxwell e ondas eletromagnéticas — eletromagnetismo — nível 4
31. Refração e lente delgada — óptica — nível 1
32. Interferência e difração — óptica — nível 2
33. Transformação de Lorentz — relatividade especial — nível 3
34. Energia-momento relativística — relatividade especial — nível 3
35. Equações de campo de Einstein — relatividade geral — nível 5
36. Geometria de Schwarzschild — relatividade geral — nível 4
37. Equação de Friedmann — cosmologia relativística — nível 5
38. Equação de Schrödinger — mecânica quântica — nível 4
39. Princípio de incerteza e de Broglie — mecânica quântica — nível 3
40. Hidrogênio e fórmula de Rydberg — física atômica/molecular — nível 3
41. Drude e Bloch — matéria condensada — nível 4
42. Energia de Fermi e semicondutores — matéria condensada — nível 4
43. Ligação e decaimento nuclear — física nuclear — nível 3
44. Valor Q e atividade nuclear — física nuclear — nível 3
45. Modelo Padrão e constante de estrutura fina — partículas — nível 5
46. Euler-Lagrange para campos — teoria de campos/QFT — nível 5
47. Frequência de plasma e comprimento de Debye — plasma — nível 4
48. Frequência ciclotrônica e expoente de Lyapunov — plasma/caos — nível 5
49. Fluxo e luminosidade estelar — astrofísica — nível 3
50. Hubble-Lemaître e densidade crítica — cosmologia — nível 4

## Fórmulas-base incluídas

O catálogo inclui relações de referência como `ΣF=ma`, `W=∫F·dr`, `J=Δp`, `τ=r×F`, `F=Gm1m2/r²`, `T²=4π²a³/(GM)`, `v=fλ`, Bernoulli, `PV=nRT`, primeira e segunda leis da termodinâmica, `S=k_B lnΩ`, função de partição, Coulomb, Gauss, Ohm, RC/RLC, Lorentz, Biot-Savart, Ampère, Faraday, as quatro equações de Maxwell, Snell, lente delgada, interferência/difração, Lorentz relativística, `E²=(pc)²+(mc²)²`, equações de Einstein, Schwarzschild, Friedmann, Schrödinger, `ΔxΔp≥ħ/2`, de Broglie, Rydberg, Drude, Bloch, energia de Fermi, semicondutores, ligação e decaimento nuclear, grupo de gauge do Modelo Padrão, Euler-Lagrange para campos, Debye, frequência de plasma, ciclotron, Lyapunov, Stefan-Boltzmann estelar e densidade crítica cosmológica.

## Fontes técnicas usadas como referência

- MIT OpenCourseWare — Classical Mechanics 8.01SC
- MIT OpenCourseWare — Electricity and Magnetism 8.022 / 8.02
- MIT OpenCourseWare — Quantum Physics I 8.04
- MIT OpenCourseWare — Statistical Physics 8.044 / 8.333
- MIT OpenCourseWare — Relativity 8.20 / 8.033
- OpenStax — University Physics, Volumes 1–3
- NIST/CODATA — 2022 Recommended Values of the Fundamental Physical Constants
- Particle Data Group — Review of Particle Physics 2026
- CERN — Standard Model reference material
- NASA — Physics of the Cosmos

O conteúdo da STAR é síntese original e não copia capítulos ou trechos extensos dessas fontes.

## Disponibilidade no STAR Watch

O STAR Watch usa o mesmo `StarCore` por meio do Device Gateway. Como o catálogo está no `Executive` central, perguntas de física feitas pelo Watch passam pelo mesmo mecanismo, sem alterar o design Plasma Orbit do relógio.
