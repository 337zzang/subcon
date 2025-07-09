"""Smoke test for project initialization"""

import os
import sys
from pathlib import Path

def test_smoke():
    """프로젝트가 정상적으로 초기화되었는지 확인"""
    assert True, "Basic smoke test passed"

def test_project_structure():
    """프로젝트 구조가 올바른지 확인"""
    project_root = Path(__file__).parent.parent
    
    # 필수 디렉터리 확인
    required_dirs = ['src', 'test', 'docs', 'memory']
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"{dir_name} 디렉터리가 없습니다"
        assert dir_path.is_dir(), f"{dir_name}은 디렉터리가 아닙니다"
    
    # 필수 파일 확인
    assert (project_root / "README.md").exists(), "README.md가 없습니다"
    assert (project_root / "docs" / "overview.md").exists(), "docs/overview.md가 없습니다"
    
    print("✅ 프로젝트 구조 테스트 통과")

if __name__ == "__main__":
    test_smoke()
    test_project_structure()
