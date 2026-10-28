"""Update from shared JSON controls, or saved native master parameters."""
import json,subprocess,sys
from pathlib import Path
if __name__=='__main__':
    root=Path(__file__).resolve().parent
    config=json.loads((root/'solidcraft/config.json').read_text(encoding='utf-8'))
    raise SystemExit(subprocess.call([config['python'],'-m','gearbox_native.configurator',*sys.argv[1:]],cwd=root))
