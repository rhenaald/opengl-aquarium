#version 330 core

struct Light {
    vec3 position;
    vec3 Ia;
    vec3 Id;
    vec3 Is;
};

uniform Light light;
uniform vec3  cam_pos;
uniform vec3  u_tint;
uniform float u_alpha;
uniform float u_time;
uniform sampler2D u_scene_color;
uniform samplerCube u_skybox;
uniform sampler2D u_imperfections;
uniform sampler2D u_normal_map;
uniform float u_ior;
uniform float u_thickness;
uniform vec3  u_absorption_color;
uniform float u_refraction_strength;
uniform float u_reflection_strength;
uniform float u_has_imperfections;
uniform float u_has_normal_map;

in vec3 frag_pos;
in vec3 normal;
in vec4 clip_pos;

out vec4 fragColor;

float schlick_fresnel(float cos_theta, float ior) {
    float f0 = pow((ior - 1.0) / (ior + 1.0), 2.0);
    return f0 + (1.0 - f0) * pow(1.0 - cos_theta, 5.0);
}

vec3 perturb_normal(vec3 n, vec2 uv) {
    vec3 map_n = texture(u_normal_map, uv).xyz * 2.0 - 1.0;
    map_n = mix(vec3(0.0, 0.0, 1.0), map_n, u_has_normal_map);

    vec3 helper = abs(n.y) < 0.92 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0);
    vec3 tangent = normalize(cross(helper, n));
    vec3 bitangent = normalize(cross(n, tangent));

    return normalize(tangent * map_n.x * 0.42 + bitangent * map_n.y * 0.42 + n * max(map_n.z, 0.25));
}

void main() {
    vec3 V = normalize(cam_pos - frag_pos);
    vec3 raw_normal = normalize(normal);
    vec2 screen_uv = clip_pos.xy / clip_pos.w * 0.5 + 0.5;
    vec2 imperfection_uv = frag_pos.xz * 0.22 + frag_pos.xy * 0.035;
    float imperfection = mix(0.5, texture(u_imperfections, imperfection_uv).r, u_has_imperfections);
    float imperfection_delta = imperfection - 0.5;
    vec3 N = faceforward(perturb_normal(raw_normal, imperfection_uv), -V, raw_normal);
    vec3 L = normalize(light.position - frag_pos);
    vec3 R = reflect(-L, N);
    vec3 normal_detail = texture(u_normal_map, imperfection_uv).xyz * 2.0 - 1.0;
    normal_detail.xy *= u_has_normal_map;

    float ripple_a = sin(frag_pos.x * 5.0 + u_time * 1.2);
    float ripple_b = cos(frag_pos.y * 4.0 - u_time * 0.9);
    vec2 ripple = vec2(ripple_a, ripple_b) * 0.0018
                + imperfection_delta * vec2(0.006, -0.004)
                + normal_detail.xy * 0.0045;

    vec3 refr_dir = refract(-V, N, 1.0 / u_ior);
    vec2 refraction_offset = (refr_dir.xy + N.xy * 0.45) * u_refraction_strength + ripple;
    vec3 refracted = texture(u_scene_color, clamp(screen_uv + refraction_offset, 0.001, 0.999)).rgb;

    vec3 reflect_dir = reflect(-V, N);
    vec3 reflected = texture(u_skybox, reflect_dir).rgb;

    float cos_theta = clamp(dot(N, V), 0.0, 1.0);
    float fresnel = schlick_fresnel(cos_theta, u_ior);
    float edge_fresnel = pow(1.0 - cos_theta, 1.8);
    float spec = pow(max(dot(V, R), 0.0), 96.0);
    vec3 absorption = exp(-u_absorption_color * max(u_thickness, 0.0));
    vec3 transmitted = refracted * absorption;
    transmitted = mix(transmitted, transmitted * u_tint, 0.18);

    vec3 color = mix(transmitted, reflected, clamp(fresnel * u_reflection_strength * 2.5, 0.0, 0.85));
    color += vec3(0.9, 0.96, 1.0) * spec * 0.45;
    color += u_tint * (0.035 + edge_fresnel * 0.14);

    float alpha = clamp(u_alpha + edge_fresnel * 0.42 + spec * 0.18 + abs(imperfection_delta) * 0.08, 0.08, 0.62);
    fragColor = vec4(color, alpha);
}
