# Operativ exekveringspolicy

Marknadskartläggaren är ett stateful och research-heavy arbetsflöde.

1. Läs strukturerad researchstatus före progression när sådan finns.
2. Välj exakt ett avgränsat researchmål eller rapportmål.
3. Återanvänd redan verifierad research och gör endast om den vid relevant förändring.
4. Verifiera centrala produktfakta mot aktuella källor före analys.
5. Prioritera blockerande scope- eller källkonflikter före bredare progression.
6. Uppdatera researchstatus först efter genomfört och verifierat delsteg.
7. Gå inte till slutrapport förrän rapportgrinden är uppfylld.
8. Härled nästa steg från faktisk status, inte från chattminne.

## Auktoritativ status

När `research-state.yaml` finns är den auktoritativ framför konversationsminne. Om runtime saknar persistent filstatus får researchjournalen i konversationen användas som fallback.

## Slutleverans

Arbetet är inte färdigt förrän den obligatoriska Markdown-filen faktiskt har skapats och länkats. Om filskapande saknas ska slutleveransen markeras blockerad, inte färdig.
