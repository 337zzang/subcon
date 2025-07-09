"""
개발 중 실행 스크립트
"""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    # src/main.py 실행
    main_path = Path(__file__).parent / "src" / "main.py"
    subprocess.run([sys.executable, str(main_path)])
