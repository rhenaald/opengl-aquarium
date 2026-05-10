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
uniform vec3  u_sun_pos;
uniform vec3  u_sun_dir;
uniform float u_sun_cutoff;
uniform float u_water_surface_y;
uniform float u_caustic_strength;
uniform float u_caustic_speed;
uniform sampler2D u_albedo_map;
uniform sampler2D u_normal_map;
uniform sampler2D u_roughness_map;
uniform sampler2D u_height_map;
uniform vec2 u_sand_tile;
uniform float u_normal_strength;
uniform float u_micro_normal_strength;

in vec3 frag_pos;
in vec2 v_uv;
in vec3 v_tangent;
in vec3 v_bitangent;
in vec3 v_normal;
in float v_height;

out vec4 fragColor;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float sandNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float a = hash(i);
    float b = hash(i + vec2(1,0));
    float c = hash(i + vec2(0,1));
    float d = hash(i + vec2(1,1));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(a,b,u.x), mix(c,d,u.x), u.y);
}

float caustic_hash(vec2 p) {
    return fract(sin(dot(p, vec2(269.5, 183.3))) * 43758.5453);
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
            vec2 jitter = vec2(caustic_hash(r), caustic_hash(r + 23.17));
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
    vec2 tiled_uv = v_uv * u_sand_tile;
    vec3 albedo = texture(u_albedo_map, tiled_uv).rgb;
    albedo *= vec3(1.03, 0.99, 0.94);
    albedo *= mix(0.94, 1.04, sandNoise(frag_pos.xz * 4.0));

    vec3 map_n = texture(u_normal_map, tiled_uv).xyz * 2.0 - 1.0;
    map_n.xy *= u_normal_strength;
    map_n.z = mix(1.0, map_n.z, u_normal_strength);

    float micro = sandNoise(frag_pos.xz * 22.0 + u_time * 0.02) - 0.5;
    map_n.xy += micro * u_micro_normal_strength;
    map_n = normalize(map_n);

    mat3 tbn = mat3(normalize(v_tangent), normalize(v_bitangent), normalize(v_normal));
    vec3 N = normalize(tbn * map_n);
    vec3 L = normalize(light.position - frag_pos);
    vec3 V = normalize(cam_pos - frag_pos);
    vec3 H = normalize(L + V);

    float diff = max(dot(N, L), 0.0);
    float raw_rough = texture(u_roughness_map, tiled_uv).r;
    float height_tex = texture(u_height_map, tiled_uv).r;
    float roughness = clamp(mix(0.90, 0.75, raw_rough * 0.7 + height_tex * 0.3), 0.75, 0.90);
    float ao = clamp(0.82 + height_tex * 0.14 + v_height * 0.08, 0.72, 1.0);

    float shininess = mix(18.0, 6.0, roughness);
    float spec = pow(max(dot(N, H), 0.0), shininess) * diff;
    vec3 F0 = vec3(0.22);

    float caus = projected_caustic(frag_pos, N);
    vec3 caustic_light = vec3(0.16, 0.24, 0.28) * min(caus, 0.65);

    vec3 ambient = light.Ia * albedo * ao;
    vec3 diffuse = light.Id * diff * albedo;
    vec3 specular = light.Is * spec * F0 * (1.0 - roughness * 0.55);

    vec3 color = ambient + diffuse + specular + caustic_light;
    fragColor = vec4(color, 1.0);
}
