#version 330 core

struct Light {
    vec3 position;
    vec3 Ia;
    vec3 Id;
    vec3 Is;
};

uniform Light light;
uniform vec3  cam_pos;
uniform float u_time;
uniform vec3  u_water_color;
uniform float u_fog_density;

in vec3  frag_pos;
in vec3  normal;
in float v_height;

out vec4 fragColor;

void main() {
    vec3 N = normalize(normal);
    vec3 L = normalize(light.position - frag_pos);
    vec3 V = normalize(cam_pos - frag_pos);
    vec3 R = reflect(-L, N);

    // Gradient from dark at base to bright green at tip
    vec3 baseColor = mix(vec3(0.05, 0.22, 0.08), vec3(0.18, 0.70, 0.22), v_height);

    float diff = max(dot(N, L), 0.0);
    // Two-sided lighting for thin seaweed
    float diff2 = max(dot(-N, L), 0.0);
    diff = max(diff, diff2 * 0.6);

    float spec = pow(max(dot(V, R), 0.0), 16.0) * step(0.001, diff);

    vec3 ambient  = light.Ia * baseColor * 1.2;
    vec3 diffuse  = light.Id * diff * baseColor;
    vec3 specular = light.Is * spec * vec3(0.5, 0.8, 0.5) * 0.3;

    vec3 color = ambient + diffuse + specular;

    float dist = length(cam_pos - frag_pos);
    float fog  = exp(-u_fog_density * dist * 0.07);
    color = mix(u_water_color, color, clamp(fog, 0.0, 1.0));

    fragColor = vec4(color, 0.92);
}
