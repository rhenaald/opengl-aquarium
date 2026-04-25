#version 330 core

struct Light {
    vec3 position;
    vec3 Ia;
    vec3 Id;
    vec3 Is;
};

uniform Light light;
uniform vec3  cam_pos;
uniform vec3  u_color;    // primary body color
uniform vec3  u_color2;   // belly / stripe color
uniform vec3  u_color3;   // fin accent color
uniform float u_time;
uniform vec3  u_water_color;
uniform float u_fog_density;

in vec3  frag_pos;
in vec3  normal;
in float v_body_x;

out vec4 fragColor;

void main() {
    vec3 N = normalize(normal);
    vec3 L = normalize(light.position - frag_pos);
    vec3 V = normalize(cam_pos - frag_pos);
    vec3 R = reflect(-L, N);

    // ── Color zoning ──────────────────────────────────────────────
    // Belly: lower half of body (normal.y < 0 roughly)
    float belly    = smoothstep(0.0, -0.5, N.y);
    // Stripe: mid-body band
    float stripe   = smoothstep(0.35, 0.55, abs(v_body_x))
                   * smoothstep(0.85, 0.65, abs(v_body_x));
    // Fin detection: fins sit outside body ellipsoid in Z
    float fin_zone = smoothstep(0.55, 0.75, abs(frag_pos.z / 0.58))
                   + smoothstep(0.60, 0.80, frag_pos.y / 0.75);
    fin_zone = clamp(fin_zone, 0.0, 1.0);

    vec3 baseColor = mix(u_color, u_color2, belly);
    baseColor = mix(baseColor, u_color2 * 0.8 + u_color * 0.2, stripe * 0.6);
    baseColor = mix(baseColor, u_color3, fin_zone * 0.7);

    // Iridescent sheen — angle-dependent color shift
    float sheen = pow(max(1.0 - dot(N, V), 0.0), 2.0);
    baseColor += u_color * sheen * 0.15;

    // ── Lighting ──────────────────────────────────────────────────
    float diff = max(dot(N, L), 0.0);
    float spec = pow(max(dot(V, R), 0.0), 40.0) * step(0.001, diff);

    vec3 ambient  = light.Ia * baseColor;
    vec3 diffuse  = light.Id * diff * baseColor;
    vec3 specular = light.Is * spec * vec3(0.9, 0.97, 1.0) * 0.6;

    // Eye: tiny bright dot near head (+X), above center
    float eyeDist = length(vec2(v_body_x - 0.75, frag_pos.y - 0.18));
    float eye     = smoothstep(0.09, 0.04, eyeDist);
    vec3 eyeColor = vec3(0.05, 0.05, 0.08) + vec3(0.9) * pow(max(dot(N,V),0.0), 8.0);

    vec3 color = ambient + diffuse + specular;
    color = mix(color, eyeColor, eye);

    // ── Underwater fog ────────────────────────────────────────────
    float dist = length(cam_pos - frag_pos);
    float fog  = exp(-u_fog_density * dist * 0.07);
    color = mix(u_water_color, color, clamp(fog, 0.0, 1.0));

    fragColor = vec4(color, 1.0);
}
