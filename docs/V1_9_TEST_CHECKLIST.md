# Checklist de aceitação — STAR V1.9 FINAL

## Automático
- [x] GitHub Actions: sintaxe Python.
- [x] GitHub Actions: validação dos manifestos.
- [x] GitHub Actions: smoke tests do pipeline de voz sem hardware.
- [x] Nenhum serviço externo de voz é obrigatório.
- [x] Versão central definida como 1.9.

## Validado no computador
- [x] Diagnóstico de voz executou e produziu áudio.
- [x] STT/TTS local foi instalado e carregado.

## Revalidação após o último pull
- [ ] Confirmar que a referência local `voice/reference/star_reference.mp3` existe.
- [ ] Confirmar que a fala usa a voz oficial da STAR quando Chatterbox estiver disponível.
- [ ] Confirmar que uma nova mensagem interrompe/cancela fala antiga.
- [ ] Testar GUI, microfone, matemática, ilhas e Closet em uma sessão normal.

## Política pós-release
A V1.9 pode ser congelada em `main`. Ajustes locais descobertos depois entram
como V1.9.x. Novos sistemas cognitivos pertencem à V2.0 MIND.
