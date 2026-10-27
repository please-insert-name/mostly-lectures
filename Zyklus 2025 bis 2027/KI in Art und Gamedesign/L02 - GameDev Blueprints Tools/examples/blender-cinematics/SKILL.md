---
name: blender-cinematics
description: Build a cinematic 3D environment in Blender via the Blender MCP (port 9876) from a text description or reference images, review it in Creator/Reviewer cycles, and render a set of graded cinematic stills (hero shots, 2.39:1, EXR + compositor grade).
---

# Cinematics with Blender Skill
Source (Original Prompt): https://www.youtube.com/watch?v=_J3H6Lfwxu0

This version produces **cinematic stills, not video**: on modest hardware an 8 s animation (192 frames, each rendered and graded) takes hours per iteration. Stills spend that time on quality per image instead — more samples, careful light, and fast grade iterations.

## Prerequisites
- Python 3.12+ (on Windows call it as `python`, not `python3`)
- Blender 5.x (on Windows found automatically under `C:\Program Files\Blender Foundation\`; otherwise set `BLENDER`)
- MCP for Blender addon installed and registered
- Skills: grilling (grill-me)

## Task
Create a 3D environment in Blender. The Blender MCP is connected at port 9876. It is the set for a series of cinematic hero stills, so plan and optimize for the chosen camera angles: what no hero camera sees needs no detail.

## Scene
User provides a scene description in scenes.md or via prompt.

### Examples
(Example 1: Text-Description)
Create a long hospital hallway or corridor with doors on both sides. A few doors should be open, with hospital rooms and beds visible on the other side. Add appropriate corridor props such as signage, noticeboards, a nurse's station, oxygen tanks, wheelchairs, extra hospital beds, and medical trolleys. There should be a window at the end of the hallway.

(Example 2: Provide Images and Context)
Build the first-floor atrium of a company building, reconstructed from reference photos:
- Per image: estimate camera position, height, lens and direction.
- Merge all views into one plan: dimensions, structure, glazing, zones, materials, lights, props.
Reviewer should check if generated results resemble original images.

## Props
Use cinematic materials and lighting. Use Sketchfab or Poly Haven (CC0) for materials and models where it clearly helps. Otherwise procedural materials first.

## Workflow
- Use the grilling skill (if installed; otherwise ask clarifying questions directly) to get a full understanding of the scene and the expected outcome. Settle the **shot list** too: how many stills, which moments/angles, aspect ratio, day or night.
- Creator Subagent:
    - Build the scene from scratch inside Blender using only allowed props.
    - Create render images from different viewpoints. One camera per reference image (Ref_Cam_01–04).
- Reviewer Subagent:
    - Rate the render images 0–10 for (a) resemblance and (b) AAA visual quality.
    - If the best scoring result in (a) and (b) is 8 or higher, accept the result. If not, send the Creator subagent a concrete list of improvements for the next cycle.
    - Stop after at most 3 review cycles and accept the latest result.
- Add the **hero cameras** (`Hero_Cam_01_<Name>` …, static, no keyframes) with `shots.hero_camera()`, ideally in a `build_cameras.py` step. A good default set of 3–4 shots that read as a sequence:
    - **Establishing / wide** (18–28 mm, f/4–8): the whole space, strong leading lines, light source in frame.
    - **Medium** (35–50 mm, f/2.8–4): a zone or a story point, foreground element for depth.
    - **Detail / close-up** (85–135 mm, f/1.4–2): one prop, shallow depth of field, bokeh from practicals.
    - Optional **low or high angle** for drama, or an over-the-shoulder view into a room.
- Composition: rule of thirds or a deliberate centre frame, horizon level, verticals straight (keep the camera level for architecture), a clear subject, layered foreground/midground/background.
- Light each shot: small per-shot fixes are allowed (an extra bounce card or rim light visible only from that camera), because nothing has to stay consistent over time.
- Render the stills through the pipeline (see Scripts): QA gate → one linear EXR per shot → graded stills in `render/stills_cinematic/<shot>.png`.
- The Reviewer judges the graded stills (and `qa_report.md`); grade-only fixes are re-output in seconds with `--grade-only`.

## Rendering
- Use Blender EEVEE exclusively. Do not switch to Cycles.
- During modeling and look development, evaluate in the EEVEE Rendered viewport (viewport screenshots via MCP); do not launch final or full-resolution renders.
- Render only what the workflow requires: review stills (Ref_Cams, QA stills, `preview.py`), then one final EXR per hero shot.
- **Still format** (`layout.py`, defaults in `scripts/shots.py`): `STILL_RES = (1920, 804)`, 2.39:1 anamorphic widescreen; use `(1920, 1080)` for 16:9 or `(3840, 1608)` for 4K. `STILL_SAMPLES = 128`. Motion blur is off for stills.
- Depth of field is part of the look: every hero camera has DOF on with a real focus distance; check the focus plane in the preview.
- Use Material Preview or Rendered viewport shading as appropriate, with the final visual appearance evaluated in EEVEE.
- Optimize the scene for responsive viewport interaction without sacrificing the final level of detail.
- Develop professional illumination.

Daytime illumination featuring:
- Natural sunlight.
- Soft but readable shadows.
- Subtle sky illumination.
- Controlled atmospheric haze.
- High-quality reflections (e.g. metals).
- Clear separation between object layers.
- Readable cavities and recessed geometry.

Nighttime illumination featuring:
- Practical light sources as motivation (fixtures, lamps, signage, screens).
- Pools of light with deliberate falloff into darkness.
- Cool moonlight or city glow through windows as ambient fill.
- Warm/cool contrast between interior practicals and exterior light.
- Deep but not crushed blacks; shadow detail stays readable.
- Haze that catches beams and glows around sources.
- Specular highlights and glossy reflections define surfaces in the dark.
- Rim light and silhouettes separate foreground, midground and background.

In Blender (night):
- No sun; use area/spot lights matched to each emissive fixture (emission alone barely lights the scene).
- Moonlight: a weak, cool sun (≈0.05–0.2 strength, slightly blue) or area lights at the windows.
- Lower world strength to near black; dark-blue sky/city backdrop with sparse lit windows.
- Haze via a bounded volume (not a world volume), low density so beams show without fogging the frame.
- Bloom and halation in the compositor; keep exposure so practicals clip only at their cores.
- Check crushed blacks with qa_check --stills (crushed-blacks % per shot).

General:
- The lighting must help reveal construction of the objects and scene details.
- Avoid overly dark recesses that conceal important details.
- Maintain coherent lighting during the modeling process.
- Gradually improve the materials and lighting as the project progresses.

## Troubleshooting
Some construction issues can cause problems in rendering:
- avoid x/y/z-fighting between coincident surfaces (shows as noisy, striped surfaces)
- presence of world volume completely blocks the sun in EEVEE
- Glass must have shadow casting off for not blocking sunlight
- Normal maps need UVs. Check: Flag image textures on meshes without UVs, or require world-space projection
- Grain direction set per object in the material may cause e.g. wood grain running in the wrong direction
- Use world coordinates for anything that has to line up across objects in order to avoid misalignment

## Post-Processing
Create a cinematic look with Blender's compositor — the full grade applies to stills exactly as it would to a film frame:
- Render each shot once to a linear multilayer EXR (`render/exr/<shot>.exr`, compositing off).
- `build_grade.py` builds the compositing-only scene `Grade_Cinematic`: teal-and-orange Lift/Gamma/Gain grade, Sun Beams glare from the window, subtle streaks on the brightest lights, halation, bloom, chromatic dispersion, vignette, film grain, and a slight desaturation (saturation 0.3 ≈ 70 % desaturated).
- The base look lives in `GRADE`; per-shot adjustments go in `layout.SHOT_GRADE`. Each shot needs its own sun-beam position on the window (`sunbeams=dict(pos=(x, y))` in 0–1 frame coordinates), or `sunbeams=None` when no window is in frame. Any effect can be set to `None`.
- Grain is static per shot (seeded by the shot name), so a re-grade gives the identical grain.
- Iterate on the grade with `render_stills.py <blend> --grade-only [--shots …]` (seconds per still, no 3D render). Output: 16-bit PNG in `render/stills_cinematic/`.

## Credits
Create a credits.md file with the applications and services used in the process. Also when using assets with cc-by or comparable license, state the creator here.

---

## Scripts
Copy `scripts/` into `<project>/scripts/`. Every script finds the project root as the parent of its own folder and has no hard-coded paths. Paths below are relative to this skill folder.

| Script | Purpose |
|---|---|
| `scripts/bl_client.py` | Talks to the BlenderMCP socket: `python bl_client.py file.py` runs a script inside the open Blender, `info` prints a scene summary, `cmd TYPE [JSON]` sends any addon command (e.g. `cmd get_polyhaven_status`). It injects `__file__` into executed scripts. |
| `scripts/lib.py` | Primitives (box, cylinder, torus, tube, rods, text, prism), collection instances, and a procedural material library. `FLOOR_STYLE`/`FLOOR_TEX` switch to Poly Haven maps projected in world space. |
| `scripts/shots.py` | Hero shots: `hero_camera(name, loc, target, lens, fstop, focus)` creates a static DOF camera; `hero_cameras()` lists the shots (`Hero_Cam_*` or `layout.SHOTS`); `STILL_RES` / `STILL_SAMPLES` from `layout.py`. |
| `scripts/build_comp.py` | Light compositor finish for the main scene (look-dev previews): bloom, dispersion, vignette. |
| `scripts/build_grade.py` | Compositing-only scene `Grade_Cinematic` that reads one shot's EXR. All parameters live in `GRADE`, per-shot overrides in `layout.SHOT_GRADE`. |
| `scripts/render_exr_setup.py` | Renders one linear multilayer EXR per hero shot (`-- shot …` for a subset) with compositing off. It asserts the format and renders from inside the script, so a setup error can't fall through to a wrong render. |
| `scripts/render_grade.py` | Grades every EXR (or `-- shot …`) to `render/stills_cinematic/<shot>.png`. |
| `scripts/render_stills.py` | Full pipeline, cross-platform, run with the system Python: QA gate → EXRs → graded stills. `--shots` limits it, `--grade-only` skips QA and 3D render. |
| `scripts/build_all_bg.py` | Headless rebuild and save: `blender -b scene.blend --python scripts/build_all_bg.py [-- steps…]`. |
| `scripts/qa_check.py` | Automatic QA (see below). It writes `previews/qa/qa_report.md` and exits with code 1 on FAIL. |
| `scripts/preview.py` | Low-res still of one shot via the socket (set `SHOT`, `PCT`, `SAMPLES`, `OUT` before it), at the final aspect ratio. |

```bash
python scripts/render_stills.py scene.blend
python scripts/render_stills.py scene.blend --shots 02_Medium
python scripts/render_stills.py scene.blend --grade-only
```

**Worked example:** `examples/hospital_corridor/` holds the complete hospital build. It was made for the earlier video version of this skill (animated push-in camera, flickering panel, `frames_*` sequences), so its own scripts still contain that; use it for the scene structure, not for the render pipeline. It has `layout.py` as the single source of truth plus the build steps `build_arch` → `build_templates` → `build_props` → `build_lighting` → `build_comp` → `build_grade`, and a README covering the layout, lighting, camera and grade. Start new scenes from this structure, replace the push-in camera block in `build_lighting` with a `build_cameras.py` of hero cameras, and use the generic `scripts/` of this skill for QA and rendering. Props are templates under `_Templates`, which is excluded from the view layer and placed as collection instances. Wall-side props go through `place_wall()`, which uses their real footprint to keep clear of the handrail.

## QA (run after every build; no render while anything FAILs)
```bash
blender -b scene.blend --python scripts/qa_check.py -- --stills --templates
```
- **Geometry:** coplanar overlapping faces (≤ 3 mm, z-fighting); props intersecting walls, trim or furniture; text inside mirrored (negative-scale) instances; clip range of every hero camera.
- **Materials:** missing texture files; UV-driven image textures on meshes without UVs.
- **Lighting:** a world volume together with a sun in EEVEE; transparent glass casting shadows; shadow pool too small for the number of shadowed lights.
- **Shots:** at least one hero camera, none animated, unique shot names, `SHOT_GRADE` entries match real shots, scenes write to separate output folders; warnings in render logs.
- **Review material:** `--stills` renders every hero shot at 50 % with clipped-highlight and crushed-black stats; `--templates` renders a close-up of every prop template.
- **Per-project overrides** in `layout.py`: `SHOTS`, `STILL_RES`, `STILL_SAMPLES`, `SHOT_GRADE`, `QA_STATIC_PREFIXES`, `QA_PROP_COLLECTIONS`, `QA_ZF_ALLOW`, `QA_COL_ALLOW`.

The Reviewer gets `qa_report.md`, the QA stills, the template close-ups and the graded stills as input.

## Pipeline lessons (Blender 5.x)
- **Multilayer EXR:** set `image_settings.media_type = 'MULTI_LAYER_IMAGE'` and nothing else; assigning `file_format` afterwards fails. Always assert render settings, because a failed setting silently falls back to PNG in the default folder.
- **Compositor:** it's a node group on `scene.compositing_node_group` with a Group Output. An Ellipse Mask needs an image-sized input to get a canvas.
- **Shadows:** with many shadowed lights, set `scene.eevee.shadow_pool_size = '1024'` and watch logs for "Shadow buffer full".
- **Render headless** (`blender -b`), not in the UI. Save after every build step so the scene is always rebuildable from scripts.
- **One output folder per version** (`stills_cinematic`, `stills_v2`, …), and check that every shot has an EXR and a graded still.
- **Windows:** read scripts as UTF-8 (`open(path, encoding='utf-8')`); the scripts contain characters such as `≤` that break the default code page.
- **Geometry:** text and decals sit at least 4 mm off their backing; frame pieces use butt joints rather than overlaps; camera `clip_start` ≥ 0.1 m for depth precision.
- **Long surfaces:** add large-scale variation over any tiling texture to hide the repeat.
