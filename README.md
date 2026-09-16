# Marknadskartläggaren

En GPT för aktuell, källbaserad kartläggning av kommersiella och open source-produkter utifrån produkttyp eller verksamhetsbehov.

## Distributioner

Projektet bygger två runtime-distributioner från samma canonical kontrakt:

- Chat ZIP
- Custom GPT

Dessutom byggs en komplett projekt-ZIP.

## Lokal validering

```bash
python scripts/lint_gpt_project.py --project-root .
python scripts/project_hygiene.py --project-root . --mode checkpoint
python scripts/build_distributions.py --project-root . --version 1.0.0 --targets project,chat,custom-gpt
python scripts/validate_distributions.py --project-root .
python scripts/validate_chat_runtime.py --project-root . --zip dist/marknadskartlaggaren-chat-1.0.0.zip
python scripts/validate_custom_gpt_runtime.py --project-root . --zip dist/marknadskartlaggaren-custom-gpt-1.0.0.zip
```

## Projektstatus

Se `project-status.yaml` och `STATUS.md`.

## Test och evals

```bash
python -m unittest discover -s tests -p 'test_*.py'
python scripts/validate_instruction_adherence.py --project-root .
```
