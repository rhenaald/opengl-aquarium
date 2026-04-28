#version 330 core

uniform vec3  cam_pos;
uniform vec3  u_box_min;
uniform vec3  u_box_max;
uniform vec3  u_water_color;
uniform float u_absorption;
uniform float u_surface_base_y;
uniform float u_wave_amplitude;
uniform float u_wave_frequency;
uniform float u_wave_speed;
uniform float u_time;
uniform sampler2D u_scene_depth;
uniform mat4 u_inv_view_proj;
uniform vec2 u_viewport_size;

in vec3 frag_pos;

out vec4 fragColor;

vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x * 34.0) + 1.0) * x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v) {
    const vec2 C = vec2(1.0 / 6.0, 1.0 / 3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);

    vec3 i = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);

    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);

    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;

    i = mod289(i);
    vec4 p = permute(permute(permute(
        i.z + vec4(0.0, i1.z, i2.z, 1.0))
      + i.y + vec4(0.0, i1.y, i2.y, 1.0))
      + i.x + vec4(0.0, i1.x, i2.x, 1.0));

    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;

    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);

    vec4 x = x_ * ns.x + ns.yyyy;
    vec4 y = y_ * ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);

    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);

    vec4 s0 = floor(b0) * 2.0 + 1.0;
    vec4 s1 = floor(b1) * 2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));

    vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;

    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);

    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
    p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;

    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m * m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}

float waterHeight(vec2 pos, float time) {
    float h = 0.0;
    float amp = u_wave_amplitude;
    float freq = u_wave_frequency;
    float spd = u_wave_speed;

    h += snoise(vec3(pos * freq * 0.4, time * spd * 0.6)) * amp;
    h += snoise(vec3(pos * freq * 0.8 + 5.2, time * spd * 0.8 + 1.3)) * amp * 0.5;
    h += snoise(vec3(pos * freq * 1.6 + 9.7, time * spd * 1.1 + 2.7)) * amp * 0.25;
    return h;
}

float surfaceHeight(vec2 pos, float time) {
    return u_surface_base_y + waterHeight(pos, time);
}

bool pointInFootprint(vec2 xz) {
    return xz.x >= u_box_min.x && xz.x <= u_box_max.x &&
           xz.y >= u_box_min.z && xz.y <= u_box_max.z;
}

vec2 ray_box(vec3 ray_origin, vec3 ray_dir, vec3 box_min, vec3 box_max) {
    const float eps = 0.00001;
    vec3 safe_dir = vec3(
        abs(ray_dir.x) < eps ? (ray_dir.x < 0.0 ? -eps : eps) : ray_dir.x,
        abs(ray_dir.y) < eps ? (ray_dir.y < 0.0 ? -eps : eps) : ray_dir.y,
        abs(ray_dir.z) < eps ? (ray_dir.z < 0.0 ? -eps : eps) : ray_dir.z
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

vec3 reconstructWorld(vec2 uv, float depth) {
    vec4 clip = vec4(uv * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    vec4 world = u_inv_view_proj * clip;
    return world.xyz / world.w;
}

bool isUnderwater(vec3 p) {
    return pointInFootprint(p.xz) && p.y <= surfaceHeight(p.xz, u_time);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_viewport_size;
    float scene_depth = texture(u_scene_depth, uv).r;
    bool has_scene_hit = scene_depth < 0.999999;

    vec3 visible_pos = has_scene_hit ? reconstructWorld(uv, scene_depth) : frag_pos;
    vec3 ray_vec = visible_pos - cam_pos;
    float visible_t = length(ray_vec);
    if (visible_t <= 0.0001) {
        discard;
    }

    vec3 ray_dir = ray_vec / visible_t;
    vec2 hit = ray_box(cam_pos, ray_dir, u_box_min, u_box_max);
    float enter_t = max(hit.x, 0.0);
    float exit_t = has_scene_hit ? min(hit.y, visible_t) : hit.y;

    if (exit_t <= enter_t) {
        discard;
    }

    bool found_underwater = false;
    bool closed_underwater = false;
    float water_enter_t = enter_t;
    float water_exit_t = exit_t;
    float prev_t = enter_t;
    bool prev_under = isUnderwater(cam_pos + ray_dir * prev_t);

    if (prev_under) {
        found_underwater = true;
        water_enter_t = enter_t;
        water_exit_t = enter_t;
    }

    for (int i = 1; i <= 16; ++i) {
        float t = mix(enter_t, exit_t, float(i) / 16.0);
        bool under = isUnderwater(cam_pos + ray_dir * t);

        if (under) {
            if (!found_underwater) {
                float lo = prev_t;
                float hi = t;
                for (int j = 0; j < 12; ++j) {
                    float mid = (lo + hi) * 0.5;
                    if (isUnderwater(cam_pos + ray_dir * mid)) {
                        hi = mid;
                    } else {
                        lo = mid;
                    }
                }
                water_enter_t = hi;
            }
            found_underwater = true;
            water_exit_t = t;
        } else if (found_underwater && prev_under) {
            float lo = prev_t;
            float hi = t;
            for (int j = 0; j < 12; ++j) {
                float mid = (lo + hi) * 0.5;
                if (isUnderwater(cam_pos + ray_dir * mid)) {
                    lo = mid;
                } else {
                    hi = mid;
                }
            }
            water_exit_t = lo;
            closed_underwater = true;
            break;
        }

        prev_t = t;
        prev_under = under;
    }

    if (!found_underwater) {
        discard;
    }

    enter_t = water_enter_t;
    exit_t = closed_underwater ? water_exit_t : max(water_exit_t, enter_t);

    if (exit_t <= enter_t) {
        discard;
    }

    vec3 sample_pos = cam_pos + ray_dir * exit_t;
    float surface_y = surfaceHeight(sample_pos.xz, u_time);
    float path_len = exit_t - enter_t;
    vec3 sigma = vec3(1.65, 0.95, 0.55) * u_absorption;
    vec3 transmittance = exp(-sigma * path_len);
    float alpha = clamp(1.0 - dot(transmittance, vec3(0.333333)), 0.0, 0.72);

    float water_height = max(surface_y - u_box_min.y, 0.0001);
    float surface_fade = smoothstep(0.0, 1.0, clamp((sample_pos.y - u_box_min.y) / water_height, 0.0, 1.0));
    float depth_factor = 1.0 - surface_fade;
    vec3 shallow_color = u_water_color * 1.18 + vec3(0.02, 0.05, 0.07);
    vec3 deep_color = u_water_color * vec3(0.55, 0.68, 0.92);
    vec3 vertical_color = mix(deep_color, shallow_color, surface_fade);
    vec3 absorbed_color = vertical_color * mix(vec3(0.72, 0.78, 0.90), transmittance, 0.45);
    absorbed_color *= mix(vec3(1.0), vec3(0.86, 0.90, 0.96), depth_factor * 0.65);
    if (!has_scene_hit) {
        alpha *= 0.78;
    }
    fragColor = vec4(absorbed_color, alpha);
}
