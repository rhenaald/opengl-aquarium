"""
AquariumRenderer - renders the scene in correct order:
  1. Skybox, opaque objects, water volume, bubbles into offscreen scene color
  2. Copy offscreen scene color to screen
  3. Glass panels with screen-space refraction/reflection
"""

import os

import pygame as pg
import moderngl as mgl

from src.objects.skybox import Skybox
from src.objects.water_volume import WaterVolume


class AquariumRenderer:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.scene = app.scene
        self.skybox = Skybox(app)
        self._init_scene_target()
        self._init_glass_imperfections()
        self._init_sand_material()
        self.water_volume = WaterVolume(app)

    def _init_scene_target(self):
        size = self.app.WIN_SIZE
        self.scene_color = self.ctx.texture(size, 4)
        self.scene_color.filter = (self.ctx.LINEAR, self.ctx.LINEAR)
        self.scene_depth = self.ctx.depth_texture(size)
        self.scene_depth.filter = (self.ctx.NEAREST, self.ctx.NEAREST)
        self.scene_fbo = self.ctx.framebuffer(
            color_attachments=[self.scene_color],
            depth_attachment=self.scene_depth,
        )
        self.composite_color = self.ctx.texture(size, 4)
        self.composite_color.filter = (self.ctx.LINEAR, self.ctx.LINEAR)
        self.composite_fbo = self.ctx.framebuffer(
            color_attachments=[self.composite_color],
        )

    def _init_glass_imperfections(self):
        base_dir = os.path.normpath(os.path.join(
            os.path.dirname(__file__),
            '..',
            'assets',
            'materials',
            'glass',
        ))
        candidates = [
            'imperfections_Opacity.png',
            'imperfections.png',
            'imperfections_color.png',
        ]
        path = None
        for name in candidates:
            candidate = os.path.join(base_dir, name)
            if os.path.exists(candidate):
                path = candidate
                break

        self.has_glass_imperfections = path is not None

        if self.has_glass_imperfections:
            surface = pg.image.load(path).convert()
            size = surface.get_size()
            data = pg.image.tostring(surface, 'RGB', False)
            self.glass_imperfections = self.ctx.texture(size, 3, data=data)
        else:
            self.glass_imperfections = self.ctx.texture(
                (1, 1), 3, data=b'\x80\x80\x80')

        self.glass_imperfections.filter = (self.ctx.LINEAR, self.ctx.LINEAR)
        self.glass_imperfections.repeat_x = True
        self.glass_imperfections.repeat_y = True

        normal_path = os.path.join(base_dir, 'imperfections_NormalGL.png')
        self.has_glass_normal_map = os.path.exists(normal_path)

        if self.has_glass_normal_map:
            surface = pg.image.load(normal_path).convert()
            size = surface.get_size()
            data = pg.image.tostring(surface, 'RGB', False)
            self.glass_normal_map = self.ctx.texture(size, 3, data=data)
        else:
            self.glass_normal_map = self.ctx.texture(
                (1, 1), 3, data=b'\x80\x80\xff')

        self.glass_normal_map.filter = (self.ctx.LINEAR, self.ctx.LINEAR)
        self.glass_normal_map.repeat_x = True
        self.glass_normal_map.repeat_y = True

    def _load_surface_texture(self, path, fallback_rgb):
        if os.path.exists(path):
            surface = pg.image.load(path).convert()
            size = surface.get_size()
            data = pg.image.tostring(surface, 'RGB', False)
            texture = self.ctx.texture(size, 3, data=data)
        else:
            texture = self.ctx.texture((1, 1), 3, data=bytes(fallback_rgb))

        texture.filter = (self.ctx.LINEAR_MIPMAP_LINEAR, self.ctx.LINEAR)
        texture.repeat_x = True
        texture.repeat_y = True
        texture.build_mipmaps()
        return texture

    def _init_sand_material(self):
        base_dir = os.path.normpath(os.path.join(
            os.path.dirname(__file__),
            '..',
            'assets',
            'materials',
            'sand',
        ))
        self.sand_material = {
            'albedo': self._load_surface_texture(
                os.path.join(base_dir, 'sand_diffuse.jpg'),
                (194, 170, 122),
            ),
            'normal': self._load_surface_texture(
                os.path.join(base_dir, 'sand_normal_gl.png'),
                (128, 128, 255),
            ),
            'roughness': self._load_surface_texture(
                os.path.join(base_dir, 'sand_roughness.png'),
                (217, 217, 217),
            ),
            'height': self._load_surface_texture(
                os.path.join(base_dir, 'sand_displacement.png'),
                (128, 128, 128),
            ),
        }

    def render(self):
        self.scene_fbo.use()
        self.ctx.clear(color=(0.02, 0.06, 0.12, 1.0), depth=1.0)
        self._render_scene_color()

        self.ctx.copy_framebuffer(self.composite_fbo, self.scene_fbo)
        self.composite_fbo.use()
        self._render_water_volume()

        self.ctx.copy_framebuffer(self.ctx.screen, self.composite_fbo)
        self.ctx.screen.use()
        self._render_glass()

        # Restore default state
        self.ctx.enable_only(self.ctx.DEPTH_TEST | self.ctx.CULL_FACE)
        self.ctx.depth_func = '<'    # LESS

    def _render_scene_color(self):
        scene = self.scene
        ctx = self.ctx
        cam = self.app.camera

        # ── 1. Skybox background ───────────────────────────────────────
        ctx.enable_only(0)
        self.skybox.render()

        # ── 2. Opaque pass ─────────────────────────────────────────────
        ctx.enable_only(self.ctx.DEPTH_TEST | self.ctx.CULL_FACE)
        for obj in scene.static_opaque:
            obj.render()
        for f in scene.fish:
            f.render()

        # ── 3. Bubbles — transparent, no back-face culling ─────────────
        ctx.enable_only(self.ctx.DEPTH_TEST | self.ctx.BLEND)
        ctx.blend_func = self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA

        # Sort bubbles back-to-front
        cam_pos = cam.position

        def bubble_dist(b):
            d = b.pos - cam_pos
            return -(d.x*d.x + d.y*d.y + d.z*d.z)

        sorted_bubbles = sorted(scene.bubbles, key=bubble_dist)
        for b in sorted_bubbles:
            b.render()

    def _render_water_volume(self):
        self.ctx.enable_only(mgl.BLEND | mgl.CULL_FACE)
        self.ctx.blend_func = self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA
        p = self.app.camera.position
        inside_water = (
            -5.0 <= p.x <= 5.0 and
            0.0 <= p.y <= 6.0 and
            -5.0 <= p.z <= 5.0
        )
        self.ctx.cull_face = 'back' if inside_water else 'front'
        self.water_volume.render()
        self.ctx.cull_face = 'back'

    def _render_glass(self):
        scene = self.scene
        ctx = self.ctx
        cam = self.app.camera

        # ── 3.5. Water surface — transparent, no culling, no depth write ─
        ctx.enable_only(self.ctx.DEPTH_TEST | self.ctx.BLEND)
        ctx.blend_func = self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA
        ctx.depth_func = '<='
        scene.water_surface.render()
        ctx.depth_func = '<'

        # ── 5. Glass panels — refraction + reflection, sorted back-to-front ─
        ctx.enable_only(self.ctx.DEPTH_TEST | self.ctx.BLEND)
        ctx.depth_func = '<='   # LEQUAL
        ctx.blend_func = self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA

        def glass_dist(g):
            d = g.pos - cam.position
            return -(d.x*d.x + d.y*d.y + d.z*d.z)

        sorted_glass = sorted(scene.glass_panels, key=glass_dist)
        if sorted_glass:
            program = sorted_glass[0].program
            program['u_scene_color'].value = 0
            program['u_skybox'].value = 1
            program['u_imperfections'].value = 2
            program['u_normal_map'].value = 3
            program['u_has_imperfections'].value = 1.0 if self.has_glass_imperfections else 0.0
            program['u_has_normal_map'].value = 1.0 if self.has_glass_normal_map else 0.0
            self.composite_color.use(location=0)
            self.skybox.texture.use(location=1)
            self.glass_imperfections.use(location=2)
            self.glass_normal_map.use(location=3)

        for g in sorted_glass:
            g.render()

    def destroy(self):
        self.skybox.destroy()
        self.scene_fbo.release()
        self.scene_color.release()
        self.scene_depth.release()
        self.composite_fbo.release()
        self.composite_color.release()
        self.glass_imperfections.release()
        self.glass_normal_map.release()
        for tex in self.sand_material.values():
            tex.release()
