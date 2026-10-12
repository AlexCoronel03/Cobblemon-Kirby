package com.alexcoronel.cobblemonkirby.ability;

import static com.alexcoronel.cobblemonkirby.ability.CopyAbilityRule.Copyable.ATTACK;
import static com.alexcoronel.cobblemonkirby.ability.CopyAbilityRule.Copyable.DEFENCE;
import static com.alexcoronel.cobblemonkirby.ability.CopyAbilityRule.Copyable.SPECIAL_ATTACK;
import static com.alexcoronel.cobblemonkirby.ability.CopyAbilityRule.Copyable.SPECIAL_DEFENCE;
import static com.alexcoronel.cobblemonkirby.ability.CopyAbilityRule.Copyable.SPEED;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class CopyAbilityRuleTest {

    @Test
    void picksTheHighestBaseStat() {
        // Machamp 130/80/65/85/55
        assertEquals(ATTACK, CopyAbilityRule.select(130, 80, 65, 85, 55));
        // Alakazam 50/45/135/95/120
        assertEquals(SPECIAL_ATTACK, CopyAbilityRule.select(50, 45, 135, 95, 120));
        // Ninjask 90/45/50/50/160
        assertEquals(SPEED, CopyAbilityRule.select(90, 45, 50, 50, 160));
        // Shuckle 10/230/10/230/5
        assertEquals(DEFENCE, CopyAbilityRule.select(10, 230, 10, 230, 5));
        // Blissey (HP 255 ignored) 10/10/75/135/55
        assertEquals(SPECIAL_DEFENCE, CopyAbilityRule.select(10, 10, 75, 135, 55));
    }

    @Test
    void tiesGoToTheEarlierStatInTheDocumentedOrder() {
        assertEquals(ATTACK, CopyAbilityRule.select(100, 100, 100, 100, 100));
        assertEquals(DEFENCE, CopyAbilityRule.select(50, 100, 100, 100, 100));
        assertEquals(SPECIAL_ATTACK, CopyAbilityRule.select(50, 50, 100, 100, 100));
        assertEquals(SPECIAL_DEFENCE, CopyAbilityRule.select(50, 50, 50, 100, 100));
        assertEquals(SPEED, CopyAbilityRule.select(50, 50, 50, 50, 100));
    }

    @Test
    void isDeterministicAndDoesNotDependOnInputOrderingAcrossCalls() {
        for (int i = 0; i < 1000; i++) {
            assertEquals(SPECIAL_DEFENCE, CopyAbilityRule.select(10, 10, 10, 90, 90 - (i % 1)));
        }
    }

    @Test
    void showdownIdsMatchTheScript() {
        assertEquals(ATTACK, CopyAbilityRule.Copyable.fromShowdownId("atk").orElseThrow());
        assertEquals(SPEED, CopyAbilityRule.Copyable.fromShowdownId("spe").orElseThrow());
        assertTrue(CopyAbilityRule.Copyable.fromShowdownId("hp").isEmpty());
    }
}
