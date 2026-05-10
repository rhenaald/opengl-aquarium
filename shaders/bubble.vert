#version 330 core

layout (location = 0) in vec3 in_normal;
layout (location = 1) in vec3 in_position;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform float u_time;
uniform float u_wobble;

out vec3 frag_pos;
out vec3 normal;
out vec3 view_dir;

void main() {
    // Slight wobble on bubble surface
    vec3 pos = in_position;
    float wobble = sin(u_time * 3.0 + in_position.y * 5.0) * u_wobble;
    pos += in_normal * wobble;

    vec4 world_pos = m_model * vec4(pos, 1.0);
    frag_pos = world_pos.xyz;
    normal   = mat3(transpose(inverse(m_model))) * in_normal;

    vec4 view_pos = m_view * world_pos;
    view_dir = normalize(-view_pos.xyz);

    gl_Position = m_proj * view_pos;
}
