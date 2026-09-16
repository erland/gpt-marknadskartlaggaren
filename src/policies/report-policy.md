# Report- och filpolicy

Den canonical instruktionen är auktoritativ. Denna policy preciserar hur slutrapporten ska byggas.

## Rapportprinciper

Rapporten ska vara självständig: en läsare ska förstå behov, avgränsning, metod, urval och osäkerheter utan att behöva läsa chatten. Skriv på samma språk som användaren om inget annat anges.

Använd en kompakt tabell för marknadsöverblick och separata produktsektioner för analys. Undvik breda tabeller med långa styrkor/svagheter eftersom de blir svårlästa i Markdown.

## Obligatorisk struktur

1. `# Marknadskartläggning: <ämne>`
2. metadata med kartläggningsdatum
3. `## Behov och avgränsning`
4. `## Metod`
5. `## Sammanfattande marknadsbild`
6. `## Produktöversikt`
7. `## Detaljerad produktgenomgång`
8. `## Observationer, osäkerheter och avgränsningar`
9. `## Källor`

Produktöversikten ska minst innehålla kolumnerna Produkt, Leverantör/Förvaltare, Typ och Driftsform.

## Produktsektion

Varje inkluderad produkt använder samma ordning:

- **Produktnamn**
- **Leverantör/Förvaltare**
- **Open Source/Kommersiell**
- **Licens** (för open source när verifierbar)
- **Driftsform**
- **Kort beskrivning av produkten**
- **Styrkor**
- **Svagheter**
- **När man bör välja en annan produkt**
- **Källor**

Styrkor, svagheter och valsituationer är analys. Formulera dem så att kopplingen till verifierade egenskaper eller användarens behov är tydlig.

## Källor

Använd klickbara Markdown-länkar, helst till specifika officiella sidor för produkt, deployment och licens. Produktens viktigaste faktakällor ska finnas i dess egen sektion. Den globala källsektionen används för marknadsövergripande och kompletterande källor samt sådant som annars skulle ge onödig duplicering.

Skriv aldrig en naken URL om ett beskrivande länknamn kan användas. Ange åtkomstdatum endast om det tillför värde; kartläggningsdatumet är alltid obligatoriskt.

## Filnamn

Format: `marknadskartlaggning-<kort-slug>-YYYY-MM-DD.md`.

Sluggen ska:

- vara kort och beskriva produkttypen eller behovskategorin,
- skrivas med gemener,
- normaliseras till ASCII (`å/ä` -> `a`, `ö` -> `o`),
- använda bindestreck mellan ord,
- ta bort annan interpunktion,
- inte innehålla användarens hela prompt eller känsliga data.

## Filgenerering och kontroll

Skapa rapporten som UTF-8 Markdown. Före leverans verifieras:

- filen existerar,
- filändelsen är `.md`,
- alla inkluderade produkter har obligatoriska fält,
- centrala okända fakta markeras `Ej verifierat`,
- produktkällor finns,
- rapporten innehåller kartläggningsdatum och avgränsning,
- ingen oavsiktlig vinnare/ranking har lagts till.

Chattsvaret efter skapandet ska vara kort och länka till filen. Rapporten är den primära leveransen.
