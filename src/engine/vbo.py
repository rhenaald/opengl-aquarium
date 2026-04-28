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


# ── Realistic Fish Body ───────────────────────────────────────────────────────
# Composed of: body (scaled ellipsoid), tail fan, dorsal fin, pectoral fins
# All packed into a single interleaved VBO so one draw call renders the fish.

class FishBodyVBOModern(BaseVBO):
    """
    High-detail realistic fish mesh.
    Head toward +X, tail toward -X.

    Parts:
      - Body      : tapered ellipsoid with lateral-line bulge, high-res UV sphere
      - Head      : detailed snout cap + jaw lower protrusion
      - Eye socket: recessed ring around eye area
      - Gill cover: curved arc cuts on side of head
      - Caudal fin : deeply forked, multi-strip swept fin (both faces)
      - Dorsal fin : long swept multi-lobe fin with curved edge
      - Anal fin   : small fin below tail
      - Pectoral   : two large swept side fins (fan strip)
      - Pelvic fins: two small fins under belly

    All fins rendered double-sided (front + back face).
    Vertex layout: (nx, ny, nz, px, py, pz)
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    # ═══════════════════════════════════════════════════════ low-level helpers ══

    @staticmethod
    def _norm(v):
        l = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
        return (v[0]/l, v[1]/l, v[2]/l) if l > 1e-9 else (0.0, 1.0, 0.0)

    @staticmethod
    def _face_normal(a, b, c):
        ab = (b[0]-a[0], b[1]-a[1], b[2]-a[2])
        ac = (c[0]-a[0], c[1]-a[1], c[2]-a[2])
        return FishBodyVBOModern._norm((
            ab[1]*ac[2] - ab[2]*ac[1],
            ab[2]*ac[0] - ab[0]*ac[2],
            ab[0]*ac[1] - ab[1]*ac[0],
        ))

    @staticmethod
    def _add_tri(data, n, a, b, c):
        for v in (a, b, c):
            data.extend(n); data.extend(v)

    @staticmethod
    def _add_quad(data, n, a, b, c, d):
        FishBodyVBOModern._add_tri(data, n, a, b, c)
        FishBodyVBOModern._add_tri(data, n, a, c, d)

    @staticmethod
    def _add_tri_auto(data, a, b, c):
        n = FishBodyVBOModern._face_normal(a, b, c)
        FishBodyVBOModern._add_tri(data, n, a, b, c)

    @staticmethod
    def _add_quad_auto(data, a, b, c, d):
        n = FishBodyVBOModern._face_normal(a, b, c)
        FishBodyVBOModern._add_quad(data, n, a, b, c, d)

    @staticmethod
    def _add_double_sided_tri(data, a, b, c):
        n  = FishBodyVBOModern._face_normal(a, b, c)
        nb = (-n[0], -n[1], -n[2])
        FishBodyVBOModern._add_tri(data, n,  a, b, c)
        FishBodyVBOModern._add_tri(data, nb, a, c, b)

    @staticmethod
    def _add_double_sided_quad(data, a, b, c, d):
        n  = FishBodyVBOModern._face_normal(a, b, c)
        nb = (-n[0], -n[1], -n[2])
        FishBodyVBOModern._add_quad(data, n,  a, b, c, d)
        FishBodyVBOModern._add_quad(data, nb, a, d, c, b)

    # ═══════════════════════════════════════════════════════════════ body ══

    def _build_body(self, data):
        """
        High-res tapered ellipsoid.
        Shape function gives:
          - narrow pointed tail (x ~ -1)
          - widest belly ~40% from head
          - slightly compressed head (x ~ +1)
        Also adds a subtle lateral-line bulge on sides.
        """
        stacks, slices = 20, 28

        sx = 1.0
        sy_base = 0.44
        sz_base = 0.56

        def radial_scale(u):
            # u=0 tail, u=1 head
            # belly bulge peaks at u=0.55
            belly  = 1.8 * (u**1.1) * ((1.0 - u)**0.55)
            return 0.30 + belly

        def dorsal_flatten(phi):
            # slightly flatten top (dorsal) and bottom (ventral)
            # phi=0 top, phi=pi bottom
            top_flat    = math.exp(-((phi - 0.0) ** 2) / 0.3)
            bottom_flat = math.exp(-((phi - math.pi) ** 2) / 0.3)
            return 1.0 - 0.12 * top_flat - 0.08 * bottom_flat

        def lateral_bulge(phi, theta):
            # subtle bulge on mid-sides (theta ~ ±90°)
            side = math.cos(2 * theta)   # +1 at 0/pi, -1 at ±90
            return 1.0 + 0.04 * (1.0 - side)

        verts = []
        for i in range(stacks + 1):
            phi = math.pi * i / stacks
            u   = 1.0 - i / stacks   # u=1 head pole, u=0 tail pole
            r   = radial_scale(u)
            df  = dorsal_flatten(phi)

            for j in range(slices + 1):
                theta = 2 * math.pi * j / slices
                lb = lateral_bulge(phi, theta)

                ux = math.sin(phi) * math.cos(theta)
                uy = math.cos(phi)
                uz = math.sin(phi) * math.sin(theta)

                sy = sy_base * r * df
                sz = sz_base * r * lb

                px = ux * sx
                py = uy * sy
                pz = uz * sz

                nx = ux / (sx + 1e-9)
                ny = uy / (sy + 1e-9)
                nz = uz / (sz + 1e-9)

                verts.append((FishBodyVBOModern._norm((nx, ny, nz)), (px, py, pz)))

        for i in range(stacks):
            for j in range(slices):
                a = i*(slices+1)+j
                b = a + slices + 1
                for tri in [(a, b, a+1), (b, b+1, a+1)]:
                    for idx in tri:
                        n, p = verts[idx]
                        data.extend(n); data.extend(p)

    # ═══════════════════════════════════════════════════════════════ head ══

    def _build_head(self, data):
        """
        Snout: two-ring tapered cap protruding at +X head.
        Lower jaw: slight downward offset ring to suggest open/closed mouth.
        """
        segs = 14
        # --- upper snout ring ---
        xb, rb = 0.85, 0.20   # base ring (where it meets body)
        xm, rm = 1.00, 0.13   # mid ring
        xt, rt = 1.10, 0.06   # tip ring (mouth opening)

        def ring(x, r, y_offset=0.0):
            return [(x,
                     r * math.cos(a) + y_offset,
                     r * math.sin(a))
                    for a in [2*math.pi*j/segs for j in range(segs+1)]]

        r_base = ring(xb, rb)
        r_mid  = ring(xm, rm, -0.01)
        r_tip  = ring(xt, rt, -0.02)

        # side walls
        for rA, rB in [(r_base, r_mid), (r_mid, r_tip)]:
            for j in range(segs):
                a, b = rA[j], rA[j+1]
                c, d = rB[j+1], rB[j]
                self._add_quad_auto(data, a, b, c, d)

        # mouth disc
        cx = (xt, -0.02, 0.0)
        nf = (1.0, 0.0, 0.0)
        for j in range(segs):
            self._add_tri(data, nf, cx, r_tip[j], r_tip[j+1])

        # --- lower jaw ---
        jaw_base = ring(0.80, 0.14, -0.08)
        jaw_tip  = ring(1.05, 0.05, -0.10)
        for j in range(segs):
            a, b = jaw_base[j], jaw_base[j+1]
            c, d = jaw_tip[j+1], jaw_tip[j]
            self._add_quad_auto(data, a, b, c, d)

    # ═══════════════════════════════════════════════════════════ eye socket ══

    def _build_eye(self, data):
        """
        Recessed eye socket ring on both sides.
        A flat annulus (outer ring → inner ring) pushed slightly inward.
        """
        for side in (+1, -1):
            segs = 12
            # eye centre on side of head
            ex, ey, ez = 0.62, 0.10, side * 0.46

            r_out = 0.13    # outer ring radius
            r_in  = 0.07    # inner (pupil) radius
            depth = 0.03    # how far recessed

            # outer ring — on body surface
            def ring_pt(r, d, k):
                a = 2*math.pi*k/segs
                # tangent plane: normal roughly pointing outward in Z
                ca, sa = math.cos(a), math.sin(a)
                # offset perpendicular to eye outward direction
                # eye normal points outward in Z mostly
                n_eye = (0.15*side, 0.25, side*0.96)
                n_eye = FishBodyVBOModern._norm(n_eye)
                # build local axes on eye plane
                fwd = n_eye
                up  = FishBodyVBOModern._norm((0, 1, 0))
                right = FishBodyVBOModern._norm((
                    fwd[1]*up[2]-fwd[2]*up[1],
                    fwd[2]*up[0]-fwd[0]*up[2],
                    fwd[0]*up[1]-fwd[1]*up[0]
                ))
                up2 = FishBodyVBOModern._norm((
                    right[1]*fwd[2]-right[2]*fwd[1],
                    right[2]*fwd[0]-right[0]*fwd[2],
                    right[0]*fwd[1]-right[1]*fwd[0]
                ))
                px = ex + r*(ca*right[0]+sa*up2[0]) - d*fwd[0]
                py = ey + r*(ca*right[1]+sa*up2[1]) - d*fwd[1]
                pz = ez + r*(ca*right[2]+sa*up2[2]) - d*fwd[2]
                return (px, py, pz)

            outer = [ring_pt(r_out, 0,     k) for k in range(segs+1)]
            inner = [ring_pt(r_in,  depth, k) for k in range(segs+1)]

            # annulus (socket wall)
            for j in range(segs):
                a, b = outer[j], outer[j+1]
                c, d = inner[j+1], inner[j]
                self._add_quad_auto(data, a, b, c, d)

            # pupil disc
            n_eye = FishBodyVBOModern._norm((0.15*side, 0.25, side*0.96))
            nb    = (-n_eye[0], -n_eye[1], -n_eye[2])
            ctr   = ring_pt(0, depth, 0)
            for j in range(segs):
                self._add_tri(data, nb, ctr, inner[j+1], inner[j])

    # ══════════════════════════════════════════════════════════ gill cover ══

    def _build_gill(self, data):
        """
        Operculum (gill cover): a curved crescent-shaped fan of quads
        on each side, sitting behind the eye area.
        """
        for side in (+1, -1):
            segs = 8
            # gill arc — from top to bottom of head side
            x_front = 0.40
            x_back  = 0.10
            y_top   =  0.28
            y_bot   = -0.26
            z_surf  = side * 0.50

            # outer edge (on body surface, at x_front)
            outer = []
            for k in range(segs+1):
                t = k / segs
                y = y_top + (y_bot - y_top) * t
                # slight x curve — arc toward back at mid-height
                xc = x_front - 0.08 * math.sin(math.pi * t)
                outer.append((xc, y, z_surf))

            # inner edge (slightly recessed and pushed back)
            inner = []
            for k in range(segs+1):
                t = k / segs
                y = y_top*0.85 + (y_bot*0.85 - y_top*0.85) * t
                xc = x_back - 0.04 * math.sin(math.pi * t)
                inner.append((xc, y, z_surf * 0.94))

            for j in range(segs):
                a, b = outer[j], outer[j+1]
                c, d = inner[j+1], inner[j]
                self._add_double_sided_quad(data, a, b, c, d)

    # ══════════════════════════════════════════════════════════ caudal fin ══

    def _build_caudal(self, data):
        """
        Deeply forked tail fin.
        Each lobe: 3-strip swept surface with concave inner edge.
        """
        strips = 3     # strips per lobe
        segs   = 5     # segments per strip

        root_x = -0.92

        for sign in (+1, -1):
            # control points for lobe centerline
            # from root → fork point → tip
            cp = [
                (root_x,        sign * 0.05, 0.0),
                (root_x - 0.18, sign * 0.14, 0.0),
                (root_x - 0.38, sign * 0.28, 0.0),
                (root_x - 0.55, sign * 0.38, 0.0),
            ]

            def lerp3(a, b, t):
                return (a[0]+(b[0]-a[0])*t,
                        a[1]+(b[1]-a[1])*t,
                        a[2]+(b[2]-a[2])*t)

            def catmull(ps, t):
                # simple linear multi-seg for now
                n = len(ps) - 1
                seg = min(int(t * n), n-1)
                lt  = t * n - seg
                return lerp3(ps[seg], ps[seg+1], lt)

            # width of fin perpendicular to lobe direction (in Z)
            def width(t):
                return 0.06 + 0.10 * math.sin(math.pi * t)

            # build grid
            grid = []
            ts = [i/(segs) for i in range(segs+1)]
            for t in ts:
                cen = catmull(cp, t)
                w   = width(t)
                row = []
                for s in range(strips+1):
                    frac = s / strips
                    z = -w + 2*w*frac
                    row.append((cen[0], cen[1], z))
                grid.append(row)

            for i in range(segs):
                for j in range(strips):
                    a = grid[i][j]
                    b = grid[i][j+1]
                    c = grid[i+1][j+1]
                    d = grid[i+1][j]
                    self._add_double_sided_quad(data, a, b, c, d)

        # connecting web at fork (small quad between two lobe roots)
        web_pts = [
            (root_x,       0.05,  -0.06),
            (root_x,       0.05,   0.06),
            (root_x - 0.12, 0.0,   0.06),
            (root_x - 0.12, 0.0,  -0.06),
        ]
        self._add_double_sided_quad(data, *web_pts)
        web_pts2 = [
            (root_x,        -0.05, -0.06),
            (root_x - 0.12,  0.0,  -0.06),
            (root_x - 0.12,  0.0,   0.06),
            (root_x,        -0.05,  0.06),
        ]
        self._add_double_sided_quad(data, *web_pts2)

    # ══════════════════════════════════════════════════════════ dorsal fin ══

    def _build_dorsal(self, data):
        """
        Long swept dorsal fin: 5-strip × 6-segment grid,
        with a curved top edge that rises at front and dips at back.
        """
        strips = 5
        segs   = 8

        # base spine along body top
        base_pts = [
            ( 0.55, 0.44, 0.0),
            ( 0.30, 0.44, 0.0),
            ( 0.05, 0.44, 0.0),
            (-0.20, 0.44, 0.0),
            (-0.45, 0.44, 0.0),
            (-0.60, 0.42, 0.0),
        ]
        # top edge (peak)
        peak_pts = [
            ( 0.50, 0.80, 0.0),
            ( 0.22, 0.90, 0.0),
            (-0.05, 0.88, 0.0),
            (-0.28, 0.78, 0.0),
            (-0.50, 0.65, 0.0),
            (-0.62, 0.50, 0.0),
        ]

        def lerp3(a, b, t):
            return (a[0]+(b[0]-a[0])*t,
                    a[1]+(b[1]-a[1])*t,
                    a[2]+(b[2]-a[2])*t)

        def seg_lerp(pts, t):
            n  = len(pts) - 1
            s  = min(int(t * n), n-1)
            lt = t * n - s
            return lerp3(pts[s], pts[s+1], lt)

        # fin width in Z (tapers at ends)
        def fin_z_width(t_base):
            return 0.025 + 0.025 * math.sin(math.pi * t_base * 0.9)

        # build 2D grid: rows=segs+1 (along base), cols=strips+1 (base→peak)
        grid = []
        for i in range(segs+1):
            tb = i / segs
            b  = seg_lerp(base_pts, tb)
            p  = seg_lerp(peak_pts, tb)
            zw = fin_z_width(tb)
            row = []
            for j in range(strips+1):
                tp = j / strips
                pt = lerp3(b, p, tp)
                # slight Z wave so fin isn't totally flat
                z_offset = zw * math.sin(math.pi * tp) * math.sin(math.pi * tb)
                row.append((pt[0], pt[1], pt[2] + z_offset))
            grid.append(row)

        for i in range(segs):
            for j in range(strips):
                a = grid[i][j]
                b = grid[i][j+1]
                c = grid[i+1][j+1]
                d = grid[i+1][j]
                self._add_double_sided_quad(data, a, b, c, d)

    # ══════════════════════════════════════════════════════════ anal fin ══

    def _build_anal(self, data):
        """Small anal fin just below tail."""
        strips = 2
        segs   = 4

        base_pts = [
            (-0.40, -0.44, 0.0),
            (-0.60, -0.44, 0.0),
            (-0.75, -0.42, 0.0),
        ]
        peak_pts = [
            (-0.45, -0.68, 0.0),
            (-0.62, -0.72, 0.0),
            (-0.78, -0.60, 0.0),
        ]

        def lerp3(a, b, t):
            return (a[0]+(b[0]-a[0])*t,
                    a[1]+(b[1]-a[1])*t,
                    a[2]+(b[2]-a[2])*t)

        def seg_lerp(pts, t):
            n = len(pts) - 1
            s = min(int(t * n), n-1)
            lt = t * n - s
            return lerp3(pts[s], pts[s+1], lt)

        grid = []
        for i in range(segs+1):
            tb = i / segs
            b  = seg_lerp(base_pts, tb)
            p  = seg_lerp(peak_pts, tb)
            row = [lerp3(b, p, j/strips) for j in range(strips+1)]
            grid.append(row)

        for i in range(segs):
            for j in range(strips):
                a, b = grid[i][j],   grid[i][j+1]
                c, d = grid[i+1][j+1], grid[i+1][j]
                self._add_double_sided_quad(data, a, b, c, d)

    # ══════════════════════════════════════════════════════ pectoral fins ══

    def _build_pectorals(self, data):
        """
        Two large swept pectoral fins. Each is a fan-strip grid,
        attaching at the side behind the gill, sweeping outward and back.
        """
        for side in (+1, -1):
            strips = 4
            segs   = 6
            z = side

            # attachment line on body (vertical strip behind gill)
            attach = [
                ( 0.25,  0.18, z * 0.50),
                ( 0.20,  0.00, z * 0.53),
                ( 0.18, -0.18, z * 0.50),
                ( 0.20, -0.30, z * 0.44),
            ]
            # fin tip line
            tips = [
                ( 0.40,  0.05, z * 0.88),
                ( 0.15, -0.10, z * 0.96),
                (-0.05, -0.22, z * 0.90),
                (-0.18, -0.32, z * 0.78),
            ]

            def lerp3(a, b, t):
                return (a[0]+(b[0]-a[0])*t,
                        a[1]+(b[1]-a[1])*t,
                        a[2]+(b[2]-a[2])*t)

            def seg_lerp(pts, t):
                n = len(pts) - 1
                s = min(int(t * n), n-1)
                lt = t * n - s
                return lerp3(pts[s], pts[s+1], lt)

            grid = []
            for i in range(segs+1):
                t  = i / segs
                a  = seg_lerp(attach, t)
                tip = seg_lerp(tips,  t)
                row = [lerp3(a, tip, j/strips) for j in range(strips+1)]
                grid.append(row)

            for i in range(segs):
                for j in range(strips):
                    a, b = grid[i][j],     grid[i][j+1]
                    c, d = grid[i+1][j+1], grid[i+1][j]
                    self._add_double_sided_quad(data, a, b, c, d)

    # ══════════════════════════════════════════════════════ pelvic fins ══

    def _build_pelvics(self, data):
        """Two small triangular pelvic fins under belly, mid-body."""
        for side in (+1, -1):
            attach = (0.05, -0.40, side * 0.18)
            tips   = [
                (-0.10, -0.58, side * 0.30),
                ( 0.15, -0.58, side * 0.28),
            ]
            self._add_double_sided_tri(data, attach, tips[0], tips[1])
            # second lobe
            attach2 = (-0.05, -0.40, side * 0.15)
            tips2   = [
                (-0.18, -0.55, side * 0.25),
                (-0.02, -0.56, side * 0.28),
            ]
            self._add_double_sided_tri(data, attach2, tips2[0], tips2[1])

    # ══════════════════════════════════════════════════════════════ main ══

    def get_vertex_data(self):
        data = []
        self._build_body(data)
        self._build_head(data)
        self._build_eye(data)
        self._build_gill(data)
        self._build_caudal(data)
        self._build_dorsal(data)
        self._build_anal(data)
        self._build_pectorals(data)
        self._build_pelvics(data)
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
            'fish_body':     FishBodyVBOModern(ctx),
            'water_grid':    WaterSurfaceVBO(ctx, subdivisions=64, size=1.0),
        }

    def destroy(self):
        for vbo in self.vbos.values():
            vbo.destroy()
