const { makeGame } = require('./harness');
const words = ['norden','sueden','osten','westen','nordost','suedost','suedwest','nordwest','hoch','runter','rein','raus','zurueck',
 'nimm lampe','nimm schluessel','nimm essen','nimm flasche','nimm stab','nimm kaefig','nimm vogel','nimm axt','nimm gold','nimm silber',
 'lass vogel','lass lampe','lass stab','lass essen','anzuenden','ausmachen','oeffne gitter','schliesse gitter','schwenke stab','giesse wasser',
 'fuelle flasche','trinke','iss essen','wirf axt','wirf gold','greife zwerg an','inventar','punkte','schau','xyzzy','plugh','plover','fee','fie','foe','foo',
 'lies zeitschrift','zerbrich vase','ja','nein','hilfe','kurz','ueber','springen','klettern','nimm vase','lass vase','nimm muenzen','lass muenzen','info','sprenge','wecke zwerg','blabla'];
let seedBase = 100, crashes = 0, maxTurns = 0, dies = 0, endings = 0, scoreMax = 0;
for (let k = 0; k < 40; k++) {
  const G = makeGame(seedBase + k);
  let s = 77 + k * 31; const rnd = () => { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; };
  // vorbereiten: tief in die Hoehle mit Lampe
  const g = G.g();
  try {
    for (let i = 0; i < 1500; i++) {
      const c = words[Math.floor(rnd() * words.length)];
      Adv.cmd(c);
      if (G.g().over) { endings++; break; }
      if (i === 20) { const gg = G.g(); gg.loc = gg.oldloc = gg.oldloc2 = 15; gg.place[2] = -1; gg.prop[2] = 1; gg.place[1] = -1; }
    }
    maxTurns = Math.max(maxTurns, G.g().turns);
    dies += G.g().numdie;
  } catch (e) { crashes++; console.log('CRASH seed', seedBase + k, e.stack.split('\n').slice(0, 4).join('\n')); }
}
console.log({ crashes, maxTurns, dies, endings });
