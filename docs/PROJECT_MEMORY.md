# Project Memory

## Project
OpenGL Aquarium: Python 3.11 interactive aquarium sim using Pygame, ModernGL, PyGLM, NumPy. Entry `main.py`. Opens 1280x720 OpenGL 3.3 core window. Renders 3D fish tank: sand, rocks, coral, seaweed, fish, bubbles, glass walls, skybox, water volume fog, projected caustics, lighting, camera modes, Pygame HUD overlay.

## Commands
- Install deps: `uv sync` or `pip install -r requirements.txt`.
- Run app: `python main.py`.
- No automated test suite yet.

## Dependencies
- Runtime deps pinned in `pyproject.toml` + `requirements.txt`: `glcontext==3.0.0`, `moderngl==5.12.0`, `numpy==2.4.4`, `pygame==2.6.1`, `pyglm==2.8.3`.
- `uv.lock` exists; prefer uv when available.

## Architecture
- `main.py` owns `AquariumEngine`, window/context setup, frame loop, HUD overlay texture, lifecycle.
- `src/renderer.py` render passes: skybox first, opaque scene next, water volume overlay, transparent bubbles back-to-front, glass panels back-to-front last.
- `src/objects/scene.py` builds tank, decorations, initial fish/bubbles, runtime spawn/update.
- `src/objects/model.py` renderable models: `BaseModel`, `SolidModel`, `GlassPanel`, `SandFloor`, `Seaweed`, `Fish`, `Bubble`.
- `src/objects/skybox.py` loads cubemap faces from `assets/materials/skybox/sky_10_cubemap_2k/` and renders the background skybox.
- `src/objects/water_volume.py` renders tank-sized Beer-Lambert absorption volume.
- `src/engine/vbo.py` builds procedural meshes: skybox cube, cube, plane, sphere, cylinder, glass panel, fish body.
- `src/engine/vao.py` maps VBOs to shader programs + model VAO names.
- `src/engine/shader_program.py` loads GLSL from `shaders/`.
- `src/engine/simulation.py` stores mutable sim state: pause, wave speed, bubble count, light intensity, water preset, fish target, caustic speed.
- `src/engine/input_handler.py` routes Pygame events to camera, HUD slider, keyboard controls.
- `src/components/camera.py` supports orbit + FPS mode.
- `src/components/hud.py` draws Pygame HUD surface + handles fish target slider.
- `src/components/lighting.py` stores point light values + recomputes ambient/diffuse/specular intensity.

## Runtime Flow
1. `AquariumEngine.__init__` initializes Pygame, creates ModernGL context, enables depth/culling/blending.
2. Engine constructs `SimulationState`, `AquariumLight`, `Camera`, `Mesh`, `AquariumScene`, `InputHandler`, `AquariumRenderer`, `HUD`.
3. Each frame: `check_events()`, `update()`, `render()`, then `delta_time = clock.tick(60)`.
4. Scene update advances fish, bubbles, seaweed, enforces HUD fish target.
5. Renderer draws 3D scene; `main.py` draws HUD into RGBA texture, overlays with fullscreen triangle strip.

## Controls
- `RMB drag`: orbit rotate.
- `Scroll Wheel`: zoom.
- `MMB drag`: pan.
- `TAB`: toggle orbit/FPS camera.
- `WASD + Q/E`: move in FPS camera.
- `SHIFT`: fast FPS movement.
- `CTRL`: slow FPS movement.
- `R`: reset camera.
- `SPACE`: pause/play sim.
- `B`: spawn bubble.
- `F`: spawn fish.
- `UP/DOWN`: wave speed up/down.
- `LEFT/RIGHT`: max bubble target down/up.
- `Z/X`: light intensity down/up.
- `1/2/3`: water color preset.
- `ESC`: quit.
- HUD fish slider adjusts `app.sim.max_fish` from 0 to 16.

## Rendering Notes
- Opaque pass uses depth test + cull face.
- Skybox renders before scene with cubemap sampler and view translation stripped.
- Water volume renders as translucent tank cube with Beer-Lambert absorption tint.
- Bubble pass uses depth test + alpha blend, culling disabled.
- Glass pass uses depth test + alpha blend, `depth_func` temporarily `<=`.
- Transparent objects sorted by squared camera distance, farthest first via negative distance key.
- `_set()` in `model.py` silently skips missing shader uniforms; shared upload works across programs with different active uniforms.

## Scene Notes
- Tank half extents: `TANK_W = 5.0`, `TANK_H = 6.0`, `TANK_D = 5.0`.
- Initial scene: sand, frame cubes, 4 glass panels, rocks, coral cylinders, seaweed cylinders, gravel cubes, 5 fish, 20 bubbles.
- `SimulationState.max_fish` default 8. Scene starts 5 fish, then `_enforce_fish_target()` grows to target during updates.
- Manual fish spawn can exceed target up to `max_fish + 10`, but next update trims back to target.
- Manual bubble spawn can exceed target up to `max_bubbles + 20`.

## Shader Notes
- Shader files live in `shaders/`.
- Loaded programs: `skybox`, `water_volume`, `phong_color`, `bubble`, `glass`, `sand`, `fish`, `seaweed`.
- Opaque shaders now use projected distorted Voronoi caustics with sun spotlight fade and depth falloff.
- New renderable type usually needs VBO entry, VAO entry, shader program entry if new shader, model class or scene spawn.

## HUD Notes
- HUD renders with Pygame into RGBA surface, flips vertically, uploads to ModernGL texture, draws after 3D.
- HUD reads `app.scene.objects`, `app.camera.use_orbit`, `app.clock.get_fps()`, `app.sim`.
- HUD uses `pygame.gfxdraw` + Pygame fonts only.
- Design spec: `docs/superpowers/specs/2026-04-28-hud-feature-design.md`. Implementation richer: top bar, live counters, object list, controls, mode pill, interactive fish slider.

## Known Caveats
- `README.md` empty.
- `main.py` imports `pygame as pg` twice.
- Some comments contain Indonesian text + decorative Unicode box drawing.
- No automated tests.
- Running app needs working GPU/OpenGL context + display.
- `assets/` currently untracked in git status.

## Style
- Keep code consistent with existing direct OOP style.
- Prefer existing procedural mesh generation in `vbo.py` for simple geometry.
- Keep ModernGL state changes explicit in renderer passes.
- Avoid broad refactors unless changing shared rendering behavior.
