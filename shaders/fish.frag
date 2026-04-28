#version 330 core

struct Light {
    vec3 position;
    vec3 Ia;
    vec3 Id;
    vec3 Is;
};

uniform Light light;
uniform vec3  cam_pos;
uniform vec3  u_color;    // primary body color
uniform vec3  u_color2;   // belly / stripe color
uniform vec3  u_color3;   // fin accent color
uniform float u_time;
uniform vec3  u_water_color;
uniform float u_fog_density;
uniform vec3  u_sun_pos;
uniform vec3  u_sun_dir;
uniform float u_sun_cutoff;
uniform float u_water_surface_y;
uniform float u_caustic_strength;
uniform float u_caustic_speed;

in vec3  frag_pos;
in vec3  normal;
in float v_body_x;

out vec4 fragColor;

float caustic_hash(vec2 p) {
    return fract(sin(dot(p, vec2(157.7, 341.9))) * 43758.5453);
}

float caustic_voronoi(vec2 uv) {
    vec2 cell = floor(uv);
    vec2 f = fract(uv);
    float d1 = 8.0;
    float d2 = 8.0;

    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            vec2 g = vec2(float(x), float(y));
            vec2 r = cell + g;
            vec2 jitter = vec2(caustic_hash(r), caustic_hash(r + 31.31));
            jitter = 0.5 + 0.42 * sin(6.28318 * jitter + u_time * u_caustic_speed);
            float d = length(g + jitter - f);
            if (d < d1) {
                d2 = d1;
                d1 = d;
            } else if (d < d2) {
                d2 = d;
            }
        }
    }

    float edge = d2 - d1;
    return 1.0 - smoothstep(0.025, 0.16, edge);
}

mat2 caustic_rot(float a) {
    float s = sin(a);
    float c = cos(a);
    return mat2(c, -s, s, c);
}

float projected_caustic(vec3 p, vec3 n) {
    vec3 sun_dir = normalize(u_sun_dir);
    vec3 sun_right = normalize(cross(vec3(0.0, 1.0, 0.0), sun_dir));
    vec3 sun_forward = normalize(cross(sun_dir, sun_right));
    vec2 uv = vec2(dot(p, sun_right), dot(p, sun_forward)) * 0.85;

    float t = u_time * u_caustic_speed;
    uv += 0.08 * vec2(
        sin(uv.y * 2.1 + t * 1.3),
        cos(uv.x * 1.7 - t * 1.1)
    );

    float layer_a = caustic_voronoi(uv * 2.1 + vec2(t * 0.12, -t * 0.08));
    float layer_b = caustic_voronoi(caustic_rot(0.72) * uv * 3.4 + vec2(-t * 0.10, t * 0.14));
    float pattern = max(layer_a, layer_b * 0.72);
    pattern = pow(pattern, 1.8);

    float cone_dot = dot(normalize(p - u_sun_pos), sun_dir);
    float spot_fade = smoothstep(u_sun_cutoff, 1.0, cone_dot);
    float depth = max(u_water_surface_y - p.y, 0.0);
    float depth_fade = exp(-depth * 0.28);
    float normal_fade = max(dot(normalize(n), -sun_dir), 0.0);

    return pattern * spot_fade * depth_fade * normal_fade * u_caustic_strength;
}

void main() {
    vec3 N = normalize(normal);
    vec3 L = normalize(light.position - frag_pos);
    vec3 V = normalize(cam_pos - frag_pos);
    vec3 R = reflect(-L, N);

    // ── Color zoning ──────────────────────────────────────────────
    // Belly: lower half of body (normal.y < 0 roughly)
    float belly    = smoothstep(0.0, -0.5, N.y);
    // Stripe: mid-body band
    float stripe   = smoothstep(0.35, 0.55, abs(v_body_x))
                   * smoothstep(0.85, 0.65, abs(v_body_x));
    // Fin detection: fins sit outside body ellipsoid in Z
    float fin_zone = smoothstep(0.55, 0.75, abs(frag_pos.z / 0.58))
                   + smoothstep(0.60, 0.80, frag_pos.y / 0.75);
    fin_zone = clamp(fin_zone, 0.0, 1.0);

    vec3 baseColor = mix(u_color, u_color2, belly);
    baseColor = mix(baseColor, u_color2 * 0.8 + u_color * 0.2, stripe * 0.6);
    baseColor = mix(baseColor, u_color3, fin_zone * 0.7);

    // Iridescent sheen — angle-dependent color shift
    float sheen = pow(max(1.0 - dot(N, V), 0.0), 2.0);
    baseColor += u_color * sheen * 0.15;

    // ── Lighting ──────────────────────────────────────────────────
    float diff = max(dot(N, L), 0.0);
    float spec = pow(max(dot(V, R), 0.0), 40.0) * step(0.001, diff);

    vec3 ambient  = light.Ia * baseColor;
    vec3 diffuse  = light.Id * diff * baseColor;
    vec3 specular = light.Is * spec * vec3(0.9, 0.97, 1.0) * 0.6;

    // Eye: tiny bright dot near head (+X), above center
    float eyeDist = length(vec2(v_body_x - 0.75, frag_pos.y - 0.18));
    float eye     = smoothstep(0.09, 0.04, eyeDist);
    vec3 eyeColor = vec3(0.05, 0.05, 0.08) + vec3(0.9) * pow(max(dot(N,V),0.0), 8.0);

    vec3 color = ambient + diffuse + specular;
    color = mix(color, eyeColor, eye);
    color += vec3(0.08, 0.13, 0.16) * projected_caustic(frag_pos, N);

    fragColor = vec4(color, 1.0);
}
