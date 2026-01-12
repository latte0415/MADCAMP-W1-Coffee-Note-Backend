from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class Process(str, Enum):
    WASHED = "WASHED"
    NATURAL = "NATURAL"
    PULPED_NATURAL = "PULPED_NATURAL"
    HONEY = "HONEY"
    ETC = "ETC"

class RoastingPoint(str, Enum):
    LIGHT = "LIGHT"
    MEDIUM = "MEDIUM"
    MEDIUM_DARK = "MEDIUM_DARK"
    DARK = "DARK"
    ETC = "ETC"

class Method(str, Enum):
    ESPRESSO = "ESPRESSO"
    FILTER = "FILTER"
    COLD_BREW = "COLD_BREW"
    ETC = "ETC"

class ChatTest:
    class Request(BaseModel):
        message: str

    class Response(BaseModel):
        message: str

class ChatForMapping:
    class Request(BaseModel):
        message: str

    class Response(BaseModel):
        location: Optional[str] = Field(None, description="국가 및 지역 (ex1: 과테말라, ex2: 에티오피아 예가체프)")
        variety: Optional[str] = Field(None, description="원산지 품종")
        process: Optional[Process] = Field(None, description="가공 방식의 enum 값 (WASHED, NATURAL, PULPED_NATURAL, HONEY, ETC 중 하나)")
        process_text: Optional[str] = Field(None, description="가공 방식의 원문(사용자 입력에 그대로 있던 표현, 예: '워시드', '내추럴')")
        roasting_point: Optional[RoastingPoint] = Field(None, description="추출 지점의 enum 값 (LIGHT, MEDIUM, MEDIUM_DARK, DARK, ETC 중 하나)")
        roasting_point_text: Optional[str] = Field(None, description="추출 지점의 원문(사용자 입력에 그대로 있던 표현, 예: '라이트', '미디움')")
        method: Optional[Method] = Field(None, description="추출 방법의 enum 값 (ESPRESSO, FILTER, COLD_BREW, ETC 중 하나)")
        method_text: Optional[str] = Field(None, description="추출 방법의 원문(사용자 입력에 그대로 있던 표현, 예: '에스프레소', '필터')")
        tasting_notes: list[str] = Field(default=[], max_length=5, description="맛, 향 등 테이스팅 노트 (최대 5개)")

class ChatForSensoryGuide:
    class Request(BaseModel):
        message: str

    class Response(BaseModel):
        mapping_result: ChatForMapping.Response = Field(description="매핑 결과")
        sensory_guide: str = Field(description="센서리 가이드 메시지")