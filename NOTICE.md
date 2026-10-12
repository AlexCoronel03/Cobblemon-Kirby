# Third-party material

This repository contains **no third-party art or model data**. The Kirby model (geometry, bones, locators), the
textures (generated procedurally by `tools/gen_assets.py` from seeded noise and hand-written pixel art) and the
animations were all created for this project.

## Other

* Cobblemon itself: MPL-2.0, not redistributed here. The addon is built against it and loads inside it.
* *Kirby* is a character of Nintendo / HAL Laboratory; this is an unofficial fan project and is not affiliated with
  or endorsed by them, Nintendo, The Pokémon Company or the Cobblemon team.
* Scream Tail's base stats (used for Kirby's stats) are game data read from Cobblemon's own species file at build
  time of the data (`tools/gen_species.py`).

## History note

Early commits (up to `e44c227`) contained a texture derived from Cobblemon's Jigglypuff model, which is published
under a Creative Commons Attribution-NonCommercial licence. It was replaced by original art and removed from the
tree; if you need a history free of it, use a clone taken after the commit that removes `tools/source/`.
