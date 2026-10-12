"""
Generates src/main/resources/data/cobblemon_kirby/species/kirby.json.

Base stats, EV yield and learnset are copied programmatically from Cobblemon's own
Scream Tail species file (data/cobblemon/species/generation9/screamtail.json) so they
are exact rather than retyped.

usage: python tools/gen_species.py <path to Cobblemon-fabric-1.8.1+1.21.1.jar>
"""
import json
import sys
import zipfile
from pathlib import Path

jar = sys.argv[1]
with zipfile.ZipFile(jar) as z:
    st = json.loads(z.read("data/cobblemon/species/generation9/screamtail.json"))

kirby = {
    "implemented": True,
    "nationalPokedexNumber": 1984,
    "name": "Kirby",
    "primaryType": "fairy",
    "maleRatio": -1,
    "height": 6,
    "weight": 45,
    "pokedex": ["cobblemon_kirby.species.kirby.desc"],
    "labels": ["custom", "kirby"],
    "aspects": [],
    "abilities": ["copyability", "h:copyability"],
    "eggGroups": ["undiscovered"],
    "baseStats": st["baseStats"],
    "evYield": st["evYield"],
    "baseExperienceYield": st["baseExperienceYield"],
    "experienceGroup": st["experienceGroup"],
    "catchRate": 45,
    "eggCycles": st["eggCycles"],
    "baseFriendship": 70,
    "baseScale": 0.7,
    "hitbox": {"width": 1.6, "height": 1.9, "fixed": False},
    "behaviour": {
        "resting": {
            "canSleep": True,
            "light": "0-4",
            "times": ["any"],
            "drowsyChance": 0.0014,
            "rouseChance": 0.0042,
        },
        "moving": {"swim": {"avoidsWater": True}, "fly": {"canFly": True}},
        "combat": {"willDefendOwner": True, "willDefendSelf": True},
    },
    "drops": {
        "amount": 2,
        "entries": [
            {"item": "cobblemon:oran_berry", "percentage": 10.0},
            {"item": "cobblemon:pecha_berry", "percentage": 10.0},
        ],
    },
    "moves": st["moves"],
    "features": [],
}

out = Path(__file__).resolve().parent.parent / "src/main/resources/data/cobblemon_kirby/species/kirby.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(kirby, indent=2) + "\n", encoding="utf-8")
print("wrote", out, "baseStats =", kirby["baseStats"])
