# -*- coding: utf-8 -*-
"""Baut aus advent.dat + deutschen Texten die Twine-Story (Twee + SugarCube-HTML).

Aufruf:  python -I build.py
Ausgabe: ../colossal-cave.twee, ../colossal-cave.html
"""
import json, os, re, sys, html, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.abspath(os.path.join(HERE, ".."))

from texts_rooms import ROOMS
from texts_misc import OBJ, MSG, UI, RANKS

# ------------------------------------------------------------------ Daten lesen
raw = open(os.path.join(HERE, "advent.dat"), encoding="latin1").read().replace("\r", "")
lines = raw.split("\n")
sections = {}
cur = None
for ln in lines:
    if re.fullmatch(r"\d+", ln.strip() or "x"):
        cur = int(ln.strip()); sections[cur] = []; continue
    if ln.strip() == "-1" or ln.startswith("-1\t"):
        continue
    if cur is not None and ln != "":
        sections[cur].append(ln)

# 3: Reisetabelle
travel = {}
for ln in sections[3]:
    p = [int(x) for x in ln.split("\t") if x.strip()]
    loc, x, verbs = p[0], p[1], p[2:]
    travel.setdefault(loc, []).append([x, verbs])

# Verb-Vererbung: eine Folgezeile mit nur dem ersten Verb der vorigen Zeile gilt fuer
# deren gesamte Verbliste (Ausweichziel, wenn die Bedingung der vorigen Zeile scheitert).
for loc, rows in travel.items():
    for i in range(1, len(rows)):
        prev, cur = rows[i - 1], rows[i]
        if len(cur[1]) == 1 and len(prev[1]) > 1 and prev[1][0] == cur[1][0]:
            cur[1] = list(prev[1])

# 4: Vokabular (englisch, auf 5 Zeichen gekuerzt)
vocab = {}
for ln in sections[4]:
    p = ln.split("\t")
    code = int(p[0]); w = p[1].strip().lower()
    w = re.sub(r"[^a-z0-9?]", "", w)
    if w and w not in vocab:
        vocab[w] = code

# 7: Objektplatzierung
place0 = {}
for ln in sections[7]:
    p = [int(x) for x in ln.split("\t") if x.strip()]
    place0[p[0]] = [p[1], p[2] if len(p) > 2 else 0]

# 9: Raumbedingungen
bits = {}
for ln in sections[9]:
    p = [int(x) for x in ln.split("\t") if x.strip()]
    bits.setdefault(p[0], []).extend(p[1:])

# 11: Hinweise
hints = []
for ln in sections[11]:
    p = [int(x) for x in ln.split("\t") if x.strip()]
    hints.append(p)

# ------------------------------------------------------------------ Deutsches Vokabular
def norm(s):
    s = s.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9?]", "", s)

DE = {}
def add(code, words):
    for w in words.split():
        n = norm(w)
        if n and n not in DE:
            DE[n] = code

# Bewegungen
add(43, "osten ost o")
add(44, "westen west w")
add(45, "norden nord n")
add(46, "sueden süden süd s")
add(47, "nordost no")
add(48, "suedost südost so")
add(49, "suedwest südwest sw")
add(50, "nordwest nw")
add(29, "hoch hinauf rauf oben aufwaerts aufwärts auf aufsteigen nach-oben")
add(30, "runter hinunter hinab unten abwaerts abwärts ab absteigen herunter")
add(19, "rein hinein hinein-gehen drinnen innen ins")
add(11, "raus hinaus aus ausgang verlassen verlass")
add(3, "betreten eintreten eingang")
add(2, "strasse straße weg huegel hügel")
add(4, "stromauf flussaufwaerts flussaufwärts bachaufwaerts bachaufwärts")
add(5, "stromab flussabwaerts flussabwärts bachabwaerts bachabwärts")
add(6, "wald")
add(7, "vorwaerts vorwärts weiter geradeaus")
add(8, "zurueck zurück zurueckgehen")
add(9, "tal")
add(10, "treppe")
add(12, "gebaeude gebäude haus")
add(13, "rinne")
add(14, "bach fluss")
add(15, "fels felsen stein")
add(16, "bett bachbett")
add(17, "kriechen kriechgang kraxeln")
add(18, "geroell geröll")
add(20, "oberflaeche oberfläche")
add(21, "nirgends nichts")
add(22, "dunkel dunkelheit")
add(23, "gang tunnel durchgang")
add(24, "niedrig")
add(25, "schlucht canyon")
add(26, "unbequem")
add(27, "riese riesig")
add(28, "aussicht blick")
add(31, "grube")
add(32, "draussen draußen")
add(33, "spalt ritze")
add(34, "stufen")
add(35, "kuppel dom")
add(36, "links")
add(37, "rechts")
add(38, "halle")
add(39, "springen spring huepfen hüpfen")
add(40, "oede öde kahl")
add(41, "hinueber hinüber ueber über")
add(42, "ueberqueren überqueren queren")
add(51, "schutt")
add(52, "loch")
add(53, "wand")
add(54, "gebrochen")
add(56, "klettern klettere kletter erklimme")
add(57, "schau schaue schauen sieh sehen untersuche untersuchen betrachte umschauen l")
add(58, "boden")
add(59, "raum")
add(60, "schlitz")
add(61, "platte plattenraum")
add(63, "senke")
add(66, "geheim")
add(67, "hoehle höhle")
add(69, "kreuzen")
add(70, "bettdecke bettdeckengang")
add(72, "orientalisch")
add(73, "kaverne")
add(74, "muschelraum")
add(75, "reservoir")
add(76, "hauptbuero hauptbüro buero büro")
add(77, "gabelung")
# Gegenstaende
add(1001, "schluessel schlüssel schluesselbund schlüsselbund")
add(1002, "lampe laterne licht")
add(1003, "gitter tor gitterrost")
add(1004, "kaefig käfig")
add(1005, "stab rute stock")
add(1007, "stufen")
add(1008, "vogel")
add(1009, "tuer tür tuere türe")
add(1010, "kissen samtkissen")
add(1011, "schlange")
add(1012, "kluft spalte riss")
add(1013, "tafel steintafel")
add(1014, "muschel riesenmuschel")
add(1015, "auster riesenauster")
add(1016, "zeitschrift magazin heft")
add(1017, "zwerg zwerge")
add(1018, "messer")
add(1019, "essen proviant nahrung futter")
add(1020, "flasche")
add(1021, "wasser")
add(1022, "oel öl")
add(1023, "spiegel")
add(1024, "pflanze bohne bohnen ranke bohnenranke")
add(1026, "stalaktit")
add(1027, "gestalt schatten figur")
add(1028, "axt beil")
add(1029, "zeichnungen zeichnung")
add(1030, "pirat")
add(1031, "drache drachen")
add(1032, "abgrund schlund")
add(1033, "troll")
add(1035, "baer bär")
add(1036, "nachricht botschaft")
add(1037, "vulkan geysir")
add(1038, "automat verkaufsautomat")
add(1039, "batterien batterie akku")
add(1040, "moos vorhang vorhaenge vorhänge")
add(1050, "gold goldklumpen klumpen nugget")
add(1051, "diamanten diamant")
add(1052, "silber silberbarren")
add(1053, "schmuck juwelen")
add(1054, "muenzen münzen geld")
add(1055, "truhe kiste schatztruhe")
add(1056, "eier ei nest")
add(1057, "dreizack")
add(1058, "vase ming")
add(1059, "smaragd")
add(1060, "pyramide platinpyramide")
add(1061, "perle")
add(1062, "teppich perserteppich")
add(1063, "gewuerze gewürze")
add(1064, "kette goldkette")
# Aktionen
add(2001, "nimm nehme nehmen nimmt hol fang fange fangen stiehl hebe heb aufheben")
add(2002, "lass lasse lege leg ablegen fallenlassen ablegen weglegen entlasse")
add(2003, "sage sag sprich sprecher rufe ruf singe sing")
add(2004, "oeffne öffne oeffnen öffnen aufschliessen aufschließen schliesse-auf entriegle aufsperren")
add(2006, "schliesse schließe schliessen schließen verschliesse verschließe zusperren zumachen abschliessen abschließen sperre")
add(2007, "anzuenden anzünden zuende zünde entzuende entzünde anmachen einschalten schalte-an")
add(2008, "loesche lösche ausmachen ausschalten ausloeschen auslöschen")
add(2009, "schwenke schwenken schwinge winke winken schuettle schüttle")
add(2010, "beruhige zaehme zähme")
add(2011, "gehe geh laufe lauf renne folge folgen")
add(2012, "attackiere angreifen greife greif greifen toete töte toeten töten kaempfe kämpfe schlage schlag erschlage haue hau ermorde")
add(2013, "giesse gieße giessen gießen schuette schütte leere")
add(2014, "iss esse essen verschlinge")
add(2015, "trinke trink trinken saufe")
add(2016, "reibe reib polier poliere")
add(2017, "wirf werfe schleudere schmeiss schmeiß")
add(2018, "ende beenden aufgeben quit")
add(2019, "finde finden suche wo")
add(2020, "inventar i inv")
add(2021, "fuettere füttere fuettern füttern")
add(2022, "fuelle fülle befuelle befülle fuellen füllen")
add(2023, "sprenge sprengen explodiere blast zuende-sprengen")
add(2024, "punkte punktestand score")
add(2026, "kurz brief")
add(2027, "lies lese lesen")
add(2028, "zerbrich zerbreche zerschlage zertruemmere zertrümmere zerstoere zerstöre")
add(2029, "wecke wecken stoere störe")
add(2030, "speichern pause")
add(2031, "oeffnungszeiten öffnungszeiten stunden")
add(3051, "hilfe hilf ?")
add(3142, "info")
add(3064, "baum baeume bäume")
add(3066, "grabe graben")
add(3147, "schwimme schwimmen")
add(3068, "verloren")
add(3069, "nebel dunst")
add(3139, "stop stopp")

for w, c in DE.items():   # deutsche Woerter ueberschreiben
    vocab[w] = c

# erstes deutsches Wort je Objekt (fuer Buttons)
first_word = {}
for w, c in DE.items():
    if 1000 < c < 2000 and (c - 1000) not in first_word:
        first_word[c - 1000] = w
# stabil: lesbare Befehlswoerter
first_word.update({1: "schluessel", 2: "lampe", 4: "kaefig", 5: "stab", 6: "stab", 8: "vogel", 10: "kissen",
                   14: "muschel", 15: "auster", 16: "zeitschrift", 18: "messer", 19: "essen", 20: "flasche",
                   28: "axt", 35: "baer", 39: "batterien", 50: "gold", 51: "diamanten", 52: "silber",
                   53: "schmuck", 54: "muenzen", 55: "truhe", 56: "eier", 57: "dreizack", 58: "vase",
                   59: "smaragd", 60: "pyramide", 61: "perle", 62: "teppich", 63: "gewuerze", 64: "kette",
                   24: "pflanze"})

# ------------------------------------------------------------------ Datenblock fuer die Engine
ui = dict(UI)
ui.update({
    "zwerge": "In diesem Raum sind {0} bedrohliche kleine Zwerge bei dir!",
    "messer": "{0} scharfe, gemeine Messer werden nach dir geworfen!",
    "getroffen": "{0} davon treffen dich!",
    "maut_zurueck": "In der Aufregung hat der Troll deinen Schatz fallen lassen – er liegt nun am Rand der Brücke.",
    "speichern": "Zum Speichern und Laden benutze die Menüleiste am linken Rand (Speichern / Laden).",
    "stunden": "Die Höhle ist für Abenteurer jederzeit geöffnet.",
})
obj_out = {}
for k, v in OBJ.items():
    d = {"name": v.get("name", "")}
    for kk, vv in v.items():
        if kk != "name":
            d[str(kk)] = vv
    obj_out[k] = d

data = {
    "travel": travel,
    "vocab": vocab,
    "place0": place0,
    "light": bits.get(0, []),
    "oilrooms": bits.get(1, []),
    "liquid": bits.get(2, []),
    "nopirate": bits.get(3, []),
    "hintrooms": {str(k): v for k, v in bits.items() if k >= 4},
    "hints": hints,
    "msg": {str(k): v for k, v in MSG.items()},
    "obj": {str(k): v for k, v in obj_out.items()},
    "ui": ui,
    "ranks": RANKS,
    "firstWord": {str(k): v for k, v in first_word.items()},
}

# ------------------------------------------------------------------ Passagen
passages = []   # (name, tags, text)

def P(name, tags, text):
    passages.append((name, tags, text))

P("StoryTitle", "", "Colossal Cave Adventure")
P("StoryInit", "", "<<run Adv.init()>>")
P("Start", "nobr", """<div class="adv-title">COLOSSAL CAVE ADVENTURE</div>
<p class="adv-sub">Das Kolossale Höhlenabenteuer – eine deutsche Twine-Adaption</p>

<p>Irgendwo in der Nähe liegt die Colossal Cave, wo andere Reichtümer in Schätzen und Gold gefunden haben.
Es heißt allerdings, dass manche, die sie betreten, nie wieder gesehen werden. Magie soll in der Höhle wirken.
Ich werde deine Augen und Hände sein.</p>

<p>Du steuerst per Klick auf die Richtungstasten und Gegenstände – oder tippst Befehle mit einem oder zwei Wörtern
ein (<em>nimm lampe</em>, <em>norden</em>, <em>xyzzy</em> …). Tippe <em>hilfe</em> für Hinweise und <em>info</em> für
die Spielregeln. Ziel: so viele der 350 Punkte sammeln wie möglich.</p>

<p class="adv-btnrow">[[Das Abenteuer beginnt|Spiel]]</p>

<p class="adv-credit">Vorlage: <em>Adventure</em> (Colossal Cave) von Will Crowther und Don Woods, 1976/77.
Raum- und Objektstruktur nach der 350-Punkte-Fassung; alle deutschen Texte sind eigene Formulierungen.</p>
""")
P("Spiel", "", "<<run Adv.consume()>><div id=\"adv-root\"></div>")

# Raeume
missing = []
for n in sorted(travel.keys()):
    pass
room_ids = set(int(x) for x in sections[1] and [l.split("\t")[0] for l in sections[1]])
for n in sorted(room_ids):
    kurz, lang = ROOMS.get(n, (None, None))
    if lang is None:
        missing.append(n); continue
    text = lang.strip()
    if kurz:
        text += "\n§§§\n" + kurz.strip()
    P("R%03d" % n, "raum", text)
if missing:
    print("WARNUNG: Raeume ohne deutschen Text:", missing)

script = open(os.path.join(HERE, "engine.js"), encoding="utf8").read().replace("\r\n", "\n")
script = "window.ADV_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n" + script
script += """
/* ---- Oberflaeche ---- */
$(document).on(':passagedisplay', function (ev) {
  if (ev.passage && ev.passage.title === 'Spiel') {
    var html = '<div class="adv-status">' + Adv.sidebar() + '</div>' + Adv.view();
    $('#adv-root').html(html);
    var lg = document.getElementById('adv-log');
    var inp = document.getElementById('advin');
    if (inp) { inp.focus({preventScroll: true}); }
    window.scrollTo(0, document.body.scrollHeight);
  }
});
$(document).on('click', '.adv-cmd', function () { Adv.run($(this).attr('data-cmd')); });
$(document).on('click', '#adv-restart', function () { Adv.restart(); });
$(document).on('submit', '#adv-form', function (e) {
  e.preventDefault();
  var v = $('#advin').val();
  if (String(v).trim() === '') { return; }
  Adv.run(v);
});
"""
if os.environ.get("ADV_HOOK"):
    script += """
/* TEST-HOOK: #play=befehl1;befehl2 */
$(document).one(':passagedisplay', function () {
  var m = location.hash.match(/play=(.*)$/);
  if (!m) { return; }
  var list = decodeURIComponent(m[1]).split(';');
  setTimeout(function () {
    SugarCube.Engine.play('Spiel');
    var i = 0;
    (function next() { if (i < list.length) { Adv.run(list[i++]); setTimeout(next, 30); } })();
  }, 50);
});
"""
P("Story JavaScript", "script", script)

css = open(os.path.join(HERE, "style.css"), encoding="utf8").read().replace("\r\n", "\n")
P("Story Stylesheet", "stylesheet", css)

# ------------------------------------------------------------------ Twee schreiben
IFID = "5C0A7E1B-3D2F-4B8A-9E6C-0C01055A1DE0"
def twee_escape_header(n):
    return n.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]").replace("{", "\\{").replace("}", "\\}")

tw = [":: StoryData", json.dumps({"ifid": IFID, "format": "SugarCube", "format-version": "2.37.3", "start": "Start"}, indent=2), ""]
for name, tags, text in passages:
    hdr = ":: " + twee_escape_header(name)
    if tags:
        hdr += " [" + tags + "]"
    tw.append(hdr)
    tw.append(text.replace("\n:: ", "\n\\:: "))
    tw.append("")
open(os.path.join(OUT, "colossal-cave.twee"), "w", encoding="utf8", newline="\n").write("\n".join(tw))

# ------------------------------------------------------------------ HTML bauen
fmt = open(os.path.join(HERE, "..", "vendor", "sc", "sugarcube-2", "format.js"), encoding="utf8").read()
m = re.search(r"window\.storyFormat\((.*)\);?\s*$", fmt, re.S)
src = json.loads(m.group(1))["source"]

def esc(s):
    return html.escape(s, quote=True)

parts = []
pid = 1
start_pid = None
for name, tags, text in passages:
    if name == "StoryTitle":
        continue
    if name == "Story Stylesheet":
        continue
    if name == "Story JavaScript":
        continue
    if name == "Start":
        start_pid = pid
    parts.append('<tw-passagedata pid="%d" name="%s" tags="%s" position="%d,%d" size="100,100">%s</tw-passagedata>'
                 % (pid, esc(name), esc(tags), 100 + (pid % 12) * 120, 100 + (pid // 12) * 120, esc(text)))
    pid += 1
story = ('<tw-storydata name="Colossal Cave Adventure" startnode="%d" creator="build.py" creator-version="1.0" '
         'ifid="%s" zoom="1" format="SugarCube" format-version="2.37.3" options="" tags="" hidden>' % (start_pid, IFID))
assert "</script" not in script.lower() and "</style" not in css.lower()
story += '<style role="stylesheet" id="twine-user-stylesheet" type="text/twine-css">%s</style>' % css
story += '<script role="script" id="twine-user-script" type="text/twine-javascript">%s</script>' % script
story += "".join(parts) + "</tw-storydata>"
out = src.replace("{{STORY_NAME}}", esc("Colossal Cave Adventure")).replace("{{STORY_DATA}}", story)
open(os.path.join(OUT, "colossal-cave.html"), "w", encoding="utf8", newline="\n").write(out)
print("OK:", len(passages), "Passagen,", os.path.getsize(os.path.join(OUT, "colossal-cave.html")) // 1024, "KB")
