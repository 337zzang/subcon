"""
기본 데이터 모델 클래스
"""
from typing import Any, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
import json

class BaseModel:
    """모든 모델의 기본 클래스"""
    
    def __init__(self):
        self.created_at: datetime = datetime.now()
        self.updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """모델을 딕셔너리로 변환"""
        if hasattr(self, '__dataclass_fields__'):
            return asdict(self)
        else:
            # dataclass가 아닌 경우 수동 변환
            result = {}
            for key, value in self.__dict__.items():
                if not key.startswith('_'):
                    result[key] = value
            return result
    
    def to_json(self) -> str:
        """모델을 JSON 문자열로 변환"""
        data = self.to_dict()
        # datetime 객체 처리
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return json.dumps(data, ensure_ascii=False)
    
    def update(self, **kwargs):
        """모델 필드 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
