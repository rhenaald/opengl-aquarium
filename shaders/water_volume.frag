#version 330 core

uniform vec3  cam_pos;
uniform vec3  u_box_min;
uniform vec3  u_box_max;
uniform vec3  u_water_color;
uniform float u_absorption;

in vec3 frag_pos;

out vec4 fragColor;

vec2 ray_box(vec3 ray_origin, vec3 ray_dir, vec3 box_min, vec3 box_max) {
    vec3 safe_dir = vec3(
        abs(ray_dir.x) < 0.00001 ? 0.00001 : ray_dir.x,
        abs(ray_dir.y) < 0.00001 ? 0.00001 : ray_dir.y,
        abs(ray_dir.z) < 0.00001 ? 0.00001 : ray_dir.z
    );
    vec3 inv_dir = 1.0 / safe_dir;
    vec3 t0 = (box_min - ray_origin) * inv_dir;
    vec3 t1 = (box_max - ray_origin) * inv_dir;
    vec3 tmin = min(t0, t1);
    vec3 tmax = max(t0, t1);
    float enter_t = max(max(tmin.x, tmin.y), tmin.z);
    float exit_t = min(min(tmax.x, tmax.y), tmax.z);
    return vec2(enter_t, exit_t);
}

void main() {
    vec3 ray_dir = normalize(frag_pos - cam_pos);
    vec2 hit = ray_box(cam_pos, ray_dir, u_box_min, u_box_max);

    if (hit.y <= max(hit.x, 0.0)) {
        discard;
    }

    float path_len = hit.y - max(hit.x, 0.0);
    vec3 sigma = vec3(1.65, 0.95, 0.55) * u_absorption;
    vec3 transmittance = exp(-sigma * path_len);
    float alpha = clamp(1.0 - dot(transmittance, vec3(0.333333)), 0.0, 0.72);

    float surface_fade = smoothstep(u_box_min.y, u_box_max.y, frag_pos.y);
    float depth_factor = 1.0 - surface_fade;
    vec3 shallow_color = u_water_color * 1.18 + vec3(0.02, 0.05, 0.07);
    vec3 deep_color = u_water_color * vec3(0.55, 0.68, 0.92);
    vec3 vertical_color = mix(deep_color, shallow_color, surface_fade);
    vec3 absorbed_color = vertical_color * mix(vec3(0.72, 0.78, 0.90), transmittance, 0.45);
    absorbed_color *= mix(vec3(1.0), vec3(0.86, 0.90, 0.96), depth_factor * 0.65);
    fragColor = vec4(absorbed_color, alpha);
}
