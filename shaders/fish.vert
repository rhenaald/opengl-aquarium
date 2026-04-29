#version 330 core

layout (location = 0) in vec3 in_normal;
layout (location = 1) in vec3 in_position;

uniform mat4  m_proj;
uniform mat4  m_view;
uniform mat4  m_model;
uniform float u_time;
uniform float u_swim_phase;

out vec3  frag_pos;
out vec3  normal;
out float v_body_x;

// ─── Travelling wave displacement ────────────────────────────────────────────
// Gerakan renang ikan yang benar adalah gelombang sinusoidal yang berjalan
// dari kepala (-x) ke ekor (+x arah negatif), bukan seluruh ekor bergerak
// serentak. Amplitudo meningkat menuju ekor (envelope).
//
// Fungsi: z_offset(x, t) = A(x) * sin(k*x - w*t + phase)
//   A(x)  = envelope — nol di kepala, maksimal di ekor
//   k     = wave number (berapa siklus gelombang sepanjang tubuh)
//   w     = angular frequency (kecepatan animasi)
//
// Kita butuh turunan ∂z/∂x untuk mengoreksi normal setelah deformasi.

float wave_freq    = 4.5;   // angular frequency (sama dengan sebelumnya)
float wave_k       = 2.8;   // wave number — ~0.9 siklus sepanjang tubuh
float wave_amp_max = 0.28;  // amplitudo maksimal di ujung ekor

// Envelope: nol di kepala (x ~ +1.1), naik menuju ekor (x ~ -1.1)
// Menggunakan kuadrat agar rise smooth dan tidak ada gerakan di kepala
float envelope(float x) {
    // x dari -1.05 (ekor) sampai +1.1 (kepala)
    // t_tail = 0 di kepala, 1 di ekor
    float t_tail = clamp((-x + 1.1) / 2.15, 0.0, 1.0);
    return wave_amp_max * t_tail * t_tail;
}

// Turunan envelope terhadap x: dibutuhkan untuk koreksi normal
float envelope_dx(float x) {
    float t_tail  = clamp((-x + 1.1) / 2.15, 0.0, 1.0);
    float dt_dx   = -1.0 / 2.15;
    return wave_amp_max * 2.0 * t_tail * dt_dx;
}

// Displacement Z di titik x dan waktu t
float wave_z(float x, float t) {
    float phase = wave_k * x - wave_freq * t + u_swim_phase;
    return envelope(x) * sin(phase);
}

// Turunan ∂(wave_z)/∂x — digunakan untuk mengoreksi normal
// Dengan chain rule:
//   ∂z/∂x = dA/dx * sin(phase) + A(x) * cos(phase) * k
float wave_z_dx(float x, float t) {
    float phase   = wave_k * x - wave_freq * t + u_swim_phase;
    float A       = envelope(x);
    float dA_dx   = envelope_dx(x);
    return dA_dx * sin(phase) + A * cos(phase) * wave_k;
}

void main() {
    vec3 pos = in_position;

    // ── Terapkan travelling wave ──────────────────────────────────────────
    float dz = wave_z(pos.x, u_time);
    pos.z += dz;

    // ── Koreksi normal setelah deformasi ─────────────────────────────────
    // Deformasi hanya terjadi di Z, sebagai fungsi dari X.
    // Jacobian transformasi: posisi baru = (x, y, z + f(x))
    // Normal baru = transpose(inverse(J)) * normal_lama
    //
    // J = | 1    0    0   |
    //     | 0    1    0   |
    //     | dz/dx 0   1   |
    //
    // inv(J)^T * n = n - (dz/dx * nx) * (0,0,1) ... diselesaikan:
    // n_new.x = n.x
    // n_new.y = n.y
    // n_new.z = n.z - (dz/dx) * n.x
    //
    // Ini exact — tidak ada approx, cost hanya satu float multiply.
    vec3 n = in_normal;
    float dzx = wave_z_dx(in_position.x, u_time);
    n.z = n.z - dzx * n.x;
    // Normalisasi di sini (sebelum mat3 transform) lebih stabil
    n = normalize(n);

    // ── Transform ke world space ──────────────────────────────────────────
    vec4 world_pos = m_model * vec4(pos, 1.0);
    frag_pos       = world_pos.xyz;

    // Normal matrix (transpose inverse model) — sudah kita koreksi deformasi
    // sebelum transform, jadi ini hanya rotasi/scale dari model matrix
    normal   = normalize(mat3(transpose(inverse(m_model))) * n);
    v_body_x = in_position.x;   // original x, sebelum deformasi

    gl_Position = m_proj * m_view * world_pos;
}
