"""Preview wrapper for bl_client (Blender runs it, so set the shot here):  python scripts/bl_client.py scripts/pv.py"""
import os
SHOT, PCT, SAMPLES = '03_TreasureDetail', 50, 16
OUT = f'{SHOT}.png'
_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'preview.py')
exec(compile(open(_p, encoding='utf-8').read(), _p, 'exec'),
     {'__file__': _p, 'SHOT': SHOT, 'PCT': PCT, 'SAMPLES': SAMPLES, 'OUT': OUT})
