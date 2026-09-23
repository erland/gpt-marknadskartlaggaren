# Projekt: Marknadskartläggaren

## Syfte

Skapa en GPT som från en produkttyp eller ett behov genomför en aktuell och källbaserad marknadskartläggning av relevanta kommersiella och open source-produkter.

## Distributioner

Projektet byggs för både Chat ZIP och Custom GPT från samma canonical instruktion.

## Kärnkrav

- aktuell webbresearch,
- balanserad kandidatinsamling,
- tydlig separation mellan fakta och analys,
- obligatoriska produktfält,
- stöd för dynamisk flerstegsresearch,
- faktisk nedladdningsbar Markdown-fil som slutleverans.


## GPT Byggaren 1.5-arkitektur

Projektet är stateful/research-heavy. För längre kartläggningar används `research-state.yaml` som strukturerad researchstatus när runtime kan bära filstatus; konversationsjournalen är fallback.

Aktiva runtimes:
- ChatGPT Chat
- ChatGPT Custom

Bedömda men inaktiva tills research-, state- och filslutleveransparitet verifierats:
- Claude Projects
- OpenCode
- OpenAI Plugin

Releasekedjan verifierar behavior, capability, artifact, workspace_state och tool samt blockerar vid runtime- eller workflow-drift.
