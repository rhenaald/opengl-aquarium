#version 330 core

struct Light {
    vec3 position;
    vec3 Ia;
    vec3 Id;
    vec3 Is;
};

uniform Light light;
uniform vec3  cam_pos;
uniform vec3  u_tint;
uniform float u_alpha;
uniform float u_time;

in vec3 frag_pos;
in vec3 normal;

out vec4 fragColor;

void main() {
    vec3 N = normalize(normal);
    vec3 V = normalize(cam_pos - frag_pos);
    vec3 L = normalize(light.position - frag_pos);
    vec3 R = reflect(-L, N);

    // Fresnel for glass edge
    float fresnel = pow(1.0 - abs(dot(N, V)), 2.5);

    float spec = pow(max(dot(V, R), 0.0), 64.0);

    // Subtle water ripple refraction hint on glass
    float ripple = sin(frag_pos.x * 2.0 + u_time * 0.8) * sin(frag_pos.y * 2.0 + u_time * 0.6);
    float ripple_alpha = ripple * 0.03;

    vec3 glass_color = u_tint + vec3(fresnel * 0.12);
    glass_color += vec3(0.9, 0.95, 1.0) * spec * 0.6;

    float alpha = u_alpha + fresnel * 0.25 + ripple_alpha;
    alpha = clamp(alpha, 0.02, 0.7);

    fragColor = vec4(glass_color, alpha);
}
