#version 330 core

struct Light {
    vec3 position;
    vec3 Ia;
    vec3 Id;
    vec3 Is;
};

uniform Light  light;
uniform vec3   cam_pos;
uniform vec3   u_color;
uniform vec3   u_color2;
uniform vec3   u_color3;
uniform float  u_time;
uniform vec3   u_water_color;
uniform float  u_fog_density;
uniform vec3   u_sun_pos;
uniform vec3   u_sun_dir;
uniform float  u_sun_cutoff;
uniform float  u_water_surface_y;
uniform float  u_caustic_strength;
uniform float  u_caustic_speed;

in vec3  frag_pos;
in vec3  normal;
in float v_body_x;

out vec4 fragColor;

// ═══════════════════════════════════════════════════════════ Caustic (sama) ══

float caustic_hash(vec2 p) {
    return fract(sin(dot(p, vec2(157.7, 341.9))) * 43758.5453);
}

float caustic_voronoi(vec2 uv) {
    vec2 cell = floor(uv);
    vec2 f    = fract(uv);
    float d1  = 8.0, d2 = 8.0;
    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            vec2 g      = vec2(float(x), float(y));
            vec2 r      = cell + g;
            vec2 jitter = vec2(caustic_hash(r), caustic_hash(r + 31.31));
            jitter = 0.5 + 0.42 * sin(6.28318 * jitter + u_time * u_caustic_speed);
            float d = length(g + jitter - f);
            if (d < d1) { d2 = d1; d1 = d; }
            else if (d < d2) { d2 = d; }
        }
    }
    return 1.0 - smoothstep(0.025, 0.16, d2 - d1);
}

mat2 caustic_rot(float a) {
    float s = sin(a), c = cos(a);
    return mat2(c, -s, s, c);
}

float projected_caustic(vec3 p, vec3 n) {
    vec3 sun_dir     = normalize(u_sun_dir);
    vec3 sun_right   = normalize(cross(vec3(0.0, 1.0, 0.0), sun_dir));
    vec3 sun_forward = normalize(cross(sun_dir, sun_right));
    vec2 uv = vec2(dot(p, sun_right), dot(p, sun_forward)) * 0.85;

    float t = u_time * u_caustic_speed;
    uv += 0.08 * vec2(sin(uv.y * 2.1 + t * 1.3), cos(uv.x * 1.7 - t * 1.1));

    float layer_a = caustic_voronoi(uv * 2.1 + vec2(t * 0.12, -t * 0.08));
    float layer_b = caustic_voronoi(caustic_rot(0.72) * uv * 3.4 + vec2(-t * 0.10, t * 0.14));
    float pattern = pow(max(layer_a, layer_b * 0.72), 1.8);

    float cone_dot   = dot(normalize(p - u_sun_pos), sun_dir);
    float spot_fade  = smoothstep(u_sun_cutoff, 1.0, cone_dot);
    float depth      = max(u_water_surface_y - p.y, 0.0);
    float depth_fade = exp(-depth * 0.28);
    float norm_fade  = max(dot(normalize(n), -sun_dir), 0.0);

    return pattern * spot_fade * depth_fade * norm_fade * u_caustic_strength;
}

// ══════════════════════════════════════════════════════════════ Fresnel ══════
//
// Schlick approximation:
//   F(θ) = F0 + (1 - F0) * (1 - cosθ)^5
//
// F0 untuk kulit ikan basah ≈ 0.02 (non-metallic, basah)
// Artinya: saat melihat dari sudut depan (cosθ ≈ 1) refleksi sangat kecil.
//          saat melihat dari sudut miring (cosθ ≈ 0) refleksi mendekati 1.
// Ini yang membuat ikan terlihat "basah" dan volumetrik.

float fresnel(vec3 N, vec3 V, float F0) {
    float cosTheta = max(dot(N, V), 0.0);
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

// ══════════════════════════════════════════════════════ Dual-lobe specular ══
//
// Permukaan ikan punya dua lapisan reflektif:
//
//   Lapis 1 — Lapisan lendir (mucus layer):
//     Sangat halus → specular lebar dan soft → shininess rendah (~20-40)
//     Warna agak kebiruan (warna air membayang)
//
//   Lapis 2 — Sisik (scales):
//     Lebih keras → specular sempit dan tajam → shininess tinggi (~120-200)
//     Warna putih ke silver
//
// Keduanya digabung dengan bobot berbeda. Hasilnya jauh lebih organik
// dibanding specular tunggal.

vec3 dual_specular(vec3 N, vec3 L, vec3 V, float diff) {
    // Blinn-Phong lebih akurat dari Phong (reflect) dan lebih murah
    vec3 H = normalize(L + V);
    float NdotH = max(dot(N, H), 0.0);

    // Lapis lendir: lebar, soft, sedikit tinted biru
    float spec_mucus  = pow(NdotH, 22.0) * step(0.001, diff);
    vec3  color_mucus = vec3(0.75, 0.88, 1.00) * 0.50;

    // Lapis sisik: sempit, tajam, hampir putih
    float spec_scale  = pow(NdotH, 160.0) * step(0.001, diff);
    vec3  color_scale = vec3(0.95, 0.97, 1.00) * 0.90;

    return light.Is * (spec_mucus * color_mucus + spec_scale * color_scale);
}

// ═════════════════════════════════════════════════════ Fake Subsurface Scattering ══
//
// SSS realistik sangat mahal (butuh raymarching). Kita pakai aproksimasi
// yang umum dipakai di game: "wrap lighting + backlight transmission".
//
// Ide utama:
//   1. Wrap lighting: diffuse tidak langsung drop ke 0 di shadow terminator,
//      tapi "membungkus" sedikit ke sisi gelap. Mirip seperti lilin menerangi
//      jari dari belakang.
//
//   2. Backlight transmission (untuk sirip): kalau cahaya datang dari sisi
//      berlawanan normal (dot(N, L) < 0), sebagian cahaya dianggap "tembus"
//      dengan warna warm (orange-merah seperti darah di bawah kulit).
//
// Untuk badan ikan: hanya wrap lighting (tubuh tidak transparan).
// Untuk sirip: wrap + transmission (sirip tipis, semi-transparan).

float wrap_diffuse(vec3 N, vec3 L, float wrap) {
    // wrap = 0.0 → Lambertian biasa
    // wrap = 0.3 → cahaya "membungkus" 30% ke sisi gelap
    return max(dot(N, L) + wrap, 0.0) / (1.0 + wrap);
}

vec3 fake_sss(vec3 N, vec3 L, vec3 V, vec3 base_color, float fin_zone) {
    // Wrap diffuse untuk seluruh tubuh
    float diff_wrap   = wrap_diffuse(N, L, 0.25);
    vec3  sss_body    = light.Id * diff_wrap * base_color;

    // Transmission untuk sirip: cahaya tembus dari belakang
    // dot(N, L) negatif artinya cahaya datang dari sisi berlawanan normal
    float back_light  = max(-dot(N, L), 0.0);
    // Tambahkan view-dependent agar hanya terlihat saat kita melihat ke arah
    // sumber cahaya melalui sirip (backlit view)
    float view_dep    = max(dot(V, -L), 0.0);
    float transmission = back_light * view_dep * 0.55;

    // Warna transmisi: warm orange-merah (darah + pigmen di bawah kulit tipis)
    vec3 trans_color  = vec3(1.0, 0.35, 0.10) * transmission;
    vec3 sss_fin      = light.Id * (base_color * diff_wrap + trans_color);

    // Blend: area badan pakai sss_body, area sirip pakai sss_fin
    return mix(sss_body, sss_fin, fin_zone);
}

// ══════════════════════════════════════════════════════════════════ Main ═════

void main() {
    vec3 N = normalize(normal);
    vec3 L = normalize(light.position - frag_pos);
    vec3 V = normalize(cam_pos - frag_pos);

    // ── Color zoning (sama seperti sebelumnya, tidak diubah) ─────────────
    float belly   = smoothstep(0.0, -0.5, N.y);
    float stripe  = smoothstep(0.35, 0.55, abs(v_body_x))
                  * smoothstep(0.85, 0.65, abs(v_body_x));
    float fin_zone = clamp(
        smoothstep(0.55, 0.75, abs(frag_pos.z / 0.58)) +
        smoothstep(0.60, 0.80, frag_pos.y / 0.75),
        0.0, 1.0
    );

    vec3 baseColor = mix(u_color, u_color2, belly);
    baseColor = mix(baseColor, u_color2 * 0.8 + u_color * 0.2, stripe * 0.6);
    baseColor = mix(baseColor, u_color3, fin_zone * 0.7);

    // ── Fresnel ──────────────────────────────────────────────────────────
    // F0 = 0.02: permukaan basah non-metallic
    // Fresnel mengontrol seberapa "reflektif" permukaan terlihat dari sudut miring
    float F = fresnel(N, V, 0.02);

    // Iridescent sheen yang dimodulasi Fresnel (lebih akurat dari sebelumnya)
    // Hanya tambahkan sheen di area yang sudah Fresnel-tinggi (sudut miring)
    vec3 sheen_color = u_color * vec3(0.8, 1.0, 1.2);  // slight blue-shift
    baseColor += sheen_color * F * 0.12;

    // ── Diffuse dengan fake SSS ───────────────────────────────────────────
    // Gantikan diffuse Lambertian biasa dengan SSS-wrapped diffuse
    float diff_plain = max(dot(N, L), 0.0);   // masih dibutuhkan untuk spec gate
    vec3  diffuse    = fake_sss(N, L, V, baseColor, fin_zone);
    vec3  ambient    = light.Ia * baseColor;

    // ── Dual-lobe specular ────────────────────────────────────────────────
    vec3 specular = dual_specular(N, L, V, diff_plain);

    // Fresnel mengatur intensitas specular: sudut miring → lebih reflektif
    // Ini mencegah specular terlalu agresif di permukaan frontal
    specular *= (0.4 + 0.6 * F);

    // ── Eye (dibiarkan, mesh-based eye sudah ada di VBO baru) ────────────
    // Deteksi eye di sini hanya sebagai fallback jika shader dipakai
    // dengan mesh lama. Dengan mesh baru ini idealnya dihapus.
    float eyeDist = length(vec2(v_body_x - 0.75, frag_pos.y - 0.18));
    float eye     = smoothstep(0.09, 0.04, eyeDist);
    vec3  eyeColor = vec3(0.04, 0.04, 0.07)
                   + vec3(0.85) * pow(max(dot(N, V), 0.0), 12.0);

    // ── Gabungkan semua ───────────────────────────────────────────────────
    vec3 color = ambient + diffuse + specular;
    color = mix(color, eyeColor, eye);

    // Caustic (tidak berubah)
    color += vec3(0.08, 0.13, 0.16) * projected_caustic(frag_pos, N);

    // ── Tone mapping sederhana ────────────────────────────────────────────
    // Mencegah over-bright dari kombinasi semua efek di atas.
    // Reinhard operator: c → c / (1 + c), mempertahankan warna gelap
    // dan secara lembut mengkompresi area terang.
    // Tanpa ini, kombinasi Fresnel + dual-specular bisa wash-out.
    color = color / (1.0 + color);

    fragColor = vec4(color, 1.0);
}
