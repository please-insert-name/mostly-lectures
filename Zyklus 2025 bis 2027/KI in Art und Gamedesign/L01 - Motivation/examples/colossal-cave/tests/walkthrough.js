const { makeGame } = require('./harness');
const fs = require('fs');
const cmds = fs.readFileSync(__dirname + '/walkthrough-350.txt', 'utf8').split('\n').map(s => s.trim()).filter(Boolean);
const verbose = process.argv.includes('-v');
function run(seed) {
  const G = makeGame(seed * 7919);
  const log = [];
  const exec = (c) => { Adv.cmd(c); const g = G.g(); const e = g.log[g.log.length - 1]; log.push({ c, loc: g.loc, out: e.o.join(' ').replace(/<[^>]+>/g, '').slice(0, 160), score: 0 }); };
  const dwarfHere = () => { const g = G.g(); for (let i = 0; i < 5; i++) if (g.dloc[i] === g.loc && g.dseen[i]) return true; return false; };
  for (const c of cmds) {
    const g = G.g();
    if (g.over || g.pending) break;
    exec(c);
    let n = 0;
    while (!G.g().over && !G.g().pending && dwarfHere() && n++ < 6) {
      const g2 = G.g();
      if (g2.place[28] === -1) exec('throw axe');
      else if (g2.place[28] === g2.loc) exec('get axe');
      else break;
      if (!G.g().pending && G.g().place[28] === G.g().loc) exec('get axe');
    }
    if (G.g().pending || G.g().over) break;
  }
  return { G, log, done: !G.g().over && !G.g().pending };
}
let best = null, okCount = 0, results = [];
for (let seed = 1; seed <= 80; seed++) {
  const r = run(seed);
  const g = r.G.g();
  results.push({ seed, n: r.log.length, died: g.numdie, over: g.over, tally: g.tally });
  if (r.log.length === cmds.length && !g.pending && !g.numdie) okCount++;
  if (!best || r.log.length > best.log.length || (r.log.length === best.log.length && !g.numdie)) best = { seed, ...r };
}
console.log('seeds ohne Tod und komplett:', okCount, '/ 80; laengster Lauf', best.log.length, '/', cmds.length, 'seed', best.seed);
const g = best.G.g();
console.log('tally', g.tally, 'closing', g.closing, 'closed', g.closed, 'over', g.over, 'pending', JSON.stringify(g.pending));
if (verbose) best.log.forEach((l, i) => console.log(i, '>', l.c, '=>', l.loc, '|', l.out.slice(0, 110)));
else best.log.slice(-6).forEach(l => console.log('>', l.c, '=>', l.loc, '|', l.out));
