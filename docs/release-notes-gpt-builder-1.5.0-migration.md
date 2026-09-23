# Marknadskartläggaren – migrering till GPT Byggaren 1.5.0

## Sammanfattning

Migreringen moderniserar runtime-, state- och releasekontrakten utan att ändra marknadskartläggningens domänmetod i version 1.0.0.

## Viktigaste förändringar

- plattformsneutrala capability-, artifact-, workspace/state- och tool-kontrakt
- stateful modellrobust workflow
- `research-state.yaml` som strukturerad researchstatus med konversationsfallback
- operativ kärna och auktoritativ status i canonical instruktion
- modellkompatibilitetsscenarier för resume, källkonflikt, nästa steg och terminalt slutläge
- explicita runtime-kontrakt i Chat och Custom GPT
- fem registrerade runtimes i parity-modellen
- Chat och Custom GPT aktiva
- Claude Projects, OpenCode och OpenAI Plugin bedömda men inaktiva
- runtime parity och release-readiness som blockerande gates
- CI och release använder samma regressionskedja och aktiva distributionsmål
- deterministisk workflow-paritetskontroll

## Bevarat beteende

Krav på aktuell webbresearch, fakta/analys-separation, dynamiskt flerstegsarbete, `Gör nästa steg`, obligatoriska produktfält och faktisk nedladdningsbar Markdown-fil är oförändrade.
