#!/bin/zsh
# Rebuild the whole scene inside the running Blender (addon socket on :9876)
cd "$(dirname "$0")"
for f in build_arch.py build_templates.py build_props.py build_lighting.py build_comp.py build_grade.py; do
  python3 bl_client.py $f || exit 1
done
