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

in vec3 frag_pos;
in vec3 normal;

out vec4 fragColor;

// Pseudo-random hash for sand grain variation
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float sandNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float a = hash(i);
    float b = hash(i + vec2(1,0));
    float c = hash(i + vec2(0,1));
    float d = hash(i + vec2(1,1));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(a,b,u.x), mix(c,d,u.x), u.y);
}

float caustic(vec3 p, float t) {
    float a = sin(p.x * 4.0 + t * 1.3) * sin(p.z * 3.5 + t * 1.0);
    float b = sin(p.x * 6.0 - t * 0.8) * sin(p.z * 5.0 + t * 1.5);
    float c = sin((p.x + p.z) * 3.0 + t * 0.6);
    return clamp(0.4 + 0.35*(a*0.5 + b*0.3 + c*0.2), 0.0, 1.0);
}

void main() {
    vec3 N = normalize(normal);
    vec3 L = normalize(light.position - frag_pos);
    vec3 V = normalize(cam_pos - frag_pos);
    vec3 R = reflect(-L, N);

    // Sand color with subtle grain variation
    float grain = sandNoise(frag_pos.xz * 6.0);
    vec3 sandBase  = vec3(0.76, 0.65, 0.42);
    vec3 sandDark  = vec3(0.58, 0.48, 0.30);
    vec3 sandColor = mix(sandDark, sandBase, grain);

    float diff = max(dot(N, L), 0.0);
    float spec = pow(max(dot(V, R), 0.0), 12.0) * step(0.001, diff);

    // Caustic light shimmer on sand
    float caus = caustic(frag_pos, u_time);
    vec3 causticLight = vec3(0.12, 0.18, 0.25) * caus * diff;

    vec3 ambient  = light.Ia * sandColor * 0.9;
    vec3 diffuse  = light.Id * diff * sandColor + causticLight;
    vec3 specular = light.Is * spec * vec3(0.3, 0.35, 0.4);

    vec3 color = ambient + diffuse + specular;

    fragColor = vec4(color, 1.0);
}
