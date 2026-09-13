# STAR Offline Evolution Alpha

Estado: **alpha integrado sobre a STAR V1.9 estável**.

Este documento registra a expansão offline-first adicionada à Foundation sem promover
V2/V3/V7/V9 para concluídas. A regra continua sendo uma única STAR: Core, identidade,
conhecimento, memória, MIND, ferramentas e interfaces compartilham a mesma arquitetura.

## 1. Contrato offline-first

A STAR inicia com `StarCore.network_enabled = False`. O setter dessa propriedade é a
trava central de rede do Core e também desabilita o `WeatherService` compartilhado.
Nenhuma interface deve habilitar internet implicitamente.

Funcionam localmente sem internet:

- identidade/Core e conhecimento interno;
- M.drives locais/removíveis já disponíveis;
- MIND/Goal Engine/Guardian alpha;
- RAG local, File Index, Knowledge Graph e simulações;
- People;
- Cura;
- idioma/localização e dicionários/modelos já materializados;
- hora/data e painel AGORA;
- voz/STT/TTS quando os modelos locais correspondentes já estiverem instalados.

Dependem de autorização ONLINE explícita quando usados:

- Web Knowledge para busca atual;
- Research Hub;
- clima ao vivo;
- qualquer outro provider que declare rede como requisito.

Internet amplia a STAR; não constitui a STAR.

## 2. Web Knowledge sem IA generativa

Implementação: `core/web_knowledge.py`.

Fluxo:

1. o Core tenta primeiro suas fontes locais;
2. se não houver resposta confiável e ONLINE estiver autorizado, Web Knowledge pesquisa;
3. SearXNG configurado é preferido; DuckDuckGo HTML é fallback;
4. URLs privadas/localhost são bloqueadas para reduzir risco de SSRF;
5. páginas textuais são extraídas dentro de limites de tamanho/timeout;
6. sentenças são ranqueadas deterministicamente por relevância e diversidade de domínio;
7. a resposta preserva URLs/títulos como proveniência;
8. documentos/evidências aceitos são gravados no `CognitiveStore` já existente;
9. em sessões futuras offline, evidência aprendida pode ser reutilizada pelo cache/RAG.

O conteúdo encontrado na web não vira verdade absoluta automaticamente. O armazenamento
mantém origem, data e confiança. A formulação atual não usa LLM.

## 3. Cura local

Implementação: `core/cure.py`.

A Cura atual pode:

- validar arquivos Python/JSON críticos;
- executar `PRAGMA quick_check` do SQLite;
- registrar avisos de disco;
- criar snapshots locais com SHA-256;
- manter um snapshot conhecido como bom (`known-good`);
- comparar arquivos atuais com o baseline;
- não sobrescrever mudanças saudáveis apenas porque o hash mudou;
- restaurar somente arquivos presentes no snapshot/allowlist;
- criar snapshot de segurança antes do reparo;
- validar novamente após restauração;
- desfazer a tentativa se o reparo não resolver;
- operar por watchdog local.

Ela **não** gera código novo, não usa GitHub como requisito, não possui liberdade para
reescrever o sistema e não substitui o Guardian V7 completo. Sandbox de SO, Secrets
Vault, autenticação forte, antimalware e backup/restore amplo ainda são futuros.

## 4. People

Implementação: `core/people.py`.

People utiliza o mesmo `star.db` e `runtime/people`. Perfis podem receber nome, aliases,
texto estruturado, notas e imagens fornecidas explicitamente. Assets locais recebem
SHA-256 e dHash para deduplicação/fingerprint técnico.

Políticas atuais:

- nenhuma rede é necessária;
- não há reconhecimento facial/biométrico;
- não há inferência de raça, religião, saúde, orientação sexual, personalidade ou
  outros traços sensíveis a partir de imagem;
- GPS de EXIF não é ingerido;
- imagens genéricas recebidas por câmera não são atribuídas automaticamente a uma pessoa
  sem contexto explícito de cadastro.

## 5. Idiomas

Fonte de verdade: `core/language_profiles.py`.

Há **18 perfis em 13 famílias**:

- Português (Brasil);
- Inglês EUA/Reino Unido;
- Espanhol;
- Italiano;
- Francês;
- Japonês;
- Polonês;
- Coreano;
- Grego moderno;
- Grego antigo;
- Latim clássico, tardio, medieval e neolatim;
- Árabe padrão moderno;
- Árabe egípcio;
- Egípcio antigo.

Egípcio antigo não é tratado como árabe. O perfil moderno do Egito é `ar-EG`; o perfil
histórico é `egy-EG`.

O catálogo contextual humano revisado continua sendo o legado de 5 famílias/6 superfícies
com **500 mil conteúdos semânticos endereçáveis**. Os novos perfis não multiplicam esse
número artificialmente. Eles usam UI embutida, dicionário local e, quando disponível,
Argos Translate já instalado.

Grego antigo, latim histórico e egípcio antigo não usam MT moderno como se fosse uma
tradução histórica validada. Sem léxico/corpus suficiente, a STAR preserva o original.

## 6. AGORA por plataforma

A informação comum vem do Core através de `StarCore.now_status()`.

- **PC:** popup no Hub/GUI localizada;
- **STAR Watch Simulator / Plasma Orbit:** modo AGORA com swipe lateral;
- **Android Watch:** segunda página `NowSwipeView`, com hora/data locais e status do Core
  quando pareado;
- **iOS:** `TabView` paginado com segunda página AGORA e hora/data locais.

A interface nunca deve bloquear aguardando clima. Sem ONLINE, clima ao vivo não é
consultado. Hora/data continuam locais.

## 7. Limites atuais

Ainda não fazem parte desta alpha como capacidade concluída:

- scene understanding e identificação visual semântica;
- reconhecimento facial automático;
- sincronização offline completa entre dispositivos;
- Guardian V7 completo/sandbox/vault;
- autonomia Agent ponta-a-ponta;
- tradução histórica neural completa;
- sensores físicos reais do Watch validados em hardware;
- garantia de que toda informação web encontrada esteja correta sem etapa de verificação.

## 8. Critério de aceitação

Esta expansão só deve ser considerada pronta para merge quando, no mesmo SHA final:

- suíte Python completa passar;
- diagnóstico passar;
- Windows smoke passar;
- Quality passar;
- Security passar;
- Android Watch build passar;
- iOS build passar;
- diff final não contiver mudanças acidentais;
- documentação/manifests refletirem o estado real.
