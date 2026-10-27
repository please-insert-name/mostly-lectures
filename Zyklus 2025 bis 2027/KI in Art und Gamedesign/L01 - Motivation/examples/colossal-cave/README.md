# Colossal Cave Adventure – deutsche Twine-Adaption

Vollständige Umsetzung des Klassikers *Adventure* (Crowther/Woods, 350-Punkte-Fassung) als
Twine-Geschichte im Format **SugarCube 2.37**: alle 140 Orte, alle 15 Schätze, Zwerge, Pirat,
Troll, Drache, Bär, Pflanze, Automat, Hinweise, Schließung der Höhle und das Endspiel mit
Sprengung – 350 Punkte sind erreichbar (per Testlauf verifiziert).

## Spielen

`colossal-cave.html` im Browser öffnen (keine Installation, kein Server nötig).
Zum Bearbeiten in Twine 2: *Bibliothek → Importieren* → `colossal-cave.twee` (oder die HTML-Datei).

**Bedienung**
- Richtungstasten und Gegenstands-Buttons (*nimm …* / *lass …*) für alles Häufige.
- Eingabezeile für alle anderen Befehle mit einem oder zwei Wörtern, z. B.
  `nimm lampe`, `norden`, `oeffne gitter`, `schwenke stab`, `wirf axt`, `xyzzy`, `plugh`, `plover`,
  `fee fie foe foo`, `inventar`, `punkte`, `kurz`, `hilfe`, `info`.
- Umlaute dürfen als `ae/oe/ue` geschrieben werden. Die originalen englischen Wörter
  (`get lamp`, `west`, `unlock grate` …, gekürzt auf 5 Buchstaben) funktionieren ebenfalls.
- Speichern/Laden/Neustart über die Seitenleiste von SugarCube; „Zurück“ (Undo) funktioniert.

## Abweichungen vom Original

| Thema | Original | Hier |
|---|---|---|
| Sprache | Englisch | Deutsch, eigene Formulierungen (Orts-, Objekt- und Systemtexte) |
| Zufall | zeitgesteuert, Wiederbelebung nach Punktabzug | gleiche Regeln, Zufall über SugarCubes seedbare Zufallszahlen (Speicherstände bleiben konsistent) |
| Zwergenmesser | ca. 9,5 % Trefferchance je Messer | **5 %**, höchstens zwei Messer pro Zug (weniger Zufallssterben) |
| Zauberer-/Öffnungszeiten, Magische-Wort-Wartung | vorhanden | entfällt (`stunden` gibt eine Notiz aus) |
| Speichern („suspend“) | Dump | SugarCube-Speicherstände |
| Bedienung | nur Texteingabe | Hybrid aus Klick und Eingabe |

Unverändert übernommen: Reisetabelle (inkl. Bedingungen und Wahrscheinlichkeiten), Vokabular,
Objektzustände, Punktesystem (350 Punkte, Hinweiskosten, Todesstrafen), Lampenlaufzeit (330 Züge,
Batteriewechsel am Automaten), Troll-Brücke mit Mautschatz, Eier-Rückholung per
`fee fie foe foo`, Schließung (15/25 Züge), Endspiel mit Stab und `blast`.

## Projektstruktur

```
colossal-cave.html       fertig gebautes Spiel (SugarCube eingebettet)
colossal-cave.twee       dieselbe Geschichte als Twee-3-Quelltext
src/advent.dat           Originaldaten (Woods, 350 Punkte), Quelle: python-adventure
src/engine.js            Spiel-Engine (Parser, Reisen, Zwerge, Pirat, Endspiel, Oberfläche)
src/texts_rooms.py       deutsche Raumtexte (lang/kurz)
src/texts_misc.py        deutsche Objekt- und Systemtexte
src/style.css            Retro-Terminal-Look
src/build.py             Generator: .dat + Texte → .twee + .html
tests/                   Headless-Tests (Node), Walkthrough, Fuzzing
vendor/sc/sugarcube-2/   SugarCube 2.37.3 (BSD-2-Clause), nur als Build-Vorlage
```

Neu bauen: `python -I src/build.py` (Python 3, keine weiteren Pakete).

## Tests

```
node tests/data-check.js     # Erreichbarkeit aller Räume, fehlende Texte
node tests/fuzz.js           # 40 Zufallsspiele à 1500 Befehle, keine Abstürze
node tests/walkthrough.js    # Sean-Palmer-Lösung (englisch) bis zum Ende
node tests/endgame.js        # Lösung + Warten auf Schließung + Sprengen
```

Optionaler Test-Hook für Browser-Screenshots: `ADV_HOOK=1 python -I src/build.py`, danach die HTML-Datei
mit `#play=rein;nimm%20lampe` aufrufen (nicht für die ausgelieferte Datei verwenden).

Mit der gemeinfreien 350-Punkte-Lösung von Sean L. Palmer
(`tests/walkthrough-350.txt`, Zwerge werden vom Testskript mit der Axt erledigt) erreicht der Lauf
**350 von 350 Punkten** (Seeds, bei denen kein Zwerg oder Pirat dazwischenfunkt).

## Hinweise und bekannte Einschränkungen

- Bei „kill dragon“ wie im Original: Rückfrage „Womit? Mit bloßen Händen?“ → `ja`.
- Der Troll verlangt bei jeder Überquerung einen Schatz (originalgetreu); die Eier kommen per
  `fee fie foe foo` im Riesenraum zurück. Mit dem Bären (zahm, folgt dir) lässt sich der Troll
  vertreiben – aber nicht mit dem Bären über die Brücke gehen.
- Der Zufall der Zwerge/des Piraten folgt dem Original *sinngemäß*, ist aber nicht
  bitgenau reproduziert (andere Zufallsquelle).
- Oberfläche in Headless-Chrome (Desktop-Breite) per Screenshot geprüft; ein echtes Smartphone
  wurde nicht getestet.

## Lizenzen

- Spieldaten und -logik: *Adventure*, Will Crowther / Don Woods (1976/77), ursprüngliches Werk
  seit Jahrzehnten frei verbreitet; die deutschen Texte sind eigene Formulierungen.
- SugarCube 2: BSD-2-Clause, © Thomas Michael Edwards (Lizenz unter `vendor/sc/sugarcube-2/LICENSE`).
- Testlösung: Sean L. Palmer, gemeinfrei.
