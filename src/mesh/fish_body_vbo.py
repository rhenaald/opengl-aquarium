import math
import numpy as np

from engine.vbo import BaseVBO


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