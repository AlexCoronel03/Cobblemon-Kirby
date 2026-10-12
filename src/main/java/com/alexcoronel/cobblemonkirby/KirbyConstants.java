package com.alexcoronel.cobblemonkirby;

import net.minecraft.resources.ResourceLocation;

/** Identifiers shared by the addon's Java components. The data itself lives in the mod's datapack resources. */
public final class KirbyConstants {
    public static final String MOD_ID = "cobblemon_kirby";

    /** Species identifier ({@code cobblemon_kirby:kirby}); the namespace keeps it clear of every Cobblemon species. */
    public static final ResourceLocation SPECIES_ID = ResourceLocation.fromNamespaceAndPath(MOD_ID, "kirby");

    /** The species whose base stats Kirby must reproduce exactly. */
    public static final ResourceLocation SCREAM_TAIL_ID = ResourceLocation.fromNamespaceAndPath("cobblemon", "screamtail");

    /** Dex numbers are tracked per namespace by Cobblemon, so 1984 cannot collide with a Cobblemon species. */
    public static final int DEX_NUMBER = 1984;

    /** Showdown/Cobblemon ability id of Copy Ability (file name of data/cobblemon_kirby/abilities/copyability.js). */
    public static final String ABILITY_ID = "copyability";

    private KirbyConstants() {
    }
}
