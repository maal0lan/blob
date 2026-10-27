"""Liquid-glass lens renderer for the Crystal orb.

Takes a BGR(A) screenshot of whatever is behind the orb and returns a
premultiplied BGRA image of a wobbly glass blob that magnifies the centre,
bends the edges and splits colours (chromatic dispersion) like the iOS lens.

Pure numpy (uses OpenCV for speed if it happens to be installed).
No Qt imports here, so it can be tested on its own.
"""
from __future__ import annotations

import ctypes
import sys

import numpy as np

try:  # optional speed-up; falls back to numpy bilinear sampling
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None

WDA_EXCLUDEFROMCAPTURE = 0x00000011  # Windows 10 2004+


def exclude_from_capture(hwnd: int) -> bool:
    """Hide this window from screen capture so the orb can sample the desktop
    behind it without photographing itself. The window is still visible to the
    user. Returns False if unsupported (old Windows / non-Windows)."""
    if sys.platform != "win32":
        return False
    try:
        from ctypes import wintypes
        fn = ctypes.windll.user32.SetWindowDisplayAffinity
        fn.argtypes = [wintypes.HWND, wintypes.DWORD]
        fn.restype = wintypes.BOOL
        return bool(fn(wintypes.HWND(int(hwnd)), WDA_EXCLUDEFROMCAPTURE))
    except Exception:
        return False


STATE_COLORS = {  # BGR
    "idle": (255, 220, 145),
    "thinking": (255, 135, 190),
    "speaking": (210, 255, 105),
    "error": (120, 100, 255),
}


class LensRenderer:
    def __init__(self, size: int, magnify: float = 0.74, edge_pull: float = 0.56,
                 dispersion: float = 0.075, wobble: float = 1.0):
        self.magnify = magnify          # <1 magnifies the centre (0.74 ≈ 1.35x)
        self.edge_pull = edge_pull      # how hard the rim bends the background
        self.dispersion = dispersion    # rainbow fringing strength
        self.wobble = wobble            # 0 = perfect circle, 1 = gentle blob
        self.configure(size)

    # ------------------------------------------------------------------ setup
    def configure(self, size: int) -> None:
        n = self.n = int(size)
        self.R = n * 0.44
        c = (n - 1) / 2.0
        ys, xs = np.mgrid[0:n, 0:n].astype(np.float32)
        self.xs, self.ys, self.c = xs, ys, c
        self.nx = (xs - c) / self.R
        self.ny = (ys - c) / self.R
        self.rho0 = np.hypot(self.nx, self.ny)
        self.theta = np.arctan2(self.ny, self.nx)
        # unit direction (safe at centre)
        safe = np.maximum(self.rho0, 1e-6)
        self.ux, self.uy = self.nx / safe, self.ny / safe
        # fixed specular highlight (top-left, tilted ellipse)
        ang = np.deg2rad(-38)
        ca, sa = np.cos(ang), np.sin(ang)
        px = (self.nx + 0.40) * ca + (self.ny + 0.48) * sa
        py = -(self.nx + 0.40) * sa + (self.ny + 0.48) * ca
        self.spec = np.exp(-((px / 0.30) ** 2 + (py / 0.085) ** 2)).astype(np.float32)
        # secondary soft glint bottom-right
        qx, qy = (self.nx - 0.42) / 0.22, (self.ny - 0.52) / 0.07
        self.glint = np.exp(-(qx ** 2 + qy ** 2)).astype(np.float32)
        # light direction for rim lighting
        facing = self.ux * -0.62 + self.uy * -0.78
        self.facing = facing.astype(np.float32)
        self._grid_i = np.arange(n, dtype=np.float32)

    # --------------------------------------------------------------- sampling
    def _sample(self, ch: np.ndarray, sx: np.ndarray, sy: np.ndarray) -> np.ndarray:
        n = self.n
        if cv2 is not None:
            return cv2.remap(ch, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        sx = np.clip(sx, 0, n - 1.001)
        sy = np.clip(sy, 0, n - 1.001)
        x0, y0 = sx.astype(np.int32), sy.astype(np.int32)
        fx, fy = sx - x0, sy - y0
        a = ch[y0, x0].astype(np.float32)
        b = ch[y0, x0 + 1]
        cc = ch[y0 + 1, x0]
        d = ch[y0 + 1, x0 + 1]
        return (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + cc * (1 - fx) * fy + d * fx * fy)

    # ----------------------------------------------------------------- render
    def render(self, frame_bgr: np.ndarray, t: float = 0.0, state: str = "idle",
               strength: float = 1.0) -> np.ndarray:
        """frame_bgr: (n, n, >=3) uint8 desktop crop. Returns (n, n, 4) uint8
        premultiplied BGRA."""
        n = self.n
        frame = np.ascontiguousarray(frame_bgr[:n, :n, :3])

        # --- blob outline: radius wobbles slowly with angle and time
        th = self.theta
        w = 0.030 * self.wobble
        edge = (1.0 + w * np.sin(2 * th + 0.9 * t)
                + 0.7 * w * np.sin(3 * th - 1.3 * t + 1.7)
                + 0.4 * w * np.sin(5 * th + 0.6 * t + 0.4)).astype(np.float32)
        rho = self.rho0 / edge
        alpha = np.clip((1.0 - rho) * self.R / 1.3, 0.0, 1.0)

        # --- refraction: source = centre + dir * f(rho) ; f grows near the rim
        rr = np.clip(rho, 0.0, 1.0)
        rp = rr ** 3
        ux, uy = self.nx / edge, self.ny / edge  # vector with length rho
        out = np.empty((n, n, 3), np.float32)
        k = self.dispersion * strength
        for idx, kc in ((0, -k), (1, 0.0), (2, k)):  # B, G, R
            f = self.magnify + self.edge_pull * strength * (1.0 + kc) * rp
            sx = (self.c + ux * f * self.R).astype(np.float32)
            sy = (self.c + uy * f * self.R).astype(np.float32)
            out[..., idx] = self._sample(frame[..., idx], sx, sy)

        # --- glass body: slight lift + saturation so it reads as a lens
        lum = out.mean(axis=2, keepdims=True)
        out = lum + (out - lum) * 1.12 + 6.0

        # --- bevel: darker band just inside the rim, bright rim outside it
        ring = np.clip((rho - 0.84) / 0.16, 0.0, 1.0) ** 2
        bevel = np.exp(-(((rho - 0.90) / 0.05) ** 2)).astype(np.float32)
        out *= (1.0 - 0.22 * bevel)[..., None]

        hi = ring * (0.22 + 0.78 * np.maximum(self.facing, 0) ** 2
                     + 0.38 * np.maximum(-self.facing, 0) ** 2)
        hi_edge = np.clip((rho - 0.965) / 0.035, 0.0, 1.0)  # crisp outer hairline
        light = np.clip(0.55 * hi + 0.45 * hi_edge * (0.35 + 0.65 * np.abs(self.facing)), 0, 1)
        spec = np.clip(self.spec * 0.55 + self.glint * 0.16, 0, 1) * (rho < 1)
        white = np.clip(light + spec, 0, 1)[..., None]
        out = out * (1.0 - white) + 255.0 * white

        # --- state glow on the rim (idle faint, others stronger + pulsing)
        col = np.array(STATE_COLORS.get(state, STATE_COLORS["idle"]), np.float32)
        s = 0.16 if state == "idle" else 0.55 * (0.75 + 0.25 * np.sin(3.2 * t))
        glow = (ring ** 3 * s)[..., None]
        out = out * (1.0 - glow) + col * glow

        out = np.clip(out, 0, 255)
        res = np.empty((n, n, 4), np.uint8)
        res[..., :3] = (out * alpha[..., None]).astype(np.uint8)  # premultiplied
        res[..., 3] = (alpha * 255).astype(np.uint8)
        return res


# =============================================================================
#  Static glass panel (chat window / dialogs). No animation: geometry maps are
#  precomputed once per size, a render is just a few remaps + a blend.
# =============================================================================
def _remap(ch: np.ndarray, sx: np.ndarray, sy: np.ndarray) -> np.ndarray:
    if cv2 is not None:
        return cv2.remap(np.ascontiguousarray(ch), sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    h, w = ch.shape
    sx = np.clip(sx, 0, w - 1.001); sy = np.clip(sy, 0, h - 1.001)
    x0, y0 = sx.astype(np.int32), sy.astype(np.int32)
    fx, fy = sx - x0, sy - y0
    a = ch[y0, x0].astype(np.float32)
    return (a * (1 - fx) * (1 - fy) + ch[y0, x0 + 1] * fx * (1 - fy)
            + ch[y0 + 1, x0] * (1 - fx) * fy + ch[y0 + 1, x0 + 1] * fx * fy)


class GlassPanelRenderer:
    """Clear rounded glass with desktop refraction and subtle edge highlights."""

    def __init__(self, radius=18.0, bevel=24.0, refraction=0.62, dispersion=0.22):
        self.radius, self.bevel, self.refraction = radius, bevel, refraction
        self.dispersion = dispersion
        self.key = None

    def configure(self, ox, oy, pw, ph, scale=1.0):
        """Panel occupies (ox, oy, pw, ph) device px inside the captured frame."""
        key = (ox, oy, pw, ph, scale)
        if key == self.key: return
        self.key = key; s = scale
        self.ox, self.oy, self.pw, self.ph, self.s = ox, oy, pw, ph, scale
        r = min(self.radius * s, min(pw, ph) / 2 - 1); bevel = self.bevel * s
        ys, xs = np.mgrid[0:ph, 0:pw].astype(np.float32)
        px, py = xs + 0.5 - pw / 2, ys + 0.5 - ph / 2
        qx, qy = np.abs(px) - (pw / 2 - r), np.abs(py) - (ph / 2 - r)
        d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r  # <0 inside
        gy, gx = np.gradient(d); gn = np.hypot(gx, gy) + 1e-6
        nxo, nyo = gx / gn, gy / gn                      # outward normal
        depth = np.clip(-d / bevel, 0, 1)                # 0 at edge .. 1 at bevel inner side
        off = self.refraction * bevel * (1 - depth) ** 2.2
        k = self.dispersion
        self.maps = []
        for kc in (-k, 0.0, k):                          # B, G, R
            self.maps.append(((xs + ox + nxo * off * (1 + kc)).astype(np.float32),
                              (ys + oy + nyo * off * (1 + kc)).astype(np.float32)))
        # --- static lighting
        facing = nxo * -0.62 + nyo * -0.78
        ring = (1 - depth) ** 3
        rim = ring * (0.25 + 0.75 * np.maximum(facing, 0) ** 2 + 0.40 * np.maximum(-facing, 0) ** 2)
        hair = np.clip(1 + d / (1.6 * s), 0, 1) * (0.30 + 0.70 * np.abs(facing))
        v = (ys + 0.5) / ph; u = (xs + 0.5) / pw
        sheen = 0.07 * np.clip(1 - v / 0.42, 0, 1) ** 1.5                       # soft top reflection
        streak = 0.05 * np.exp(-((((u * 0.8 - v * 0.6) + 0.30) / 0.07) ** 2))   # diagonal glint
        inside = (d < 0).astype(np.float32)
        self.light = np.clip(0.60 * rim + 0.50 * hair + (sheen + streak) * inside, 0, 0.92)[..., None].astype(np.float32)
        self.alpha = np.clip(0.5 - d, 0, 1).astype(np.float32)[..., None]
    def render(self, frame_bgr: np.ndarray) -> np.ndarray:
        """frame_bgr: full captured window (H, W, 3) uint8. Returns (ph, pw, 4) premultiplied BGRA."""
        pw, ph = self.pw, self.ph
        sharp = np.empty((ph, pw, 3), np.float32)
        for i, (mx, my) in enumerate(self.maps):
            sharp[..., i] = _remap(frame_bgr[..., i], mx, my)
        body = sharp * (1 - self.light) + 255.0 * self.light
        res = np.empty((ph, pw, 4), np.uint8)
        res[..., :3] = (np.clip(body, 0, 255) * self.alpha).astype(np.uint8)
        res[..., 3] = (self.alpha[..., 0] * 255).astype(np.uint8)
        return res
