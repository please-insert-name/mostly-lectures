const { makeGame, passages } = require('./harness');
const G = makeGame(3);
const D = window.ADV_DATA;
// BFS ignoring conditions
const seen = new Set([1]); const q = [1];
while (q.length) { const l = q.shift(); for (const [x, vs] of (D.travel[l] || [])) {
  let n = x % 1000; const m = Math.floor(x/1000);
  const cand = [];
  if (n <= 300) cand.push(n); else if (n === 301) cand.push(99,100); else if (n === 303) cand.push(117,122);
  cand.forEach(c => { if (c && !seen.has(c)) { seen.add(c); q.push(c); } });
}}
const all = Object.keys(passages).filter(k => /^R\d+$/.test(k)).map(k => +k.slice(1));
console.log('Raeume:', all.length, 'unerreichbar:', all.filter(r => !seen.has(r)));
// Reisetabellen-Ziele ohne Raumtext
const dests = new Set(); Object.values(D.travel).forEach(rows => rows.forEach(([x]) => { const n = x % 1000; if (n <= 300 && n > 0) dests.add(n); }));
console.log('Ziele ohne Text:', [...dests].filter(d => !(('R' + ('00'+d).slice(-3)) in passages)));
// Objekte ohne Text/Name
const noObj = []; for (let i = 1; i <= 64; i++) { if (D.place0[i] !== undefined && !D.obj[i]) noObj.push(i); }
console.log('Objekte ohne Text:', noObj);
// Vokabular-Konflikte (deutsche Woerter, die auf mehrere Dinge zeigen sind nicht moeglich) - Stichproben
['norden','nimm','lampe','xyzzy','plugh','plover','fee','hilfe','info','punkte','kurz'].forEach(w => console.log(w, D.vocab[w]));
