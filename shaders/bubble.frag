#version 330 core

uniform vec3  cam_pos;
uniform float u_time;
uniform vec3  u_water_color;

in vec3 frag_pos;
in vec3 normal;
in vec3 view_dir;

out vec4 fragColor;

void main() {
    vec3 N = normalize(normal);
    vec3 V = normalize(cam_pos - frag_pos);

    // Fresnel rim
    float fresnel = pow(1.0 - max(dot(N, V), 0.0), 3.0);

    // Iridescent tint
    float shimmer = sin(u_time * 2.0 + frag_pos.y * 4.0) * 0.5 + 0.5;
    vec3 rimColor = mix(vec3(0.6, 0.85, 1.0), vec3(0.9, 0.95, 1.0), shimmer);

    vec3 baseColor = vec3(0.75, 0.92, 1.0);
    vec3 color = mix(baseColor * 0.1, rimColor, fresnel);

    float alpha = 0.15 + fresnel * 0.55;

    // Subtle highlight
    vec3 L = normalize(vec3(0, 1, 0));
    float spec = pow(max(dot(reflect(-L, N), V), 0.0), 48.0);
    color += vec3(0.8, 0.95, 1.0) * spec * 0.8;

    fragColor = vec4(color, alpha);
}
