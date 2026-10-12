package com.alexcoronel.cobblemonkirby.command;

import com.alexcoronel.cobblemonkirby.ability.CopyAbilityRule;
import com.cobblemon.mod.common.api.pokemon.PokemonSpecies;
import com.cobblemon.mod.common.api.pokemon.stats.Stat;
import com.cobblemon.mod.common.api.pokemon.stats.Stats;
import com.cobblemon.mod.common.pokemon.Species;
import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;

import java.util.Map;

/**
 * {@code /kirbycopy <species>} - shows which base stat Copy Ability would take from the given species.
 *
 * <p>Read-only helper for server owners and testers: it reads the live species registry (no hard-coded list), so it
 * also covers species added by other addons. The actual copying happens in the battle script.
 */
public final class KirbyCopyCommand {
    private KirbyCopyCommand() {
    }

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("kirbycopy")
                .then(Commands.argument("species", StringArgumentType.greedyString())
                        .executes(ctx -> run(ctx.getSource(), StringArgumentType.getString(ctx, "species")))));
    }

    private static int run(CommandSourceStack source, String input) {
        String trimmed = input.trim().toLowerCase();
        ResourceLocation id = trimmed.contains(":")
                ? ResourceLocation.tryParse(trimmed)
                : ResourceLocation.fromNamespaceAndPath("cobblemon", trimmed.replace(" ", ""));
        Species species = id == null ? null : PokemonSpecies.INSTANCE.getByIdentifier(id);
        if (species == null) {
            source.sendFailure(Component.literal("Unknown species '" + input + "'. Use e.g. 'machamp' or 'namespace:name'."));
            return 0;
        }
        Map<Stat, Integer> base = species.getBaseStats();
        int atk = base.getOrDefault(Stats.ATTACK, 0);
        int def = base.getOrDefault(Stats.DEFENCE, 0);
        int spa = base.getOrDefault(Stats.SPECIAL_ATTACK, 0);
        int spd = base.getOrDefault(Stats.SPECIAL_DEFENCE, 0);
        int spe = base.getOrDefault(Stats.SPEED, 0);
        int hp = base.getOrDefault(Stats.HP, 0);
        CopyAbilityRule.Copyable copied = CopyAbilityRule.select(atk, def, spa, spd, spe);
        int value = switch (copied) {
            case ATTACK -> atk;
            case DEFENCE -> def;
            case SPECIAL_ATTACK -> spa;
            case SPECIAL_DEFENCE -> spd;
            case SPEED -> spe;
        };
        String hpNote = hp > value ? " (HP " + hp + " is higher but HP cannot be copied)" : "";
        source.sendSuccess(() -> Component.literal("Against " + species.getName() + " (HP " + hp + ", Atk " + atk
                + ", Def " + def + ", SpA " + spa + ", SpD " + spd + ", Spe " + spe + ") Kirby copies "
                + copied.label + " = " + value + hpNote), false);
        return 1;
    }
}
