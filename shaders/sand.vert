#version 330 core

in vec3 in_normal;
in vec2 in_uv;
in vec3 in_position;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform sampler2D u_height_map;
uniform vec2 u_sand_tile;
uniform float u_time;
uniform float u_disp_strength;
uniform float u_ripple_strength;
uniform vec2 u_floor_half_extent;

out vec3 frag_pos;
out vec2 v_uv;
out vec3 v_tangent;
out vec3 v_bitangent;
out vec3 v_normal;
out float v_height;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

float noise2(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float edgeFade(vec2 p) {
    vec2 dist_to_edge = u_floor_half_extent - abs(p);
    float min_dist = min(dist_to_edge.x, dist_to_edge.y);
    return smoothstep(0.0, 0.85, min_dist);
}

float heightField(vec3 pos, vec2 uv) {
    float tex_height = texture(u_height_map, uv * u_sand_tile).r;

    const float A1 = 0.006;
    const float A2 = 0.010;
    const float A3 = 0.028;
    const float f1 = 9.0;
    const float f2 = 16.0;
    const vec2  k3 = vec2(0.85, 0.5);
    const vec2  s1 = vec2(0.025, -0.018);
    const vec2  s2 = vec2(-0.012, 0.020);
    const float w3 = 0.07;

    float fade = edgeFade(pos.xz);
    float ripple =
        A1 * noise2(pos.xz * f1 + u_time * s1) +
        A2 * noise2(pos.xz * f2 + u_time * s2) +
        A3 * sin(dot(pos.xz, k3) + u_time * w3) * fade;

    return tex_height * u_disp_strength + ripple * u_ripple_strength / 0.03;
}

void main() {
    vec2 uv = in_uv;
    vec3 pos = in_position;

    float base_h = heightField(pos, uv);
    float eps = 0.06;

    float h_l = heightField(pos + vec3(-eps, 0.0, 0.0), uv + vec2(-eps / (u_floor_half_extent.x * 2.0), 0.0));
    float h_r = heightField(pos + vec3( eps, 0.0, 0.0), uv + vec2( eps / (u_floor_half_extent.x * 2.0), 0.0));
    float h_d = heightField(pos + vec3(0.0, 0.0, -eps), uv + vec2(0.0, -eps / (u_floor_half_extent.y * 2.0)));
    float h_u = heightField(pos + vec3(0.0, 0.0,  eps), uv + vec2(0.0,  eps / (u_floor_half_extent.y * 2.0)));

    vec3 local_tangent = normalize(vec3(2.0 * eps, h_r - h_l, 0.0));
    vec3 local_bitangent = normalize(vec3(0.0, h_u - h_d, 2.0 * eps));
    vec3 local_normal = normalize(cross(local_bitangent, local_tangent));

    vec3 displaced = vec3(pos.x, pos.y + base_h, pos.z);
    vec4 world_pos = m_model * vec4(displaced, 1.0);
    mat3 normal_mat = mat3(transpose(inverse(m_model)));
    mat3 model3 = mat3(m_model);

    frag_pos = world_pos.xyz;
    v_uv = uv;
    v_tangent = normalize(model3 * local_tangent);
    v_bitangent = normalize(model3 * local_bitangent);
    v_normal = normalize(normal_mat * local_normal);
    v_height = clamp(base_h / max(u_disp_strength + u_ripple_strength, 0.0001), 0.0, 1.0);

    gl_Position = m_proj * m_view * world_pos;
}
