"""Run the self-contained gold research desk."""
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from desk_core.cli import main
if __name__=="__main__":
    raise SystemExit(main('gold'))
