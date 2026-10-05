# OpenAI Plugin runtime

Marknadskartläggaren distribueras som en skills-first peer-runtime enligt GPT Byggaren 1.5.1.

## Runtime contract

Fullt kärnbeteende kräver följande host capabilities:

- aktuell webbresearch,
- läsbar och skrivbar filyta,
- code execution för faktisk filslutleverans,
- persistent workspace/state för robust cross-session resume.

`research-state.yaml` paketeras som state-template under skillens assets. En runtime-arbetskopia ska användas som auktoritativ status när den finns. Konversationsjournalen är fallback endast när persistent filstatus saknas.

## Fallbacks

- Utan webbförmåga blockeras aktuell marknadskartläggning; modellminne är inte ersättning.
- Utan persistent state kan research fortsätta inom aktuell session, men cross-session resume får inte påstås vara robust.
- Utan skrivbar filyta eller code execution får arbetet inte markeras färdigt eftersom den obligatoriska Markdown-filen inte kan skapas.

## Package policy

Pluginen innehåller canonical beteende och runtime policies som references samt research-state- och rapportmall som assets. Den innehåller inga runtime-skript, evals, tests, docs eller MCP-wrapper.
