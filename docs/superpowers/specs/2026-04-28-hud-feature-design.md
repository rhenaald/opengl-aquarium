# HUD Feature Design Spec

## Overview
Add a simple but modern-feeling HUD overlay to the aquarium OpenGL app. The HUD displays real-time object counts and types, plus basic camera controls, using semi-transparent panels with rounded corners and subtle gradients for a clean, sci-fi aesthetic.

## Requirements
- **Object Info**: Show types and counts (e.g., Fish: 5, Bubbles: 10, Rocks: 3).
- **Controls**: Display basic camera interactions (orbit via RMB drag, zoom via scroll, pan via MMB).
- **Modern Feel**: Semi-transparent backgrounds, rounded panels, teal accents – no clutter.
- **Simplicity**: Lightweight, no animations or interactivity beyond display.

## Architecture
- New `HUD` class in `src/components/hud.py`.
- Instantiated in `main.py` alongside other components.
- Renders to Pygame surface after 3D scene, using RGBA for transparency.
- No external dependencies beyond Pygame.

## Components
- **Top Bar**: Engine name, camera mode (Orbit/Free), FPS.
- **Object Panel (Bottom-Left)**: Bullet-pointed list of object types/counts.
- **Controls Panel (Bottom-Right)**: Text descriptions of camera controls with icons.
- Color palette: Dark backgrounds (RGBA), teal highlights.

## Data Flow
- Collects data from `app.scene.objects` (via property), `app.camera.use_orbit`, `app.clock.get_fps()`.
- Renders to `screenHUD` surface, blits to main screen post-3D.
- Real-time updates, cached where possible.

## Error Handling
- Empty panel if `scene.objects` unavailable ("Loading...").
- Font fallback to default monospace.
- Skip rendering on surface errors, log warnings.

## Testing
- Manual: Verify appearance, counts, transparency, readability.
- Performance: <1ms/frame render time.
- Edge cases: 0 objects, max objects, font failures, resize.

## Implementation Notes
- Use Pygame's `Surface` with `SRCALPHA`, `draw_rounded_rect` for panels.
- Integrate with existing render loop in `main.py`.