package com.alexcoronel.cobblemonkirby.species;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

/**
 * Data-level checks on the shipped species file against Scream Tail's species file taken from the Cobblemon jar
 * that is on the test classpath. (Cobblemon's own Kotlin classes cannot be initialised outside Fabric's runtime
 * remapper, so the in-game load is verified by {@code KirbySpeciesVerifier} instead.)
 */
class KirbySpeciesJsonTest {
    private static JsonObject kirby;
    private static JsonObject screamTail;

    private static JsonObject read(String resource) throws Exception {
        try (InputStream in = KirbySpeciesJsonTest.class.getClassLoader().getResourceAsStream(resource)) {
            assertNotNull(in, resource + " must be on the classpath");
            return JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }

    @BeforeAll
    static void load() throws Exception {
        kirby = read("data/cobblemon_kirby/species/kirby.json");
        screamTail = read("data/cobblemon/species/generation9/screamtail.json");
    }

    @Test
    void dexNumberIs1984AndScreamTailKeepsItsOwn() {
        assertEquals(1984, kirby.get("nationalPokedexNumber").getAsInt());
        assertEquals("Kirby", kirby.get("name").getAsString());
        assertEquals(985, screamTail.get("nationalPokedexNumber").getAsInt());
    }

    @Test
    void baseStatsAreExactlyScreamTails() {
        JsonObject expected = screamTail.getAsJsonObject("baseStats");
        JsonObject actual = kirby.getAsJsonObject("baseStats");
        assertEquals(6, actual.size());
        for (String key : expected.keySet()) {
            assertEquals(expected.get(key).getAsInt(), actual.get(key).getAsInt(), key);
        }
        // Literal values as a second, independent anchor (Scream Tail: 115/65/99/65/115/111).
        assertEquals(115, actual.get("hp").getAsInt());
        assertEquals(65, actual.get("attack").getAsInt());
        assertEquals(99, actual.get("defence").getAsInt());
        assertEquals(65, actual.get("special_attack").getAsInt());
        assertEquals(115, actual.get("special_defence").getAsInt());
        assertEquals(111, actual.get("speed").getAsInt());
    }

    @Test
    void pureFairyTyping() {
        assertEquals("fairy", kirby.get("primaryType").getAsString());
        assertFalse(kirby.has("secondaryType"));
    }

    @Test
    void copyAbilityIsTheOnlyAbility() {
        JsonArray abilities = kirby.getAsJsonArray("abilities");
        assertEquals(2, abilities.size());
        for (JsonElement ability : abilities) {
            assertTrue(ability.getAsString().endsWith("copyability"), ability.getAsString());
        }
    }

    @Test
    void canFly() {
        assertTrue(kirby.getAsJsonObject("behaviour").getAsJsonObject("moving").getAsJsonObject("fly")
                .get("canFly").getAsBoolean());
    }

    @Test
    void implementedAndHasLearnset() {
        assertTrue(kirby.get("implemented").getAsBoolean());
        assertEquals(screamTail.getAsJsonArray("moves"), kirby.getAsJsonArray("moves"));
    }

    @Test
    void abilityScriptIsSingleLineSafe() throws Exception {
        // Cobblemon joins the script into one line before evaluating it, so no '//' line comments are allowed.
        try (InputStream in = getClass().getClassLoader().getResourceAsStream("data/cobblemon_kirby/abilities/copyability.js")) {
            assertNotNull(in);
            String script = new String(in.readAllBytes(), StandardCharsets.UTF_8);
            for (String line : script.split("\\R")) {
                String t = line.stripLeading();
                assertFalse(t.startsWith("//"), "line comments are not allowed: " + t);
                assertFalse(line.contains(" //"), "line comments are not allowed: " + t);
            }
        }
    }
}
