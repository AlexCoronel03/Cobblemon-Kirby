package com.alexcoronel.cobblemonkirby;

import com.alexcoronel.cobblemonkirby.command.KirbyCopyCommand;
import com.alexcoronel.cobblemonkirby.species.KirbySpeciesVerifier;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Entry point of the Cobblemon Kirby addon.
 *
 * <p>Almost everything is data: the species, the Showdown ability script, the dex entries and spawn are datapack
 * files, and the model/animations/textures are resource-pack files, all bundled in this jar. The Java side only
 * verifies that Cobblemon accepted that data and offers a small preview command.
 */
public final class CobblemonKirby implements ModInitializer {
    public static final Logger LOGGER = LoggerFactory.getLogger(KirbyConstants.MOD_ID);

    @Override
    public void onInitialize() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) ->
                KirbyCopyCommand.register(dispatcher));
        // Cobblemon loads its registries (abilities -> species -> dex) while the server starts; verify afterwards.
        ServerLifecycleEvents.SERVER_STARTED.register(server -> KirbySpeciesVerifier.verifyAndLog(LOGGER));
    }
}
