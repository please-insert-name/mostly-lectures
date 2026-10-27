/* ============================================================
   COLOSSAL CAVE ADVENTURE – Twine/SugarCube-Engine
   Portierung der Logik von Crowther/Woods (350 Punkte).
   Daten (Reisetabelle, Vokabular, Texte) kommen aus ADV_DATA.
   ============================================================ */
(function () {
  "use strict";
  var D = window.ADV_DATA;
  var A = window.Adv = {};

  /* ---------- Objektnummern ---------- */
  var KEYS = 1, LAMP = 2, GRATE = 3, CAGE = 4, ROD = 5, ROD2 = 6, STEPS = 7, BIRD = 8, DOOR = 9,
      PILLOW = 10, SNAKE = 11, FISSURE = 12, TABLET = 13, CLAM = 14, OYSTER = 15, MAGAZINE = 16,
      DWARF = 17, KNIFE = 18, FOOD = 19, BOTTLE = 20, WATER = 21, OIL = 22, MIRROR = 23, PLANT = 24,
      PLANT2 = 25, STALACTITE = 26, FIGURE = 27, AXE = 28, DRAWINGS = 29, PIRATE = 30, DRAGON = 31,
      CHASM = 32, TROLL = 33, TROLL2 = 34, BEAR = 35, MESSAGE = 36, VOLCANO = 37, MACHINE = 38,
      BATTERIES = 39, MOSS = 40, GOLD = 50, DIAMONDS = 51, SILVER = 52, JEWELS = 53, COINS = 54,
      CHEST = 55, EGGS = 56, TRIDENT = 57, VASE = 58, EMERALD = 59, PYRAMID = 60, PEARL = 61,
      RUG = 62, SPICES = 63, CHAIN = 64;
  var MAXDIE = 3, MAXHOLD = 7, CHLOC = 114, CHLOC2 = 140;

  /* ---------- Hilfsfunktionen ---------- */
  function G() {
    var v = State.variables;
    if (!v.g && !A._initing) { A._initing = true; try { A.init(); } finally { A._initing = false; } }
    return v.g;
  }
  function rnd() { return State.random(); }
  function pct(n) { return rnd() * 100 < n; }
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function norm(s) {
    return String(s).toLowerCase().replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue")
      .replace(/ß/g, "ss").replace(/[^a-z0-9?\s]/g, " ").replace(/\s+/g, " ").trim();
  }
  function msgText(n) { return D.msg[n] || ""; }
  function say(t) { if (t) G().out.push(t); }
  function msg(n) { say(msgText(n)); }
  function inList(arr, v) { return arr.indexOf(v) >= 0; }
  function isTreasure(o) { return o >= 50; }
  function objName(o) { return D.obj[o] ? D.obj[o].name : ("Ding " + o); }
  function objText(o, p) { var t = D.obj[o]; return t ? t[String(p)] : null; }

  /* ---------- Orte & Objekte ---------- */
  function placeOf(o) { return G().place[o]; }
  function toting(o) { return G().place[o] === -1; }
  function at(o) { var g = G(); return g.place[o] === g.loc || g.fixed[o] === g.loc; }
  function here(o) { return toting(o) || at(o); }
  function holding() {
    var g = G(), n = 0;
    for (var k in g.place) { if (g.place[k] === -1 && +k !== WATER && +k !== OIL) { n++; } }
    return n;
  }
  function move(o, loc) { G().place[o] = loc; }
  function carry(o) {
    var g = G();
    if (o <= 100 && g.place[o] === -1) { return; }
    g.place[o] = -1;
    g.fixed[o] = 0;
  }
  function dropAt(o, loc) { G().place[o] = loc; }
  function destroy(o) { G().place[o] = 0; }
  function put(o, loc, prop) { var g = G(); g.place[o] = loc; g.prop[o] = prop; g.fixed[o] = 0; }
  function liq() {   // Inhalt der Flasche: Wasser, Oel oder 0
    var g = G(), b = g.prop[BOTTLE];
    if (b === 0) { return WATER; }
    if (b === 2) { return OIL; }
    return 0;
  }
  function liqLoc(loc) {
    if (!inList(D.liquid, loc)) { return 0; }
    return inList(D.oilrooms, loc) ? OIL : WATER;
  }
  function lit(loc) {
    var g = G();
    if (inList(D.light, loc)) { return true; }
    return g.prop[LAMP] === 1 && here(LAMP);
  }
  function forced(loc) {
    var rows = D.travel[loc];
    if (!rows || !rows.length) { return false; }
    return rows[0][1].indexOf(1) >= 0;
  }

  /* ---------- Initialisierung ---------- */
  A.init = function () {
    var g = { loc: 1, oldloc: 1, oldloc2: 1, turns: 0, limit: 330, lmwarn: false, numdie: 0,
      gaveup: false, closing: false, closed: false, clock1: 15, clock2: 25, tally: 15,
      dflag: 0, dloc: [19, 27, 33, 44, 64, CHLOC], odloc: [0, 0, 0, 0, 0, 0], dseen: [0, 0, 0, 0, 0, 0],
      visit: {}, brief: false, hintct: {}, hintgiven: {}, hintscore: 0, pending: null,
      over: false, bonus: 0, foobar: 0, detail: 0, log: [], out: [], prop: {}, place: {}, fixed: {},
      dkilled: 0, firstturn: true, cmdcount: 0, ended: "" };
    for (var o in D.place0) {
      g.place[o] = D.place0[o][0];
      g.fixed[o] = D.place0[o][1];
      g.prop[o] = isTreasure(+o) ? -1 : 0;
    }
    for (var i = 1; i <= 64; i++) {
      if (g.place[i] === undefined) { g.place[i] = 0; g.fixed[i] = 0; g.prop[i] = isTreasure(i) ? -1 : 0; }
    }
    g.prop[CHEST] = -1; g.prop[PEARL] = -1;
    State.variables.g = g;
    g.out = [];
    msg(1);
    g.out.push("<hr>");
    look(true);
    flushLog("");
  };

  /* ---------- Log ---------- */
  function flushLog(cmdText) {
    var g = G();
    g.log.push({ c: cmdText, o: g.out });
    if (g.log.length > 14) { g.log.shift(); }
    g.out = [];
  }

  /* ---------- Beschreibung ---------- */
  function roomTexts(loc) {
    var p = Story.has("R" + ("00" + loc).slice(-3)) ? Story.get("R" + ("00" + loc).slice(-3)).text : "";
    var parts = p.split(/\r?\n§§§\r?\n/);
    var longT = parts[0].trim();
    var shortT = parts.length > 1 ? parts[1].trim() : "";
    return { long: longT, short: shortT || longT };
  }
  function itemLines(loc) {
    var g = G(), out = [];
    var ids = [];
    for (var k in g.place) {
      var o = +k;
      if (g.place[o] === loc || (g.fixed[o] === loc && g.place[o] !== -1)) { ids.push(o); }
    }
    ids.sort(function (a, b) { return a - b; });
    ids.forEach(function (o) {
      if (g.place[o] === -1) { return; }
      if (g.closed && (loc === 115 || loc === 116)) { return; }
      if (o === BEAR && g.prop[BEAR] === 2 && toting(BEAR)) { return; }
      if (o === BIRD && g.prop[BIRD] === 1 && toting(CAGE)) { return; }
      var p = g.prop[o];
      if (p < 0) {                       // Schatz zum ersten Mal gesehen
        if (g.closed) { return; }
        g.prop[o] = (o === RUG || o === CHAIN) ? 1 : 0;
        g.tally--;
        p = g.prop[o];
      }
      var idx = p;
      if (o === STEPS && loc === g.fixed[STEPS]) { idx = 1; }
      var t = objText(o, idx);
      if (o === BEAR) { t = objText(BEAR, p); }
      if (t) { g.out.push(t); }
    });
  }
  function look(forceLong) {
    var g = G(), loc = g.loc;
    if (!lit(loc)) {
      msg(16);
      return;
    }
    var t = roomTexts(loc);
    var first = !g.visit[loc];
    var useLong = forceLong || first || (!g.brief && (g.visit[loc] % 5 === 0));
    g.visit[loc] = (g.visit[loc] || 0) + 1;
    var txt = useLong ? t.long : t.short;
    if (txt) { g.out.push(txt); }
    if (loc === 33 && g.visit[loc] === 1) { /* Y2 */ }
    // Bruecke, Stalaktit usw. stehen im Objekttext
    if (toting(BEAR) && g.prop[BEAR] === 2) { msg(141); }
    itemLines(loc);
  }
  function roomName(loc) {
    var t = roomTexts(loc).short;
    var m = t.split(/[.!]/)[0];
    return m.length > 60 ? "" : m;
  }

  /* ---------- Tod, Ende, Punkte ---------- */
  function score(final) {
    var g = G(), s = 2;
    for (var i = 50; i <= 64; i++) {
      var k = i < CHEST ? 12 : (i === CHEST ? 14 : 16);
      if (g.prop[i] >= 0) { s += 2; }
      if (g.place[i] === 3 && g.prop[i] === 0) { s += k - 2; }
    }
    s += (MAXDIE - g.numdie) * 10;
    if (!g.gaveup) { s += 4; }
    if (g.dflag > 0) { s += 25; }
    if (g.closing) { s += 25; }
    if (g.closed) {
      if (g.bonus === 0) { s += 10; }
      else if (g.bonus === 135) { s += 25; }
      else if (g.bonus === 134) { s += 30; }
      else if (g.bonus === 133) { s += 45; }
    }
    if (g.place[MAGAZINE] === 108) { s += 1; }
    s -= g.hintscore;
    return Math.max(0, s);
  }
  function rank(s) {
    for (var i = 0; i < D.ranks.length; i++) { if (s <= D.ranks[i][0]) { return D.ranks[i][1]; } }
    return "";
  }
  function finish(reasonMsg) {
    var g = G();
    var s = score(true);
    g.out.push("<hr>");
    g.out.push("<strong>" + esc(D.ui.ende_titel) + "</strong>");
    g.out.push(esc(D.ui.punkte.replace("{0}", s).replace("{1}", g.turns)));
    g.out.push(esc(rank(s)));
    g.over = true;
    g.pending = null;
  }
  function die() {
    var g = G();
    g.numdie++;
    var dl = (g.loc === 20 || g.loc === 21 || g.loc === 0) ? g.oldloc : g.loc;
    if (g.closing || g.closed) { msg(131); finish(); return; }
    if (g.numdie >= MAXDIE) { msg(81 + (g.numdie - 1) * 2); finish(); return; }
    g.pending = { type: "reinc", n: g.numdie, dl: dl };
    msg(81 + (g.numdie - 1) * 2);
  }
  function reincarnate() {
    var g = G(), p = g.pending;
    msg(82 + (p.n - 1) * 2);
    g.pending = null;
    if (toting(LAMP)) { put(LAMP, 1, 0); }
    for (var k in g.place) {
      if (g.place[k] === -1) { g.place[k] = p.dl; }
    }
    g.prop[BIRD] = g.prop[BIRD];
    g.loc = g.oldloc = g.oldloc2 = 3;
    g.out.push("<hr>");
    look(true);
  }

  /* ---------- Reisen ---------- */
  function cond(m, trav) {
    var g = G();
    if (m === 0) { return true; }
    if (m < 100) { return pct(m); }
    if (m === 100) { return true; }
    if (m <= 200) { return toting(m - 100); }
    if (m <= 300) { return toting(m - 200) || at(m - 200); }
    return g.prop[m % 100] !== (Math.floor(m / 100) - 3);
  }
  function describeAfterMove() {
    var g = G();
    if (g.loc === 0) { return; }
    look(false);
  }
  function goVerb(verb, skipCount) {
    var g = G();
    var rows = D.travel[g.loc] || [];
    var found = false;
    for (var i = 0; i < rows.length; i++) {
      var x = rows[i][0], vs = rows[i][1];
      if (vs.indexOf(verb) < 0) { continue; }
      found = true;
      var m = Math.floor(x / 1000), n = x % 1000;
      if (!cond(m)) { continue; }
      if (n <= 300) { return enter(n); }
      if (n > 500) { msg(n - 500); return false; }
      if (n === 301) {
        var hold = holding();
        if (hold === 0 || (hold === 1 && toting(EMERALD))) { return enter(99 + 100 - g.loc); }
        msg(117); return false;
      }
      if (n === 302) { dropAt(EMERALD, g.loc); continue; }
      if (n === 303) { return bridge(); }
    }
    if (!found) { return null; }
    return false;
  }
  function bridge() {
    var g = G();
    if (g.prop[TROLL] === 1) {                 // Troll tritt beim zweiten Mal wieder hervor
      say(objText(TROLL, 1));
      g.prop[TROLL] = 0;
      destroy(TROLL2); g.fixed[TROLL2] = 0;
      g.place[TROLL] = 117; g.fixed[TROLL] = 122;
      return false;
    }
    var dest = g.loc === 117 ? 122 : 117;
    if (g.prop[TROLL] === 0) { g.prop[TROLL] = 1; }
    if (toting(BEAR)) {
      msg(162);
      g.prop[CHASM] = 1; g.prop[TROLL] = 2;
      dropAt(BEAR, dest); g.fixed[BEAR] = -1; g.prop[BEAR] = 3;
      g.oldloc = dest;
      g.loc = 21;
      die();
      return true;
    }
    return enter(dest);
  }
  function enter(newloc) {
    var g = G();
    var from = g.loc;
    var wasDark = !lit(from);
    g.oldloc2 = g.oldloc;
    g.oldloc = from;
    g.loc = newloc;
    if (newloc === 0 || newloc === 20 || newloc === 21) {
      // Todesfaelle: Text, dann Tod
      var t = (newloc === 0) ? "" : roomTexts(newloc).long;
      if (t) { say(t); }
      die();
      return true;
    }
    if (forced(newloc)) {
      var tx = roomTexts(newloc).long;
      if (tx) { say(tx); }
      var guard = 0;
      while (forced(g.loc) && guard++ < 6 && !g.over && !g.pending) {
        var r = goVerb(1);
        if (r === null || r === false) { break; }
      }
      return true;
    }
    if (wasDark && !lit(newloc) && newloc >= 15 && pct(35)) {
      msg(23);
      die();
      return true;
    }
    describeAfterMove();
    return true;
  }

  /* ---------- Bewegung per Wort ---------- */
  function motion(m) {
    var g = G();
    if (m === 21 || m === 22) { msg(54); return; }
    if (m === 57) { g.detail++; look(true); return; }
    if (m === 59 || m === 58) { msg(m === 59 ? 138 : 138); return; }
    if (m === 67) { if (g.loc < 8) { msg(57); } else { msg(58); } return; }
    if (m === 8) {
      var k = g.oldloc;
      if (forced(k)) { k = g.oldloc2; }
      if (k === g.loc) { msg(91); return; }
      var rows = D.travel[g.loc] || [];
      for (var i = 0; i < rows.length; i++) {
        var n = rows[i][0] % 1000;
        if (n === k) { enter(k); return; }
      }
      msg(140);
      return;
    }
    if (m === 2 && g.loc > 8) { msg(9); return; }
    if (m === 42 || m === 69) {
      var rr = D.travel[g.loc] || [];
      for (var q = 0; q < rr.length; q++) { if (rr[q][1].indexOf(41) >= 0 && rr[q][1].indexOf(m) < 0) { m = 41; break; } }
    }
    var n0 = g.out.length, l0 = g.loc;
    var r = goVerb(m);
    if (r === false && g.out.length === n0 && g.loc === l0) { msg(9); return; }
    if (r === null) {
      if (m === 62 || m === 65 || m === 71) { msg(42); return; }
      if (inList([29, 30, 43, 44, 45, 46, 47, 48, 49, 50], m)) { msg(9); }
      else if (inList([7, 36, 37, 68], m)) { msg(10); }
      else if (inList([11, 19], m)) { msg(11); }
      else if (m === 3 || m === 4 || m === 5) { msg(12); }
      else if (m === 12 && g.loc < 8) { msg(12); }
      else { msg(12); }
    }
  }

  /* ---------- Zug-Ende: Zwerge, Pirat, Lampe, Schliessung ---------- */
  function atDwarf() {
    var g = G();
    for (var i = 0; i < 5; i++) { if (g.dloc[i] === g.loc && g.dseen[i]) { return i + 1; } }
    return 0;
  }
  function dwarfMove(i) {
    var g = G(), here0 = g.dloc[i];
    var rows = D.travel[here0] || [], opts = [];
    rows.forEach(function (r) {
      var m = Math.floor(r[0] / 1000), n = r[0] % 1000;
      if (n > 300 || n < 15) { return; }
      if (n === g.odloc[i] || n === here0) { return; }
      if (forced(n) || inList(D.nopirate, n)) { return; }
      if (m === 100) { return; }
      if (r[1].indexOf(1) >= 0) { return; }
      opts.push(n);
    });
    if (!opts.length) { return here0; }
    return opts[Math.floor(rnd() * opts.length)];
  }
  function dwarvesAndPirate() {
    var g = G();
    if (g.loc === 0 || forced(g.loc) || inList(D.nopirate, g.loc)) { return; }
    if (g.dflag === 0) { if (g.loc >= 15) { g.dflag = 1; } return; }
    if (g.dflag === 1) {
      if (g.loc < 15 || !pct(5)) { return; }
      g.dflag = 2;
      for (var q = 0; q < 2; q++) { if (pct(50)) { g.dloc[Math.floor(rnd() * 5)] = 0; } }
      for (var z = 0; z < 5; z++) { if (g.dloc[z] === g.loc) { g.dloc[z] = 18; } g.odloc[z] = g.dloc[z]; }
      msg(3);
      dropAt(AXE, g.loc);
      return;
    }
    var dtotal = 0, attack = 0, stick = 0;
    for (var i = 0; i < 6; i++) {
      if (g.dloc[i] === 0) { continue; }
      var nl = dwarfMove(i);
      g.odloc[i] = g.dloc[i];
      g.dloc[i] = nl;
      var seen = (g.dseen[i] && g.loc >= 15) || g.dloc[i] === g.loc || g.odloc[i] === g.loc;
      g.dseen[i] = seen ? 1 : 0;
      if (seen) {
        g.dloc[i] = g.loc;
        if (i === 5) { pirate(); }
        else {
          dtotal++;
          if (g.odloc[i] === g.dloc[i] && attack < 2) {   // hoechstens zwei Messer pro Zug
            attack++;
            if (rnd() * 1000 < 50 * (g.dflag - 2)) { stick++; }
          }
        }
      }
    }
    if (dtotal === 0) { return; }
    if (dtotal === 1) { msg(4); } else { say(D.ui.zwerge.replace("{0}", dtotal)); }
    if (attack === 0) { return; }
    if (g.dflag === 2) { g.dflag = 3; }
    if (attack === 1) { msg(5); } else { say(D.ui.messer.replace("{0}", attack)); }
    if (stick === 0) { msg(6); if (attack > 1) { return; } return; }
    if (stick === 1) { msg(7); } else { say(D.ui.getroffen.replace("{0}", stick)); }
    g.loc = 21;
    die();
  }
  function pirate() {
    var g = G();
    if (g.loc === CHLOC || g.prop[CHEST] >= 0) { return; }
    var k = false;
    for (var i = 50; i <= 64; i++) {
      if (i === PYRAMID && (g.loc === g.place[PYRAMID] || g.loc === g.place[EMERALD])) { continue; }
      if (toting(i) || (g.place[i] === g.loc && g.prop[i] >= 0)) { k = true; break; }
    }
    if (!k) {
      if (g.tally === 1 && g.place[CHEST] === 0 && here(LAMP) && g.prop[LAMP] === 1) {
        msg(186);
        move(CHEST, CHLOC); move(MESSAGE, CHLOC2);
        g.dloc[5] = CHLOC; g.odloc[5] = CHLOC; g.dseen[5] = 0;
        return;
      }
      if (g.odloc[5] !== g.dloc[5] && pct(20)) { msg(127); }
      return;
    }
    msg(128);
    if (g.place[CHEST] === 0) { move(CHEST, CHLOC); move(MESSAGE, CHLOC2); }
    for (var j = 50; j <= 64; j++) {
      if (j === PYRAMID && (g.loc === g.place[PYRAMID] || g.loc === g.place[EMERALD])) { continue; }
      if ((g.place[j] === g.loc && g.fixed[j] === 0) || toting(j)) {
        if (g.place[j] === g.loc && j === 62 && g.prop[DRAGON] === 0) { continue; }
        g.place[j] = CHLOC;
        if (g.prop[j] < 0) { g.prop[j] = 0; }
      }
    }
    g.dloc[5] = CHLOC; g.odloc[5] = CHLOC; g.dseen[5] = 0;
  }
  function closingBegins() {
    var g = G();
    g.prop[GRATE] = 0; g.prop[FISSURE] = 0;
    for (var i = 0; i < 6; i++) { g.dseen[i] = 0; g.dloc[i] = 0; }
    g.place[TROLL] = 0; g.fixed[TROLL] = 0;
    g.place[TROLL2] = 117; g.fixed[TROLL2] = 122;
    if (g.prop[CHASM] !== 0) { g.prop[CHASM] = 0; }
    if (g.prop[BEAR] !== 3) { destroy(BEAR); }
    g.prop[CHAIN] = 0; g.fixed[CHAIN] = 0;
    g.prop[AXE] = 0; g.fixed[AXE] = 0;
    msg(129);
    g.closing = true;
  }
  function closedNow() {
    var g = G();
    put(BOTTLE, 115, 1); put(PLANT, 115, 0); put(OYSTER, 115, 0); put(LAMP, 115, 0);
    put(ROD, 115, 0); put(DWARF, 115, 0);
    g.loc = g.oldloc = g.oldloc2 = 115;
    put(GRATE, 116, 0); put(SNAKE, 116, 1); put(BIRD, 116, 1); put(CAGE, 116, 0);
    put(ROD2, 116, 0); put(PILLOW, 116, 0);
    put(MIRROR, 115, 0); g.fixed[MIRROR] = 116;
    for (var i = 1; i <= 64; i++) { if (g.place[i] === -1) { g.place[i] = 0; } }
    msg(132);
    g.closed = true;
    g.out.push("<hr>");
    look(true);
  }
  function hintCheck() {
    var g = G();
    D.hints.forEach(function (h) {
      var no = h[0], thr = h[1], cost = h[2];
      if (thr === 9999) { return; }
      var rooms = D.hintrooms[no] || [];
      if (g.hintgiven[no]) { return; }
      if (rooms.indexOf(g.loc) < 0) { g.hintct[no] = 0; return; }
      g.hintct[no] = (g.hintct[no] || 0) + 1;
      if (g.hintct[no] >= thr && !g.pending && !g.over) {
        g.hintct[no] = 0;
        g.pending = { type: "hintq", no: no, q: h[3], a: h[4], cost: cost };
        say(msgText(h[3]));
      }
    });
  }
  function trollScare() {
    var g = G();
    if (!toting(BEAR) || !at(TROLL)) { return; }
    msg(163);
    g.place[TROLL] = 0; g.fixed[TROLL] = 0;
    g.place[TROLL2] = 117; g.fixed[TROLL2] = 122;
    g.prop[TROLL] = 2;
  }
  function endTurn() {
    var g = G();
    if (g.over || g.pending) { return; }
    g.turns++;
    trollScare();
    // Schliessung
    if (!g.closing && g.tally === 0 && g.loc >= 15 && g.loc !== 33 && !g.closed) {
      g.clock1--;
      if (g.clock1 === 0) { closingBegins(); }
    } else if (g.closing && !g.closed) {
      g.clock2--;
      if (g.clock2 === 0) { closedNow(); return; }
    }
    if (g.closed) { return; }
    dwarvesAndPirate();
    if (g.over || g.pending) { return; }
    // Lampe
    if (g.prop[LAMP] === 1) { g.limit--; }
    if (g.limit <= 30 && here(BATTERIES) && g.prop[BATTERIES] === 0 && here(LAMP)) {
      msg(188);
      g.prop[BATTERIES] = 1;
      if (toting(BATTERIES)) { dropAt(BATTERIES, g.loc); }
      g.limit += 2500; g.lmwarn = false;
    } else if (g.limit === 0) {
      g.limit = -1; g.prop[LAMP] = 0;
      if (here(LAMP)) { msg(184); }
    } else if (g.limit < 0 && g.loc <= 8) {
      msg(185); g.gaveup = true; finish(); return;
    } else if (g.limit <= 30 && !g.lmwarn && here(LAMP)) {
      g.lmwarn = true;
      if (g.place[BATTERIES] === 0) { msg(183); }
      else if (g.prop[BATTERIES] === 1) { msg(189); }
      else { msg(187); }
    }
    hintCheck();
  }

  /* ---------- Aktionen ---------- */
  function listInventory() {
    var g = G(), items = [];
    for (var k in g.place) {
      var o = +k;
      if (g.place[o] === -1 && o !== BEAR && o !== WATER && o !== OIL) { items.push(o); }
    }
    items.sort(function (a, b) { return a - b; });
    if (!items.length && !toting(BEAR)) { msg(98); return; }
    msg(99);
    items.forEach(function (o) {
      var n = objName(o);
      if (o === BOTTLE) { n = ["Flasche mit Wasser", "Leere Flasche", "Flasche mit Öl"][g.prop[BOTTLE]]; }
      if (o === LAMP) { n = g.prop[LAMP] === 1 ? "Messinglampe (an)" : "Messinglampe (aus)"; }
      if (o === CAGE && g.prop[BIRD] === 1) { n = "Weidenkäfig mit Vogel"; }
      if (o === BIRD) { return; }
      g.out.push("&nbsp;&nbsp;– " + esc(n));
    });
    if (toting(BEAR)) { msg(141); }
  }
  function doTake(o) {
    var g = G();
    if (o === ROD && (toting(ROD) || !here(ROD)) && here(ROD2) && !toting(ROD2)) { o = ROD2; }
    if (toting(o)) { msg(24); return; }
    if (o === WATER || o === OIL) {
      if (!here(BOTTLE) || liq() !== o) {
        if (toting(BOTTLE) && g.prop[BOTTLE] === 1) { return doFill(BOTTLE); }
        if (liqLoc(g.loc) === o || liqLoc(g.loc) === 0) { /* fallthrough */ }
        if (!toting(BOTTLE)) { msg(104); return; }
        return doFill(BOTTLE);
      }
      o = BOTTLE;
    }
    if (o === KNIFE) { msg(116); return; }
    if (!at(o) && !toting(o) && o !== BOTTLE) {
      say(esc(D.ui.hier_nichts));
      return;
    }
    if (g.fixed[o] !== 0) {
      if (o === PLANT && g.prop[PLANT] <= 0) { msg(115); return; }
      if (o === BEAR && g.prop[BEAR] === 1) { msg(169); return; }
      if (o === CHAIN) { if (g.prop[BEAR] === 0) { msg(41); } else { msg(170); } return; }
      msg(25); return;
    }
    if (o === BEAR && g.prop[BEAR] !== 2) { msg(25); return; }
    if (holding() >= MAXHOLD) { msg(92); return; }
    if (o === BIRD && g.prop[BIRD] === 0) {
      if (toting(ROD)) { msg(26); return; }
      if (!toting(CAGE)) { msg(27); return; }
      g.prop[BIRD] = 1;
    }
    carry(o);
    if ((o === BIRD || o === CAGE) && g.prop[BIRD] !== 0) {
      carry(BIRD); carry(CAGE);
    }
    if (o === BOTTLE && g.prop[BOTTLE] === 0) { /* Wasser rutscht mit */ }
    msg(54);
  }
  function doDrop(o) {
    var g = G();
    if (o === ROD && !toting(ROD) && toting(ROD2)) { o = ROD2; }
    if (o === WATER || o === OIL) { return doPour(o); }
    if (!toting(o)) { msg(29); return; }
    if (o === BIRD && here(SNAKE)) {
      msg(30);
      if (g.closed) { msg(137); return; }
      destroy(SNAKE); g.prop[SNAKE] = 1;
      g.prop[BIRD] = 0; dropAt(BIRD, g.loc);
      return;
    }
    if (o === COINS && here(MACHINE)) {
      destroy(COINS);
      dropAt(BATTERIES, g.loc);
      g.prop[BATTERIES] = 0;
      say(objText(BATTERIES, 0));
      return;
    }
    if (o === BIRD && here(DRAGON) && g.prop[DRAGON] === 0) {
      msg(154);
      destroy(BIRD); g.prop[BIRD] = 0;
      return;
    }
    if (o === BEAR && at(TROLL)) { /* Troll haelt Abstand */ }
    if (o === BIRD) { g.prop[BIRD] = 0; }
    if (o === VASE) {
      if (g.place[PILLOW] === g.loc) { say(objText(VASE, 1)); }
      else { g.prop[VASE] = 2; g.fixed[VASE] = -1; say(objText(VASE, 3)); }
    } else if (o === CAGE && g.prop[BIRD] !== 0) {
      dropAt(BIRD, g.loc);
    } else if (o === BEAR) {
      msg(54);
    } else {
      msg(54);
    }
    dropAt(o, g.loc);
    if (o === CAGE && g.prop[BIRD] !== 0) { dropAt(BIRD, g.loc); }
  }
  function doPour(o) {
    var g = G();
    if (o === 0 || o === BOTTLE) { o = liq(); }
    if (o === 0) { msg(78); return; }
    if (!toting(BOTTLE) || liq() !== o) { msg(29); return; }
    g.prop[BOTTLE] = 1;
    g.place[o] = 0;
    if (at(PLANT)) {
      if (o !== WATER) { msg(112); return; }
      var p = g.prop[PLANT];
      if (p === 0) { say(objText(PLANT, 1)); g.prop[PLANT] = 2; }
      else if (p === 2) { say(objText(PLANT, 3)); g.prop[PLANT] = 4; }
      else { say(objText(PLANT, 5)); g.prop[PLANT] = 0; }
      g.prop[PLANT2] = g.prop[PLANT] / 2;
      return;
    }
    if (at(DOOR)) {
      if (o === OIL) { g.prop[DOOR] = 1; msg(114); } else { msg(113); }
      return;
    }
    msg(77);
  }
  function doFill(o) {
    var g = G();
    if (o === VASE) {
      if (liqLoc(g.loc) === 0) { msg(144); return; }
      msg(145);
      g.prop[VASE] = 2; g.fixed[VASE] = -1;
      if (toting(VASE)) { dropAt(VASE, g.loc); }
      return;
    }
    if (o !== 0 && o !== BOTTLE) { msg(109); return; }
    if (!here(BOTTLE)) { msg(o === 0 ? 61 : 29); return; }
    if (liqLoc(g.loc) === 0) { msg(106); return; }
    if (liq() !== 0) { msg(105); return; }
    var oil = liqLoc(g.loc) === OIL;
    g.prop[BOTTLE] = oil ? 2 : 0;
    if (toting(BOTTLE)) { g.place[oil ? OIL : WATER] = -1; }
    msg(oil ? 108 : 107);
  }
  function doUnlock(o, lock) {
    var g = G();
    if (o !== 0 && !here(o) && !(o === GRATE && at(GRATE))) { say(esc(D.ui.hier_nichts)); return; }
    if (o === 0) {
      if (here(GRATE)) { o = GRATE; }
      else if (here(DOOR)) { o = DOOR; }
      else if (here(CHAIN)) { o = CHAIN; }
      else if (here(CLAM)) { o = CLAM; }
      else if (here(OYSTER)) { o = OYSTER; }
      else { msg(28); return; }
    }
    if (o === CLAM || o === OYSTER) {
      if (lock) { msg(33); return; }
      var isClam = o === CLAM;
      if (toting(o)) { msg(isClam ? 120 : 121); return; }
      if (!toting(TRIDENT)) { msg(isClam ? 122 : 123); return; }
      if (isClam) {
        msg(124);
        destroy(CLAM); dropAt(OYSTER, g.loc); dropAt(PEARL, 105);
      } else { msg(125); }
      return;
    }
    if (o === DOOR) { msg(g.prop[DOOR] === 1 ? 54 : 111); return; }
    if (o === CAGE) { msg(32); return; }
    if (o === KEYS) { msg(55); return; }
    if (o === GRATE || o === CHAIN) {
      if (!here(KEYS)) { msg(31); return; }
      if (o === GRATE) {
        if (g.closing) { msg(130); if (!g.pending) { /* kein Toten-Ausgang */ } return; }
        if (lock) { if (g.prop[GRATE] === 0) { msg(34); } else { g.prop[GRATE] = 0; msg(35); } }
        else { if (g.prop[GRATE] === 1) { msg(37); } else { g.prop[GRATE] = 1; msg(36); } }
        return;
      }
      // Kette
      if (lock) {
        if (g.prop[CHAIN] !== 0) { msg(34); return; }
        if (g.loc !== g.place[BEAR] && g.loc !== 130) { msg(173); return; }
        g.prop[CHAIN] = 2;
        if (toting(CHAIN)) { dropAt(CHAIN, g.loc); }
        g.fixed[CHAIN] = -1;
        msg(172);
      } else {
        if (g.prop[BEAR] === 0) { msg(41); return; }
        if (g.prop[CHAIN] === 0) { msg(37); return; }
        g.prop[CHAIN] = 0; g.fixed[CHAIN] = 0;
        if (g.prop[BEAR] !== 3) { g.prop[BEAR] = 2; g.fixed[BEAR] = 0; }
        msg(171);
      }
      return;
    }
    msg(33);
  }
  function doAttack(o) {
    var g = G();
    if (o === 0) {
      var cands = [];
      if (atDwarf()) { cands.push(DWARF); }
      if (here(SNAKE)) { cands.push(SNAKE); }
      if (at(DRAGON) && g.prop[DRAGON] === 0) { cands.push(DRAGON); }
      if (at(TROLL)) { cands.push(TROLL); }
      if (here(BEAR) && g.prop[BEAR] === 0) { cands.push(BEAR); }
      if (here(BIRD) && !g.closed) { cands.push(BIRD); }
      if (cands.length === 0) { msg(44); return; }
      if (cands.length > 1) { msg(61); return; }
      o = cands[0];
    }
    if (o !== 0 && !here(o) && !(o === DWARF && atDwarf()) && o !== DRAGON && o !== TROLL) { say(esc(D.ui.hier_nichts)); return; }
    if (o === BIRD) {
      if (g.closed) { msg(137); return; }
      destroy(BIRD); g.prop[BIRD] = 0; msg(45); return;
    }
    if (o === CLAM || o === OYSTER) { msg(150); return; }
    if (o === SNAKE) { msg(46); return; }
    if (o === DWARF) {
      if (g.closed) { msg(199); msg(136); finish(); return; }
      msg(49); return;
    }
    if (o === DRAGON) {
      if (g.prop[DRAGON] !== 0) { msg(167); return; }
      g.pending = { type: "dragon" };
      msg(49);
      return;
    }
    if (o === TROLL) { msg(157); return; }
    if (o === BEAR) { msg(165 + Math.floor((g.prop[BEAR] + 1) / 2)); return; }
    msg(inList([MAGAZINE, MIRROR], o) ? 146 : 110);
  }
  function killDragon() {
    var g = G();
    g.pending = null;
    say(objText(DRAGON, 1));
    g.prop[DRAGON] = 2; g.prop[RUG] = 0;
    var k = Math.floor((g.place[DRAGON] + g.fixed[DRAGON]) / 2);
    g.place[DRAGON] = k; g.fixed[DRAGON] = -1;
    g.place[RUG] = k; g.fixed[RUG] = 0;
    for (var i = 1; i <= 64; i++) { if (g.place[i] === 119 || g.place[i] === 121) { if (i !== DRAGON && i !== RUG) { g.place[i] = k; } } }
    g.oldloc2 = g.loc;
    g.loc = k; g.oldloc = k;
    look(true);
  }
  function doThrow(o) {
    var g = G();
    if (o === ROD && !toting(ROD) && toting(ROD2)) { o = ROD2; }
    if (!toting(o)) { msg(29); return; }
    if (isTreasure(o) && at(TROLL)) {
      msg(159);
      destroy(o);
      g.toll = o;
      g.place[TROLL] = 0; g.fixed[TROLL] = 0;
      g.place[TROLL2] = 117; g.fixed[TROLL2] = 122;
      return;
    }
    if (o === FOOD && here(BEAR)) { return doFeed(BEAR); }
    if (o !== AXE) { return doDrop(o); }
    var d = atDwarf();
    if (d) {
      if (pct(66)) {
        g.dloc[d - 1] = 0; g.dseen[d - 1] = 0;
        msg(149);
      } else { msg(48); }
      dropAt(AXE, g.loc);
      return;
    }
    if (at(DRAGON) && g.prop[DRAGON] === 0) { msg(152); dropAt(AXE, g.loc); return; }
    if (at(TROLL)) { msg(158); return; }
    if (here(BEAR) && g.prop[BEAR] === 0) {
      msg(164);
      dropAt(AXE, g.loc); g.fixed[AXE] = -1; g.prop[AXE] = 1;
      return;
    }
    doDrop(o);
  }
  function doFeed(o) {
    var g = G();
    if (o !== 0 && !here(o)) { say(esc(D.ui.hier_nichts)); return; }
    if (o === BIRD) { msg(100); return; }
    if (o === SNAKE || o === DRAGON || o === TROLL) { msg(o === DRAGON && g.prop[DRAGON] !== 0 ? 110 : 102); return; }
    if (o === DWARF) {
      if (here(FOOD)) { g.dflag++; msg(103); } else { msg(14); }
      return;
    }
    if (o === BEAR) {
      if (!here(FOOD)) {
        if (g.prop[BEAR] === 0) { msg(102); }
        else if (g.prop[BEAR] === 3) { msg(110); }
        else { msg(14); }
        return;
      }
      destroy(FOOD);
      g.prop[BEAR] = 1; g.fixed[AXE] = 0; g.prop[AXE] = 0;
      msg(168);
      return;
    }
    msg(14);
  }
  function doEat(o) {
    var g = G();
    if (o === 0) { if (here(FOOD)) { o = FOOD; } else { msg(174); return; } }
    if (o === FOOD) {
      if (!here(FOOD)) { msg(29); return; }
      destroy(FOOD); msg(72); return;
    }
    if (inList([BIRD, SNAKE, CLAM, OYSTER, DWARF, DRAGON, TROLL, BEAR], o)) { msg(71); return; }
    msg(110);
  }
  function doDrink(o) {
    var g = G();
    if (o === BOTTLE || o === 0 || o === WATER) {
      if (liq() === WATER && here(BOTTLE) && (o !== 0 || !liqLoc(g.loc))) {
        g.prop[BOTTLE] = 1; g.place[WATER] = 0; msg(74); return;
      }
      if (liqLoc(g.loc) === WATER) { msg(73); return; }
      if (liq() === WATER && here(BOTTLE)) { g.prop[BOTTLE] = 1; g.place[WATER] = 0; msg(74); return; }
    }
    msg(110);
  }
  function doRead(o) {
    var g = G();
    if (o === 0) {
      if (here(MAGAZINE)) { o = MAGAZINE; }
      else if (at(TABLET)) { o = TABLET; }
      else if (at(MESSAGE)) { o = MESSAGE; }
      else if (here(OYSTER) && g.closed) { o = OYSTER; }
      else { msg(195); return; }
    }
    if (o === MAGAZINE) { msg(190); return; }
    if (o === TABLET) { msg(196); return; }
    if (o === MESSAGE) { msg(191); return; }
    if (o === OYSTER && g.closed && toting(OYSTER)) {
      if (g.hintgiven[2]) { msg(194); return; }
      g.pending = { type: "hintq2" };
      msg(192);
      return;
    }
    if (o === OYSTER && here(OYSTER)) { msg(g.closed ? 195 : 195); return; }
    msg(195);
  }
  function doWave(o) {
    var g = G();
    if (o === ROD && !toting(ROD) && toting(ROD2)) { o = ROD2; }
    if (!toting(o)) { msg(29); return; }
    if (o !== ROD || !toting(ROD) || (!here(BIRD) && g.closing && false)) { msg(42); return; }
    if (at(FISSURE)) {
      var p = g.prop[FISSURE];
      say(objText(FISSURE, p === 0 ? 1 : 2));
      g.prop[FISSURE] = p === 0 ? 1 : 0;
      return;
    }
    if (g.closed && here(BIRD)) { msg(42); return; }
    msg(42);
  }
  function doBlast() {
    var g = G();
    if (g.prop[ROD2] < 0 || !g.closed) { msg(67); return; }
    g.bonus = 133;
    if (g.loc === 115) { g.bonus = 134; }
    if (here(ROD2)) { g.bonus = 135; }
    msg(g.bonus);
    finish();
  }
  function doBreak(o) {
    var g = G();
    if (o === MIRROR) {
      if (g.closed) { msg(197); msg(136); finish(); return; }
      msg(148); return;
    }
    if (o === VASE && g.prop[VASE] === 0) {
      if (toting(VASE)) { dropAt(VASE, g.loc); }
      msg(198);
      g.prop[VASE] = 2; g.fixed[VASE] = -1;
      return;
    }
    msg(146);
  }
  function doFoo(k) {
    var g = G();
    if (k !== g.foobar + 1) {
      msg(g.foobar === 0 ? 42 : 151);
      g.foobar = 0;
      return;
    }
    g.foobar = k;
    if (k !== 4) { msg(54); return; }
    g.foobar = 0;
    if (g.place[EGGS] === 92 || (toting(EGGS) && g.loc === 92)) { msg(42); return; }
    if (g.place[EGGS] === 0 && g.place[TROLL] === 0 && g.prop[TROLL] === 0) { g.prop[TROLL] = 1; }
    var kk;
    if (g.loc === 92) { kk = 2; }
    else if (here(EGGS)) { kk = 1; }
    else { kk = 0; }
    if (toting(EGGS)) { dropAt(EGGS, g.loc); }
    g.place[EGGS] = 92;
    if (g.prop[EGGS] < 0) { g.prop[EGGS] = 0; }
    if (kk === 0) { msg(42); return; }
    say(objText(EGGS, kk));
    if (kk === 2 && g.loc === 92) { /* Nest erscheint hier */ }
  }
  function doHint(yes) {
    var g = G(), p = g.pending;
    g.pending = null;
    if (!yes) { msg(54); return; }
    if (p.type === "hintq2") {
      g.hintscore += 10; g.hintgiven[2] = true; msg(193); return;
    }
    if (p.stage === 1) {
      g.hintscore += p.cost; g.hintgiven[p.no] = true; say(msgText(p.a)); return;
    }
  }

  /* ---------- Parser ---------- */
  var FILLER = {};
  ("nach zu zum zur der die das den dem ein eine einen einem mit am an im in auf aus von vom bitte mal doch noch dann und " +
   "dort hier ihn sie es ihm").split(" ").forEach(function (w) { FILLER[w] = 1; });
  // "auf", "aus", "an", "in" sind teils auch Richtungswoerter -> Vokabular hat Vorrang (siehe lookup)
  function lookup(w) {
    var v = D.vocab[w];
    if (v === undefined && w.length > 5) { v = D.vocab[w.slice(0, 5)]; }
    return v;
  }
  function parse(text) {
    var words = norm(text).split(" ").filter(Boolean);
    var toks = [];
    words.forEach(function (w) {
      var v = lookup(w);
      if (v !== undefined) { toks.push({ w: w, v: v }); }
      else if (FILLER[w]) { /* ignorieren */ }
      else { toks.push({ w: w, v: -1 }); }
    });
    return toks;
  }
  function ynAnswer(text) {
    var t = norm(text);
    if (/^(ja|j|jo|y|yes|klar|ok|okay|gerne|yep)$/.test(t)) { return true; }
    if (/^(nein|n|no|nee|nope)$/.test(t)) { return false; }
    return null;
  }
  function objectsHere() {
    var g = G(), out = [];
    for (var k in g.place) {
      var o = +k;
      if (here(o) && o !== WATER && o !== OIL) { out.push(o); }
    }
    return out;
  }
  function inferObject(verb) {
    var g = G(), list = objectsHere().filter(function (o) { return g.fixed[o] === 0 || verb === 2004 || verb === 2006; });
    return list;
  }
  function execute(toks, raw) {
    var g = G();
    if (!toks.length) { msg(61); return; }
    // erstes bekanntes Wort pruefen
    var unknown = toks.filter(function (t) { return t.v === -1; });
    if (toks[0].v === -1) { msg(60); return; }
    var verb = null, obj = null, mot = null, spec = null, k;
    for (k = 0; k < toks.length; k++) {
      var v = toks[k].v;
      if (v < 0) { continue; }
      if (v < 1000) { if (mot === null) { mot = v; } }
      else if (v < 2000) { if (obj === null) { obj = v - 1000; } }
      else if (v < 3000) { if (verb === null) { verb = v; } }
      else { if (spec === null) { spec = v; } }
    }
    // Sonderfaelle: reine Bewegung ohne Verb
    if (verb === null && spec === null && obj === null && mot !== null) {
      if (mot === 57) { motion(57); return; }
      motion(mot); return;
    }
    // "gehe norden"
    if (verb === 2011) {
      if (mot !== null) { motion(mot); return; }
      if (obj !== null) { msg(43); return; }
      msg(43); return;
    }
    if (spec !== null && verb === null) {
      var s = spec - 3000;
      if (s >= 1 && s <= 5) { doFoo(s); return; }
      if (s === 142) { say(msgText(142)); return; }
      msg(s); return;
    }
    if (verb === null && obj !== null) {
      // "oel tuer" / "wasser pflanze": Fluessigkeit + Ziel -> ausgiessen
      if ((obj === OIL || obj === WATER) && toks.length > 1 && (at(DOOR) || at(PLANT))) { doPour(obj); return; }
      // nur ein Objekt: Standardverb ableiten
      if (mot !== null && (mot === 57)) { look(true); return; }
      if (mot !== null && toks.length > 1) { motion(mot); return; }
      if (here(obj)) { say(D.ui.kein_objekt.replace("{0}", esc(objName(obj)))); }
      else { say(esc(D.ui.hier_nichts)); }
      return;
    }
    if (verb === null && mot !== null) { motion(mot); return; }
    if (verb === null) { msg(13); return; }
    /* Verben */
    var vb = verb - 2000;
    if (obj !== null && (obj === 6 || obj === 5)) { /* Stab */ }
    switch (vb) {
      case 1:  // nehmen
        if (obj === null) {
          if (mot === 57) { motion(57); return; }
          var cand = inferObject(1).filter(function (o) { return g.place[o] !== -1 && o < 100; });
          if (cand.length === 1) { doTake(cand[0]); } else { msg(cand.length === 0 ? 43 : 61); }
          return;
        }
        doTake(obj); return;
      case 2:  // ablegen
        if (obj === null) { msg(61); return; }
        doDrop(obj); return;
      case 3:  // sagen
        if (spec !== null) { var ss = spec - 3000; if (ss >= 1 && ss <= 5) { doFoo(ss); return; } msg(ss); return; }
        if (mot !== null && (mot === 62 || mot === 65 || mot === 71)) { motion(mot); return; }
        if (toks.length > 1) {
          var wd = toks.slice(1).map(function (t) { return t.w; }).join(" ");
          say("Okay, \"" + esc(wd) + "\".");
        } else { msg(61); }
        return;
      case 4: doUnlock(obj === null ? 0 : obj, false); return;
      case 6: doUnlock(obj === null ? 0 : obj, true); return;
      case 7:  // anzuenden
        if (obj !== null && obj !== LAMP) { msg(110); return; }
        if (!here(LAMP)) { msg(38); return; }
        if (g.limit < 0) { msg(184); return; }
        if (g.prop[LAMP] === 1) { say(msgText(39)); return; }
        g.prop[LAMP] = 1; msg(39);
        look(true);
        return;
      case 8:
        if (obj !== null && obj !== LAMP) { msg(110); return; }
        if (!here(LAMP)) { msg(38); return; }
        g.prop[LAMP] = 0; msg(40);
        if (!lit(g.loc)) { msg(16); }
        return;
      case 9: doWave(obj === null ? 0 : obj); return;
      case 10: msg(14); return;
      case 12: doAttack(obj === null ? 0 : obj); return;
      case 13: doPour(obj === null ? 0 : obj); return;
      case 14: doEat(obj === null ? 0 : obj); return;
      case 15: doDrink(obj === null ? 0 : obj); return;
      case 16:
        if (obj === LAMP) { msg(75); } else { msg(76); }
        return;
      case 17:
        if (obj === null) { msg(61); return; }
        doThrow(obj); return;
      case 18:
        g.pending = { type: "quit" };
        msg(22); return;
      case 19:
        if (obj === null) { msg(61); return; }
        if (toting(obj)) { msg(24); return; }
        if (g.closed) { msg(138); return; }
        if (at(obj) || (liqLoc(g.loc) === obj) || (obj === WATER && liq() === WATER && here(BOTTLE))) { msg(94); return; }
        msg(59); return;
      case 20: listInventory(); return;
      case 21: doFeed(obj === null ? 0 : obj); return;
      case 22: doFill(obj === null ? 0 : obj); return;
      case 23: doBlast(); return;
      case 24:
        var sc = score(false);
        say(esc(D.ui.punkte.replace("{0}", sc).replace("{1}", g.turns)));
        return;
      case 25:
        if (spec !== null && spec > 3000 && spec <= 3005) { doFoo(spec - 3000); return; }
        { var kw = toks[0].w; var kidx = { fee: 1, fie: 2, foe: 3, foo: 4, fum: 5 }[kw];
          if (kidx) { doFoo(kidx); return; } }
        msg(42); return;
      case 26: g.brief = true; msg(156); return;
      case 27: doRead(obj === null ? 0 : obj); return;
      case 28: doBreak(obj === null ? 0 : obj); return;
      case 29:
        if (g.closed && atDwarfClosed()) { msg(199); msg(136); finish(); return; }
        msg(110); return;
      case 30:
        say(esc(D.ui.speichern)); return;
      case 31:
        say(esc(D.ui.stunden)); return;
      default:
        msg(13);
    }
  }
  function atDwarfClosed() { return here(DWARF); }

  /* ---------- Kommando ---------- */
  A.cmd = function (text) {
    var g = G();
    if (!g || g.over) { return; }
    text = String(text || "").trim();
    g.out = [];
    g.cmdcount++;
    if (g.pending) {
      var yn = ynAnswer(text);
      var p = g.pending;
      if (yn === null) {
        if (p.type === "hintq" || p.type === "hint2" || p.type === "hintq2" || p.type === "dragon") {
          g.pending = null;      // Hinweis-/Drachenfrage: anderer Befehl bricht sie ab
          p = null;
        } else {
          say(esc(D.ui.ja_nein));  // Wiederbelebung / Aufgeben: ausdrueckliche Antwort noetig
          flushLog(text);
          return;
        }
      }
      if (p && p.type === "reinc") {
        if (yn) { reincarnate(); }
        else { msg(54); finish(); }
        flushLog(text); return;
      }
      if (p && p.type === "quit") {
        g.pending = null;
        if (yn) { g.gaveup = true; finish(); } else { msg(54); }
        flushLog(text); return;
      }
      if (p && p.type === "dragon") {
        g.pending = null;
        if (yn) { killDragon(); } else { msg(54); }
        flushLog(text); return;
      }
      if (p && p.type === "hintq") {
        if (!yn) { g.pending = null; msg(54); flushLog(text); return; }
        p.type = "hint2"; p.stage = 1;
        say(esc(D.ui.hint_preis.replace("{0}", p.cost)));
        flushLog(text); return;
      }
      if (p && p.type === "hint2") {
        if (yn) { g.pending = null; g.hintscore += p.cost; g.hintgiven[p.no] = true; say(msgText(p.a)); }
        else { g.pending = null; msg(54); }
        flushLog(text); return;
      }
      if (p && p.type === "hintq2") {
        g.pending = null;
        if (yn) { g.hintscore += 10; g.hintgiven[2] = true; msg(193); } else { msg(54); }
        flushLog(text); return;
      }
    }
    var toks = parse(text);
    execute(toks, text);
    // Zug zaehlt, ausser bei reinen Informationsbefehlen
    var info = toks.length && toks[0].v >= 2000 && inList([2020, 2024, 2026, 2030, 2031], toks[0].v);
    if (!info && !g.over) { endTurn(); }
    if (g.pending && g.pending.type === "reinc") { /* Frage steht schon in out */ }
    flushLog(text);
  };

  /* ---------- Ansicht ---------- */
  var DIRS = [
    ["NW", "nordwest", 50], ["N", "norden", 45], ["NO", "nordost", 47],
    ["W", "westen", 44], ["⌖", "schau", 57], ["O", "osten", 43],
    ["SW", "südwest", 49], ["S", "süden", 46], ["SO", "südost", 48]
  ];
  A.view = function () {
    var g = G(), h = [];
    if (!g) { return ""; }
    h.push('<div id="adv-log">');
    g.log.forEach(function (e, i) {
      h.push('<div class="adv-turn">');
      if (e.c) { h.push('<div class="adv-echo">&gt; ' + esc(e.c) + "</div>"); }
      e.o.forEach(function (p) {
        if (p === "<hr>") { h.push("<hr>"); }
        else { h.push('<p class="' + (/^<strong>/.test(p) ? "adv-room" : "adv-p") + '">' + fmt(p) + "</p>"); }
      });
      h.push("</div>");
    });
    h.push("</div>");
    if (g.over) {
      h.push('<p><button class="adv-btn" id="adv-restart">Neu beginnen</button></p>');
      return h.join("\n");
    }
    if (g.pending) {
      h.push('<p class="adv-yn"><button class="adv-btn adv-cmd" data-cmd="ja">Ja</button> ' +
             '<button class="adv-btn adv-cmd" data-cmd="nein">Nein</button></p>');
    } else {
      h.push('<div id="adv-controls"><div id="adv-compass">');
      DIRS.forEach(function (d) {
        if (d[2] === 57) { h.push('<button class="adv-btn adv-cmd" data-cmd="schau" title="Umschauen">·</button>'); }
        else { h.push('<button class="adv-btn adv-cmd" data-cmd="' + d[1] + '" title="' + d[1] + '">' + d[0] + "</button>"); }
      });
      h.push("</div>");
      h.push('<div id="adv-vert">' +
        '<button class="adv-btn adv-cmd" data-cmd="hoch">hoch</button>' +
        '<button class="adv-btn adv-cmd" data-cmd="runter">runter</button>' +
        '<button class="adv-btn adv-cmd" data-cmd="rein">rein</button>' +
        '<button class="adv-btn adv-cmd" data-cmd="raus">raus</button>' +
        '<button class="adv-btn adv-cmd" data-cmd="zurück">zurück</button></div></div>');
      // Gegenstaende
      var inv = [], hr = [];
      objectsHere().forEach(function (o) {
        if (g.place[o] === -1) { inv.push(o); } else if (g.fixed[o] === 0 && o < 100 && !(o === BIRD && g.prop[BIRD] === 1 && toting(CAGE))) { hr.push(o); }
      });
      h.push('<div id="adv-items">');
      if (hr.length) {
        h.push('<span class="adv-lbl">Hier:</span> ');
        hr.forEach(function (o) {
          h.push('<button class="adv-btn adv-cmd" data-cmd="nimm ' + esc(shortWord(o)) + '">nimm ' + esc(shortLabel(o)) + "</button> ");
        });
      }
      if (inv.length) {
        h.push('<br><span class="adv-lbl">Bei dir:</span> ');
        inv.forEach(function (o) {
          if (o === BIRD) { return; }
          h.push('<button class="adv-btn adv-cmd" data-cmd="lass ' + esc(shortWord(o)) + '">lass ' + esc(shortLabel(o)) + "</button> ");
        });
      }
      h.push("</div>");
      h.push('<div id="adv-quick"><button class="adv-btn adv-cmd" data-cmd="inventar">Inventar</button> ' +
             '<button class="adv-btn adv-cmd" data-cmd="punkte">Punkte</button> ' +
             '<button class="adv-btn adv-cmd" data-cmd="hilfe">Hilfe</button> ' +
             '<button class="adv-btn adv-cmd" data-cmd="kurz">Kurz</button></div>');
    }
    h.push('<form id="adv-form" autocomplete="off"><span class="adv-prompt">&gt;</span> ' +
           '<input id="advin" type="text" spellcheck="false" autocapitalize="off" autocomplete="off" ' +
           'placeholder="Befehl eingeben, z. B. nimm lampe, xyzzy, wirf axt …"> ' +
           '<button class="adv-btn" type="submit">OK</button></form>');
    return h.join("\n");
  };
  function fmt(p) {
    if (/^<strong>/.test(p)) { return p; }
    if (/^&nbsp;/.test(p)) { return p; }
    return esc(p).replace(/\n/g, "<br>").replace(/&lt;strong&gt;/g, "<strong>").replace(/&lt;\/strong&gt;/g, "</strong>");
  }
  function shortWord(o) { return D.firstWord[o] || ("obj" + o); }
  function shortLabel(o) {
    var n = objName(o);
    return n.length > 22 ? n.slice(0, 20) + "…" : n;
  }
  A.sidebar = function () {
    var g = G();
    if (!g) { return ""; }
    var lamp = g.prop[LAMP] === 1 ? (g.limit < 0 ? "leer" : "an (" + Math.max(g.limit, 0) + ")") : "aus";
    var carrying = [];
    for (var k in g.place) {
      var o = +k;
      if (g.place[o] === -1 && o !== WATER && o !== OIL && o !== BIRD) { carrying.push(objName(o)); }
    }
    return '<div class="adv-side"><div><strong>Punkte:</strong> ' + score(false) + ' / 350</div>' +
      "<div><strong>Züge:</strong> " + g.turns + "</div>" +
      "<div><strong>Lampe:</strong> " + lamp + "</div>" +
      "<div><strong>Tod:</strong> " + g.numdie + " / " + MAXDIE + "</div>" +
      "<div class='adv-carry'><strong>Bei dir:</strong> " + (carrying.length ? esc(carrying.join(", ")) : "nichts") + "</div></div>";
  };

  /* Befehl aus der Oberflaeche */
  var queued = null;
  A.run = function (text) {
    queued = text;
    Engine.play("Spiel");
  };
  A.consume = function () {
    if (queued !== null) { var q = queued; queued = null; A.cmd(q); }
  };
  A.restart = function () { queued = null; Engine.restart(); };
})();
