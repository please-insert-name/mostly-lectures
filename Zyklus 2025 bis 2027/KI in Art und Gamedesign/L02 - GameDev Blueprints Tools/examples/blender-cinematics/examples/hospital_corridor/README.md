# Hospital Corridor – cinematic environment (Blender 5.1)

Everything is procedural and built from scratch by the scripts in `scripts/`, except the v2 floor.
The v2 floor uses the CC0 Poly Haven texture **Terrazzo Tiles** by Amal Kumar (https://polyhaven.com/a/terrazzo_tiles).
Its 2K maps are in `textures/polyhaven/` and packed into the .blend.

## Files
- `hospital_corridor.blend`: the environment, camera animation, lighting and render settings
- `render/hospital_corridor_pushin.mp4`: v1, 8 s shot with the procedural vinyl floor (1920×1080, 24 fps, H.264)
- `render/hospital_corridor_pushin_v2.mp4`: v2, the same shot with the Poly Haven terrazzo floor
- `render/hospital_corridor_pushin_v3.mp4`: v3, the v2 shot with the cinematic grade
- `render/exr/`: linear multilayer EXR renders (16-bit half, DWAA), the input for grading in Blender or DaVinci Resolve
- `render/frames/`, `render/frames_v2/`, `render/frames_v3/`: the PNG frame sequences
- `previews/`: look-dev stills

## Scene layout (metres, +Y runs down the corridor)
- Corridor: 3 m wide, 2.8 m ceiling, 37 m long; end wall window at y = 34 with venetian blinds
- Doors: 9 doors (402–411). Rooms 403, 404 and 408 are open and room 409 is ajar, with a furnished patient room behind each
- Nurse station: recess on the right at y 12.5–16.5 with a counter, monitors, a patient whiteboard, binders, a clock and chairs
- Props: spare beds, wheelchairs, an oxygen cart and rack, a crash cart, a med cart, a supply trolley, IV poles, a vitals stand,
  a wet-floor sign, noticeboards, sanitizers, extinguishers, plants, waiting chairs, hanging signs, a green EXIT sign

## Optimisation for animation work
- Repeated props are **collection instances** of templates under `_Templates`, which is excluded from the view layer.
  To change every wheelchair, bed, door or patient room at once, edit its `T_*` collection.
- Collections are split by department: `01_Architecture` … `07_Camera`.
- Haze is a bounded `Haze_Volume` box rather than a world volume. A world volume extinguishes sun lights in EEVEE.
- EEVEE settings: ray tracing, fast GI, volumetric shadows, 64 samples, motion blur, a 1 GB shadow pool.
  A frame renders in about 13 s on an M1 Pro.

## Floor material
`scripts/lib.py` → `FLOOR_STYLE` switches between `'polyhaven'` (terrazzo) and `'procedural'` (the original vinyl).
`FLOOR_TEX` sets the tone: saturation 0.35 and value 1.6 give a cool grey. Try saturation 0.85 and value 1.45 for the warm natural tone.
The floor boxes have no UVs, so the maps are projected top-down in world space at the real 2 m scale. The grout and micro-relief
come from bump on the displacement map. A tangent-space normal map would need UVs.

## Quality checks (run after every build)
```bash
/Applications/Blender.app/Contents/MacOS/Blender -b hospital_corridor.blend --python scripts/qa_check.py -- --stills --templates --flicker render/frames_v3
```
The script writes `previews/qa/qa_report.md`, the Reviewer's input, and exits with code 1 on any FAIL, so the render waits until QA passes.

| Check | Catches |
|---|---|
| Coplanar overlapping faces (≤ 3 mm) | z-fighting / flicker. Faces pressed against walls and reviewed same-material joints are skipped. |
| Prop vs wall/trim/furniture intersections | props pushed into handrails or walls, items through the counter |
| Text in mirrored instances | backwards signage |
| Camera clip range | poor depth precision in the distance |
| Textures | missing files; UV-driven images on meshes without UVs |
| Lighting | world volume + sun (EEVEE extinguishes the sun), transparent glass casting shadows, shadow pool too small |
| Render settings | resolution, fps, frame range, animated camera, scenes writing to the same output folder |
| Render logs | "Shadow buffer full", tracebacks, silent setting failures |
| `--stills` | start/mid/end composition frames, clipped highlights and crushed blacks |
| `--templates` | close-up render of every prop template (hidden or broken detail) |
| `--flicker DIR` | one-frame flicker spikes in the rendered sequence (panel 08's intentional flicker is excluded via `layout.FLICKER_PATTERN`) |

Rules the checks enforce:
- Text and decals sit at least 4 mm off their backing.
- Wall-side props use `place_wall()`, which keeps 1.5 cm clear of the handrail.
- Transparent items don't cast shadows.
- Each version renders into its own folder.

## Lighting
- Cool fluorescent ceiling panels with a deliberate on/off rhythm. Panel 08 flickers (keyed, constant interpolation).
- A golden-hour sun (`Sun_Golden_Hour`) through the end window, plus `Window_Skyfill`, gives warm light shafts in the haze.
- Warm practicals: the nurse station ceiling light, a desk lamp, an LED strip, and reading lights in the rooms.
- Compositor (`Cinematic_Comp`): bloom, slight lens dispersion and a soft vignette. AgX view with the Medium High Contrast look.

## Cinematic grade (v3)
`scripts/build_grade.py` builds a compositing-only scene, `Grade_v3`, that reads the EXR sequence. Re-grading takes
about 1.5 s per frame and doesn't re-render the 3D scene. All parameters live in the `GRADE` dict at the top of the script:
- Light effects: bloom, warm halation (a tinted wide bloom), subtle 4-point streaks on the brightest lights,
  and warm sun beams from the window (masked to the glass so the EXIT sign doesn't streak)
- Lens: chromatic dispersion
- Grade: Lift/Gamma/Gain (teal shadows, warm highlights), about 70% desaturation (saturation 0.3), exposure −0.08
- Finish: blurred-ellipse vignette and animated multiplicative film grain (white noise seeded by the frame number)

## Camera
`Cinematic_Camera`: 30 mm, f/2.2, focusing on `Camera_Focus_Target`. A slow push-in from y 0.6 to y 4.4 over frames 1–192,
with gently eased Bezier handles.

## Rebuild / re-render
With Blender open and the BlenderMCP addon listening on port 9876:
```bash
scripts/build_all.sh
```
Or headless, without the UI, which also saves the file:
```bash
/Applications/Blender.app/Contents/MacOS/Blender -b hospital_corridor.blend --python scripts/build_all_bg.py
```
Geometry rule: surfaces must never be coplanar. Door linings sit 8 mm proud of the wall reveal, and adjoining boxes meet
edge to edge instead of overlapping. Coincident faces z-fight, which shows up as flicker in the animation.
Render and encode:
```bash
/Applications/Blender.app/Contents/MacOS/Blender -b hospital_corridor.blend -o //render/frames_v2/frame_ -a
ffmpeg -framerate 24 -i render/frames_v2/frame_%04d.png -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart render/hospital_corridor_pushin_v2.mp4
```
v3: render the linear EXRs once (compositing off), then output the grade:
```bash
/Applications/Blender.app/Contents/MacOS/Blender -b hospital_corridor.blend --python-exit-code 1 --python scripts/render_exr_setup.py
/Applications/Blender.app/Contents/MacOS/Blender -b hospital_corridor.blend -S Grade_v3 -a
ffmpeg -framerate 24 -i render/frames_v3/frame_%04d.png -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart render/hospital_corridor_pushin_v3.mp4
```
