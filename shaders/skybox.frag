#version 330 core

uniform samplerCube u_skybox;

in vec3 tex_dir;

out vec4 fragColor;

void main() {
    fragColor = texture(u_skybox, tex_dir);
}
