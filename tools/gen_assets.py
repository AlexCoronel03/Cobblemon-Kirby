"""
Generates every Kirby art/animation asset of the addon from code so it is reproducible and reviewable:

  assets/cobblemon_kirby/bedrock/pokemon/models/kirby/kirby.geo.json        Blockbench/Bedrock geometry
  assets/cobblemon_kirby/bedrock/pokemon/animations/kirby/kirby.animation.json
  assets/cobblemon_kirby/bedrock/pokemon/posers/kirby/kirby.json
  assets/cobblemon_kirby/bedrock/pokemon/resolvers/kirby/0_kirby_base.json
  assets/cobblemon_kirby/textures/pokemon/kirby/kirby.png (+ kirby_shiny.png)

Everything here is original work: the body is a plain 24 x 24 x 24 cube with notched edges and a fluffy
texture generated procedurally (seeded value noise, see body_region). No third-party art is used.

The files are plain Blockbench-compatible JSON/PNG: open kirby.geo.json + kirby.png in Blockbench
(File > Open Model, Bedrock Entity) to edit them by hand.

usage: python tools/gen_assets.py
"""
import json
import math
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "src/main/resources/assets/cobblemon_kirby"
MODEL_DIR = ASSETS / "bedrock/pokemon/models/kirby"
ANIM_DIR = ASSETS / "bedrock/pokemon/animations/kirby"
POSER_DIR = ASSETS / "bedrock/pokemon/posers/kirby"
RESOLVER_DIR = ASSETS / "bedrock/pokemon/resolvers/kirby"
TEX_DIR = ASSETS / "textures/pokemon/kirby"

TEX_W, TEX_H = 128, 192

# --------------------------------------------------------------------------------------
# Texture layout (box-UV origins) on the 128 x 128 sheet.
# --------------------------------------------------------------------------------------
UV_BODY = (0, 0)        # 96 x 48   body Z box (carries the face); procedural fluff
UV_BODY_X = (0, 94)     # 96 x 48   body X box (sides)
UV_BODY_Y = (0, 142)    # 96 x 48   body Y box (top / bottom)
UV_PLAIN = (0, 50)      # 40 x 20   arms (plain body colour)
UV_EYE = (100, 0)       # 12 x 11   eye cube 5 x 10 x 1 (flush with the face)
UV_MOUTH = (100, 14)    # 14 x 4    mouth cube 6 x 3 x 1 (flush with the face)
UV_FOOT_A = (0, 72)     # 44 x 17   foot cubes (red)
UV_FOOT_B = (50, 72)    # 44 x 20   foot cubes (red)

# --------------------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------------------
# The body is a 24 x 24 x 24 cube centred on the `body`/`head` pivot so every bone pivot used by the
# animations lines up.
CENTER_Y = 17.0         # body centre; the cube spans y 5 .. 29, the feet 0 .. 5
FACE_Z = -12.0          # front face of the body cube
EYE_Y = 19.5            # eye centre (eyes are 10 tall)
MOUTH_Y = 11.0          # mouth centre
FLUSH = 0.02            # face details sit this far in front of the face plane (just avoids z-fighting)


def r(v):
    return round(v, 4)


def cube(origin, size, uv, pivot=None, rotation=None, inflate=None):
    c = {"origin": [r(o) for o in origin], "size": [r(s) for s in size], "uv": list(uv)}
    if pivot is not None:
        c["pivot"] = [r(p) for p in pivot]
    if rotation is not None:
        c["rotation"] = list(rotation)
    if inflate:
        c["inflate"] = inflate
    return c


def head_cubes():
    """
    A 24^3 body cube with its 12 edges notched by 2 units: three overlapping boxes (a 3D cross).
    The Z box carries the flat 20 x 20 face. Kirby has no ears.
    """
    c = CENTER_Y
    return [
        cube((-12, c - 10, -10), (24, 20, 20), UV_BODY_X),   # X box: left/right sides
        cube((-10, c - 12, -10), (20, 24, 20), UV_BODY_Y),   # Y box: top/bottom
        cube((-10, c - 10, -12), (20, 20, 24), UV_BODY),   # Z box: front face / back
    ]


def foot_bone(side):
    """side = +1 for foot_left (+x), -1 for foot_right (-x)."""
    x = 7.5 * side
    name = "foot_left" if side > 0 else "foot_right"
    return {
        "name": name, "parent": "kirby", "pivot": [x, 5, -5],
        "cubes": [
            # two tiers of crossed boxes -> a rounded, pill-like red foot
            cube((x - 5, 0, -11), (10, 3, 11), UV_FOOT_A),
            cube((x - 3.5, 0, -12.5), (7, 3, 14), UV_FOOT_B),
            cube((x - 4.25, 3, -10), (8.5, 2, 9), UV_FOOT_A),
            cube((x - 3, 3, -11.5), (6, 2, 12), UV_FOOT_B),
        ],
    }


def arm_bone(side):
    x = 12.5 * side
    name = "arm_left" if side > 0 else "arm_right"
    return {
        "name": name, "parent": "body", "pivot": [x, 16.5, 0],
        "cubes": [
            cube((x - 1 if side > 0 else x - 6, 13, -3.5), (7, 7, 7), UV_PLAIN),
            cube((x + 1 if side > 0 else x - 5.5, 14, -6), (4.5, 5, 12), UV_PLAIN),
        ],
    }


def build_geometry():
    bones = [
        {"name": "kirby", "pivot": [0, 0, 0]},
        {"name": "body", "parent": "kirby", "pivot": [0, CENTER_Y, 0]},
        {"name": "head", "parent": "body", "pivot": [0, CENTER_Y, 0], "cubes": head_cubes()},
        {"name": "eye_left", "parent": "head", "pivot": [4.5, EYE_Y, FACE_Z],
         "cubes": [cube((2, EYE_Y - 5, FACE_Z - FLUSH), (5, 10, 1), UV_EYE)]},
        {"name": "eye_right", "parent": "head", "pivot": [-4.5, EYE_Y, FACE_Z],
         "cubes": [cube((-7, EYE_Y - 5, FACE_Z - FLUSH), (5, 10, 1), UV_EYE)]},
        {"name": "mouth", "parent": "head", "pivot": [0, MOUTH_Y, FACE_Z],
         "cubes": [cube((-3, MOUTH_Y - 1.5, FACE_Z - FLUSH), (6, 3, 1), UV_MOUTH)]},
        arm_bone(1),
        arm_bone(-1),
        foot_bone(1),
        foot_bone(-1),
    ]
    # Locators (Cobblemon effects / held items / particles look these up by name).
    def loc(bone_name, parent, pivot, locators):
        bones.append({"name": bone_name, "parent": parent, "pivot": list(pivot), "locators": locators})
    loc("locator_root", "kirby", (0, 0, 0), {"root": [0, 0, 0]})
    loc("locator_middle", "body", (0, CENTER_Y, 0), {"middle": [0, CENTER_Y, 0]})
    loc("locator_top", "body", (0, 30, 0), {"top": [0, 30, 0]})
    loc("locator_head", "head", (0, 28, -2), {"head": [0, 28, -2]})
    loc("locator_item_hat", "head", (0, 30, -2), {"item_hat": [0, 30, -2]})
    loc("locator_face", "head", (0, EYE_Y, FACE_Z), {"face": [0, EYE_Y, FACE_Z]})
    loc("locator_item_face", "head", (0, EYE_Y + 1, FACE_Z - 1), {"item_face": [0, EYE_Y + 1, FACE_Z - 1]})
    loc("locator_mouth", "head", (0, MOUTH_Y, FACE_Z - 0.5),
        {"mouth": [0, MOUTH_Y, FACE_Z - 0.5], "special": [0, MOUTH_Y, FACE_Z - 0.5]})
    loc("locator_target", "head", (0, CENTER_Y, FACE_Z - 2), {"target": [0, CENTER_Y, FACE_Z - 2]})
    loc("locator_eye_left", "eye_left", (4.5, EYE_Y + 1, FACE_Z - 1), {"eye2": [4.5, EYE_Y + 1, FACE_Z - 1]})
    loc("locator_eye_right", "eye_right", (-4.5, EYE_Y + 1, FACE_Z - 1), {"eye1": [-4.5, EYE_Y + 1, FACE_Z - 1]})
    loc("locator_hand_primary", "arm_right", (-18, 16.5, -4), {"hand_primary": [-18, 16.5, -4], "physical": [-18, 16.5, -4]})
    loc("locator_hand_secondary", "arm_left", (18, 16.5, -4), {"hand_secondary": [18, 16.5, -4]})
    loc("locator_item", "arm_right", (-18, 16.5, -6), {"item": [-18, 16.5, -6]})
    loc("locator_foot_primary", "foot_right", (-7.5, 1, -6), {"foot_primary": [-7.5, 1, -6]})
    loc("locator_foot_secondary", "foot_left", (7.5, 1, -6), {"foot_secondary": [7.5, 1, -6]})
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": "geometry.kirby",
                "texture_width": TEX_W,
                "texture_height": TEX_H,
                "visible_bounds_width": 4,
                "visible_bounds_height": 4,
                "visible_bounds_offset": [0, 1, 0],
            },
            "bones": bones,
        }],
    }


# --------------------------------------------------------------------------------------
# Texture
# --------------------------------------------------------------------------------------
PALETTES = {
    "kirby": {
        "body": (255, 158, 190, 255), "cheek": (255, 99, 146, 255), "foot": (222, 40, 70, 255),
        "foot_dark": (170, 24, 50, 255),
    },
    "kirby_shiny": {
        "body": (255, 226, 130, 255), "cheek": (255, 168, 80, 255), "foot": (64, 132, 232, 255),
        "foot_dark": (40, 96, 190, 255),
    },
}
NAVY = BLACK = (8, 8, 12, 255)       # eye border / black part of the eye gradient
EYE_BLUE = (40, 100, 232, 255)
EYE_LIGHT = (122, 196, 255, 255)
WHITE = (255, 255, 255, 255)

# 5 x 10 eye with a white -> black -> blue vertical gradient inside a black border ('.' = body colour).
EYE_GREY = (120, 120, 128, 255)
EYE_DARK_BLUE = (18, 40, 150, 255)
EYE_ART = [
    ".NNN.",
    "NWWWN",
    "NWWWN",
    "NGGGN",
    "NKKKN",
    "NKKKN",
    "NDDDN",
    "NBBBN",
    "NBBBN",
    ".NNN.",
]
EYE_KEY = {"N": NAVY, "W": WHITE, "G": EYE_GREY, "K": BLACK, "D": EYE_DARK_BLUE, "B": EYE_BLUE}

# 6 x 3 mouth (reference picture): dark red mouth with a bright red tongue.
MOUTH = (170, 55, 55, 255)            # dark red (also used for the cube's sides)
MOUTH_DARK = MOUTH
MOUTH_TONGUE = (225, 35, 40, 255)
MOUTH_ART = [
    ".DDDD.",
    "DDDDDD",
    ".DTTD.",
]
MOUTH_KEY = {"D": MOUTH_DARK, "T": MOUTH_TONGUE}


def fill(img, x, y, w, h, color):
    for yy in range(int(y), int(math.ceil(y + h))):
        for xx in range(int(x), int(math.ceil(x + w))):
            img.putpixel((xx, yy), color)


def body_region(body, seed):
    """
    96 x 48 px of soft "fluffy" body texture in Kirby's pink, generated from three octaves of seeded value
    noise (coarse patches, medium blotches, fine speckle) quantised to a few shades.
    """
    import random

    rng = random.Random(seed)
    w, h = 96, 48
    layers = []
    for cell, weight in ((12, 0.50), (6, 0.32), (3, 0.18)):
        gw, gh = w // cell + 2, h // cell + 2
        grid = [[rng.random() for _ in range(gw)] for _ in range(gh)]
        layers.append((cell, weight, grid))
    out = Image.new("RGBA", (w, h), body)
    px = out.load()
    for y in range(h):
        for x in range(w):
            v = sum(wt * grid[y // cell][x // cell] for cell, wt, grid in layers)   # 0 .. 1
            level = min(4, int(v * 5))                                                # 5 shades
            f = (0.86, 0.93, 1.0, 1.05, 1.1)[level]
            px[x, y] = tuple(max(0, min(255, int(round(ch * f)))) for ch in body[:3]) + (255,)
    return out


def paint(name, pal):
    img = Image.new("RGBA", (TEX_W, TEX_H), (0, 0, 0, 0))
    body = pal["body"]

    # body boxes: procedural fluff; the Z box's front face is (24, 24) .. (44, 44)
    for seed, uv in enumerate((UV_BODY, UV_BODY_X, UV_BODY_Y), start=1):
        img.paste(body_region(body, seed), uv)
    fx, fy = UV_BODY[0] + 24, UV_BODY[1] + 24            # Z box front face: 20 x 20 at (24, 24)
    for cx in (2.5, 17.5):                               # blush cheeks, outside and a little below the eyes
        for yy in range(20):
            for xx in range(20):
                ex, ey = (xx + 0.5 - cx) / 2.4, (yy + 0.5 - 13.0) / 1.7
                if ex * ex + ey * ey <= 1.0:
                    img.putpixel((fx + xx, fy + yy), pal["cheek"])

    fill(img, UV_PLAIN[0], UV_PLAIN[1], 40, 20, body)    # arms

    # eyes: cube 5 x 10 x 1 -> north face region at (u+1, v+1)
    ex0, ey0 = UV_EYE
    fill(img, ex0, ey0, 12, 11, NAVY)
    for row, line in enumerate(EYE_ART):
        for col, ch in enumerate(line):
            color = body if ch == "." else EYE_KEY[ch]
            img.putpixel((ex0 + 1 + col, ey0 + 1 + row), color)

    # mouth: cube 6 x 3 x 1 -> north face region at (u+1, v+1)
    mx0, my0 = UV_MOUTH
    fill(img, mx0, my0, 14, 4, MOUTH)
    for row, line in enumerate(MOUTH_ART):
        for col, ch in enumerate(line):
            color = body if ch == "." else MOUTH_KEY[ch]
            img.putpixel((mx0 + 1 + col, my0 + 1 + row), color)

    # feet
    for (ux, uy), (w, h) in (((UV_FOOT_A), (44, 17)), ((UV_FOOT_B), (44, 20))):
        fill(img, ux, uy, w, h, pal["foot"])

    TEX_DIR.mkdir(parents=True, exist_ok=True)
    img.save(TEX_DIR / f"{name}.png")


# --------------------------------------------------------------------------------------
# Animations (Bedrock 1.8.0 animation JSON, Molang-driven so loops stay seamless)
# --------------------------------------------------------------------------------------
# Conventions in this file (positions are in model units, rotations in degrees):
#   rotation x > 0 : front (-z) of the bone tips down   rotation z > 0 : +x side of the bone tips down
#   rotation y > 0 : the bone's +x side swings toward -z (forward)
#   position y > 0 : up, position z < 0 : forward
# Rest pose of the arms is "slightly raised outwards": arm_left rz = -20, arm_right rz = +20.
ARM_L_REST, ARM_R_REST = -20, 20


def sin(expr):
    return f"math.sin({expr})"


def kf(frames):
    """keyframes: {time: value} with python lists, time -> str."""
    return {str(float(t)): v for t, v in frames.items()}


def build_animations():
    A = {}

    # ---- ground idle: breathing, tiny sway, arms drift ----
    s = sin("q.anim_time*90")
    A["animation.kirby.ground_idle"] = {
        "loop": True, "animation_length": 4,
        "bones": {
            "body": {
                "position": [0, f"0.25*{s}", 0],
                "scale": [f"1-0.012*{s}", f"1+0.025*{s}", f"1-0.012*{s}"],
            },
            "head": {"rotation": [0, f"2*{sin('q.anim_time*90')}", f"1.5*{sin('q.anim_time*90+90')}"]},
            "arm_left": {"rotation": [0, 0, f"{ARM_L_REST}+3*{sin('q.anim_time*90+40')}"]},
            "arm_right": {"rotation": [0, 0, f"{ARM_R_REST}-3*{sin('q.anim_time*90+40')}"]},
        },
    }

    # ---- walking: waddle bounce, feet step, arms swing (0.8 s cycle) ----
    a = "q.anim_time*450"
    A["animation.kirby.ground_walk"] = {
        "loop": True, "animation_length": 0.8,
        "bones": {
            "body": {
                "position": [0, f"1.4*math.abs({sin(a)})", 0],
                "rotation": [3, 0, f"4*{sin(a)}"],
                "scale": [f"1+0.03*math.abs({sin(a)})", f"1-0.04*math.abs({sin(a)})", f"1+0.03*math.abs({sin(a)})"],
            },
            "head": {"rotation": [0, 0, f"-2*{sin(a)}"]},
            "foot_left": {
                "rotation": [f"-24*{sin(a)}", 0, 0],
                "position": [0, f"1.6*math.max(0,{sin(a)})", f"-2.5*{sin(a)}"],
            },
            "foot_right": {
                "rotation": [f"24*{sin(a)}", 0, 0],
                "position": [0, f"1.6*math.max(0,-{sin(a)})", f"2.5*{sin(a)}"],
            },
            "arm_left": {"rotation": [f"-18*{sin(a)}", 0, ARM_L_REST]},
            "arm_right": {"rotation": [f"18*{sin(a)}", 0, ARM_R_REST]},
        },
    }

    # ---- running: faster, bigger bounce, leaning forward, arms thrown back (0.5 s cycle) ----
    a = "q.anim_time*720"
    A["animation.kirby.ground_run"] = {
        "loop": True, "animation_length": 0.5,
        "bones": {
            "body": {
                "position": [0, f"3*math.abs({sin(a)})", f"-1*{sin(a)}"],
                "rotation": [10, 0, f"5*{sin(a)}"],
                "scale": [f"1+0.05*math.abs({sin(a)})", f"1-0.07*math.abs({sin(a)})", f"1+0.05*math.abs({sin(a)})"],
            },
            "foot_left": {
                "rotation": [f"-38*{sin(a)}", 0, 0],
                "position": [0, f"2.6*math.max(0,{sin(a)})", f"-4*{sin(a)}"],
            },
            "foot_right": {
                "rotation": [f"38*{sin(a)}", 0, 0],
                "position": [0, f"2.6*math.max(0,-{sin(a)})", f"4*{sin(a)}"],
            },
            "arm_left": {"rotation": [f"-30*{sin(a)}", f"-40", ARM_L_REST]},
            "arm_right": {"rotation": [f"30*{sin(a)}", f"40", ARM_R_REST]},
        },
    }

    # ---- flying: Kirby inflates like a balloon (hover = air_idle, moving = air_fly) ----
    # The body (and its arm/eye children) is blown up 1.4x; arms get 0.7x back so they stay small like in the games,
    # the whole thing is lifted so the shrunken feet dangle underneath, the mouth is pursed (the drawn open mouth
    # would look odd on a puffed face).
    def inflated(period, lean, flap, bob):
        a = f"q.anim_time*{360 / period:g}"
        b = f"q.anim_time*{720 / period:g}"
        return {
            "loop": True, "animation_length": period,
            "bones": {
                "body": {
                    "position": [0, f"5+{bob}*{sin(a)}", 0],
                    "rotation": [lean, 0, f"{lean / 2:g}*{sin(a)}"],
                    "scale": [f"1.4+0.03*{sin(b)}", f"1.4-0.03*{sin(b)}", f"1.4+0.03*{sin(b)}"],
                },
                "head": {"rotation": [0, f"3*{sin(a)}", 0]},
                "mouth": {"scale": [0.55, 0.35, 1]},
                "arm_left": {"scale": [0.7, 0.7, 0.7], "rotation": [0, 0, f"-48+{flap}*{sin(b)}"]},
                "arm_right": {"scale": [0.7, 0.7, 0.7], "rotation": [0, 0, f"48-{flap}*{sin(b)}"]},
                "foot_left": {
                    "scale": [0.8, 0.8, 0.8], "position": [0.5, 1, 0],
                    "rotation": [f"12+8*{sin(b)}", 0, 0],
                },
                "foot_right": {
                    "scale": [0.8, 0.8, 0.8], "position": [-0.5, 1, 0],
                    "rotation": [f"12-8*{sin(b)}", 0, 0],
                },
            },
        }

    A["animation.kirby.air_idle"] = inflated(3, 0, 10, 0.9)
    A["animation.kirby.air_fly"] = inflated(0.6, 7, 22, 0.6)

    # ---- battle idle: alert crouch, quick bounce, arms raised, feet planted ----
    s = sin("q.anim_time*225")
    A["animation.kirby.battle_idle"] = {
        "loop": True, "animation_length": 1.6,
        "bones": {
            "body": {
                "position": [0, f"-0.8+0.5*{s}", 0],
                "rotation": [5, 0, 0],
                "scale": [f"1.04-0.012*{s}", f"0.94+0.02*{s}", f"1.04-0.012*{s}"],
            },
            "head": {"rotation": [0, f"3*{sin('q.anim_time*225+90')}", 0]},
            "arm_left": {"rotation": [-18, 8, f"-38+4*{s}"]},
            "arm_right": {"rotation": [-18, -8, f"38-4*{s}"]},
            "foot_left": {"position": [1.2, 0, 0], "rotation": [0, -6, 0]},
            "foot_right": {"position": [-1.2, 0, 0], "rotation": [0, 6, 0]},
        },
    }

    # ---- blink quirk: eyes squash shut ----
    eye = {"scale": kf({0.0: [1, 1, 1], 0.07: [1, 0.08, 1], 0.14: [1, 0.08, 1], 0.24: [1, 1, 1]})}
    A["animation.kirby.blink"] = {"animation_length": 0.24, "bones": {"eye_left": eye, "eye_right": eye}}

    # ---- recoil (damaged): flinch back, squash, eyes squeezed, arms flung ----
    squint = {"scale": kf({0.0: [1, 1, 1], 0.08: [1, 0.35, 1], 0.4: [1, 0.35, 1], 0.6: [1, 1, 1]})}
    recoil = {
        "animation_length": 0.6,
        "bones": {
            "body": {
                "rotation": kf({0.0: [0, 0, 0], 0.08: [-16, 0, 4], 0.28: [5, 0, -2], 0.45: [-2, 0, 0], 0.6: [0, 0, 0]}),
                "position": kf({0.0: [0, 0, 0], 0.08: [0, 0, 3.5], 0.3: [0, 0, -0.5], 0.6: [0, 0, 0]}),
                "scale": kf({0.0: [1, 1, 1], 0.08: [1.1, 0.88, 1.1], 0.3: [0.97, 1.04, 0.97], 0.6: [1, 1, 1]}),
            },
            "arm_left": {"rotation": kf({0.0: [0, 0, 0], 0.08: [0, 0, -40], 0.6: [0, 0, 0]})},
            "arm_right": {"rotation": kf({0.0: [0, 0, 0], 0.08: [0, 0, 40], 0.6: [0, 0, 0]})},
            "eye_left": squint, "eye_right": squint,
            "mouth": {"scale": kf({0.0: [1, 1, 1], 0.08: [1.08, 1.3, 1], 0.45: [1.08, 1.3, 1], 0.6: [1, 1, 1]})},
        },
    }
    A["animation.kirby.recoil"] = recoil
    A["animation.kirby.battle_recoil"] = json.loads(json.dumps(recoil))

    # ---- physical attack: wind up, lunge forward punching, settle ----
    A["animation.kirby.physical"] = {
        "animation_length": 0.9,
        "bones": {
            "body": {
                "position": kf({0.0: [0, 0, 0], 0.22: [0, -1, 2.5], 0.38: [0, 1, -6], 0.55: [0, 0, -6], 0.9: [0, 0, 0]}),
                "rotation": kf({0.0: [0, 0, 0], 0.22: [-10, 0, 0], 0.38: [16, 0, 0], 0.55: [12, 0, 0], 0.9: [0, 0, 0]}),
                "scale": kf({0.0: [1, 1, 1], 0.22: [1.1, 0.88, 1.1], 0.38: [0.95, 1.05, 0.95], 0.9: [1, 1, 1]}),
            },
            "arm_left": {"rotation": kf({0.0: [0, 0, 0], 0.22: [0, -30, 0], 0.38: [-60, 70, 20], 0.55: [-40, 60, 20], 0.9: [0, 0, 0]})},
            "arm_right": {"rotation": kf({0.0: [0, 0, 0], 0.22: [0, 30, 0], 0.38: [-60, -70, -20], 0.55: [-40, -60, -20], 0.9: [0, 0, 0]})},
            "foot_left": {"position": kf({0.0: [0, 0, 0], 0.38: [0, 0, -3], 0.9: [0, 0, 0]})},
            "foot_right": {"position": kf({0.0: [0, 0, 0], 0.38: [0, 0, -3], 0.9: [0, 0, 0]})},
            "mouth": {"scale": kf({0.0: [1, 1, 1], 0.38: [1.08, 1.35, 1], 0.7: [1.08, 1.35, 1], 0.9: [1, 1, 1]})},
        },
    }

    # ---- special attack: inhale and puff up, then blow out ----
    A["animation.kirby.special"] = {
        "animation_length": 1.2,
        "bones": {
            "body": {
                "scale": kf({0.0: [1, 1, 1], 0.45: [1.22, 1.2, 1.22], 0.8: [1.22, 1.2, 1.22], 0.95: [0.93, 0.96, 0.93], 1.2: [1, 1, 1]}),
                "position": kf({0.0: [0, 0, 0], 0.45: [0, 2, 0], 0.8: [0, 2, 0], 0.95: [0, 0, -3], 1.2: [0, 0, 0]}),
                "rotation": kf({0.0: [0, 0, 0], 0.45: [-6, 0, 0], 0.95: [8, 0, 0], 1.2: [0, 0, 0]}),
            },
            "arm_left": {"rotation": kf({0.0: [0, 0, 0], 0.45: [0, 0, -45], 0.8: [0, 0, -45], 1.2: [0, 0, 0]})},
            "arm_right": {"rotation": kf({0.0: [0, 0, 0], 0.45: [0, 0, 45], 0.8: [0, 0, 45], 1.2: [0, 0, 0]})},
            "mouth": {"scale": kf({0.0: [1, 1, 1], 0.3: [1.12, 1.45, 1], 0.95: [1.12, 1.45, 1], 1.2: [1, 1, 1]})},
        },
    }

    # ---- status move: happy wiggle hop ----
    A["animation.kirby.status"] = {
        "animation_length": 0.9,
        "bones": {
            "body": {
                "position": kf({0.0: [0, 0, 0], 0.15: [0, 2.8, 0], 0.3: [0, 0, 0], 0.45: [0, 2.8, 0], 0.6: [0, 0, 0], 0.9: [0, 0, 0]}),
                "rotation": kf({0.0: [0, 0, 0], 0.15: [0, 0, 9], 0.3: [0, 0, 0], 0.45: [0, 0, -9], 0.6: [0, 0, 0]}),
                "scale": kf({0.0: [1, 1, 1], 0.3: [1.05, 0.93, 1.05], 0.6: [1.05, 0.93, 1.05], 0.9: [1, 1, 1]}),
            },
            "arm_left": {"rotation": kf({0.0: [0, 0, 0], 0.15: [0, 0, -35], 0.3: [0, 0, 0], 0.45: [0, 0, -35], 0.6: [0, 0, 0]})},
            "arm_right": {"rotation": kf({0.0: [0, 0, 0], 0.15: [0, 0, 35], 0.3: [0, 0, 0], 0.45: [0, 0, 35], 0.6: [0, 0, 0]})},
        },
    }

    # ---- faint: wobble, then flop into a flat puddle with closed eyes; holds the final pose ----
    A["animation.kirby.faint"] = {
        "animation_length": 1.6,
        "bones": {
            "body": {
                "rotation": kf({0.0: [0, 0, 0], 0.15: [-10, 0, 8], 0.35: [4, 0, -14], 0.6: [0, 0, 22], 0.95: [0, 0, 0], 1.6: [0, 0, 0]}),
                "position": kf({0.0: [0, 0, 0], 0.6: [0, -1.5, 0], 0.95: [0, -5, 0], 1.1: [0, -4.2, 0], 1.25: [0, -5, 0], 1.6: [0, -5, 0]}),
                "scale": kf({0.0: [1, 1, 1], 0.6: [1.04, 0.96, 1.04], 0.95: [1.28, 0.55, 1.28], 1.1: [1.2, 0.64, 1.2], 1.25: [1.26, 0.57, 1.26], 1.6: [1.26, 0.57, 1.26]}),
            },
            "arm_left": {"rotation": kf({0.0: [0, 0, 0], 0.35: [0, 0, -50], 0.95: [0, 0, 55], 1.6: [0, 0, 55]})},
            "arm_right": {"rotation": kf({0.0: [0, 0, 0], 0.35: [0, 0, 50], 0.95: [0, 0, -55], 1.6: [0, 0, -55]})},
            "eye_left": {"scale": kf({0.0: [1, 1, 1], 0.35: [1, 0.3, 1], 0.6: [1, 0.08, 1], 1.6: [1, 0.08, 1]})},
            "eye_right": {"scale": kf({0.0: [1, 1, 1], 0.35: [1, 0.3, 1], 0.6: [1, 0.08, 1], 1.6: [1, 0.08, 1]})},
            "foot_left": {
                "position": kf({0.0: [0, 0, 0], 0.95: [3, 0, 0], 1.6: [3, 0, 0]}),
                "rotation": kf({0.0: [0, 0, 0], 0.95: [0, -12, 0], 1.6: [0, -12, 0]}),
            },
            "foot_right": {
                "position": kf({0.0: [0, 0, 0], 0.95: [-3, 0, 0], 1.6: [-3, 0, 0]}),
                "rotation": kf({0.0: [0, 0, 0], 0.95: [0, 12, 0], 1.6: [0, 12, 0]}),
            },
            "mouth": {"scale": kf({0.0: [1, 1, 1], 0.95: [1, 1.25, 1], 1.6: [1, 1.25, 1]})},
        },
    }

    # ---- sleep: squashed, eyes shut, slow breathing, arms resting ----
    s = sin("q.anim_time*90")
    A["animation.kirby.sleep"] = {
        "loop": True, "animation_length": 4,
        "bones": {
            "body": {
                "position": [0, f"-2.1+0.15*{s}", 0],
                "scale": [f"1.12-0.01*{s}", f"0.78+0.02*{s}", f"1.12-0.01*{s}"],
                "rotation": [0, 0, 3],
            },
            "head": {"rotation": [6, 0, 4]},
            "eye_left": {"scale": [1, 0.08, 1]},
            "eye_right": {"scale": [1, 0.08, 1]},
            "mouth": {"scale": [0.8, 0.8, 1]},
            "arm_left": {"rotation": [0, 0, 28]},
            "arm_right": {"rotation": [0, 0, -28]},
            "foot_left": {"position": [1, 0, 0]},
            "foot_right": {"position": [-1, 0, 0]},
        },
    }

    # ---- cry: open mouth, little bounce ----
    cry = {
        "animation_length": 1.0,
        "bones": {
            "body": {
                "position": kf({0.0: [0, 0, 0], 0.15: [0, 2.4, 0], 0.35: [0, 0, 0], 0.55: [0, 1.6, 0], 0.75: [0, 0, 0], 1.0: [0, 0, 0]}),
                "scale": kf({0.0: [1, 1, 1], 0.15: [0.97, 1.05, 0.97], 0.35: [1.05, 0.95, 1.05], 1.0: [1, 1, 1]}),
            },
            "head": {"rotation": kf({0.0: [0, 0, 0], 0.15: [-9, 0, 0], 0.7: [-9, 0, 0], 1.0: [0, 0, 0]})},
            "mouth": {"scale": kf({0.0: [1, 1, 1], 0.12: [1.1, 1.35, 1], 0.8: [1.1, 1.35, 1], 1.0: [1, 1, 1]})},
            "arm_left": {"rotation": kf({0.0: [0, 0, 0], 0.15: [0, 0, -22], 0.7: [0, 0, -22], 1.0: [0, 0, 0]})},
            "arm_right": {"rotation": kf({0.0: [0, 0, 0], 0.15: [0, 0, 22], 0.7: [0, 0, 22], 1.0: [0, 0, 0]})},
        },
    }
    A["animation.kirby.cry"] = cry
    A["animation.kirby.battle_cry"] = json.loads(json.dumps(cry))
    return {"format_version": "1.8.0", "animations": A}


# --------------------------------------------------------------------------------------
# Poser + resolver
# --------------------------------------------------------------------------------------
def build_poser():
    look = "q.look('head', 0.6, 0.6, 20, -15, 30, -30)"
    quirk = ["q.bedrock_quirk('kirby', 'blink')"]
    return {
        "portraitScale": 1.3,
        "portraitTranslation": [0, -0.38, 0],
        "profileScale": 0.83,
        "profileTranslation": [0, 0.36, 0],
        "rootBone": "kirby",
        "animations": {
            "cry": "q.bedrock_stateful('kirby', 'cry')",
            "recoil": "q.bedrock_stateful('kirby', 'recoil')",
            "faint": "q.bedrock_primary('kirby', 'faint', q.curve('one'))",
            "physical": "q.bedrock_primary('kirby', 'physical', q.curve('symmetrical_wide'))",
            "special": "q.bedrock_primary('kirby', 'special', q.curve('symmetrical_wide'))",
            "status": "q.bedrock_primary('kirby', 'status', q.curve('symmetrical_wide'))",
        },
        "poses": {
            "battle-standing": {
                "poseTypes": ["STAND"],
                "isBattle": True,
                "animations": [look, "q.bedrock('kirby', 'battle_idle')"],
                "quirks": quirk,
                "namedAnimations": {
                    "cry": "q.bedrock_stateful('kirby', 'battle_cry')",
                    "recoil": "q.bedrock_stateful('kirby', 'battle_recoil')",
                },
            },
            "standing": {
                "poseTypes": ["STAND", "NONE", "PORTRAIT", "PROFILE", "FLOAT"],
                "isBattle": False,
                "animations": [look, "q.bedrock('kirby', 'ground_idle')"],
                "quirks": quirk,
            },
            "walking": {
                "poseTypes": ["WALK", "SWIM"],
                "condition": "!q.is_sprinting",
                "animations": [look, "q.bedrock('kirby', 'ground_walk')"],
                "quirks": quirk,
            },
            "run": {
                "poseTypes": ["WALK", "SWIM"],
                "condition": "q.is_sprinting",
                "animations": [look, "q.bedrock('kirby', 'ground_run')"],
                "quirks": quirk,
            },
            "battle-hover": {
                "poseTypes": ["HOVER", "FLY"],
                "isBattle": True,
                "animations": [look, "q.bedrock('kirby', 'air_idle')"],
                "quirks": quirk,
                "transformTicks": 10,
                "transformToTicks": 10,
                "namedAnimations": {
                    "cry": "q.bedrock_stateful('kirby', 'battle_cry')",
                    "recoil": "q.bedrock_stateful('kirby', 'battle_recoil')",
                },
            },
            "hover": {
                "poseTypes": ["HOVER"],
                "isBattle": False,
                "animations": [look, "q.bedrock('kirby', 'air_idle')"],
                "quirks": quirk,
                "transformTicks": 10,
                "transformToTicks": 10,
            },
            "fly": {
                "poseTypes": ["FLY"],
                "isBattle": False,
                "animations": [look, "q.bedrock('kirby', 'air_fly')"],
                "quirks": quirk,
                "transformTicks": 10,
                "transformToTicks": 10,
            },
            "sleep": {
                "poseTypes": ["SLEEP"],
                "animations": ["q.bedrock('kirby', 'sleep')"],
                "namedAnimations": {"cry": "q.bedrock_stateful('dummy', 'cry')"},
            },
        },
    }


def build_resolver():
    return {
        "species": "cobblemon_kirby:kirby",
        "order": 0,
        "variations": [
            {
                "aspects": [],
                "poser": "cobblemon_kirby:kirby",
                "model": "cobblemon_kirby:kirby.geo",
                "texture": "cobblemon_kirby:textures/pokemon/kirby/kirby.png",
                "layers": [],
            },
            {
                "aspects": ["shiny"],
                "texture": "cobblemon_kirby:textures/pokemon/kirby/kirby_shiny.png",
            },
        ],
    }


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def main():
    write(MODEL_DIR / "kirby.geo.json", build_geometry())
    write(ANIM_DIR / "kirby.animation.json", build_animations())
    write(POSER_DIR / "kirby.json", build_poser())
    write(RESOLVER_DIR / "0_kirby_base.json", build_resolver())
    paint("kirby", PALETTES["kirby"])
    paint("kirby_shiny", PALETTES["kirby_shiny"])
    geo = build_geometry()["minecraft:geometry"][0]["bones"]
    n_cubes = sum(len(b.get("cubes", [])) for b in geo)
    print(f"model: {len(geo)} bones, {n_cubes} cubes ({n_cubes * 6} quads)")


if __name__ == "__main__":
    main()
