package com.alexcoronel.cobblemonkirby.species;

import com.alexcoronel.cobblemonkirby.KirbyConstants;
import com.cobblemon.mod.common.api.abilities.PotentialAbility;
import com.cobblemon.mod.common.api.pokemon.PokemonSpecies;
import com.cobblemon.mod.common.api.pokemon.stats.Stats;
import com.cobblemon.mod.common.pokemon.Species;
import org.slf4j.Logger;

import java.util.ArrayList;
import java.util.List;

/**
 * Read-only integrity check run once the server has finished loading Cobblemon's registries.
 *
 * <p>Kirby is pure data (a datapack species JSON), so the realistic failure modes are data problems: the species
 * did not load, the ability script was rejected (an unknown ability silently disappears from an {@code AbilityPool}),
 * or the stats drifted away from Scream Tail's. This class reports those clearly in the log. It never mutates
 * species data.
 */
public final class KirbySpeciesVerifier {
    private KirbySpeciesVerifier() {
    }

    /** @return human readable problems; empty when everything is as specified. */
    public static List<String> verify() {
        List<String> problems = new ArrayList<>();
        Species kirby = PokemonSpecies.INSTANCE.getByIdentifier(KirbyConstants.SPECIES_ID);
        if (kirby == null) {
            problems.add("species " + KirbyConstants.SPECIES_ID + " is not loaded");
            return problems;
        }
        if (kirby.getNationalPokedexNumber() != KirbyConstants.DEX_NUMBER) {
            problems.add("dex number is " + kirby.getNationalPokedexNumber() + ", expected " + KirbyConstants.DEX_NUMBER);
        }
        if (!"fairy".equalsIgnoreCase(kirby.getPrimaryType().getName()) || kirby.getSecondaryType() != null) {
            problems.add("typing is not pure Fairy");
        }
        boolean hasAbility = false;
        for (PotentialAbility ability : kirby.getAbilities()) {
            if (KirbyConstants.ABILITY_ID.equals(ability.getTemplate().getName())) {
                hasAbility = true;
            }
        }
        if (!hasAbility) {
            problems.add("ability '" + KirbyConstants.ABILITY_ID + "' is missing from Kirby's ability pool "
                    + "(the Showdown script data/cobblemon_kirby/abilities/copyability.js failed to register)");
        }

        Species screamTail = PokemonSpecies.INSTANCE.getByIdentifier(KirbyConstants.SCREAM_TAIL_ID);
        if (screamTail == null) {
            problems.add("cobblemon:screamtail not found, cannot compare base stats");
        } else {
            Stats[] permanent = {Stats.HP, Stats.ATTACK, Stats.DEFENCE, Stats.SPECIAL_ATTACK, Stats.SPECIAL_DEFENCE, Stats.SPEED};
            for (Stats stat : permanent) {
                Integer expected = screamTail.getBaseStats().get(stat);
                Integer actual = kirby.getBaseStats().get(stat);
                if (expected == null || !expected.equals(actual)) {
                    problems.add("base " + stat.getShowdownId() + " is " + actual + ", Scream Tail has " + expected);
                }
            }
        }
        return problems;
    }

    public static void verifyAndLog(Logger logger) {
        List<String> problems = verify();
        if (problems.isEmpty()) {
            logger.info("Kirby (#{}) verified: stats match Scream Tail, Fairy type, Copy Ability registered.",
                    KirbyConstants.DEX_NUMBER);
        } else {
            problems.forEach(p -> logger.error("Kirby verification failed: {}", p));
        }
    }
}
