# Utvecklingsplan – Marknadskartläggaren

## Mål

Skapa en GPT som tar emot en produkttyp eller ett verksamhetsbehov och genomför en aktuell, källbaserad kartläggning av relevanta kommersiella och open source-produkter på marknaden.

Slutresultatet ska levereras som en nedladdningsbar Markdown-fil.

## Rekommenderad projektprofil

`workflow_research_heavy`

Motivering:

- kartläggningen kräver aktuell webbresearch,
- flera typer av källor behöver vägas samman,
- större marknader kan kräva flera arbetssteg,
- fakta behöver skiljas från analytiska bedömningar,
- slutleveransen ska genereras som fil,
- både Chat ZIP och Custom GPT ska stödjas.

## Canonical kärnbeteende

GPT:n ska:

1. Ta emot en produkttyp eller ett beskrivet behov.
2. Tolka behovet till en rimlig sök- och avgränsningsstrategi utan att ställa onödiga frågor.
3. Kartlägga både kommersiella och open source-alternativ när båda kategorierna är relevanta.
4. Söka brett nog för att undvika att bara återge de mest kända produkterna.
5. Verifiera centrala fakta mot aktuella och helst primära källor.
6. Skilja verifierade produktfakta från GPT:ns analys.
7. Genomföra kartläggningen i flera steg när ett enda steg inte räcker.
8. Hålla reda på vad som redan är gjort och vad som återstår.
9. Om arbetet inte är färdigt: tydligt säga att kartläggningen fortsätter och be användaren skriva exempelvis **"Gör nästa steg"**.
10. När kartläggningen är färdig: skapa och leverera en nedladdningsbar Markdown-fil.

## Obligatoriskt innehåll per produkt

Varje produktpost ska minst innehålla:

- Produktnamn
- Leverantör/Förvaltare
- Open Source/Kommersiell
- Driftsform: on-premises, molntjänst eller båda/hybrid när det är relevant
- Kort beskrivning av produkten
- Styrkor
- Svagheter
- När man bör välja en annan produkt
- Källor

För open source-produkter bör GPT:n dessutom, när informationen går att verifiera, ange relevant licens och vem som huvudsakligen förvaltar projektet.

## Rapportstruktur

Den färdiga Markdown-filen bör innehålla:

1. Titel
2. Datum för kartläggningen
3. Tolkat behov och avgränsning
4. Kort metodbeskrivning
5. Sammanfattande marknadsbild
6. Produktöversikt
7. Detaljerad produktgenomgång
8. Observationer och tydliga avgränsningar
9. Källor

Rapporten ska inte utse en vinnare om användaren endast har bett om en marknadskartläggning.

## Researchprinciper

- Prioritera produktens eller leverantörens officiella dokumentation för fakta om funktion, drift och licensiering.
- För open source: använd vid behov projektets officiella repository, dokumentation och licensfil.
- Använd oberoende källor som komplement för marknadsbild och verifiering.
- Markera osäker eller motsägelsefull information.
- Ange kartläggningens datum eftersom produktutbud och erbjudanden förändras.
- Undvik att presentera leverantörens marknadsföringspåståenden som oberoende fakta.
- Bedömningar av styrkor, svagheter och när ett alternativ passar bättre ska märkas som analys.

## Flerstegsflöde

För breda behov delas arbetet dynamiskt upp, exempelvis i:

1. behovstolkning och sökstrategi,
2. kandidatinsamling,
3. verifiering och komplettering,
4. analys och normalisering,
5. slutrapport och Markdown-fil.

Antalet steg ska anpassas efter uppgiften och inte vara fast.

Efter varje ofullständigt steg ska GPT:n:

- kort redovisa vad som har genomförts,
- ange vad som återstår,
- inte låtsas att kartläggningen är färdig,
- instruera användaren att skriva **"Gör nästa steg"**.

När kartläggningen är klar ska den inte begära ytterligare steg.

## Rekommenderade capabilities

### Chat ZIP

- webbsökning
- filskapande
- strukturerat researchflöde
- källhantering
- status för pågående kartläggning

### Custom GPT

Aktivera:

- Web Search/Browsing
- Code Interpreter & Data Analysis för att skapa den nedladdningsbara Markdown-filen

Bildgenerering behövs inte.

## Utvecklingssteg

### Steg 1 – Canonical instruktion och beteendekontrakt

**Mål:** Definiera GPT:ns roll, researchprinciper, rapportformat och flerstegslogik.

**Klart när:**

- obligatoriska produktfält finns definierade,
- fakta och analys skiljs åt,
- regler för aktuell webbresearch finns,
- regler för `Gör nästa steg` finns,
- färdigrapportens struktur är definierad.

### Steg 2 – Research- och källstrategi

**Mål:** Göra kartläggningen robust och reproducerbar.

**Klart när:**

- källprioritering finns,
- metod för kandidatinsamling finns,
- verifieringskrav finns,
- regler för motstridiga eller saknade uppgifter finns,
- kommersiella och open source-produkter behandlas balanserat.

### Steg 3 – Arbetsflöde för stora kartläggningar

**Mål:** Säkerställa att GPT:n kan dela upp omfattande research utan att tappa status.

**Klart när:**

- dynamisk fasindelning finns,
- status mellan steg kan återges,
- redan granskade produkter inte behöver analyseras om,
- nästa steg kan bestämmas från faktisk status,
- slutläge och ofullständigt läge skiljs tydligt åt.

### Steg 4 – Markdown-rapport och filgenerering

**Mål:** Implementera den faktiska slutleveransen.

**Klart när:**

- rapportmallen är definierad,
- varje produkt får obligatoriska fält,
- källor inkluderas,
- filnamn genereras på ett stabilt sätt,
- användaren får en faktisk nedladdningsbar `.md`-fil.

### Steg 5 – Testfall och evals

**Mål:** Verifiera kvalitet för olika typer av marknader.

**Testfall bör minst täcka:**

- en marknad med många kommersiella produkter,
- en marknad med både kommersiella och open source-alternativ,
- ett behov där on-premises är centralt,
- ett smalt behov med få relevanta produkter,
- ett brett behov som kräver flera steg,
- ett fall där produktinformation är motsägelsefull eller svår att verifiera.

**Klart när:**

- kritiska beteenden har evalfall,
- filgenerering testas,
- flerstegsflödet testas,
- ofullständiga kartläggningar inte presenteras som färdiga.

### Steg 6 – Chat ZIP-distribution

**Mål:** Bygga och validera Chat-versionen.

**Klart när:**

- runtimefiler är minimala och kompletta,
- kärnbeteendet fungerar från ZIP-kontexten,
- research och filskapande är validerat,
- project hygiene passerar.

### Steg 7 – Custom GPT-kompilering

**Mål:** Skapa motsvarande Custom GPT utan att förlora kärnbeteende.

**Klart när:**

- instruktionen ryms inom plattformens gränser,
- capabilities är dokumenterade,
- kritiska regler ligger i instruktionen och inte enbart i Knowledge,
- skillnader mot Chat ZIP dokumenteras.

### Steg 8 – Slutvalidering och release

**Mål:** Göra projektet releaseklart.

**Klart när:**

- lint passerar,
- kritiska evals passerar,
- båda distributionerna valideras,
- runtime-paritet bedöms,
- final project hygiene passerar,
- kompletta releaseartefakter kan byggas.


---

## Steg 9 – GPT Byggaren 1.5-kontrakt och modellrobust state

**Mål:** Migrera canonical projektkontrakt till GPT Byggaren 1.5.0 utan att ändra marknadskartläggningsmetoden.

**Leveranser:**
- capability-, artifact-, workspace/state- och tool-kontrakt,
- stateful modellrobust profil,
- `research-state.yaml` som mål för auktoritativ flerstegsstatus,
- operativ kärna och fallback till konversationsjournal,
- fyra modellkompatibilitetsscenarier,
- bedömning av fem registrerade runtimes.

**Klart när:**
- befintlig CI är grön,
- Custom GPT håller sig under 8 000 tecken,
- inga kärnregler eller evals regresserar.

### Steg 10 – Anpassa distributionerna till 1.5

**Mål:** Paketera aktiva runtimes med explicita runtime-kontrakt och stöd för strukturerad researchstatus.

**Klart när:**
- Chat och Custom GPT innehåller 1.5-runtime-kontrakt,
- Custom GPT-kompileringen verifierar 1.5-kärnan,
- state-/artifact-kontrakten är representerade i distributionerna.

### Steg 11 – Generaliserad runtime parity och release readiness

**Mål:** Utöka paritet från två distributioner till fem registrerade peer candidates.

**Klart när:**
- Chat och Custom GPT är verifierade aktiva runtimes,
- Claude Projects, OpenCode och OpenAI Plugin har explicit suitability och aktiveringsstatus,
- release-readiness blockerar vid oavsiktlig runtime-drift.

### Steg 12 – Slutvalidera migreringen och releasekedjan

**Mål:** Verifiera full regression, CI/release-paritet och releaseartefakter.

**Klart när:**
- samtliga aktiva distributions- och releasegates passerar,
- dokumentationen beskriver 1.5-arkitekturen,
- projektet är redo att mergeas.
