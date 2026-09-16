# Tests

Steg 5 innehåller två testlager:

- `tests/test_project_contract.py` – deterministiska kontraktstester för canonical instruktion, rapportmall, Knowledge-oberoende och obligatoriska evalfall.
- `evals/instruction-adherence/` – kriteriebaserade evalfall för kvalitativa beteenden som research, flerstegsarbete, källhantering och rapportleverans.

Kör lokalt:

```bash
python -m unittest discover -s tests -p 'test_*.py'
python scripts/validate_instruction_adherence.py --project-root .
```
