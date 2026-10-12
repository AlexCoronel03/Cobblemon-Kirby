/*
 * Copy Ability - Kirby's signature ability (Cobblemon Kirby addon).
 *
 * Kirby copies the highest BASE stat of the opposing Pokemon it is facing.
 * The copied base stat is fed through the regular stat formula with Kirby's own
 * level / IVs / EVs / nature, so only that one battle stat changes. Species data,
 * the other five stats, stat stages, items and statuses are never touched.
 *
 * Rules (documented in README.md):
 *   - Facing foe : the foe in the mirrored slot, otherwise the first active foe.
 *   - Candidates : Atk, Def, SpA, SpD, Spe (HP is not copyable, see README).
 *   - Tie-break  : the stat that comes first in the order Atk, Def, SpA, SpD, Spe wins.
 *   - Source     : foe.species.baseStats (current forme), never the foe's final stats.
 *   - Recalc     : on entry (onStart) and whenever the facing foe's species changes (onUpdate).
 *   - Cleanup    : onSwitchOut / onEnd restore the original stat; Showdown also rebuilds
 *                  all stats from species data on every switch.
 *
 * NOTE: Cobblemon strips line breaks before evaluating this file, so only block
 * comments may be used (a line comment would swallow the rest of the script).
 */
(function () {
	var COPYABLE = ['atk', 'def', 'spa', 'spd', 'spe'];
	var LABEL = {atk: 'Attack', def: 'Defense', spa: 'Special Attack', spd: 'Special Defense', spe: 'Speed'};

	function highestCopyableStat(baseStats) {
		var best = null;
		for (var i = 0; i < COPYABLE.length; i++) {
			var stat = COPYABLE[i];
			if (best === null || baseStats[stat] > baseStats[best]) best = stat;
		}
		return best;
	}

	function facingFoe(pokemon) {
		var foes = pokemon.foes();
		if (!foes.length) return null;
		var mirrored = pokemon.side.active.length - 1 - pokemon.position;
		for (var i = 0; i < foes.length; i++) {
			if (foes[i].position === mirrored) return foes[i];
		}
		return foes[0];
	}

	function writeStat(battle, pokemon, stat, baseValue) {
		var base = {};
		for (var key in pokemon.species.baseStats) base[key] = pokemon.species.baseStats[key];
		base[stat] = baseValue;
		var value = battle.spreadModify(base, pokemon.set)[stat];
		pokemon.storedStats[stat] = value;
		if (pokemon.baseStoredStats) pokemon.baseStoredStats[stat] = value;
		if (pokemon.modifiedStats) pokemon.modifiedStats[stat] = value;
		if (stat === 'spe') pokemon.updateSpeed();
	}

	function restore(battle, pokemon, state) {
		if (state.stat) writeStat(battle, pokemon, state.stat, pokemon.species.baseStats[state.stat]);
		state.stat = null;
		state.key = null;
	}

	function refresh(battle, pokemon, announce) {
		var state = pokemon.abilityState;
		if (pokemon.fainted || pokemon.transformed) return;
		var foe = facingFoe(pokemon);
		if (!foe) return;
		var stat = highestCopyableStat(foe.species.baseStats);
		var key = foe.species.id + ':' + stat;
		if (state.key === key) return;
		restore(battle, pokemon, state);
		writeStat(battle, pokemon, stat, foe.species.baseStats[stat]);
		state.stat = stat;
		state.key = key;
		if (announce) battle.add('-activate', pokemon, 'ability: Copy Ability', LABEL[stat], '[of] ' + foe);
	}

	return {
		name: "Copy Ability",
		num: -1984,
		rating: 4,
		gen: 9,
		flags: {failroleplay: 1, noreceiver: 1, noentrain: 1, notrace: 1, failskillswap: 1},
		onStart: function (pokemon) {
			refresh(this, pokemon, true);
		},
		onUpdate: function (pokemon) {
			refresh(this, pokemon, true);
		},
		onSwitchOut: function (pokemon) {
			restore(this, pokemon, pokemon.abilityState);
		},
		onEnd: function (pokemon) {
			restore(this, pokemon, pokemon.abilityState);
		}
	};
})()
