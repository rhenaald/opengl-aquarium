"""
VBO - Vertex Buffer Objects. Format: [normal(3f) | position(3f)]
"""

import numpy as np
import math
from .lib import (
    build_body, build_mouth, build_eyes, build_gills, build_caudal,
    build_dorsal, build_anal, build_pectorals, build_pelvics, build_lateral_line,
)

class BaseVBO:
    format  = '3f 3f'
    attribs = ['in_normal', 'in_position']

    def __init__(self, ctx):
        self.ctx = ctx
        vertex_data = self.get_vertex_data().astype('f4')
        self.vbo = ctx.buffer(vertex_data.tobytes())

    def get_vertex_data(self):
        raise NotImplementedError

    def destroy(self):
        self.vbo.release()


# ── Skybox Cube ───────────────────────────────────────────────────────────────
class SkyboxVBO(BaseVBO):
    format = '3f'
    attribs = ['in_position']

    def get_vertex_data(self):
        data = [
            -1,  1, -1, -1, -1, -1,  1, -1, -1,
             1, -1, -1,  1,  1, -1, -1,  1, -1,

            -1, -1,  1, -1, -1, -1, -1,  1, -1,
            -1,  1, -1, -1,  1,  1, -1, -1,  1,

             1, -1, -1,  1, -1,  1,  1,  1,  1,
             1,  1,  1,  1,  1, -1,  1, -1, -1,

            -1, -1,  1, -1,  1,  1,  1,  1,  1,
             1,  1,  1,  1, -1,  1, -1, -1,  1,

            -1,  1, -1,  1,  1, -1,  1,  1,  1,
             1,  1,  1, -1,  1,  1, -1,  1, -1,

            -1, -1, -1, -1, -1,  1,  1, -1, -1,
             1, -1, -1, -1, -1,  1,  1, -1,  1,
        ]
        return np.array(data, dtype='f4').reshape(-1, 3)


# ── Position-Only Cube ────────────────────────────────────────────────────────
class CubePositionVBO(BaseVBO):
    format = '3f'
    attribs = ['in_position']

    def get_vertex_data(self):
        data = [
            -1,  1, -1, -1, -1, -1,  1, -1, -1,
             1, -1, -1,  1,  1, -1, -1,  1, -1,

            -1, -1,  1, -1, -1, -1, -1,  1, -1,
            -1,  1, -1, -1,  1,  1, -1, -1,  1,

             1, -1, -1,  1, -1,  1,  1,  1,  1,
             1,  1,  1,  1,  1, -1,  1, -1, -1,

            -1, -1,  1, -1,  1,  1,  1,  1,  1,
             1,  1,  1,  1, -1,  1, -1, -1,  1,

            -1,  1, -1,  1,  1, -1,  1,  1,  1,
             1,  1,  1, -1,  1,  1, -1,  1, -1,

            -1, -1, -1, -1, -1,  1,  1, -1, -1,
             1, -1, -1, -1, -1,  1,  1, -1,  1,
        ]
        return np.array(data, dtype='f4').reshape(-1, 3)


# ── Cube ──────────────────────────────────────────────────────────────────────
class CubeVBO(BaseVBO):
    def get_vertex_data(self):
        v = [(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1),
             (-1,1,-1),(-1,-1,-1),(1,-1,-1),(1,1,-1)]
        faces = [
            ((0,2,3),(0,1,2),(0,0,1)),
            ((1,7,2),(1,6,7),(1,0,0)),
            ((6,5,4),(4,7,6),(0,0,-1)),
            ((3,4,5),(3,5,0),(-1,0,0)),
            ((3,7,4),(3,2,7),(0,1,0)),
            ((0,6,1),(0,5,6),(0,-1,0)),
        ]
        data = []
        for tri_a, tri_b, n in faces:
            for tri in (tri_a, tri_b):
                for i in tri:
                    data.extend(n); data.extend(v[i])
        return np.array(data, dtype='f4').reshape(-1, 6)


# ── Plane ─────────────────────────────────────────────────────────────────────
class PlaneVBO(BaseVBO):
    def __init__(self, ctx, size=1.0):
        self.size = size
        super().__init__(ctx)

    def get_vertex_data(self):
        s = self.size
        pos = [(-s,0,-s),(s,0,-s),(s,0,s),(-s,0,s)]
        idx = [(0,2,1),(0,3,2)]
        data = []
        for tri in idx:
            for i in tri:
                data.extend((0,1,0)); data.extend(pos[i])
        return np.array(data, dtype='f4').reshape(-1, 6)


class SandBedVBO(BaseVBO):
    format = '3f 2f 3f'
    attribs = ['in_normal', 'in_uv', 'in_position']

    def __init__(self, ctx, subdivisions=128, size=1.0, thickness=0.35):
        self.subdivisions = subdivisions
        self.size = size
        self.thickness = thickness
        super().__init__(ctx)

    @staticmethod
    def _smoothstep(edge0, edge1, x):
        t = min(max((x - edge0) / (edge1 - edge0), 0.0), 1.0)
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def _hash(ix, iz):
        value = math.sin(ix * 127.1 + iz * 311.7) * 43758.5453123
        return value - math.floor(value)

    @classmethod
    def _noise(cls, x, z):
        ix = math.floor(x)
        iz = math.floor(z)
        fx = x - ix
        fz = z - iz
        ux = fx * fx * (3.0 - 2.0 * fx)
        uz = fz * fz * (3.0 - 2.0 * fz)

        a = cls._hash(ix, iz)
        b = cls._hash(ix + 1, iz)
        c = cls._hash(ix, iz + 1)
        d = cls._hash(ix + 1, iz + 1)
        return (a + (b - a) * ux) * (1.0 - uz) + (c + (d - c) * ux) * uz

    def _edge_fade(self, x, z):
        dist = self.size - max(abs(x), abs(z))
        return self._smoothstep(0.05, 0.95, dist)

    def _height(self, x, z):
        fade = self._edge_fade(x, z)
        ridge_a = math.sin(x * 1.05 + z * 0.42 + 0.7) * 0.12
        ridge_b = math.sin(x * -0.62 + z * 1.28 + 2.4) * 0.08
        ridge_c = math.sin(x * 1.85 - z * 1.55 + 1.1) * 0.035
        broad_noise = (self._noise(x * 0.62 + 12.0, z * 0.62 - 4.0) - 0.5) * 0.11
        fine_noise = (self._noise(x * 1.55 - 7.0, z * 1.55 + 9.0) - 0.5) * 0.035
        shaped = ridge_a + ridge_b + ridge_c + broad_noise + fine_noise
        return max(0.0, (0.10 + shaped) * fade)

    @staticmethod
    def _norm(v):
        length = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
        if length <= 1e-8:
            return (0.0, 1.0, 0.0)
        return (v[0] / length, v[1] / length, v[2] / length)

    def _normal(self, x, z):
        eps = 0.06
        h_l = self._height(x - eps, z)
        h_r = self._height(x + eps, z)
        h_d = self._height(x, z - eps)
        h_u = self._height(x, z + eps)
        return self._norm((-(h_r - h_l) / (2.0 * eps), 1.0, -(h_u - h_d) / (2.0 * eps)))

    def get_vertex_data(self):
        n = self.subdivisions
        s = self.size
        bottom_y = -self.thickness
        data = []

        def uv_for(x, z):
            return ((x + s) / (2.0 * s), (z + s) / (2.0 * s))

        def emit(normal, uv, pos):
            data.extend(normal)
            data.extend(uv)
            data.extend(pos)

        def top_vertex(x, z):
            return (self._normal(x, z), uv_for(x, z), (x, self._height(x, z), z))

        def emit_top(a, b, c):
            for normal, uv, pos in (a, b, c):
                emit(normal, uv, pos)

        for iz in range(n):
            z0 = -s + 2.0 * s * iz / n
            z1 = -s + 2.0 * s * (iz + 1) / n
            for ix in range(n):
                x0 = -s + 2.0 * s * ix / n
                x1 = -s + 2.0 * s * (ix + 1) / n

                p00 = top_vertex(x0, z0)
                p10 = top_vertex(x1, z0)
                p01 = top_vertex(x0, z1)
                p11 = top_vertex(x1, z1)

                emit_top(p00, p11, p10)
                emit_top(p00, p01, p11)

        def emit_quad(normal, a, b, c, d):
            ua = uv_for(a[0], a[2])
            ub = uv_for(b[0], b[2])
            uc = uv_for(c[0], c[2])
            ud = uv_for(d[0], d[2])
            for uv, pos in ((ua, a), (uc, c), (ub, b), (ua, a), (ud, d), (uc, c)):
                emit(normal, uv, pos)

        # Side walls follow the wavy top edge, making the sand a real slab.
        for i in range(n):
            a = -s + 2.0 * s * i / n
            b = -s + 2.0 * s * (i + 1) / n

            emit_quad(
                (0.0, 0.0, -1.0),
                (a, bottom_y, -s),
                (b, bottom_y, -s),
                (b, self._height(b, -s), -s),
                (a, self._height(a, -s), -s),
            )
            emit_quad(
                (0.0, 0.0, 1.0),
                (b, bottom_y, s),
                (a, bottom_y, s),
                (a, self._height(a, s), s),
                (b, self._height(b, s), s),
            )
            emit_quad(
                (-1.0, 0.0, 0.0),
                (-s, bottom_y, b),
                (-s, bottom_y, a),
                (-s, self._height(-s, a), a),
                (-s, self._height(-s, b), b),
            )
            emit_quad(
                (1.0, 0.0, 0.0),
                (s, bottom_y, a),
                (s, bottom_y, b),
                (s, self._height(s, b), b),
                (s, self._height(s, a), a),
            )

        emit_quad(
            (0.0, -1.0, 0.0),
            (-s, bottom_y, s),
            (s, bottom_y, s),
            (s, bottom_y, -s),
            (-s, bottom_y, -s),
        )

        return np.array(data, dtype='f4').reshape(-1, 8)


# ── Sphere ────────────────────────────────────────────────────────────────────
class SphereVBO(BaseVBO):
    def __init__(self, ctx, stacks=8, slices=12):
        self.stacks = stacks
        self.slices = slices
        super().__init__(ctx)

    def get_vertex_data(self):
        verts = []
        for i in range(self.stacks + 1):
            phi = math.pi * i / self.stacks
            for j in range(self.slices + 1):
                theta = 2 * math.pi * j / self.slices
                x = math.sin(phi) * math.cos(theta)
                y = math.cos(phi)
                z = math.sin(phi) * math.sin(theta)
                verts.append((x, y, z))
        indices = []
        for i in range(self.stacks):
            for j in range(self.slices):
                a = i * (self.slices + 1) + j
                b = a + self.slices + 1
                indices += [(a, b, a+1), (b, b+1, a+1)]
        data = []
        for tri in indices:
            for idx in tri:
                n = verts[idx]
                data.extend(n); data.extend(n)
        return np.array(data, dtype='f4').reshape(-1, 6)


# ── Cylinder ──────────────────────────────────────────────────────────────────
class CylinderVBO(BaseVBO):
    def __init__(self, ctx, segments=10, height=1.0, radius=1.0):
        self.segments = segments
        self.height   = height
        self.radius   = radius
        super().__init__(ctx)

    def get_vertex_data(self):
        seg, h, r = self.segments, self.height * 0.5, self.radius
        data = []
        for i in range(seg):
            a0 = 2*math.pi*i/seg
            a1 = 2*math.pi*(i+1)/seg
            nx0,nz0 = math.cos(a0), math.sin(a0)
            nx1,nz1 = math.cos(a1), math.sin(a1)
            p0b=(r*nx0,-h,r*nz0); p0t=(r*nx0,h,r*nz0)
            p1b=(r*nx1,-h,r*nz1); p1t=(r*nx1,h,r*nz1)
            for n,tri in [((nx0,0,nz0),(p0b,p0t,p1b)),((nx1,0,nz1),(p1b,p0t,p1t))]:
                for v in tri: data.extend(n); data.extend(v)
            tc=(0,h,0); bc=(0,-h,0)
            for v in [p0t,p1t]: data.extend((0,1,0)); data.extend(tc); data.extend((0,1,0)); data.extend(v)
            for v in [p1b,p0b]: data.extend((0,-1,0)); data.extend(bc); data.extend((0,-1,0)); data.extend(v)
        return np.array(data, dtype='f4').reshape(-1, 6)


# ── Glass Panel ───────────────────────────────────────────────────────────────
class GlassPanelVBO(BaseVBO):
    def __init__(self, ctx, w=1.0, h=1.0):
        self.w = w; self.h = h
        super().__init__(ctx)

    def get_vertex_data(self):
        w, h = self.w*0.5, self.h*0.5
        pos = [(-w,-h,0),(w,-h,0),(w,h,0),(-w,h,0)]
        data = []
        for tri in [(0,1,2),(0,2,3)]:
            for i in tri: data.extend((0,0,1)); data.extend(pos[i])
        return np.array(data, dtype='f4').reshape(-1, 6)

# ── Water Surface Grid ────────────────────────────────────────────────────────
class WaterSurfaceVBO(BaseVBO):
    """High-resolution grid plane for water surface with per-vertex noise displacement."""
    format  = '3f'
    attribs = ['in_position']

    def __init__(self, ctx, subdivisions=64, size=1.0):
        self.subdivisions = subdivisions
        self.size = size
        super().__init__(ctx)

    def get_vertex_data(self):
        n = self.subdivisions
        s = self.size
        data = []
        for i in range(n):
            for j in range(n):
                x0 = -s + 2.0 * s * i / n
                z0 = -s + 2.0 * s * j / n
                x1 = -s + 2.0 * s * (i + 1) / n
                z1 = -s + 2.0 * s * (j + 1) / n

                # Two triangles per cell (position only)
                for tri in [(x0, z0, x1, z0, x0, z1), (x1, z0, x1, z1, x0, z1)]:
                    for k in range(0, 6, 2):
                        data.extend((tri[k], 0.0, tri[k + 1]))
        return np.array(data, dtype='f4').reshape(-1, 3)


#  FishBodyVBORealistic
# ─────────────────────────────────────────────────────────────────
class FishBodyVBORealistic(BaseVBO):
    def __init__(self, ctx):
        super().__init__(ctx)
 
    def get_vertex_data(self):
        data = []
        build_body(data, stacks=32, slices=36)
        build_mouth(data, segs=18)
        build_eyes(data, segs=20)
        build_gills(data, segs=10)
        build_caudal(data, strips=4, segs=7)
        build_dorsal(data, strips=6, segs=10)
        build_anal(data, strips=3, segs=5)
        build_pectorals(data, strips=5, segs=7)
        build_pelvics(data)
        build_lateral_line(data, n_dots=22)
        return np.array(data, dtype='f4').reshape(-1, 6)

# ── VBO Container ─────────────────────────────────────────────────────────────
class VBO:
    def __init__(self, ctx):
        self.vbos = {
            'skybox':        SkyboxVBO(ctx),
            'cube_pos':      CubePositionVBO(ctx),
            'cube':          CubeVBO(ctx),
            'plane':         PlaneVBO(ctx, size=1.0),
            'sand_grid':     SandBedVBO(ctx, subdivisions=128, size=5.0),
            'sphere':        SphereVBO(ctx, stacks=8, slices=12),
            'sphere_tiny':   SphereVBO(ctx, stacks=5, slices=8),
            'cylinder':      CylinderVBO(ctx, segments=10, height=1.0, radius=1.0),
            'glass_panel':   GlassPanelVBO(ctx, w=1.0, h=1.0),
            'fish_body':     FishBodyVBORealistic(ctx),
            'water_grid':    WaterSurfaceVBO(ctx, subdivisions=64, size=1.0),
        }

    def destroy(self):
        for vbo in self.vbos.values():
            vbo.destroy()
