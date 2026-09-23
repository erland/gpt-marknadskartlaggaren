# Runtime-paritet – GPT Byggaren 1.5

## Slutsats

**Aktiva runtimes: ChatGPT Chat och ChatGPT Custom.**

Båda bär samma canonical kärnbeteende, samma capability-/artifact-/workspace-state-/tool-kontrakt och samma neutraliserade `research-state.yaml`-template. Custom GPT använder kompilerad instruktion inom 8 000-teckengränsen.

## Registrerade runtimes

| Runtime | Suitability | Aktiv | Motivering |
| --- | --- | --- | --- |
| ChatGPT Chat | ready | Ja | Webbresearch, filskapande och flerstegsarbete stöds direkt. |
| ChatGPT Custom | reduced | Ja | Kärnflödet stöds när Web Search och Code Interpreter/Data Analysis är aktiverade. |
| Claude Projects | reduced | Nej | Research-, state- och filslutleveransparitet är inte verifierad. |
| OpenCode | reduced | Nej | Workspace/lokal exekvering passar, men aktuell webbresearch och filslutleverans är miljöberoende. |
| OpenAI Plugin | reduced | Nej | Plugin v1 realiserar inte själv hela research-, state- och filgenereringsflödet. |

## Paritetskategorier

GPT Byggaren 1.5 jämför behavior, capability, artifact, workspace_state och tool.

## Release gate

`scripts/validate_runtime_parity.py` verifierar de fem runtime-bedömningarna och djup paritet för Chat/Custom GPT. `scripts/validate_release_readiness.py` verifierar samma beslut mot byggda artefakter, checksummor och migrationsstatus.

De tre inaktiva runtimes får inte aktiveras enbart för att en teknisk distribution går att bygga. För Marknadskartläggaren krävs verifierad aktuell webbresearch, resumable state och faktisk Markdown-filslutleverans.
