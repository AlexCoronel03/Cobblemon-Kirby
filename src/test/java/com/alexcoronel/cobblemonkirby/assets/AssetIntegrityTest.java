package com.alexcoronel.cobblemonkirby.assets;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.bedrockk.molang.MoLang;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.awt.image.BufferedImage;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

/**
 * Static validation of the model / animation / poser / resolver files, mirroring what Cobblemon's loaders do:
 * <ul>
 *   <li>every Molang expression is parsed with Cobblemon's own Molang parser (after the same {@code q.} -> {@code query.}
 *       clean-up the animation adapter applies),</li>
 *   <li>every animated bone exists in the geometry, every referenced animation exists,</li>
 *   <li>every cube's UV footprint lies inside the texture and the referenced files exist.</li>
 * </ul>
 */
class AssetIntegrityTest {
    private static final String ASSETS = "assets/cobblemon_kirby/";
    private static JsonObject geo;
    private static JsonObject animations;
    private static JsonObject poser;
    private static JsonObject resolver;
    private static Set<String> bones;

    private static JsonObject json(String path) throws Exception {
        try (InputStream in = AssetIntegrityTest.class.getClassLoader().getResourceAsStream(path)) {
            assertNotNull(in, path + " missing");
            return JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }

    @BeforeAll
    static void load() throws Exception {
        geo = json(ASSETS + "bedrock/pokemon/models/kirby/kirby.geo.json")
                .getAsJsonArray("minecraft:geometry").get(0).getAsJsonObject();
        animations = json(ASSETS + "bedrock/pokemon/animations/kirby/kirby.animation.json").getAsJsonObject("animations");
        poser = json(ASSETS + "bedrock/pokemon/posers/kirby/kirby.json");
        resolver = json(ASSETS + "bedrock/pokemon/resolvers/kirby/0_kirby_base.json");
        bones = new HashSet<>();
        for (JsonElement b : geo.getAsJsonArray("bones")) {
            bones.add(b.getAsJsonObject().get("name").getAsString());
        }
    }

    /** Same clean-up BedrockAnimationAdapter.cleanExpression performs before parsing. */
    private static String clean(String value) {
        String v = value.startsWith("+") ? value.substring(1) : value;
        if (v.startsWith("-(")) {
            v = v.replaceFirst("-\\(", "-1*(");
        }
        return v.replace("*+", "*").replace("q.", "query.");
    }

    private static void parse(String expression, String where) {
        try {
            assertFalse(MoLang.parse(clean(expression)).isEmpty(), where);
        } catch (RuntimeException e) {
            throw new AssertionError("Molang parse failure in " + where + ": " + expression, e);
        }
    }

    private static List<JsonArray> vectors(JsonElement transform) {
        List<JsonArray> out = new ArrayList<>();
        if (transform.isJsonArray()) {
            out.add(transform.getAsJsonArray());
        } else {
            for (Map.Entry<String, JsonElement> frame : transform.getAsJsonObject().entrySet()) {
                Double.parseDouble(frame.getKey()); // keyframe time must be numeric
                JsonElement v = frame.getValue();
                if (v.isJsonArray()) {
                    out.add(v.getAsJsonArray());
                } else {
                    JsonObject o = v.getAsJsonObject();
                    assertTrue(o.has("post") || o.has("pre"), "jump keyframe needs pre/post");
                    if (o.has("pre")) out.add(o.getAsJsonArray("pre"));
                    if (o.has("post")) out.add(o.getAsJsonArray("post"));
                }
            }
        }
        return out;
    }

    @Test
    void everyAnimationExpressionParsesAndTargetsAnExistingBone() {
        assertFalse(animations.entrySet().isEmpty());
        for (Map.Entry<String, JsonElement> anim : animations.entrySet()) {
            JsonObject a = anim.getValue().getAsJsonObject();
            for (Map.Entry<String, JsonElement> bone : a.getAsJsonObject("bones").entrySet()) {
                assertTrue(bones.contains(bone.getKey()), anim.getKey() + " animates unknown bone " + bone.getKey());
                for (Map.Entry<String, JsonElement> t : bone.getValue().getAsJsonObject().entrySet()) {
                    assertTrue(Set.of("position", "rotation", "scale").contains(t.getKey()), t.getKey());
                    for (JsonArray vec : vectors(t.getValue())) {
                        assertEquals(3, vec.size(), anim.getKey() + "/" + bone.getKey());
                        for (JsonElement component : vec) {
                            parse(component.getAsString(), anim.getKey() + "/" + bone.getKey() + "/" + t.getKey());
                        }
                    }
                }
            }
        }
    }

    @Test
    void requiredAnimationSetExists() {
        for (String name : List.of("ground_idle", "ground_walk", "ground_run", "battle_idle", "physical", "special",
                "status", "recoil", "battle_recoil", "faint", "sleep", "cry", "battle_cry", "blink", "air_idle", "air_fly")) {
            assertTrue(animations.has("animation.kirby." + name), "missing animation " + name);
        }
        // Looping animations must declare a length their Molang period divides evenly (seamless loops).
        for (String loop : List.of("ground_idle", "ground_walk", "ground_run", "battle_idle", "sleep", "air_idle", "air_fly")) {
            JsonObject a = animations.getAsJsonObject("animation.kirby." + loop);
            assertTrue(a.get("loop").getAsBoolean(), loop);
            assertTrue(a.get("animation_length").getAsDouble() > 0, loop);
        }
    }

    @Test
    void poserReferencesExistingAnimationsAndBones() {
        String all = poser.toString();
        Matcher refs = Pattern.compile("q\\.bedrock(?:_stateful|_primary|_quirk)?\\('(\\w+)', ?'(\\w+)'").matcher(all);
        int found = 0;
        while (refs.find()) {
            found++;
            if (refs.group(1).equals("dummy")) {
                continue; // Cobblemon's own empty animation group
            }
            assertEquals("kirby", refs.group(1));
            assertTrue(animations.has("animation.kirby." + refs.group(2)), "poser uses unknown animation " + refs.group(2));
        }
        assertTrue(found >= 10, "expected the poser to reference the animation set");
        assertTrue(bones.contains(poser.get("rootBone").getAsString()));
        Matcher looks = Pattern.compile("q\\.look\\('(\\w+)'").matcher(all);
        while (looks.find()) {
            assertTrue(bones.contains(looks.group(1)), "q.look on unknown bone " + looks.group(1));
        }
        // every poser expression is valid Molang
        collectStrings(poser.getAsJsonObject("poses"), s -> {
            if (s.startsWith("q.") || s.startsWith("!q.") || s.contains("q.")) {
                parse(s, "poser");
            }
        });
        collectStrings(poser.getAsJsonObject("animations"), s -> parse(s, "poser.animations"));
    }

    private static void collectStrings(JsonElement e, java.util.function.Consumer<String> sink) {
        if (e.isJsonPrimitive() && e.getAsJsonPrimitive().isString()) {
            sink.accept(e.getAsString());
        } else if (e.isJsonArray()) {
            e.getAsJsonArray().forEach(x -> collectStrings(x, sink));
        } else if (e.isJsonObject()) {
            e.getAsJsonObject().entrySet().forEach(x -> collectStrings(x.getValue(), sink));
        }
    }

    @Test
    void poserCoversEveryRequiredPoseType() {
        Set<String> types = new HashSet<>();
        for (Map.Entry<String, JsonElement> pose : poser.getAsJsonObject("poses").entrySet()) {
            pose.getValue().getAsJsonObject().getAsJsonArray("poseTypes").forEach(t -> types.add(t.getAsString()));
        }
        for (String needed : List.of("STAND", "WALK", "SLEEP", "PORTRAIT", "PROFILE", "NONE", "HOVER", "FLY")) {
            assertTrue(types.contains(needed), "no pose for " + needed);
        }
        assertTrue(poser.getAsJsonObject("poses").getAsJsonObject("battle-standing").get("isBattle").getAsBoolean());
    }

    @Test
    void geometryIsConsistent() {
        int width = geo.getAsJsonObject("description").get("texture_width").getAsInt();
        int height = geo.getAsJsonObject("description").get("texture_height").getAsInt();
        Set<String> seen = new HashSet<>();
        int cubes = 0;
        for (JsonElement el : geo.getAsJsonArray("bones")) {
            JsonObject b = el.getAsJsonObject();
            String name = b.get("name").getAsString();
            assertTrue(seen.add(name), "duplicate bone " + name);
            if (b.has("parent")) {
                assertTrue(seen.contains(b.get("parent").getAsString()), name + " parent must be declared first");
            }
            if (!b.has("cubes")) continue;
            for (JsonElement c : b.getAsJsonArray("cubes")) {
                cubes++;
                JsonObject cube = c.getAsJsonObject();
                JsonArray size = cube.getAsJsonArray("size");
                JsonArray uv = cube.getAsJsonArray("uv");
                double w = size.get(0).getAsDouble(), h = size.get(1).getAsDouble(), d = size.get(2).getAsDouble();
                double footprintW = uv.get(0).getAsDouble() + 2 * (w + d);
                double footprintH = uv.get(1).getAsDouble() + d + h;
                assertTrue(footprintW <= width && footprintH <= height, name + " cube UV leaves the texture");
                if (cube.has("rotation")) {
                    assertTrue(cube.has("pivot"), name + ": rotated cube needs its own pivot");
                }
            }
        }
        assertTrue(cubes > 0 && cubes < 150, "polygon budget: " + cubes + " cubes");
        for (String locator : List.of("root", "middle", "target", "special", "face", "head", "hand_primary", "item")) {
            assertTrue(geo.toString().contains("\"" + locator + "\""), "missing locator " + locator);
        }
    }

    @Test
    void texturesExistAndAreOpaqueWhereTheModelSamplesThem() throws Exception {
        List<String> textures = new ArrayList<>();
        for (JsonElement v : resolver.getAsJsonArray("variations")) {
            JsonObject variation = v.getAsJsonObject();
            if (variation.has("texture")) {
                textures.add(variation.get("texture").getAsString());
            }
        }
        assertEquals(2, textures.size(), "base + shiny");
        for (String tex : textures) {
            String path = tex.replace("cobblemon_kirby:", ASSETS);
            try (InputStream in = getClass().getClassLoader().getResourceAsStream(path)) {
                assertNotNull(in, tex + " missing");
                BufferedImage img = ImageIO.read(in);
                assertEquals(geo.getAsJsonObject("description").get("texture_width").getAsInt(), img.getWidth());
                assertEquals(geo.getAsJsonObject("description").get("texture_height").getAsInt(), img.getHeight());
                // body region (0,0)-(96,48) must be fully opaque or the body would have holes
                for (int y = 0; y < 48; y++) {
                    for (int x = 0; x < 96; x++) {
                        assertEquals(255, (img.getRGB(x, y) >>> 24) & 0xFF, tex + " transparent at " + x + "," + y);
                    }
                }
            }
        }
        assertEquals("cobblemon_kirby:kirby", resolver.get("species").getAsString());
        assertEquals("cobblemon_kirby:kirby.geo", resolver.getAsJsonArray("variations").get(0).getAsJsonObject().get("model").getAsString());
    }

    @Test
    void everyLangKeyNeededIsPresent() throws Exception {
        JsonObject lang = json(ASSETS + "lang/en_us.json");
        for (String key : List.of("cobblemon_kirby.species.kirby.name", "cobblemon_kirby.species.kirby.desc",
                "cobblemon.ability.copyability", "cobblemon.ability.copyability.desc",
                "cobblemon.battle.activate.copyability")) {
            assertTrue(lang.has(key), key);
        }
    }
}
