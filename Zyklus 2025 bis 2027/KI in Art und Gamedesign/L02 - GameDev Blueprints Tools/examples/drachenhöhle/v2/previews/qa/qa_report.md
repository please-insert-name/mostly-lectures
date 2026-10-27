# QA report: dragon_cave.blend

| Status | Check |
|---|---|
| PASS | Coplanar overlapping faces (z-fighting), gap ≤ 3 mm: 0 pairs |
| PASS | Props intersecting walls / trim / furniture: 0 |
| PASS | Text inside negatively scaled (mirrored) instances |
| PASS | Hero camera depth precision (keep clip ratio ≤ 5000, start ≥ 0.1) |
| PASS | Textures: files present, UV-driven images only on UV-mapped meshes |
| PASS | Lighting setup (world volume vs sun, glass shadows, shadow pool) |
| PASS | Shots: 4 static hero cameras, separate outputs (stills render at 1920×804, 96 samples) |
| PASS | Render logs free of warnings/errors |

## PASS: Hero camera depth precision (keep clip ratio ≤ 5000, start ≥ 0.1)
- Hero_Cam_01_Wide: clip 0.1–200 m (ratio 2000)
- Hero_Cam_02_DragonHead: clip 0.1–200 m (ratio 2000)
- Hero_Cam_03_TreasureDetail: clip 0.1–200 m (ratio 2000)
- Hero_Cam_04_LowAngle: clip 0.1–200 m (ratio 2000)

## PASS: Lighting setup (world volume vs sun, glass shadows, shadow pool)
- 2 shadow-casting lights, shadow pool 1024 MB
