#version 330 core
uniform sampler2D u_texture;
in vec2 v_texcoord;
out vec4 f_color;

void main() {
    f_color = texture(u_texture, v_texcoord);
}
