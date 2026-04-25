#version 330 core

struct Light {
    vec3 position;
    vec3 Ia;
    vec3 Id;
    vec3 Is;
};

uniform Light light;
uniform vec3  cam_pos;
uniform vec3  u_color;
uniform float u_time;
uniform vec3  u_water_color;
uniform float u_fog_density;

in vec3 frag_pos;
in vec3 normal;

out vec4 fragColor;

// Simple caustic-like shimmer
float caustic(vec3 p, float t) {
    float a = sin(p.x * 3.0 + t * 1.2) * sin(p.z * 3.0 + t * 0.9);
    float b = sin(p.x * 5.0 - t * 0.7) * sin(p.z * 4.0 + t * 1.4);
    return 0.5 + 0.5 * (a * 0.6 + b * 0.4);
}

void main() {
    vec3 N = normalize(normal);
    vec3 L = normalize(light.position - frag_pos);
    vec3 V = normalize(cam_pos - frag_pos);
    vec3 R = reflect(-L, N);

    float diff = max(dot(N, L), 0.0);
    float spec = pow(max(dot(V, R), 0.0), 32.0) * step(0.001, diff);

    // Caustic shimmer from above
    float caus = caustic(frag_pos, u_time);
    vec3 causticBoost = vec3(0.04, 0.08, 0.12) * caus * diff;

    vec3 ambient  = light.Ia * u_color;
    vec3 diffuse  = light.Id * diff * u_color + causticBoost;
    vec3 specular = light.Is * spec * vec3(0.8, 0.9, 1.0);

    vec3 color = ambient + diffuse + specular;

    // Underwater depth fog
    float dist = length(cam_pos - frag_pos);
    float fog  = exp(-u_fog_density * dist * 0.08);
    color = mix(u_water_color, color, clamp(fog, 0.0, 1.0));

    fragColor = vec4(color, 1.0);
}
