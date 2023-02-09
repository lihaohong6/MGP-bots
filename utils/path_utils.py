import platform
from pathlib import Path

if platform.system() == 'Windows':
    EMPTY_PATH = Path("nul")
else:
    EMPTY_PATH = Path("/dev/null")
