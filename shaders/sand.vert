#version 330 core

in vec3 in_normal;
in vec2 in_uv;
in vec3 in_position;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;

out vec3 frag_pos;
out vec2 v_uv;
out vec3 v_tangent;
out vec3 v_bitangent;
out vec3 v_normal;
out float v_height;

void main() {
    vec4 world_pos = m_model * vec4(in_position, 1.0);
    mat3 normal_mat = mat3(transpose(inverse(m_model)));
    mat3 model3 = mat3(m_model);

    vec3 local_normal = normalize(in_normal);
    vec3 local_tangent;
    if (abs(local_normal.y) > 0.2) {
        local_tangent = normalize(vec3(1.0, -local_normal.x / max(abs(local_normal.y), 0.0001), 0.0));
    } else {
        local_tangent = normalize(cross(vec3(0.0, 1.0, 0.0), local_normal));
    }
    vec3 local_bitangent = normalize(cross(local_tangent, local_normal));
    local_tangent = normalize(cross(local_normal, local_bitangent));

    frag_pos = world_pos.xyz;
    v_uv = in_uv;
    v_tangent = normalize(model3 * local_tangent);
    v_bitangent = normalize(model3 * local_bitangent);
    v_normal = normalize(normal_mat * local_normal);
    v_height = clamp(in_position.y / 0.28, 0.0, 1.0);

    gl_Position = m_proj * m_view * world_pos;
}
