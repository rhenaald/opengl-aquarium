#version 330 core

layout (location = 0) in vec3 in_position;

uniform mat4 m_proj;
uniform mat4 m_view;

out vec3 tex_dir;

void main() {
    tex_dir = in_position;
    vec4 pos = m_proj * m_view * vec4(in_position, 1.0);
    gl_Position = pos.xyww;
}
