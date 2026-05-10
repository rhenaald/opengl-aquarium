#version 330 core

layout (location = 0) in vec3 in_normal;
layout (location = 1) in vec3 in_position;

uniform mat4  m_proj;
uniform mat4  m_view;
uniform mat4  m_model;
uniform float u_time;
uniform float u_sway_phase;
uniform float u_wave_speed;

out vec3 frag_pos;
out vec3 normal;
out float v_height;

void main() {
    vec3 pos = in_position;

    // Sway increases with height (top of seaweed moves more)
    float height_factor = clamp((pos.y + 1.0) * 0.5, 0.0, 1.0);
    float sway = sin(u_time * u_wave_speed * 1.2 + u_sway_phase) * height_factor * 0.35;
    float sway2 = cos(u_time * u_wave_speed * 0.9 + u_sway_phase * 1.3) * height_factor * 0.15;
    pos.x += sway;
    pos.z += sway2;

    vec4 world_pos = m_model * vec4(pos, 1.0);
    frag_pos = world_pos.xyz;
    normal   = mat3(transpose(inverse(m_model))) * in_normal;
    v_height = height_factor;

    gl_Position = m_proj * m_view * world_pos;
}
