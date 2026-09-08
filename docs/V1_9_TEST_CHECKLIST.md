# Checklist de aceitação — STAR V1.9 FINAL

## Automático
- [x] GitHub Actions: sintaxe Python.
- [x] GitHub Actions: validação dos manifestos.
- [x] GitHub Actions: smoke tests do pipeline de voz sem hardware.
- [x] GitHub Actions: suíte `pytest` completa em Linux e Windows.
- [x] GitHub Actions: higiene do repositório (sem banco local, referências privadas, testes soltos ou assets vazios).
- [x] Consistência de nome/versão/release validada a partir de `STAR_MANIFEST.json`.
- [x] Nenhum serviço externo de voz é obrigatório.
- [x] Versão pública central definida como 1.9.

## Validado no computador
- [x] Diagnóstico de voz executou e produziu áudio.
- [x] STT/TTS local foi instalado e carregado.

## Revalidação após o último pull — exige hardware/Windows real
- [ ] Confirmar que a referência local autorizada em `voice/reference/` existe.
- [ ] Confirmar que a fala usa a voz oficial da STAR quando Chatterbox estiver disponível.
- [ ] Confirmar que uma nova mensagem interrompe/cancela fala antiga.
- [ ] Testar GUI, microfone, matemática, ilhas e Closet em uma sessão normal.

Esses quatro itens não podem ser certificados apenas por CI/GitHub porque dependem dos arquivos privados, dispositivos e sessão gráfica da máquina da STAR. Eles nunca devem ser marcados automaticamente como concluídos.

## Política pós-release
A V1.9 permanece congelada em `main`. Correções comprovadas entram como V1.9.x e devem passar por PR + CI antes do merge. Novos sistemas cognitivos pertencem à V2.0 MIND.
