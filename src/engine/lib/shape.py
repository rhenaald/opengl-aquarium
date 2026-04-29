"""
Fish shape generation functions for aquarium rendering.
Provides parametric body profile and mesh building utilities.
"""

import math


# ─────────────────────────────────────────────────────────────────────────────
#  VECTOR UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def norm(v):
    """Normalize vector."""
    l = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    return (v[0]/l, v[1]/l, v[2]/l) if l > 1e-9 else (0.0, 1.0, 0.0)

def cross(a, b):
    """Cross product of two 3D vectors."""
    return (a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])

def face_normal(a, b, c):
    """Compute face normal from three vertices."""
    ab = (b[0]-a[0], b[1]-a[1], b[2]-a[2])
    ac = (c[0]-a[0], c[1]-a[1], c[2]-a[2])
    return norm(cross(ab, ac))

def lerp3(a, b, t):
    """Linear interpolation between two 3D points."""
    return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t)


# ─────────────────────────────────────────────────────────────────────────────
#  VERTEX AND FACE BUILDING
# ─────────────────────────────────────────────────────────────────────────────

def add_tri(data, n, a, b, c):
    """Add single-sided triangle to vertex data."""
    for v in (a, b, c):
        data.extend(n)
        data.extend(v)

def add_quad(data, n, a, b, c, d):
    """Add single-sided quad to vertex data."""
    add_tri(data, n, a, b, c)
    add_tri(data, n, a, c, d)

def add_tri_auto(data, a, b, c):
    """Add triangle with auto-computed face normal."""
    n = face_normal(a, b, c)
    add_tri(data, n, a, b, c)

def add_quad_auto(data, a, b, c, d):
    """Add quad with auto-computed face normal."""
    n = face_normal(a, b, c)
    add_quad(data, n, a, b, c, d)

def add_ds_tri(data, a, b, c):
    """Add double-sided triangle."""
    n = face_normal(a, b, c)
    nb = (-n[0], -n[1], -n[2])
    add_tri(data, n,  a, b, c)
    add_tri(data, nb, a, c, b)

def add_ds_quad(data, a, b, c, d):
    """Add double-sided quad."""
    n  = face_normal(a, b, c)
    nb = (-n[0], -n[1], -n[2])
    add_quad(data, n,  a, b, c, d)
    add_quad(data, nb, a, d, c, b)


# ─────────────────────────────────────────────────────────────────────────────
#  UNIFIED BODY PROFILE FUNCTION
#  Returns the 3-D point on the body surface for any (u, phi) parameter.
#
#  u   ∈ [0, 1]        0 = tail tip,  1 = snout tip
#  phi ∈ [0, 2π]       angle around the body (0 = dorsal top)
#
#  This is the SINGLE source of truth used by EVERY other part so that fins
#  attach with zero gap.
# ─────────────────────────────────────────────────────────────────────────────

def body_x(u):
    """Map u→x along the fish axis.  u=0→tail x=-1.05, u=1→snout x=+1.10"""
    return -1.05 + 2.15 * u

def body_radius(u, phi):
    """
    Cross-sectional radius at longitudinal position u and angle phi.
    Encodes:
      • pointed tail, blunt head (operculum at ~u=0.75), tapering snout
      • dorsal/ventral flatten
      • lateral belly bulge
    """
    # ── longitudinal profile ──────────────────────────────────────────────
    # tail region  0 < u < 0.18  → cubic taper to point
    # body region  0.18 < u < 0.80 → main oval girth
    # head region  0.80 < u < 1.0  → taper toward snout
    if u < 0.18:
        r_long = (u / 0.18) ** 1.4 * 0.30          # pointed tail peduncle
    elif u < 0.55:
        t = (u - 0.18) / (0.55 - 0.18)
        r_long = 0.30 + 0.22 * (3*t*t - 2*t*t*t)   # smooth rise to belly max
    elif u < 0.78:
        t = (u - 0.55) / (0.78 - 0.55)
        r_long = 0.52 - 0.06 * t                    # broad mid-section
    elif u < 0.90:
        t = (u - 0.78) / (0.90 - 0.78)
        r_long = 0.46 - 0.12 * t                    # operculum region
    else:
        t = (u - 0.90) / (0.10)
        r_long = 0.34 - 0.28 * t                    # snout taper

    # ── angular modifiers ─────────────────────────────────────────────────
    # phi=0 → dorsal (top), phi=π → ventral (bottom)

    # dorsal flatten: fish are flatter on top
    dorsal_flat  = 1.0 - 0.18 * math.exp(-((phi - 0.0)**2) / 0.4)
    # ventral flatten
    ventral_flat = 1.0 - 0.10 * math.exp(-((phi - math.pi)**2) / 0.5)
    # lateral bulge at phi=π/2 and phi=3π/2 (sides)
    lat_bulge    = 1.0 + 0.06 * (math.cos(phi)**2)   # max on sides

    return r_long * dorsal_flat * ventral_flat * lat_bulge

def body_point(u, phi):
    """
    Return (x, y, z) on body surface.
    Y-axis scale: 0.90 (slightly taller than wide for a typical bony fish)
    Z-axis scale: 1.00
    """
    x   = body_x(u)
    r   = body_radius(u, phi)
    y   = r * 0.90 * math.cos(phi)
    z   = r * 1.00 * math.sin(phi)
    return (x, y, z)

def body_normal(u, phi):
    """Approximate outward surface normal via finite differences."""
    eps_u   = 0.008
    eps_phi = 0.008
    # clamp u to valid range
    u_lo = max(0.001, u - eps_u)
    u_hi = min(0.999, u + eps_u)
    pu = body_point(u_hi, phi)
    pd = body_point(u_lo, phi)
    pl = body_point(u, phi - eps_phi)
    pr = body_point(u, phi + eps_phi)
    scale_u = u_hi - u_lo
    du = ((pu[0]-pd[0])/scale_u, (pu[1]-pd[1])/scale_u, (pu[2]-pd[2])/scale_u)
    dv = ((pr[0]-pl[0])/(2*eps_phi), (pr[1]-pl[1])/(2*eps_phi), (pr[2]-pl[2])/(2*eps_phi))
    # cross product: du × dv points outward when u increases toward head (+X)
    cx = cross(du, dv)
    # ensure it points outward (away from axis)
    p  = body_point(u, phi)
    dot = cx[1]*p[1] + cx[2]*p[2]   # radial dot
    if dot < 0:
        cx = (-cx[0], -cx[1], -cx[2])
    return norm(cx)


# ─────────────────────────────────────────────────────────────────────────────
#  MESH BUILDING FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def build_body(data, stacks=32, slices=36):
    """
    Tessellate the body surface into quads using body_point.
    Normals are computed analytically via finite differences.
    """
    # Build vertex grid
    verts = []
    for i in range(stacks + 1):
        u = i / stacks
        row = []
        for j in range(slices + 1):
            phi = 2 * math.pi * j / slices
            p   = body_point(u, phi)
            n   = body_normal(u, phi)
            row.append((n, p))
        verts.append(row)

    for i in range(stacks):
        for j in range(slices):
            (n0, a) = verts[i  ][j  ]
            (n1, b) = verts[i  ][j+1]
            (n2, c) = verts[i+1][j+1]
            (n3, d) = verts[i+1][j  ]
            # Per-vertex normals (smooth shading)
            for n, v in [(n0,a),(n1,b),(n2,c)]:
                data.extend(n)
                data.extend(v)
            for n, v in [(n0,a),(n2,c),(n3,d)]:
                data.extend(n)
                data.extend(v)

    # Tail cap (close the mesh at u=0)
    u_tip = 0.0
    tip   = body_point(u_tip, 0.0)
    tip_n = (-1.0, 0.0, 0.0)
    for j in range(slices):
        phi0 = 2*math.pi*j/slices
        phi1 = 2*math.pi*(j+1)/slices
        p0 = body_point(u_tip + 0.01, phi0)
        p1 = body_point(u_tip + 0.01, phi1)
        add_tri(data, tip_n, tip, p0, p1)

    # Snout cap (close at u=1)
    u_snout = 1.0
    # Build a small disc at the snout
    snout_c = body_point(u_snout, 0.0)
    # snout is tiny — just fan from a central point
    snout_n = (1.0, 0.0, 0.0)
    for j in range(slices):
        phi0 = 2*math.pi*j/slices
        phi1 = 2*math.pi*(j+1)/slices
        p0 = body_point(u_snout - 0.01, phi0)
        p1 = body_point(u_snout - 0.01, phi1)
        add_tri(data, snout_n, snout_c, p1, p0)


def build_mouth(data, segs=16):
    """
    Small open-oval mouth at the snout.
    Upper jaw slightly protrudes over lower jaw (like most bony fish).
    The mouth ring samples from the body at u=0.98, giving zero gap.
    """
    u_mouth = 0.98

    # Ring of vertices from body surface in lower hemisphere (ventral side)
    # phi from 5π/4 to 7π/4 wraps under the snout for lower jaw
    # We keep it simple: oval ring slightly offset from body tip
    cx = body_x(1.02)   # slightly in front of snout
    segs_half = segs // 2

    def mouth_pt(t):
        # t ∈ [0,1], ellipse in YZ plane, slightly downward offset
        angle = math.pi + math.pi * t   # from bottom→top going around
        ry = 0.045
        rz = 0.06
        y  = ry * math.cos(angle) - 0.012  # shift center down a bit
        z  = rz * math.sin(angle)
        return (cx, y, z)

    ring = [mouth_pt(j/segs) for j in range(segs+1)]
    centre = (cx, -0.012, 0.0)
    nf = (1.0, 0.0, 0.0)
    for j in range(segs):
        add_tri(data, nf, centre, ring[j], ring[j+1])

    # Lip ring connecting mouth to body surface
    # Sample body ring at u=0.985
    body_ring = [body_point(0.985, 2*math.pi*j/segs) for j in range(segs+1)]
    for j in range(segs):
        a = body_ring[j]
        b = body_ring[j+1]
        c = ring[j+1]
        d = ring[j]
        add_quad_auto(data, a, b, c, d)


def build_eyes(data, segs=20):
    """
    Eye placed on body surface by sampling body_point.
    The socket is a cone (annulus) pressed inward along the surface normal.
    """
    for side in (+1, -1):
        # eye centre in angular terms: upper lateral side
        u_eye   = 0.86
        phi_eye = math.pi/2 * (-side)   # side=+1 → right side (phi=-π/2), side=-1 → left

        # centre point and inward normal
        eye_c  = body_point(u_eye, phi_eye)
        eye_n  = body_normal(u_eye, phi_eye)
        eye_n_in = (-eye_n[0], -eye_n[1], -eye_n[2])   # pointing inward

        r_out  = 0.10   # outer socket ring radius
        r_in   = 0.055  # pupil radius
        depth  = 0.025  # recess depth

        # Build local tangent frame on the surface
        forward = norm(eye_n)
        world_up = (0.0, 1.0, 0.0)
        right = norm(cross(forward, world_up))
        up2   = norm(cross(right, forward))

        def ring_pt(r, d, k):
            a  = 2*math.pi*k/segs
            ca, sa = math.cos(a), math.sin(a)
            ox = eye_c[0] + r*(ca*right[0]+sa*up2[0]) - d*forward[0]
            oy = eye_c[1] + r*(ca*right[1]+sa*up2[1]) - d*forward[1]
            oz = eye_c[2] + r*(ca*right[2]+sa*up2[2]) - d*forward[2]
            return (ox, oy, oz)

        outer = [ring_pt(r_out, 0,     k) for k in range(segs+1)]
        inner = [ring_pt(r_in,  depth, k) for k in range(segs+1)]

        # Socket wall (annulus)
        for j in range(segs):
            a, b = outer[j], outer[j+1]
            c, d = inner[j+1], inner[j]
            add_quad_auto(data, a, b, c, d)

        # Pupil disc
        ctr = ring_pt(0, depth, 0)
        for j in range(segs):
            add_tri(data, eye_n_in, ctr, inner[j+1], inner[j])


def build_gills(data, segs=10):
    """
    Operculum: curved crescent whose edge vertices are sampled directly
    from the body surface → zero gap.
    """
    for side in (+1, -1):
        phi_side = math.pi/2 * (-side)  # lateral angle for this side

        # operculum spans u from 0.62..0.80, phi range ±50° from lateral
        u_front = 0.80
        u_back  = 0.62
        dphi    = math.radians(55)   # angular spread of operculum

        # Outer edge (on body surface)
        outer = []
        for k in range(segs+1):
            t   = k / segs
            u   = u_front - (u_front - u_back) * t
            phi = phi_side - dphi + 2*dphi * (k/segs)
            outer.append(body_point(u, phi))

        # Inner edge (shifted inward and slightly compressed)
        inner = []
        for k in range(segs+1):
            t   = k / segs
            u   = (u_front+0.02) - ((u_front+0.02) - (u_back+0.12)) * t
            phi = phi_side - dphi*0.55 + 2*dphi*0.55*(k/segs)
            # push inward by small offset along surface normal
            n   = body_normal(u, phi)
            p   = body_point(u, phi)
            inner.append((p[0]-0.008*n[0], p[1]-0.008*n[1], p[2]-0.008*n[2]))

        for j in range(segs):
            a, b = outer[j], outer[j+1]
            c, d = inner[j+1], inner[j]
            add_ds_quad(data, a, b, c, d)


def build_caudal(data, strips=4, segs=7):
    """
    Forked tail fin.
    Attachment ring sampled from body at u=0.05 → guaranteed flush join.
    """
    u_root = 0.06
    # Sample attachment arc (dorsal half and ventral half) from body
    # Upper lobe: phi 0..π, Lower lobe: phi π..2π
    for lobe_sign in (+1, -1):
        # phi range for this lobe
        phi_start = 0.0       if lobe_sign > 0 else math.pi
        phi_end   = math.pi   if lobe_sign > 0 else 2*math.pi

        # Root line on body surface
        root = []
        for k in range(strips+1):
            phi = phi_start + (phi_end - phi_start) * k / strips
            root.append(body_point(u_root, phi))

        # Fin tip line (extends behind the tail)
        # Lobe sweeps outward (in Y) and back (in -X)
        tip_y_max = lobe_sign * 0.52
        tip_x     = -1.35
        tip_z_hw  = 0.10   # half-width in Z at tip

        tips = []
        for k in range(strips+1):
            t   = k / strips
            # concave inner edge: tips curve toward axis at center
            # straight outer edge at k=0 and k=strips
            concave = math.sin(math.pi * t) * 0.08  # inward concavity
            y_tip   = lobe_sign * (0.10 + (abs(tip_y_max) - 0.10) * t) - lobe_sign*concave
            z_tip   = -tip_z_hw + 2*tip_z_hw*(k/strips)
            tips.append((tip_x, y_tip, z_tip))

        # Build segs-row sweep grid
        grid = []
        for i in range(segs+1):
            s = i / segs
            row = [lerp3(root[k], tips[k], s) for k in range(strips+1)]
            grid.append(row)

        for i in range(segs):
            for j in range(strips):
                a = grid[i  ][j  ]
                b = grid[i  ][j+1]
                c = grid[i+1][j+1]
                d = grid[i+1][j  ]
                add_ds_quad(data, a, b, c, d)

    # Fork web (small connecting membrane between lobes)
    web_segs = 3
    for k in range(web_segs):
        t0 = k     / web_segs
        t1 = (k+1) / web_segs
        y0 = lerp3((0,  0.05, 0), (0, -0.05, 0), t0)[1]
        y1 = lerp3((0,  0.05, 0), (0, -0.05, 0), t1)[1]
        x0 = body_x(u_root) - 0.04 * abs(math.cos(math.pi * t0))
        x1 = body_x(u_root) - 0.04 * abs(math.cos(math.pi * t1))
        for z_s in [-1, +1]:
            z  = z_s * 0.07
            a = (x0, y0, -z)
            b = (x0, y0,  z)
            c = (x1, y1,  z)
            d = (x1, y1, -z)
            add_ds_quad(data, a, b, c, d)


def build_dorsal(data, strips=6, segs=10):
    """
    Long dorsal fin.  Base row sampled directly from body at phi=0 (top).
    """
    # u range along dorsal spine (from behind head to tail peduncle)
    u_start = 0.72   # near head
    u_end   = 0.16   # near tail

    phi_top = 0.0    # dorsal (top)

    # Base row on body surface
    base = []
    for i in range(segs+1):
        u = u_start - (u_start - u_end) * i / segs
        base.append(body_point(u, phi_top))

    # Peak row (fin top edge)
    # Height profile: tall near front, shorter toward tail
    def fin_height(t):
        # t=0 front, t=1 back
        return 0.38 * math.sin(math.pi * t * 0.95 + 0.05)**0.6

    peak = []
    for i in range(segs+1):
        t  = i / segs
        b  = base[i]
        h  = fin_height(t)
        # slight backward rake (x shifts toward tail as we go up)
        rake = 0.06 * (h / 0.38) * (-1.0)
        peak.append((b[0] + rake, b[1] + h, b[2]))

    # Fin has slight Z curvature to look less flat
    def z_wave(i, j):
        t = i / segs
        s = j / strips
        return 0.018 * math.sin(math.pi * s) * math.sin(math.pi * t * 0.8 + 0.1)

    grid = []
    for i in range(segs+1):
        b = base[i]
        p = peak[i]
        row = []
        for j in range(strips+1):
            s  = j / strips
            pt = lerp3(b, p, s)
            row.append((pt[0], pt[1], pt[2] + z_wave(i, j)))
        grid.append(row)

    for i in range(segs):
        for j in range(strips):
            a = grid[i][j]
            b = grid[i][j+1]
            c = grid[i+1][j+1]
            d = grid[i+1][j]
            add_ds_quad(data, a, b, c, d)


def build_anal(data, strips=3, segs=5):
    """Small anal fin — base sampled from ventral body surface (phi=π)."""
    u_start = 0.30
    u_end   = 0.12
    phi_bot = math.pi

    base = []
    for i in range(segs+1):
        u = u_start - (u_start - u_end) * i / segs
        base.append(body_point(u, phi_bot))

    peak = []
    for i in range(segs+1):
        b = base[i]
        t = i / segs
        h = 0.20 * math.sin(math.pi * t * 0.9 + 0.05)
        peak.append((b[0], b[1] - h, b[2]))

    grid = []
    for i in range(segs+1):
        b = base[i]
        p = peak[i]
        row = [lerp3(b, p, j/strips) for j in range(strips+1)]
        grid.append(row)

    for i in range(segs):
        for j in range(strips):
            a = grid[i][j]
            b = grid[i][j+1]
            c = grid[i+1][j+1]
            d = grid[i+1][j]
            add_ds_quad(data, a, b, c, d)


def build_pectorals(data, strips=5, segs=7):
    """
    Large pectoral fins sampled from body at phi = ±π/2 (sides),
    behind operculum (u ≈ 0.60..0.72).
    """
    for side in (+1, -1):
        phi_side = math.pi/2 * (-side)

        # Attachment: a vertical strip on body side
        u_top = 0.72
        u_bot = 0.58
        attach = []
        for i in range(segs+1):
            u   = u_top - (u_top - u_bot) * i / segs
            phi = phi_side + math.radians(30) * (i/segs - 0.5)
            attach.append(body_point(u, phi))

        # Tip line: sweeps outward and slightly rearward
        def tip_pt(i):
            t  = i / segs
            at = attach[i]
            # outward in Z (side) and slightly downward and rearward
            out_z   = side * 0.55
            out_x   = -0.12
            out_y   = -0.14 * math.sin(math.pi * t)
            z_scale = 0.7 + 0.3 * math.sin(math.pi * t)
            return (at[0] + out_x,
                    at[1] + out_y,
                    at[2] + out_z * z_scale)

        tips = [tip_pt(i) for i in range(segs+1)]

        grid = []
        for i in range(segs+1):
            row = [lerp3(attach[i], tips[i], j/strips) for j in range(strips+1)]
            grid.append(row)

        for i in range(segs):
            for j in range(strips):
                a = grid[i][j]
                b = grid[i][j+1]
                c = grid[i+1][j+1]
                d = grid[i+1][j]
                add_ds_quad(data, a, b, c, d)


def build_pelvics(data):
    """
    Small paired pelvic fins under belly, mid-body.
    Attachment sampled from ventral-lateral body surface.
    """
    for side in (+1, -1):
        phi_belly = math.pi + side * math.radians(35)
        u_root    = 0.52

        attach = body_point(u_root, phi_belly)

        # Three tip points define the triangular fin
        tips = [
            (attach[0] - 0.14, attach[1] - 0.22, attach[2] + side * 0.18),
            (attach[0] + 0.06, attach[1] - 0.20, attach[2] + side * 0.16),
            (attach[0] - 0.08, attach[1] - 0.18, attach[2] + side * 0.28),
        ]
        add_ds_tri(data, attach, tips[0], tips[1])
        add_ds_tri(data, attach, tips[1], tips[2])
        add_ds_tri(data, attach, tips[2], tips[0])


def build_lateral_line(data, n_dots=22):
    """
    Lateral line organ: a row of tiny square patches along the mid-lateral
    body surface (phi = ±π/2 ± small offset), giving a subtle textural detail.
    """
    for side in (+1, -1):
        phi_lat = math.pi/2 * (-side) + 0.04 * side
        u_start = 0.80
        u_end = 0.10

        for k in range(n_dots):
            t  = k / (n_dots - 1)
            u  = u_start - (u_start - u_end) * t
            p  = body_point(u, phi_lat)
            n  = body_normal(u, phi_lat)

            # tangent along body axis
            eps = 0.015
            pa  = body_point(u + eps, phi_lat)
            pb  = body_point(u - eps, phi_lat)
            tang = norm((pa[0]-pb[0], pa[1]-pb[1], pa[2]-pb[2]))

            # tangent perpendicular (angular direction on surface)
            bitan = norm(cross(n, tang))

            s = 0.010   # half-size of dot
            d = 0.004   # raised height
            v0 = (p[0]+s*tang[0]+s*bitan[0]+d*n[0],
                  p[1]+s*tang[1]+s*bitan[1]+d*n[1],
                  p[2]+s*tang[2]+s*bitan[2]+d*n[2])
            v1 = (p[0]-s*tang[0]+s*bitan[0]+d*n[0],
                  p[1]-s*tang[1]+s*bitan[1]+d*n[1],
                  p[2]-s*tang[2]+s*bitan[2]+d*n[2])
            v2 = (p[0]-s*tang[0]-s*bitan[0]+d*n[0],
                  p[1]-s*tang[1]-s*bitan[1]+d*n[1],
                  p[2]-s*tang[2]-s*bitan[2]+d*n[2])
            v3 = (p[0]+s*tang[0]-s*bitan[0]+d*n[0],
                  p[1]+s*tang[1]-s*bitan[1]+d*n[1],
                  p[2]+s*tang[2]-s*bitan[2]+d*n[2])
            add_quad_auto(data, v0, v1, v2, v3)
