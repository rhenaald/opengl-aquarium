#version 330 core

layout (location = 0) in vec3 in_normal;
layout (location = 1) in vec3 in_position;

uniform mat4  m_proj;
uniform mat4  m_view;
uniform mat4  m_model;
uniform float u_time;
uniform float u_swim_phase;

out vec3 frag_pos;
out vec3 normal;
out float v_body_x;   // -1 = tail, +1 = head

void main() {
    vec3 pos = in_position;

    // Animate tail: vertices near x=-1 swing more
    float tail_w = clamp((-pos.x - 0.2) / 0.8, 0.0, 1.0);
    float wave   = sin(u_time * 4.5 + u_swim_phase) * tail_w * 0.30;
    pos.z += wave;

    // Gentle body undulation (middle of fish)
    float body_w = (1.0 - abs(pos.x)) * 0.4;
    pos.z += sin(u_time * 4.5 + u_swim_phase + 1.0) * body_w * 0.07;

    vec4 world_pos  = m_model * vec4(pos, 1.0);
    frag_pos        = world_pos.xyz;
    normal          = mat3(transpose(inverse(m_model))) * in_normal;
    v_body_x        = in_position.x;   // original, before deform

    gl_Position = m_proj * m_view * world_pos;
}
