# {{GPT_NAME}} – Chat ZIP

Den här ZIP-filen är den portabla Chat-runtime-distributionen för **{{GPT_NAME}}**.

## Användning

Bifoga ZIP-filen i en ChatGPT-konversation och ange att den ska användas som GPT-kontext i konversationen.

## Runtime-innehåll

- `assistant/instructions.md` – canonical runtimeinstruktion
- `assistant/policies/` – kompletterande runtimepolicies
- `assistant/conversation-starters.md` – exempel på startprompter
- `templates/` – mallar som används av runtime när de finns
- `MANIFEST.json` – maskinläsbar lista över exakt vilka filer som ingår, med checksumma och storlek
- `VERSION` – distributionsversion

`MANIFEST.json` är sanningskällan för paketets faktiska filinnehåll. Utvecklingsmaterial som `docs/`, `evals/`, `tests/`, byggscript och projektstatus ska inte finnas i Chat-runtime-paketet.

## Version

{{VERSION}}

## Entry point

Detta dokument är den mänskliga entrypointen. Läs därefter `assistant/instructions.md`; policies och mallar kompletterar instruktionen men kärnbeteendet ska inte vara beroende av externa projektfiler.
