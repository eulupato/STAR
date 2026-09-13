# STAR Global Localization

## Objetivo

A STAR mantém uma única fonte de verdade para conhecimento, memória, MIND, projetos, respostas científicas e demais conteúdos. Idioma é uma camada de apresentação, não uma cópia da informação.

Isso evita seis versões divergentes do mesmo fato e permite corrigir ou ampliar o conhecimento apenas uma vez.

## Idiomas atuais

- pt-BR — Português (Brasil)
- en-US — English (US)
- en-GB — English (UK)
- es-ES — Español
- it-IT — Italiano
- fr-FR — Français

Internamente, o conteúdo canônico continua em pt-BR. Entrada e saída passam pelo `LanguageManager` nas bordas do Core.

## Pipeline

1. O usuário escolhe um locale.
2. A entrada é traduzida para o idioma canônico quando necessário.
3. O STAR Core executa exatamente os mesmos engines de identidade, conhecimento, MIND, matemática, RAG, projetos e ferramentas.
4. A resposta canônica é enviada ao `GlobalLocalizationEngine`.
5. Elementos invariáveis são protegidos.
6. A tradução usa, nesta ordem:
   - catálogo estático de UI;
   - equivalência contextual;
   - dicionário offline exato;
   - Argos Translate local, se instalado;
   - tradução lexical somente quando 100% dos termos traduzíveis são cobertos.
7. Os elementos protegidos são restaurados.
8. Se a tradução não for completa ou algum invariável mudar, a tradução é rejeitada e o texto original é preservado.

## Invariáveis

A camada de idioma não deve alterar:

- IDs como `CHEMX-0000042`;
- números e unidades;
- URLs;
- e-mails;
- caminhos de arquivo;
- código inline;
- blocos de código;
- expressões delimitadas como matemática.

Essa proteção existe para impedir que tradução altere informação técnica.

## UI

Mensagens e rótulos essenciais possuem superfícies determinísticas nos seis locales. O STAR Watch usa o mesmo `LanguageManager` do Core; não possui sistema linguístico independente.

O locale selecionado continua persistido em `runtime/language/settings.json`.

## Tradução neural offline opcional

Para textos livres longos, a STAR suporta Argos Translate como backend opcional e lazy. Ele não é obrigatório para inicialização e nenhum modelo é baixado automaticamente.

Instalação do pacote opcional:

```powershell
python -m pip install -r requirements-translation.txt
```

Ver estado:

```powershell
python scripts/setup_offline_translation.py
```

Baixar explicitamente os pares mínimos:

```powershell
python scripts/setup_offline_translation.py --install
```

O conjunto mínimo usa inglês como pivô e instala:

- pt ↔ en
- es ↔ en
- it ↔ en
- fr ↔ en

Com esses pares, os cinco idiomas semânticos da STAR podem interoperar offline. en-US e en-GB compartilham o mesmo backend neural `en`; diferenças de superfície fixa continuam tratadas pelo catálogo de locale.

## Dicionário offline

A infraestrutura anterior permanece válida. `scripts/build_offline_dictionaries.py` continua construindo `runtime/language/dictionaries.sqlite3` a partir de fontes lexicais abertas. O índice completo melhora tradução lexical e continua opcional no startup.

## Política de integridade

Tradução nunca cria conhecimento novo e nunca altera a fonte canônica.

Uma resposta traduzida pode mudar a forma linguística, mas não deve mudar:

- valores;
- relações;
- IDs;
- conclusões;
- grau de confiança;
- origem/proveniência;
- código;
- conteúdo estruturado.

Quando não houver tradução local completa e segura, a STAR preserva o original. Isso é preferível a produzir uma tradução parcial que pareça correta.

## Limites atuais

- Os modelos Argos não são versionados no GitHub.
- A instalação de modelos exige uma ação explícita e conexão somente durante o download.
- Depois de instalados, a tradução neural pode funcionar offline.
- Tradução automática não transforma o conteúdo em uma nova fonte factual; o conteúdo canônico continua sendo a referência.
- Nomes próprios e terminologia científica podem exigir expansão futura de glossários especializados para melhorar estilo sem mudar significado.
