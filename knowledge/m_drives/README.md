# ⭐ M.drives

**M.drive = Memory + Drive/Pendrive.**

Este é o nome oficial dos módulos removíveis de conhecimento/memória da STAR.
Cada M.drive vive em uma subpasta com `manifest.json`. A STAR mantém leitura
compatível do caminho legado `knowledge/packs`, mas novas extensões devem usar
`knowledge/m_drives`.

Princípios:
- conteúdo local e removível;
- manifesto explícito com identidade, versão e domínios;
- nada é executado automaticamente apenas por conectar/descobrir um M.drive;
- conteúdo duplicado deve ser resolvido por identidade/proveniência, não copiado;
- manifests legados podem ser migrados sem apagar a origem.
