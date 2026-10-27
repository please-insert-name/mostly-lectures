// Headless-Testharness: laedt die Engine mit minimalen SugarCube-Attrappen.
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'colossal-cave.html'), 'utf8');
const un = s => s.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#x27;/g,"'").replace(/&#39;/g,"'").replace(/&amp;/g,'&');
const script = (html.match(/<script role="script"[^>]*>([\s\S]*?)<\/script>/)[1]);
const passages = {};
for (const m of html.matchAll(/<tw-passagedata pid="\d+" name="([^"]*)"[^>]*>([\s\S]*?)<\/tw-passagedata>/g)) passages[un(m[1])] = un(m[2]);
function makeGame(seed) {
  let s = seed || 12345;
  const rand = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
  global.window = global;
  global.State = { variables: {}, random: rand };
  global.Story = { has: n => n in passages, get: n => ({ text: passages[n] }) };
  global.Engine = { play() {}, restart() {} };
  global.$ = () => ({ on() { return this; } }); global.$.fn = {};
  global.$ = Object.assign(() => ({ on() { return this; } }), {});
  const code = script.replace(/\$\(document\)[\s\S]*$/, '');
  (0, eval)(code);
  global.Adv.init();
  return {
    g: () => State.variables.g,
    run(cmds) {
      const outs = [];
      for (const c of cmds) {
        Adv.cmd(c);
        const e = State.variables.g.log[State.variables.g.log.length - 1];
        outs.push('> ' + c + '\n' + e.o.map(x => x.replace(/<[^>]+>/g, '')).join('\n'));
      }
      return outs.join('\n\n');
    }
  };
}
module.exports = { makeGame, passages };
