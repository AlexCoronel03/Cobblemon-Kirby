"""
Tiny software renderer used to sanity-check kirby.geo.json + kirby.png without Blockbench / Minecraft.

It applies Bedrock box-UV mapping and cube rotations exactly as described in gen_assets.py, optionally
posing bones by simple per-bone (rotation, position, scale) dictionaries, and writes PNG previews.

usage: python tools/preview.py [out_dir]
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "src/main/resources/assets/cobblemon_kirby"
GEO = json.loads((ASSETS / "bedrock/pokemon/models/kirby/kirby.geo.json").read_text())["minecraft:geometry"][0]
TEX = np.array(Image.open(ASSETS / "textures/pokemon/kirby/kirby.png").convert("RGBA"))
BONES = {b["name"]: b for b in GEO["bones"]}


def rot_xyz(v, rx, ry, rz):
    """Rotate a vector by animation-style Euler angles using Cobblemon's mapping (Rx(-rx) Ry(ry) Rz(-rz))."""
    x, y, z = v
    a, b, c = math.radians(-rx), math.radians(ry), math.radians(-rz)
    # Rz then Ry then Rx (applied to the vector in that order)
    x, y = x * math.cos(c) - y * math.sin(c), x * math.sin(c) + y * math.cos(c)
    x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    return (x, y, z)


def bone_chain(name):
    chain = []
    while name:
        chain.append(name)
        name = BONES[name].get("parent")
    return list(reversed(chain))


def faces(cube):
    ox, oy, oz = cube["origin"]
    w, h, d = cube["size"]
    u, v = cube["uv"]
    return [
        # P0, U, V, uvregion(x, y, w, h)
        ((ox + w, oy + h, oz), (-w, 0, 0), (0, -h, 0), (u + d, v + d, w, h)),            # north / front
        ((ox, oy + h, oz + d), (w, 0, 0), (0, -h, 0), (u + 2 * d + w, v + d, w, h)),      # south
        ((ox + w, oy + h, oz + d), (0, 0, -d), (0, -h, 0), (u, v + d, d, h)),             # east
        ((ox, oy + h, oz), (0, 0, d), (0, -h, 0), (u + d + w, v + d, d, h)),              # west
        ((ox, oy + h, oz), (w, 0, 0), (0, 0, d), (u + d, v, w, d)),                       # up
        ((ox, oy, oz + d), (w, 0, 0), (0, 0, -d), (u + d + w, v, w, d)),                  # down
    ]


def render(view_yaw=0.0, pose=None, size=(640, 640), scale=15.0, shade=True):
    pose = pose or {}
    W, H = size
    img = np.zeros((H, W, 4), dtype=np.uint8)
    img[..., :3] = 235
    img[..., 3] = 255
    zbuf = np.full((H, W), 1e9)
    cx, cy = W / 2, H * 0.88
    cy_yaw = math.radians(view_yaw)

    def transform(p, bone_name, cube_rot=None, cube_pivot=None):
        x, y, z = p
        if cube_rot and cube_rot != [0, 0, 0]:
            px, py, pz = cube_pivot
            # cube rotations in the geo file are plain math Ry(theta) in model coordinates:
            t = math.radians(cube_rot[1])
            ox_, oz_ = (x - px), (z - pz)
            lx = ox_ * math.cos(t) + oz_ * math.sin(t)
            lz = -ox_ * math.sin(t) + oz_ * math.cos(t)
            ly = y - py
            x, y, z = px + lx, py + ly, pz + lz
        # pose chain (leaf -> root)
        for name in reversed(bone_chain(bone_name)):
            tr = pose.get(name)
            if not tr:
                continue
            piv = BONES[name]["pivot"]
            lx, ly, lz = x - piv[0], y - piv[1], z - piv[2]
            sx, sy, sz = tr.get("scale", (1, 1, 1))
            lx, ly, lz = lx * sx, ly * sy, lz * sz
            lx, ly, lz = rot_xyz((lx, ly, lz), *tr.get("rotation", (0, 0, 0)))
            px_, py_, pz_ = tr.get("position", (0, 0, 0))
            x, y, z = piv[0] + lx + px_, piv[1] + ly + py_, piv[2] + lz + pz_
        # view: yaw about Y then viewer-right = -x
        xr = x * math.cos(cy_yaw) + z * math.sin(cy_yaw)
        zr = -x * math.sin(cy_yaw) + z * math.cos(cy_yaw)
        return (-xr, y, zr)

    for bone in GEO["bones"]:
        for cube in bone.get("cubes", []):
            for p0, uvec, vvec, region in faces(cube):
                pts = []
                for (a, b) in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    p = tuple(p0[i] + a * uvec[i] + b * vvec[i] for i in range(3))
                    pts.append(transform(p, bone["name"], cube.get("rotation"), cube.get("pivot", bone["pivot"])))
                P0, PU, PV = pts[0], pts[1], pts[3]
                s0 = np.array([cx + P0[0] * scale, cy - P0[1] * scale])
                su = np.array([cx + PU[0] * scale, cy - PU[1] * scale]) - s0
                sv = np.array([cx + PV[0] * scale, cy - PV[1] * scale]) - s0
                det = su[0] * sv[1] - su[1] * sv[0]
                if abs(det) < 1e-6:
                    continue
                # back-face cull via normal facing the camera (camera looks along +z in view space)
                n = np.cross(np.array(PU) - np.array(P0), np.array(PV) - np.array(P0))
                if n[2] >= 0:
                    continue
                xs = [s0[0], s0[0] + su[0], s0[0] + sv[0], s0[0] + su[0] + sv[0]]
                ys = [s0[1], s0[1] + su[1], s0[1] + sv[1], s0[1] + su[1] + sv[1]]
                x_lo, x_hi = max(int(min(xs)), 0), min(int(max(xs)) + 1, W)
                y_lo, y_hi = max(int(min(ys)), 0), min(int(max(ys)) + 1, H)
                if x_lo >= x_hi or y_lo >= y_hi:
                    continue
                gx, gy = np.meshgrid(np.arange(x_lo, x_hi) + 0.5, np.arange(y_lo, y_hi) + 0.5)
                dx, dy = gx - s0[0], gy - s0[1]
                a = (dx * sv[1] - dy * sv[0]) / det
                b = (su[0] * dy - su[1] * dx) / det
                inside = (a >= 0) & (a < 1) & (b >= 0) & (b < 1)
                if not inside.any():
                    continue
                depth = P0[2] + a * (PU[2] - P0[2]) + b * (PV[2] - P0[2])
                rx, ry, rw, rh = region
                tx = np.clip((rx + a * rw).astype(int), 0, TEX.shape[1] - 1)
                ty = np.clip((ry + b * rh).astype(int), 0, TEX.shape[0] - 1)
                col = TEX[ty, tx].astype(float)
                if shade:
                    nn = n / (np.linalg.norm(n) + 1e-9)
                    light = 0.62 + 0.38 * max(0.0, float(-nn[2] * 0.6 + nn[1] * -0.5 + nn[0] * 0.2) + 0.45)
                    col[..., :3] *= min(1.0, light)
                yy, xx = np.nonzero(inside)
                ay, ax = yy + y_lo, xx + x_lo
                closer = depth[yy, xx] < zbuf[ay, ax]
                opaque = col[yy, xx, 3] > 0
                ok = closer & opaque
                zbuf[ay[ok], ax[ok]] = depth[yy, xx][ok]
                img[ay[ok], ax[ok]] = col[yy, xx][ok].astype(np.uint8)
    return Image.fromarray(img)


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "docs")
    out.mkdir(parents=True, exist_ok=True)
    views = {"front": 0, "three_quarter": -35, "side": -90, "back": 180}
    tiles = [render(yaw) for yaw in views.values()]
    sheet = Image.new("RGBA", (640 * 2, 640 * 2))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % 2) * 640, (i // 2) * 640))
    sheet.save(out / "kirby_preview.png")
    print("wrote", out / "kirby_preview.png")


if __name__ == "__main__":
    main()
