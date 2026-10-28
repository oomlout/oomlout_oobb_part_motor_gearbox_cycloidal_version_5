"""Export the saved native V7; this does not rebuild or modify the source design."""
import json
from pathlib import Path
import subprocess
import sys


def main(args=None):
    root=Path(__file__).resolve().parent
    config=json.loads((root/'solidcraft/config.json').read_text(encoding='utf-8'))
    return subprocess.call([config['python'],'-m','gearbox_native.native_exports',
                            *(sys.argv[1:] if args is None else args)],cwd=root)


if __name__=='__main__':raise SystemExit(main())
