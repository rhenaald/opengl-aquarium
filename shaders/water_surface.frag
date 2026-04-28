#version 330 core

struct Light {
    vec3 position;
    vec3 Ia;
    vec3 Id;
    vec3 Is;
};

uniform Light light;
uniform vec3  cam_pos;
uniform float u_time;
uniform vec3  u_water_color;
uniform float u_fog_density;
uniform float u_wave_amplitude;

in vec3 frag_pos;
in vec3 normal;
in vec3 world_pos;

out vec4 fragColor;

// ── Simplex noise for surface detail ────────────────────────────────────────
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x * 34.0) + 1.0) * x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v) {
    const vec2 C = vec2(1.0 / 6.0, 1.0 / 3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
    vec3 i = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);
    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;
    i = mod289(i);
    vec4 p = permute(permute(permute(
        i.z + vec4(0.0, i1.z, i2.z, 1.0))
      + i.y + vec4(0.0, i1.y, i2.y, 1.0))
      + i.x + vec4(0.0, i1.x, i2.x, 1.0));
    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;
    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);
    vec4 x = x_ * ns.x + ns.yyyy;
    vec4 y = y_ * ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);
    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);
    vec4 s0 = floor(b0) * 2.0 + 1.0;
    vec4 s1 = floor(b1) * 2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));
    vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);
    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
    p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m * m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}

void main() {
    vec3 N = normalize(normal);
    vec3 V = normalize(cam_pos - frag_pos);
    vec3 L = normalize(light.position - frag_pos);
    vec3 R = reflect(-L, N);
    vec3 H = normalize(L + V);

    // ── Fresnel (Schlick approximation) ─────────────────────────────────
    float cosTheta = max(dot(N, V), 0.0);
    float F0 = 0.02;  // water IOR ~1.33
    float fresnel = F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);

    // ── Diffuse lighting ────────────────────────────────────────────────
    float diff = max(dot(N, L), 0.0);

    // ── Specular — sharp sun glints on wave peaks ───────────────────────
    float spec = pow(max(dot(N, H), 0.0), 256.0);
    float spec2 = pow(max(dot(N, H), 0.0), 64.0);

    // ── Water body color ────────────────────────────────────────────────
    vec3 deepColor = u_water_color * 1.8;
    vec3 shallowColor = vec3(0.15, 0.55, 0.55);

    // Mix based on viewing angle (Fresnel-like depth effect)
    vec3 waterBody = mix(deepColor, shallowColor, fresnel * 0.6);

    // ── Surface noise detail for micro-ripples ──────────────────────────
    float microNoise = snoise(vec3(frag_pos.xz * 8.0, u_time * 0.5)) * 0.03;

    // ── Reflected "sky" color (simplified environment reflection) ───────
    vec3 reflDir = reflect(-V, N);
    float skyMix = clamp(reflDir.y * 0.5 + 0.5, 0.0, 1.0);
    vec3 skyColor = mix(vec3(0.08, 0.15, 0.22), vec3(0.25, 0.45, 0.55), skyMix);

    // ── Combine ─────────────────────────────────────────────────────────
    vec3 ambient = light.Ia * waterBody * 0.6;
    vec3 diffuse = light.Id * diff * waterBody * 0.4;

    // Specular — two layers: sharp glints + broad sheen
    vec3 specColor = light.Is * (spec * 1.2 + spec2 * 0.3) * vec3(0.9, 0.95, 1.0);

    // Blend reflection based on Fresnel
    vec3 color = ambient + diffuse;
    color = mix(color, skyColor, fresnel * 0.5);
    color += specColor;
    color += microNoise;

    // ── Caustic projection hint (light patterns from waves) ─────────────
    float caustic = sin(frag_pos.x * 4.0 + u_time * 1.5) *
                    sin(frag_pos.z * 3.5 + u_time * 1.2) * 0.08 * diff;
    color += vec3(0.1, 0.2, 0.25) * caustic;

    // ── Final alpha ─────────────────────────────────────────────────────
    float alpha = 0.35 + fresnel * 0.4;
    alpha *= 0.95;

    alpha *= 0.7 + u_wave_amplitude * 3.0;
    alpha = clamp(alpha, 0.1, 0.85);

    fragColor = vec4(color, alpha);
}
