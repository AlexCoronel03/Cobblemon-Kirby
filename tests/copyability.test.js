/*
 * Battle-level test of Copy Ability against Cobblemon's own bundled Showdown simulator.
 *
 *   SHOWDOWN_DIR=<extracted data/cobblemon/showdown.zip> node tests/copyability.test.js
 *
 * It loads the real ability script + the real species JSON from src/main/resources and
 * drives real battles through the same BattleStream Cobblemon uses.
 */
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const Module = require('module');

const SD = process.env.SHOWDOWN_DIR;
if (!SD) { console.error('Set SHOWDOWN_DIR to the extracted Cobblemon showdown directory'); process.exit(2); }
const ROOT = path.join(__dirname, '..', 'src', 'main', 'resources', 'data', 'cobblemon_kirby');
const sdRequire = Module.createRequire(path.join(SD, 'index.js'));

/* index.js is a plain script for GraalVM; wrap it so we can reach its globals under Node. */
const indexSrc = fs.readFileSync(path.join(SD, 'index.js'), 'utf8');
const api = (() => {
  const m = { exports: {} };
  new Function('require', 'module', indexSrc + '\nmodule.exports={receiveData,afterSpeciesInit};')(sdRequire, m);
  return m.exports;
})();
const { BattleStream } = sdRequire('./sim/battle-stream');
const { Dex } = sdRequire('./sim/dex');
const { Battle } = sdRequire('./sim/battle');

/* Record every Battle.add() call (one entry per protocol line the engine emits). */
const originalAdd = Battle.prototype.add;
Battle.prototype.add = function (...args) {
  (this.addLog || (this.addLog = [])).push(args.map(String).join('|'));
  return originalAdd.apply(this, args);
};

/* Same wire format GraalShowdownService.sendRegistryData uses: {"key": <js-or-json>, ...} on one line. */
function send(map, type) {
  const payload = '{' + Object.entries(map).map(([k, v]) => `"${k}": ${v.replace(/[\r\n]+/g, ' ')}`).join(',') + '}';
  api.receiveData(payload, type);
}

send({ copyability: fs.readFileSync(path.join(ROOT, 'abilities', 'copyability.js'), 'utf8') }, 'ability');

const kirbyJson = JSON.parse(fs.readFileSync(path.join(ROOT, 'species', 'kirby.json'), 'utf8'));
const bs = kirbyJson.baseStats;
const KIRBY_NAME = 'cobblemon_kirby:Kirby';
send({
  cobblemonkirbykirby: JSON.stringify({
    num: kirbyJson.nationalPokedexNumber, name: KIRBY_NAME, baseSpecies: KIRBY_NAME,
    abilities: { 0: 'No Ability', 1: 'No Ability', H: 'No Ability', S: 'No Ability' },
    types: ['Fairy'], gender: 'N', eggGroups: ['Undiscovered'],
    baseStats: { hp: bs.hp, atk: bs.attack, def: bs.defence, spa: bs.special_attack, spd: bs.special_defence, spe: bs.speed },
    heightm: kirbyJson.height / 10, weightkg: kirbyJson.weight / 10,
  }),
}, 'species');
api.afterSpeciesInit();
const KIRBY = Dex.toID(KIRBY_NAME);

/* ---- helpers ---- */
const base = (id) => Dex.mod('cobblemon').species.get(id).baseStats;
let uuidN = 0;
/* Field order matches BattleRegistry.packTeam in Cobblemon 1.8.1. */
function mon(species, o = {}) {
  return [species, '', `uuid-${++uuidN}`, o.hp ?? 100, '', '-1', '', o.ability ?? (species === KIRBY ? 'copyability' : 'pressure'),
    (o.moves ?? ['splash']).join(','), (o.moves ?? ['splash']).map(() => '35/35').join(','), o.nature ?? 'serious', '0,0,0,0,0,0', 'N',
    o.ivs ?? '31,31,31,31,31,31', '', String(o.level ?? 50), '70,pokeball,,,,Fairy,'].join('|');
}
function stat(baseV, level, iv, ev, nat = 1) {
  return Math.floor((Math.floor((2 * baseV + iv + Math.floor(ev / 4)) * level / 100) + 5) * nat);
}

function start(team1, team2, gameType = 'singles') {
  const s = new BattleStream();
  const out = [];
  s.write(`>start ${JSON.stringify({ format: { mod: 'cobblemon', gameType, gen: 9, ruleset: ['Obtainable', '+Past', '+Unobtainable'], effectType: 'Format' } })}`);
  s.write(`>player p1 ${JSON.stringify({ name: 'a', team: team1.join(']') })}`);
  s.write(`>player p2 ${JSON.stringify({ name: 'b', team: team2.join(']') })}`);
  s.write(`>p1 team ${team1.length}`);
  s.write(`>p2 team ${team2.length}`);
  (async () => { for await (const chunk of s) out.push(chunk); })();
  return { s, out, b: () => s.battle, log: () => out.join('\n') };
}
/* Battle-visible protocol lines only (drops request JSON), for readable failure output. */
const protocol = (log) => log.split('\n').filter((l) => /^\|(-|switch|turn|move|faint|cant|win)/.test(l)).join('\n');
const visible = (t) => t.b().addLog.filter((l) => /^-activate/.test(l)).map((l) => l.slice(0, 120)).join(' ## ');
const stats5 = (p) => ({ atk: p.storedStats.atk, def: p.storedStats.def, spa: p.storedStats.spa, spd: p.storedStats.spd, spe: p.storedStats.spe });

const queue = [];
const test = (name, fn) => queue.push([name, fn]);
const flush = () => new Promise((resolve) => setImmediate(resolve));
async function runAll() {
  let passed = 0;
  console.log('Copy Ability battle tests');
  for (const [name, fn] of queue) {
    try { await fn(); passed++; console.log('  ok   ' + name); }
    catch (e) { console.log('  FAIL ' + name + '\n       ' + String(e.stack || e).split('\n').slice(0, 8).join('\n       ')); process.exitCode = 1; }
  }
  console.log(`\n${passed}/${queue.length} passed`);
}

const L = 50, IV = 31;
const kirbyBaseline = {
  atk: stat(bs.attack, L, IV, 0), def: stat(bs.defence, L, IV, 0), spa: stat(bs.special_attack, L, IV, 0),
  spd: stat(bs.special_defence, L, IV, 0), spe: stat(bs.speed, L, IV, 0),
};
const kirbyMaxHp = Math.floor((2 * bs.hp + IV + 100) * L / 100 + 10);

test("Kirby species: base stats are exactly Scream Tail's, dex 1984, Fairy only", () => {
  assert.deepStrictEqual(base(KIRBY), base('screamtail'));
  assert.strictEqual(Dex.mod('cobblemon').species.get(KIRBY).num, 1984);
  assert.deepStrictEqual(Dex.mod('cobblemon').species.get(KIRBY).types, ['Fairy']);
});

test('ability is registered in the cobblemon dex', () => {
  assert.ok(Dex.mod('cobblemon').abilities.get('copyability').exists);
});

/* [foe, expected copied stat]. Shuckle: Def=SpD=230 tie -> Def. Ditto: all 48 -> Atk (first).
   Chansey/Blissey: HP is the top stat but not copyable -> best of the remaining five. */
const cases = [
  ['machamp', 'atk'], ['shuckle', 'def'], ['chansey', 'spd'], ['ninjask', 'spe'],
  ['alakazam', 'spa'], ['blissey', 'spd'], ['ditto', 'atk'],
];
for (const [foe, expected] of cases) {
  test(`vs ${foe}: copies ${expected} only (HP untouched, announced once)`, async () => {
    const t = start([mon(KIRBY)], [mon(foe)]);
    await flush();
    const k = t.b().p1.active[0];
    const expectedStats = Object.assign({}, kirbyBaseline, { [expected]: stat(base(foe)[expected], L, IV, 0) });
    assert.deepStrictEqual(stats5(k), expectedStats);
    assert.strictEqual(k.maxhp, kirbyMaxHp, 'HP must be untouched');
    const announcements = t.b().addLog.filter((l) => l.startsWith('-activate|p1a'));
    assert.strictEqual(announcements.length, 1, visible(t));
  });
}

test('species data is never modified by the battle', () => {
  const before = JSON.stringify(Dex.mod('cobblemon').species.get(KIRBY).baseStats);
  start([mon(KIRBY)], [mon('machamp')]);
  assert.strictEqual(JSON.stringify(Dex.mod('cobblemon').species.get(KIRBY).baseStats), before);
});

test('nature, IVs and level still apply to the copied base stat', () => {
  const t = start([mon(KIRBY, { nature: 'adamant', level: 80, ivs: '31,20,31,31,31,31' })], [mon('machamp')]);
  const expected = Math.floor(stat(base('machamp').atk, 80, 20, 0) * 1.1);
  assert.strictEqual(t.b().p1.active[0].storedStats.atk, expected);
});

test('foe switching re-targets the copy, no stacking, other stats untouched', () => {
  const t = start([mon(KIRBY)], [mon('machamp'), mon('alakazam')]);
  const k = t.b().p1.active[0];
  assert.strictEqual(k.storedStats.atk, stat(base('machamp').atk, L, IV, 0));
  t.s.write('>p1 move 1');
  t.s.write('>p2 switch 2');
  assert.deepStrictEqual(stats5(k), Object.assign({}, kirbyBaseline, { spa: stat(base('alakazam').spa, L, IV, 0) }));
});

test('switching Kirby out restores everything; switching back copies again', () => {
  const t = start([mon(KIRBY), mon('pikachu')], [mon('machamp')]);
  const kirby = t.b().p1.pokemon[0];
  t.s.write('>p1 switch 2');
  t.s.write('>p2 move 1');
  assert.deepStrictEqual(stats5(kirby), kirbyBaseline, 'benched Kirby must hold baseline stats');
  assert.strictEqual(kirby.abilityState.stat, null);
  t.s.write('>p1 switch 2');
  t.s.write('>p2 move 1');
  assert.strictEqual(t.b().p1.active[0], kirby);
  assert.strictEqual(kirby.storedStats.atk, stat(base('machamp').atk, L, IV, 0));
  assert.strictEqual(kirby.storedStats.def, kirbyBaseline.def);
});

test('two Kirbys keep separate state', () => {
  const t = start([mon(KIRBY)], [mon(KIRBY)]);
  const [a, b] = [t.b().p1.active[0], t.b().p2.active[0]];
  assert.notStrictEqual(a.abilityState, b.abilityState);
  assert.strictEqual(a.abilityState.stat, 'spd');
  assert.strictEqual(b.abilityState.stat, 'spd');
});

test('doubles: copies from the facing (mirrored) foe', () => {
  const t = start([mon(KIRBY), mon('pikachu')], [mon('machamp'), mon('alakazam')], 'doubles');
  assert.strictEqual(t.b().p1.active[0].abilityState.stat, 'spa');
});

test('speed copy is reflected in battle speed', () => {
  const t = start([mon(KIRBY, { moves: ['tackle'] })], [mon('ninjask', { moves: ['tackle'] })]);
  const k = t.b().p1.active[0];
  assert.strictEqual(k.storedStats.spe, stat(base('ninjask').spe, L, IV, 0));
  assert.strictEqual(k.speed, k.storedStats.spe);
});

test('fainted foe replaced: Kirby recalculates once for the replacement', async () => {
  const t = start([mon(KIRBY, { moves: ['tackle'] })], [mon('machamp', { moves: ['tackle'], hp: 1 }), mon('alakazam')]);
  t.s.write('>p1 move 1');
  t.s.write('>p2 move 1');
  await flush();
  if (t.b().p2.active[0].fainted || t.b().p2.pokemonLeft < 2) { /* machamp fainted, replacement request pending */ }
  t.s.write('>p2 switch 2');
  await flush();
  const k = t.b().p1.active[0];
  assert.strictEqual(k.abilityState.stat, 'spa');
  assert.deepStrictEqual(stats5(k), Object.assign({}, kirbyBaseline, { spa: stat(base('alakazam').spa, L, IV, 0) }));
});

test('ability suppression (Gastro Acid) reverts the copied stat', async () => {
  const t = start([mon(KIRBY, { moves: ['splash'] })], [mon('machamp', { moves: ['gastroacid'] })]);
  const k = t.b().p1.active[0];
  assert.strictEqual(k.storedStats.atk, stat(base('machamp').atk, L, IV, 0));
  t.s.write('>p1 move 1');
  t.s.write('>p2 move 1');
  await flush();
  assert.ok(k.volatiles.gastroacid, 'Gastro Acid should have landed');
  assert.deepStrictEqual(stats5(k), kirbyBaseline);
});

test('Kirby fainting does not break the battle or the foe', async () => {
  const t = start([mon(KIRBY, { hp: 1 }), mon('pikachu')], [mon('machamp', { moves: ['tackle'] })]);
  t.s.write('>p1 move 1');
  t.s.write('>p2 move 1');
  await flush();
  const kirby = t.b().p1.pokemon[0];
  assert.ok(kirby.fainted, 'Kirby should have fainted');
  t.s.write('>p1 switch 2');
  await flush();
  assert.strictEqual(t.b().p1.active[0].species.name, 'Pikachu');
  assert.deepStrictEqual(stats5(kirby), kirbyBaseline, 'fainted Kirby keeps baseline stats once benched');
});

test('survives several turns without errors or repeated announcements', async () => {
  const t = start([mon(KIRBY, { moves: ['tackle'] })], [mon('machamp', { moves: ['tackle'] })]);
  for (let i = 0; i < 5 && !t.b().ended; i++) {
    t.s.write('>p1 move 1');
    t.s.write('>p2 move 1');
  }
  await flush();
  const adds = t.b().addLog;
  const bad = t.log().split('\n').filter((l) => /^\|(error|crash)|^(error|crash)/i.test(l) || /Cannot read|TypeError/.test(l)).filter((l) => !/Team Preview/.test(l));
  assert.deepStrictEqual(bad.map((l) => l.slice(0, 200)), [], 'engine reported errors');
  const activations = adds.filter((l) => l.startsWith('-activate|p1a')).length;
  assert.strictEqual(activations, 1, 'only one announcement while the foe is unchanged\n' + visible(t));
});

runAll();
