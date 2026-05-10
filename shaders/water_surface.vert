#version 330 core

layout (location = 0) in vec3 in_position;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform float u_time;
uniform float u_wave_amplitude;
uniform float u_wave_frequency;
uniform float u_wave_speed;

out vec3 frag_pos;
out vec3 normal;
out vec3 world_pos;

// ── Simplex 3D Noise (Ashima Arts) ──────────────────────────────────────────
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

// ── Multi-octave noise for natural waves ────────────────────────────────────
float waterHeight(vec2 pos, float time) {
    float h = 0.0;
    float amp = u_wave_amplitude;
    float freq = u_wave_frequency;
    float spd = u_wave_speed;

    // 3 octaves of simplex noise
    h += snoise(vec3(pos * freq * 0.4, time * spd * 0.6)) * amp;
    h += snoise(vec3(pos * freq * 0.8 + 5.2, time * spd * 0.8 + 1.3)) * amp * 0.5;
    h += snoise(vec3(pos * freq * 1.6 + 9.7, time * spd * 1.1 + 2.7)) * amp * 0.25;

    return h;
}

void main() {
    vec4 wp = m_model * vec4(in_position, 1.0);

    // Displace Y with multi-octave simplex noise
    float h = waterHeight(wp.xz, u_time);
    wp.y += h;

    // Compute normal from partial derivatives (finite difference)
    float eps = 0.05;
    float hx = waterHeight(wp.xz + vec2(eps, 0.0), u_time);
    float hz = waterHeight(wp.xz + vec2(0.0, eps), u_time);
    vec3 N = normalize(vec3(-(hx - h) / eps, 1.0, -(hz - h) / eps));

    frag_pos  = wp.xyz;
    normal    = N;
    world_pos = wp.xyz;

    gl_Position = m_proj * m_view * wp;
}
