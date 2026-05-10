#version 330 core

in vec3 in_position;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;

out vec3 frag_pos;

void main() {
    vec4 world_pos = m_model * vec4(in_position, 1.0);
    frag_pos = world_pos.xyz;
    gl_Position = m_proj * m_view * world_pos;
}
