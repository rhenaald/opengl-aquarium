from pyglm import glm
import pygame as pg

FOV = 70
NEAR = 0.1
FAR = 100.0
MOUSE_SENS = 0.04


class Camera:
    def __init__(self, app, position=(6.0, 4.5, 6.0), look_lr=225.0, look_ud=-25.0):
        self.app = app
        self.aspect_ratio = app.WIN_SIZE[0] / app.WIN_SIZE[1]

        self.position = glm.vec3(position)
        self.world_up = glm.vec3(0, 1, 0)
        self.up = glm.vec3(0, 1, 0)
        self.right = glm.vec3(1, 0, 0)
        self.forward = glm.vec3(0, 0, -1)

        self.look_lr = look_lr
        self.look_ud = look_ud

        self.use_orbit = False
        self.orbit_target = glm.vec3(0, 0.8, 0)
        self.orbit_radius = 10.0

        self.m_proj = self.get_projection_matrix()
        self.update_camera_vectors()
        self.m_view = self.get_view_matrix()

    def rotate(self):
        dx, dy = pg.mouse.get_rel()
        self.look_lr += dx * MOUSE_SENS
        self.look_ud -= dy * MOUSE_SENS
        self.look_ud = max(-89.0, min(89.0, self.look_ud))

    def update_camera_vectors(self):
        yaw = glm.radians(self.look_lr)
        pitch = glm.radians(self.look_ud)

        self.forward.x = glm.cos(yaw) * glm.cos(pitch)
        self.forward.y = glm.sin(pitch)
        self.forward.z = glm.sin(yaw) * glm.cos(pitch)
        self.forward = glm.normalize(self.forward)
        self.right = glm.normalize(glm.cross(self.forward, self.world_up))
        self.up = glm.normalize(glm.cross(self.right, self.forward))

    def move(self):
        input_mgr = self.app.input
        velocity = 0.02 * self.app.delta_time
        
        if input_mgr.is_pressed(pg.K_LSHIFT) or input_mgr.is_pressed(pg.K_RSHIFT):
            velocity = 0.05 * self.app.delta_time
        elif input_mgr.is_pressed(pg.K_LCTRL) or input_mgr.is_pressed(pg.K_RCTRL):
            velocity = 0.004 * self.app.delta_time

        if input_mgr.is_pressed(pg.K_w):
            self.position += self.forward * velocity
        if input_mgr.is_pressed(pg.K_s):
            self.position -= self.forward * velocity
        if input_mgr.is_pressed(pg.K_a):
            self.position -= self.right * velocity
        if input_mgr.is_pressed(pg.K_d):
            self.position += self.right * velocity
        if input_mgr.is_pressed(pg.K_q):
            self.position -= self.up * velocity
        if input_mgr.is_pressed(pg.K_e):
            self.position += self.up * velocity

    def update_orbit(self):
        input_mgr = self.app.input
        rotate_speed = 0.05 * self.app.delta_time
        
        if input_mgr.is_pressed(pg.K_LSHIFT) or input_mgr.is_pressed(pg.K_RSHIFT):
            rotate_speed = 0.10 * self.app.delta_time
        elif input_mgr.is_pressed(pg.K_LCTRL) or input_mgr.is_pressed(pg.K_RCTRL):
            rotate_speed = 0.02 * self.app.delta_time

        if input_mgr.is_pressed(pg.K_LEFT):
            self.look_lr += rotate_speed
        if input_mgr.is_pressed(pg.K_RIGHT):
            self.look_lr -= rotate_speed
        if input_mgr.is_pressed(pg.K_UP):
            self.look_ud += rotate_speed
        if input_mgr.is_pressed(pg.K_DOWN):
            self.look_ud -= rotate_speed

        dx, dy = pg.mouse.get_rel()
        self.look_lr += dx * MOUSE_SENS
        self.look_ud -= dy * MOUSE_SENS
        self.look_ud = max(-89.0, min(89.0, self.look_ud))

        theta = glm.radians(self.look_lr)
        phi = glm.radians(self.look_ud)
        x = self.orbit_radius * glm.cos(phi) * glm.cos(theta)
        y = self.orbit_radius * glm.sin(phi)
        z = self.orbit_radius * glm.cos(phi) * glm.sin(theta)

        self.position = self.orbit_target + glm.vec3(x, y, z)
        self.forward = glm.normalize(self.orbit_target - self.position)
        self.right = glm.normalize(glm.cross(self.forward, self.world_up))
        self.up = glm.normalize(glm.cross(self.right, self.forward))
        self.m_view = self.get_view_matrix()

    def update(self):
        if self.use_orbit:
            self.update_orbit()
        else:
            self.move()
            self.rotate()
            self.update_camera_vectors()
            self.m_view = self.get_view_matrix()

    def set_default(self):
        self.position = glm.vec3(6.0, 4.5, 6.0)
        self.orbit_target = glm.vec3(0, 0.8, 0)
        self.orbit_radius = 10.0
        if self.use_orbit:
            self.look_lr = 45.0
            self.look_ud = 25.0
        else:
            self.look_lr = 225.0
            self.look_ud = -25.0
        self.update_camera_vectors()
        self.m_view = self.get_view_matrix()

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.position + self.forward, self.up)

    def get_projection_matrix(self):
        return glm.perspective(glm.radians(FOV), self.aspect_ratio, NEAR, FAR)
