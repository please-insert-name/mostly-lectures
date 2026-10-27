const { makeGame } = require('./harness');
const fs = require('fs');
const cmds = fs.readFileSync(__dirname + '/walkthrough-350.txt', 'utf8').split('\n').map(s => s.trim()).filter(Boolean);
const verbose = process.argv.includes('-v');
let finals = [], notes = {};
for (let seed = 1; seed <= 200; seed++) {
  const G = makeGame(seed * 104729);
  let died = false;
  const out = [];
  const dw = () => { const g = G.g(); for (let i = 0; i < 5; i++) if (g.dloc[i] === g.loc && g.dseen[i]) return true; return false; };
  const ex = (c) => { Adv.cmd(c); const g = G.g(); const t = g.log[g.log.length - 1].o.join(' ').replace(/<[^>]+>/g, ''); out.push(c + ' => ' + g.loc + ' | ' + t.slice(0, 150)); if (g.pending && g.pending.type === 'reinc') died = true; return t; };
  const guard = (c) => { if (died || G.g().over) return; ex(c); let k = 0; while (!died && !G.g().over && dw() && k++ < 6) { const g = G.g(); if (g.place[28] === -1) ex('throw axe'); else if (g.place[28] === g.loc) ex('get axe'); else break; } };
  for (const c of cmds) { guard(c); if (died) break; }
  if (died) continue;
  // Warten bis Hoehle schliesst
  for (let i = 0; i < 160 && !G.g().closed && !died && !G.g().over; i++) guard('schau');
  if (died || !G.g().closed) { notes[died ? 'tod-beim-warten' : 'nicht-geschlossen'] = (notes[died ? 'tod-beim-warten' : 'nicht-geschlossen'] || 0) + 1; if (verbose && !died) console.log(out.slice(-6).join('\n'), G.g().tally, G.g().closing); continue; }
  for (const c of ['sw', 'get rod', 'ne', 'drop rod', 'sw', 'blast']) guard(c);
  const g = G.g();
  const t = G.g().log[G.g().log.length - 1].o.join(' ').replace(/<[^>]+>/g, '');
  finals.push({ seed, over: g.over, text: t.slice(-160) });
  if (verbose && finals.length === 1) { console.log(out.slice(-14).join('\n')); console.log(t); }
}
console.log('Vollstaendige Laeufe bis Ende:', finals.length, notes);
finals.slice(0, 5).forEach(f => console.log(f.seed, f.over, f.text));
