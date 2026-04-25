"""
VBO - Vertex Buffer Objects. Format: [normal(3f) | position(3f)]
"""

import numpy as np
import math


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


# ── Realistic Fish Body ───────────────────────────────────────────────────────
# Composed of: body (scaled ellipsoid), tail fan, dorsal fin, pectoral fins
# All packed into a single interleaved VBO so one draw call renders the fish.

class FishBodyVBO(BaseVBO):
    """
    A multi-part fish mesh in local space:
      - Body: ellipsoid scaled (1.0, 0.5, 0.65) along X
      - Caudal (tail) fin: fan of triangles at X = -1
      - Dorsal fin: thin triangle ridge on top
      - Pectoral fins: two small flat triangles on sides
    Head points toward +X, tail toward -X.
    """
    def __init__(self, ctx):
        super().__init__(ctx)

    def get_vertex_data(self):
        data = []

        # ── Body (ellipsoid via subdivided UV sphere) ─────────────────
        stacks, slices = 10, 16
        sx, sy, sz = 1.0, 0.42, 0.58   # ellipsoid scale
        verts = []
        for i in range(stacks + 1):
            phi = math.pi * i / stacks
            for j in range(slices + 1):
                theta = 2 * math.pi * j / slices
                ux = math.sin(phi) * math.cos(theta)
                uy = math.cos(phi)
                uz = math.sin(phi) * math.sin(theta)
                # position on ellipsoid
                px, py, pz = ux*sx, uy*sy, uz*sz
                # normal = inverse-scale then normalize
                nx, ny, nz = ux/sx, uy/sy, uz/sz
                ln = math.sqrt(nx*nx + ny*ny + nz*nz)
                verts.append(((nx/ln, ny/ln, nz/ln), (px, py, pz)))

        for i in range(stacks):
            for j in range(slices):
                a = i*(slices+1)+j
                b = a+slices+1
                for tri in [(a,b,a+1),(b,b+1,a+1)]:
                    for idx in tri:
                        n, p = verts[idx]
                        data.extend(n); data.extend(p)

        # ── Caudal (tail) fin — forked fan at x = -1.0 ───────────────
        # Root points along body axis, two lobes flare out
        tail_root = (-1.0, 0.0, 0.0)
        tail_top  = (-1.55, 0.30, 0.0)
        tail_bot  = (-1.55,-0.30, 0.0)
        tail_mid  = (-1.20, 0.0, 0.0)
        tail_n    = (0.0, 0.0, 1.0)   # flat, facing camera side
        tail_nb   = (0.0, 0.0,-1.0)

        for n in [tail_n, tail_nb]:
            for tri in [
                (tail_root, tail_mid, tail_top),
                (tail_root, tail_bot, tail_mid),
            ]:
                for v in tri:
                    data.extend(n); data.extend(v)

        # ── Dorsal fin — ridge triangle on top ────────────────────────
        d_back  = (-0.4, 0.42, 0.0)
        d_front = ( 0.3, 0.42, 0.0)
        d_peak  = (-0.05, 0.75, 0.0)
        d_n     = (0.0, 0.0, 1.0)
        d_nb    = (0.0, 0.0,-1.0)
        for n in [d_n, d_nb]:
            for v in [d_back, d_peak, d_front]:
                data.extend(n); data.extend(v)

        # ── Pectoral fins — left and right small ovals ────────────────
        for side in (+1, -1):
            pc = (0.1, -0.05, side * 0.58)   # attach to body side
            p1 = (0.3, -0.20, side * 0.90)
            p2 = (-0.2,-0.15, side * 0.85)
            fn = (0.0, -0.5, side * 0.87)
            for v in [pc, p1, p2]:
                data.extend(fn); data.extend(v)

        return np.array(data, dtype='f4').reshape(-1, 6)


# ── VBO Container ─────────────────────────────────────────────────────────────
class VBO:
    def __init__(self, ctx):
        self.vbos = {
            'cube':        CubeVBO(ctx),
            'plane':       PlaneVBO(ctx, size=1.0),
            'sphere':      SphereVBO(ctx, stacks=8, slices=12),
            'sphere_tiny': SphereVBO(ctx, stacks=5, slices=8),
            'cylinder':    CylinderVBO(ctx, segments=10, height=1.0, radius=1.0),
            'glass_panel': GlassPanelVBO(ctx, w=1.0, h=1.0),
            'fish_body':   FishBodyVBO(ctx),
        }

    def destroy(self):
        for vbo in self.vbos.values():
            vbo.destroy()