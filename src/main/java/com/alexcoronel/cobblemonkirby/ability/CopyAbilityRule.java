package com.alexcoronel.cobblemonkirby.ability;

import java.util.Optional;

/**
 * Reference implementation of Copy Ability's stat selection, kept free of Minecraft/Cobblemon types.
 *
 * <p>The authoritative battle logic is the Showdown script {@code data/cobblemon_kirby/abilities/copyability.js}
 * (Cobblemon runs all ability logic inside its embedded Showdown simulator). This class mirrors only the
 * <em>selection rule</em> so it can be unit-tested, used by the {@code /kirbycopy} preview command, and compared
 * against the script.
 *
 * <h2>Rule</h2>
 * <ul>
 *   <li>Candidates are the five stats Attack, Defense, Sp. Atk, Sp. Def, Speed.</li>
 *   <li>The candidate with the highest <em>base</em> stat of the facing opponent is copied.</li>
 *   <li><b>Ties</b> are resolved by candidate order (the order of {@link Copyable#values()}): the earlier stat wins.</li>
 *   <li>HP is compared by nobody: Cobblemon writes Showdown's absolute HP values straight back into the stored
 *       Pokémon, so rescaling max HP mid-battle would corrupt saved health. When HP is the opponent's highest stat the
 *       best of the remaining five is copied instead. See the README ("Known limitation: HP").</li>
 * </ul>
 */
public final class CopyAbilityRule {

    /** Copyable stats, in tie-break order. {@link #showdownId} matches the ids Showdown uses. */
    public enum Copyable {
        ATTACK("atk", "Attack"),
        DEFENCE("def", "Defense"),
        SPECIAL_ATTACK("spa", "Special Attack"),
        SPECIAL_DEFENCE("spd", "Special Defense"),
        SPEED("spe", "Speed");

        public final String showdownId;
        public final String label;

        Copyable(String showdownId, String label) {
            this.showdownId = showdownId;
            this.label = label;
        }

        public static Optional<Copyable> fromShowdownId(String id) {
            for (Copyable stat : values()) {
                if (stat.showdownId.equals(id)) {
                    return Optional.of(stat);
                }
            }
            return Optional.empty();
        }
    }

    private CopyAbilityRule() {
    }

    /**
     * @param attack      opponent base Attack
     * @param defence     opponent base Defense
     * @param specialAtk  opponent base Special Attack
     * @param specialDef  opponent base Special Defense
     * @param speed       opponent base Speed
     * @return the stat Kirby copies (never null)
     */
    public static Copyable select(int attack, int defence, int specialAtk, int specialDef, int speed) {
        int[] values = {attack, defence, specialAtk, specialDef, speed};
        Copyable[] order = Copyable.values();
        int best = 0;
        for (int i = 1; i < values.length; i++) {
            if (values[i] > values[best]) { // strict '>' keeps the earlier stat on ties
                best = i;
            }
        }
        return order[best];
    }
}
