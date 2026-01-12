# LangChain 답변 형식 강제 마이그레이션 가이드

이 문서는 LangChain을 사용하여 LLM 응답 형식을 강제하는 방법을 설명합니다.

## 개요

LangChain에서 LLM의 응답 형식을 강제하려면 `PydanticOutputParser`를 사용하여 Pydantic 모델을 기반으로 출력 스키마를 정의하고, 이를 체인에 통합해야 합니다.

## 사전 요구사항

### 1. 필수 패키지 설치

다음 패키지들이 설치되어 있어야 합니다:

```bash
pip install langchain==0.3.25
pip install langchain-core==0.3.64
pip install langchain-openai==0.3.21
pip install pydantic==2.11.5
pip install pydantic-settings==2.9.1
```

또는 `requirements.txt` 파일에 추가 후:

```bash
pip install -r requirements.txt
```

**중요:** LangChain 0.3.x 버전을 사용합니다. 버전에 따라 import 경로가 다를 수 있습니다.

### 2. 환경 변수 설정

`.env` 파일에 다음 환경 변수를 설정합니다:

```env
# OpenAI API 키 (필수)
OPENAI_API_KEY=your_openai_api_key_here

# LangChain Tracing (선택사항, 디버깅용)
LANGCHAIN_API_KEY=your_langchain_api_key_here
LANGCHAIN_TRACING=false
```

**참고:** `LANGCHAIN_TRACING`은 LangSmith 트래킹을 활성화하는 옵션입니다. 디버깅이 필요할 때만 `true`로 설정합니다.

## 핵심 개념

1. **Pydantic 모델**: 응답 형식을 정의하는 Pydantic BaseModel
2. **PydanticOutputParser**: Pydantic 모델을 기반으로 LLM 출력을 파싱하는 파서
3. **Format Instructions**: LLM에게 전달할 자동 생성된 형식 지침
4. **Chain 구성**: Prompt → LLM → Parser 순서로 구성

## 단계별 구현 방법

### 1. Pydantic 모델 정의

응답 형식을 정의하는 Pydantic 모델을 생성합니다.

```python
from pydantic import BaseModel, Field

class NutritionLog(BaseModel):
    """영양 추정 결과"""
    name: str = Field(..., description="입력된 음식 이름")
    parsed_name: str = Field(..., description="표준화된 음식 이름")
    amount: int = Field(..., description="섭취량 (숫자)")
    unit: str = Field(..., description="섭취 단위 (예: g, ml)")
    calories: int = Field(..., description="총 열량 (kcal)")
    nutritions: Nutrition = Field(
        ..., description="영양소 정보 (단백질, 지방, 탄수화물, 당류)"
    )

class NutritionLogList(BaseModel):
    """NutritionLog 리스트 래퍼"""
    logs: list[NutritionLog] = Field(..., description="영양 추정 결과 리스트")
```

**주요 포인트:**
- `Field`의 `description`은 LLM이 각 필드를 이해하는 데 도움이 되므로 상세하게 작성
- 중첩된 모델도 지원 (예: `Nutrition` 모델 사용)
- 리스트나 옵셔널 필드도 지원

### 2. Parser 생성 및 등록

`PydanticOutputParser`를 사용하여 파서를 생성하고, label별로 매핑합니다.

```python
from langchain.output_parsers import PydanticOutputParser
from src.domain.models.nutrition import NutritionLogList

# Label별 매핑
parser_map = {
    "nutrition_estimator": PydanticOutputParser(pydantic_object=NutritionLogList),
    # 다른 parser들도 추가 가능
    # "message_classify": PydanticOutputParser(pydantic_object=MessageClassifyResponse),
}

def get_parser(label: str):
    """
    Label에 해당하는 parser를 반환합니다.
    
    Args:
        label: parser를 식별하는 문자열
        
    Returns:
        PydanticOutputParser 또는 None (parser가 없을 경우)
    """
    return parser_map.get(label)
```

**주요 포인트:**
- `pydantic_object`에 정의한 Pydantic 모델 전달
- Label 기반으로 여러 파서를 관리할 수 있음
- `get_parser()`가 `None`을 반환하면 parser 없이 실행 (일반 문자열 응답)

### 3. LLM 초기화 함수 구현

LLM을 초기화하는 함수를 구현합니다. (선택사항이지만 권장)

```python
# core/external/langchain/config.py 또는 적절한 위치
from langchain.callbacks import StdOutCallbackHandler
from langchain.globals import set_verbose
from langchain_openai import ChatOpenAI
import os

# 환경 변수에서 API 키 읽기 (또는 설정 파일에서)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGCHAIN_TRACING = os.getenv("LANGCHAIN_TRACING", "false").lower() == "true"

# LangSmith 트래킹 활성화 (선택사항)
if LANGCHAIN_TRACING:
    set_verbose(True)

callback_handler = StdOutCallbackHandler()

def get_llm():
    """
    ChatOpenAI 모델을 초기화하고 반환합니다.
    
    Returns:
        ChatOpenAI: 초기화된 LLM 인스턴스
    """
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model_name="gpt-4-turbo",  # 또는 "gpt-3.5-turbo", "gpt-4o" 등
        temperature=0.7,
        max_tokens=2048,
        timeout=30,
        max_retries=2,
        callbacks=[callback_handler],
    )
    return llm
```

### 4. 프롬프트 로딩 함수 구현

프롬프트를 파일에서 로드하는 함수를 구현합니다. (선택사항이지만 권장)

```python
# infra/langchain/prompts/__init__.py 또는 적절한 위치
import os

_PROMPT_DIR = os.path.dirname(__file__)
_PROMPT_CACHE = {}

def get_prompt(category: str, name: str) -> str:
    """
    prompts/{category}/{name}.txt 파일을 불러와 캐시하고 반환합니다.
    
    Args:
        category: 프롬프트 종류 (예: "system", "human")
        name: 텍스트 파일 이름 (확장자 제외)
        
    Returns:
        str: 텍스트 파일 내용
        
    Raises:
        FileNotFoundError: 파일이 존재하지 않을 경우
    """
    key = f"{category}/{name}"
    if key in _PROMPT_CACHE:
        return _PROMPT_CACHE[key]
    
    path = os.path.join(_PROMPT_DIR, category, f"{name}.txt")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Prompt '{name}' does not exist at {path}")
    
    with open(path, encoding="utf-8") as file:
        content = file.read()
        _PROMPT_CACHE[key] = content
        return content
```

**프롬프트 파일 구조 예시:**
```
infra/langchain/prompts/
├── system/
│   └── nutrition_estimator.txt
└── human/
    └── nutrition_estimator.txt
```

### 5. Chain 구성

프롬프트, LLM, 파서를 순서대로 연결하여 체인을 구성합니다.

```python
from typing import Any
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import Runnable

def get_chain(input_variables: dict[str, Any], label: str) -> Runnable:
    """
    Label에 해당하는 체인을 구성합니다.
    
    Args:
        input_variables: 프롬프트에 전달할 변수들
        label: 체인을 식별하는 문자열
        
    Returns:
        Runnable: 구성된 체인
    """
    llm = get_llm()
    parser: PydanticOutputParser | None = get_parser(label)
    
    system_prompt = get_prompt("system", label)
    human_prompt = get_prompt("human", label)
    
    if parser:
        # Format instructions 자동 생성
        format_instructions = parser.get_format_instructions()
        
        # 프롬프트 템플릿에서 사용하는 중괄호와 충돌 방지를 위한 이스케이프
        # 중요: 이스케이프를 반드시 해야 함!
        escaped_format = format_instructions.replace("{", "{{").replace("}", "}}")
        
        # System 프롬프트에 format instructions 추가
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt + "\n\n" + escaped_format),
                ("human", human_prompt),
            ]
        )
        # Chain 구성: Prompt → LLM → Parser
        return prompt | llm | parser
    else:
        # Parser가 없으면 일반 체인
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", human_prompt),
            ]
        )
        return prompt | llm
```

**핵심 구현 사항:**
- `parser.get_format_instructions()`: Pydantic 모델 기반으로 자동 생성된 형식 지침
- 중괄호 이스케이프: `{{`와 `}}`로 변환하여 프롬프트 템플릿 변수와 충돌 방지
- Chain 구성: `prompt | llm | parser` 순서로 연결 (LangChain의 파이프 연산자 사용)
- `input_variables` 매개변수는 함수 시그니처에 포함하지만 실제로는 `run_chain`에서 사용

### 6. Runnable 실행 함수 구현

체인을 비동기로 실행하는 함수를 구현합니다. 재시도 로직 포함을 권장합니다.

```python
# infra/langchain/executors/executor.py 또는 적절한 위치
import asyncio
import time
from typing import Any
from langchain_core.runnables import Runnable

# 재시도 설정
MAX_RETRIES = 3
DELAY = 0.5
TIMEOUT_SECONDS = 30.0

async def ainvoke_runnable(
    chain: Runnable,
    variables: dict[str, Any],
    step_label: str = "",
    config: dict[str, Any] | None = None,
) -> tuple[Any | None, str | None]:
    """
    Runnable을 비동기적으로 실행하며, 재시도 옵션을 지원합니다.
    
    Args:
        chain: 실행할 LangChain Runnable 객체
        variables: 체인에 전달할 입력 변수
        step_label: 현재 단계의 라벨 (디버깅용)
        config: 체인 실행 설정 (timeout 등)
        
    Returns:
        Tuple[Optional[Any], Optional[str]]: 
            성공 시 (결과, None), 실패 시 (None, 에러 메시지)
    """
    last_error = None
    start = time.time()
    
    # 기본 설정 병합
    merged_config = {"timeout": TIMEOUT_SECONDS, **(config or {})}
    
    for attempt in range(MAX_RETRIES):
        try:
            # 체인 실행
            response = await chain.ainvoke(variables, config=merged_config)
            
            # 응답 타입에 따라 content 추출
            if hasattr(response, "content"):
                content = response.content
            elif isinstance(response, dict):
                content = response.get("output", None)
            else:
                # Pydantic 모델 등 직접 반환된 경우
                content = response
            
            elapsed = time.time() - start
            print(f"🔄 LLM 응답 시간: {elapsed:.2f}초")
            
            return content, None
            
        except Exception as e:
            last_error = f"[{step_label}] invoke 에러 (시도 {attempt + 1}/{MAX_RETRIES}): {e!s}"
            print(last_error)
            
            # 마지막 시도가 아니면 대기
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(DELAY)
    
    # 모든 재시도 실패
    elapsed = time.time() - start
    print(f"🔄 LLM 응답 시간: {elapsed:.2f}초 (실패)")
    return None, last_error
```

### 7. Chain 실행 래퍼 함수

체인 생성과 실행을 함께 처리하는 래퍼 함수를 구현합니다.

```python
# infra/langchain/runnables/chains.py
from typing import Any
from infra.langchain.executors.executor import ainvoke_runnable
from infra.langchain.runnables.chains import get_chain

async def run_chain(
    input_variables: dict[str, Any],
    label: str,
) -> tuple[bool, Any | None]:
    """
    체인을 생성하고 실행합니다.
    
    Args:
        input_variables: 프롬프트에 전달할 변수들
        label: 체인을 식별하는 문자열
        
    Returns:
        Tuple[bool, Optional[Any]]: 
            (에러 여부, 파싱된 결과)
            - 에러가 있으면: (True, None)
            - 성공하면: (False, 파싱된 Pydantic 모델 인스턴스)
    """
    # RunnableSequence 구성
    sequence = get_chain(input_variables=input_variables, label=label)
    
    # 체인 실행
    result, error = await ainvoke_runnable(
        chain=sequence,
        variables=input_variables,
        step_label=label
    )
    
    if error:
        return True, None
    
    return False, result
```

### 8. 서비스에서 사용

서비스 레이어에서 체인을 실행하고 결과를 사용합니다.

```python
async def estimate_nutritions(
    self, meal_list: list[str], note: str
) -> list[NutritionLog]:
    """영양 정보를 추정합니다."""
    input_variables = {
        "meal_list": meal_list,
        "note": note,
    }
    
    error, result = await run_chain(
        input_variables=input_variables,
        label="nutrition_estimator",  # parser_map에 등록된 label
    )
    
    if error or not result:
        raise ValueError("영양 정보 추정 실패")
    
    try:
        # result는 이미 파싱된 Pydantic 모델 인스턴스
        parsed: list[NutritionLog] = result.logs
        return parsed
    except Exception as e:
        raise ValueError(f"응답 파싱 실패: {e}") from e
```

**주요 포인트:**
- `result`는 이미 파싱된 Pydantic 모델 인스턴스입니다
- `result.logs`처럼 모델의 필드에 직접 접근 가능
- 파싱 실패 시 예외가 발생하므로 에러 핸들링 필요

## 완전한 실행 예제

### 최소 실행 가능한 예제

아래 예제는 바로 실행 가능한 최소 구현입니다:

```python
# 1. 환경 변수 설정 (.env 파일 또는 직접 설정)
import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

# 2. 도메인 모델 정의
from pydantic import BaseModel, Field

class Nutrition(BaseModel):
    protein: int = Field(..., description="단백질 (g)")
    fat: int = Field(..., description="지방 (g)")
    carbs: int = Field(..., description="탄수화물 (g)")
    sugar: int = Field(..., description="당류 (g)")

class NutritionLog(BaseModel):
    name: str = Field(..., description="입력된 음식 이름")
    parsed_name: str = Field(..., description="표준화된 음식 이름")
    amount: int = Field(..., description="섭취량 (숫자)")
    unit: str = Field(..., description="섭취 단위 (예: g, ml)")
    calories: int = Field(..., description="총 열량 (kcal)")
    nutritions: Nutrition = Field(..., description="영양소 정보")

class NutritionLogList(BaseModel):
    logs: list[NutritionLog] = Field(..., description="영양 추정 결과 리스트")

# 3. Parser 등록
from langchain.output_parsers import PydanticOutputParser

parser_map = {
    "nutrition_estimator": PydanticOutputParser(pydantic_object=NutritionLogList),
}

def get_parser(label: str):
    return parser_map.get(label)

# 4. LLM 초기화
from langchain_openai import ChatOpenAI

def get_llm():
    return ChatOpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4-turbo",
        temperature=0.7,
    )

# 5. 프롬프트 정의 (파일 대신 직접 문자열 사용 가능)
def get_prompt(category: str, name: str) -> str:
    prompts = {
        "system/nutrition_estimator": """너는 여러 음식에 대한 영양 정보를 정확한 근거를 가지고 추론할 수 있어.
사용자가 식사 내용으로 입력한 내용을 요청한 출력 형식에 맞게 변환해줘.

제약 조건:
- 영양 성분은 사용자의 입력 내용을 바탕으로 충분한 근거를 가지고 추측할 것
- 칼로리는 kcal 단위로 작성할 것
- 양은 가능하면 g, ml 단위를 사용할 것
- 탄수화물, 단백질, 지방, 당류는 g 단위로 작성할 것
- 주어진 출력 형식에 맞춰서 해당 내용만 출력할 것""",
        "human/nutrition_estimator": """#입력 데이터
{meal_list}

#비고
{note}"""
    }
    return prompts.get(f"{category}/{name}", "")

# 6. Chain 구성
from typing import Any
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import Runnable

def get_chain(input_variables: dict[str, Any], label: str) -> Runnable:
    llm = get_llm()
    parser = get_parser(label)
    
    system_prompt = get_prompt("system", label)
    human_prompt = get_prompt("human", label)
    
    if parser:
        format_instructions = parser.get_format_instructions()
        escaped_format = format_instructions.replace("{", "{{").replace("}", "}}")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt + "\n\n" + escaped_format),
            ("human", human_prompt),
        ])
        return prompt | llm | parser
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt),
        ])
        return prompt | llm

# 7. 실행 함수
async def run_chain(input_variables: dict[str, Any], label: str):
    sequence = get_chain(input_variables=input_variables, label=label)
    result = await sequence.ainvoke(input_variables)
    return result

# 8. 사용 예제
import asyncio

async def main():
    input_variables = {
        "meal_list": ["김치찌개", "공기밥"],
        "note": "점심 식사"
    }
    
    result = await run_chain(input_variables, "nutrition_estimator")
    print(result.logs)  # 파싱된 NutritionLog 리스트

# 실행
# asyncio.run(main())
```

## 전체 예제 (프로젝트 구조 기준)

### 도메인 모델 (`domain/models/nutrition.py`)

```python
from pydantic import BaseModel, Field

class Nutrition(BaseModel):
    protein: int = Field(..., description="단백질 (g)")
    fat: int = Field(..., description="지방 (g)")
    carbs: int = Field(..., description="탄수화물 (g)")
    sugar: int = Field(..., description="당류 (g)")

class NutritionLog(BaseModel):
    name: str = Field(..., description="입력된 음식 이름")
    parsed_name: str = Field(..., description="표준화된 음식 이름")
    amount: int = Field(..., description="섭취량 (숫자)")
    unit: str = Field(..., description="섭취 단위 (예: g, ml)")
    calories: int = Field(..., description="총 열량 (kcal)")
    nutritions: Nutrition = Field(..., description="영양소 정보")

class NutritionLogList(BaseModel):
    logs: list[NutritionLog] = Field(..., description="영양 추정 결과 리스트")
```

### Parser 등록 (`infra/langchain/runnables/parsers.py`)

```python
from langchain.output_parsers import PydanticOutputParser
from src.domain.models.nutrition import NutritionLogList

parser_map = {
    "nutrition_estimator": PydanticOutputParser(pydantic_object=NutritionLogList),
}

def get_parser(label: str):
    return parser_map.get(label)
```

### Chain 구성 (`infra/langchain/runnables/chains.py`)

```python
from typing import Any
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import Runnable

from src.core.external.langchain.config import get_llm
from src.infra.langchain.executors.executor import ainvoke_runnable
from src.infra.langchain.prompts import get_prompt
from src.infra.langchain.runnables.parsers import get_parser

def get_chain(input_variables: dict[str, Any], label: str) -> Runnable:
    llm = get_llm()
    parser: PydanticOutputParser | None = get_parser(label)
    
    system_prompt = get_prompt("system", label)
    human_prompt = get_prompt("human", label)
    
    if parser:
        format_instructions = parser.get_format_instructions()
        escaped_format = format_instructions.replace("{", "{{").replace("}", "}}")
        
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt + "\n\n" + escaped_format),
                ("human", human_prompt),
            ]
        )
        return prompt | llm | parser
    else:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", human_prompt),
            ]
        )
        return prompt | llm

async def run_chain(
    input_variables: dict[str, Any],
    label: str,
) -> tuple[bool, Any | None]:
    """체인을 생성하고 실행합니다."""
    sequence = get_chain(input_variables=input_variables, label=label)
    result, error = await ainvoke_runnable(
        chain=sequence,
        variables=input_variables,
        step_label=label
    )
    if error:
        return True, None
    return False, result
```

### 프롬프트 예제

**System 프롬프트** (`prompts/system/nutrition_estimator.txt`)
```
#지시사항
너는 여러 음식에 대한 영양 정보를 정확한 근거를 가지고 추론할 수 있어.
사용자가 식사 내용으로 입력한 [입력 내용]을 요청한 출력 형식에 맞게 변환해줘.

#제약 조건
- 영양 성분은 사용자의 입력 내용을 바탕으로 충분한 근거를 가지고 추측할 것
- 칼로리는 kcal 단위로 작성할 것
- 양은 가능하면 g, ml 단위를 사용할 것
- 탄수화물, 단백질, 지방, 당류는 g 단위로 작성할 것
- 주어진 출력 형식에 맞춰서 해당 내용만 출력할 것
```

**Human 프롬프트** (`prompts/human/nutrition_estimator.txt`)
```
#입력 데이터
{meal_list}

#비고
{note}
```

**참고:** System 프롬프트에 `format_instructions`가 자동으로 추가됩니다. 프롬프트 파일 자체에는 포함하지 않아도 됩니다.

## Import 경로 참고

LangChain 0.3.x 버전에서 사용하는 주요 import 경로:

```python
# 출력 파서
from langchain.output_parsers import PydanticOutputParser

# 프롬프트
from langchain.prompts import ChatPromptTemplate

# Runnable (체인 타입 힌팅용)
from langchain.schema.runnable import Runnable

# LLM
from langchain_openai import ChatOpenAI

# Callback 및 설정
from langchain.callbacks import StdOutCallbackHandler
from langchain.globals import set_verbose

# Core (일부 기능)
from langchain_core.runnables import Runnable
```

**중요:** LangChain 버전에 따라 import 경로가 다를 수 있습니다. 공식 문서를 참고하세요.

## 주의사항

### 1. 중괄호 이스케이프 처리

`format_instructions`에는 중괄호가 포함되어 있지만, ChatPromptTemplate에서 중괄호는 변수를 의미하므로 반드시 이스케이프해야 합니다.

```python
escaped_format = format_instructions.replace("{", "{{").replace("}", "}}")
```

### 2. Format Instructions 자동 생성

`PydanticOutputParser.get_format_instructions()`는 Pydantic 모델을 기반으로 자동으로 형식 지침을 생성합니다. 이는 JSON 스키마 형태로 LLM에게 전달됩니다.

**예시 출력:**
```
The output should be formatted as a JSON instance that conforms to the following JSON schema:

{
  "properties": {
    "logs": {
      "items": {
        "properties": {
          "amount": {"title": "Amount", "type": "integer"},
          "calories": {"title": "Calories", "type": "integer"},
          ...
        },
        "required": ["name", "parsed_name", ...],
        "title": "NutritionLog",
        "type": "object"
      },
      "title": "Logs",
      "type": "array"
    }
  },
  "required": ["logs"],
  "title": "NutritionLogList",
  "type": "object"
}
```

### 3. 파싱 에러 처리

LLM이 형식에 맞지 않는 응답을 반환하면 `PydanticOutputParser`가 예외를 발생시킵니다. 적절한 에러 핸들링이 필요합니다.

```python
try:
    error, result = await run_chain(...)
    if error or not result:
        raise ValueError("처리 실패")
    # result 사용
except Exception as e:
    # 파싱 실패 처리
    raise ValueError(f"응답 파싱 실패: {e}") from e
```

### 4. Parser 없이 사용하는 경우

Parser를 등록하지 않으면 (`get_parser(label)`가 `None` 반환) 일반 문자열 응답을 받을 수 있습니다. 이 경우 파싱을 수동으로 처리해야 합니다.

### 5. 복잡한 중첩 구조 지원

Pydantic 모델은 중첩된 구조를 지원하므로, 복잡한 응답 형식도 정의할 수 있습니다.

```python
class InnerModel(BaseModel):
    field1: str

class OuterModel(BaseModel):
    inner: InnerModel
    items: list[InnerModel]
```

### 6. 응답 타입 처리

`ainvoke_runnable` 함수에서 응답 타입을 올바르게 처리해야 합니다:

- **Parser 사용 시**: 응답이 이미 파싱된 Pydantic 모델 인스턴스
- **Parser 미사용 시**: 문자열 또는 AIMessage 객체

```python
# Parser 사용 시
result = await run_chain(...)
if not result[0]:  # 에러가 없으면
    parsed_model = result[1]  # 이미 NutritionLogList 인스턴스
    logs = parsed_model.logs  # 직접 접근 가능

# Parser 미사용 시
result = await run_chain(...)
if not result[0]:
    raw_text = result[1]  # 문자열 또는 AIMessage
    if hasattr(raw_text, "content"):
        text = raw_text.content
    else:
        text = str(raw_text)
```

### 7. 에러 처리 전략

LLM 응답이 형식에 맞지 않을 경우를 대비한 에러 처리:

```python
try:
    error, result = await run_chain(input_variables, label)
    if error:
        # 네트워크 에러, 타임아웃 등
        raise ValueError(f"체인 실행 실패: {error}")
    
    if not result:
        raise ValueError("응답이 비어있습니다")
    
    # 타입 검증
    if not isinstance(result, NutritionLogList):
        raise TypeError(f"예상 타입과 다릅니다: {type(result)}")
    
    return result.logs
    
except ValueError as e:
    # 비즈니스 로직 에러
    logger.error(f"서비스 에러: {e}")
    raise
except Exception as e:
    # 예상치 못한 에러
    logger.exception(f"예상치 못한 에러: {e}")
    raise ValueError(f"처리 중 오류 발생: {e}") from e
```

### 8. 디버깅 팁

- **Format Instructions 확인**: `parser.get_format_instructions()` 출력값을 직접 확인
- **프롬프트 확인**: System 프롬프트에 format instructions가 제대로 추가되었는지 확인
- **LangSmith 트래킹**: `LANGCHAIN_TRACING=true`로 설정하여 실행 추적
- **응답 로깅**: `ainvoke_runnable`에서 원본 응답을 로깅하여 문제 파악

```python
# 디버깅을 위한 로깅 추가
import logging
logger = logging.getLogger(__name__)

# Chain 구성 전에 format instructions 확인
if parser:
    format_instructions = parser.get_format_instructions()
    logger.debug(f"Format Instructions:\n{format_instructions}")
    
# 실행 후 원본 응답 확인
response = await chain.ainvoke(variables)
logger.debug(f"Raw response: {response}")
```

## 마이그레이션 체크리스트

### 필수 단계

- [ ] 1. **필수 패키지 설치**: langchain, langchain-openai, pydantic 등
- [ ] 2. **환경 변수 설정**: `.env` 파일에 `OPENAI_API_KEY` 등 설정
- [ ] 3. **Pydantic 모델 정의**: 응답 형식을 정의하는 모델 생성
- [ ] 4. **Parser 생성 및 등록**: `PydanticOutputParser` 생성 및 `parser_map`에 등록
- [ ] 5. **LLM 초기화 함수**: `get_llm()` 함수 구현 (선택사항이지만 권장)
- [ ] 6. **프롬프트 로딩 함수**: `get_prompt()` 함수 구현 (선택사항이지만 권장)
- [ ] 7. **Chain 구성 함수**: `get_chain()` 함수에서 parser 사용
- [ ] 8. **Format instructions 추가**: System 프롬프트에 추가 (중괄호 이스케이프 필수!)
- [ ] 9. **실행 함수**: `ainvoke_runnable()` 및 `run_chain()` 구현
- [ ] 10. **에러 핸들링**: 파싱 에러 및 네트워크 에러 처리
- [ ] 11. **테스트**: 실제 실행하여 결과 검증

### 검증 항목

- [ ] Pydantic 모델의 모든 필드에 `description`이 명확히 정의되어 있는가?
- [ ] `format_instructions`가 System 프롬프트에 제대로 추가되었는가?
- [ ] 중괄호 이스케이프가 올바르게 처리되었는가?
- [ ] 에러 발생 시 적절한 에러 메시지가 출력되는가?
- [ ] 응답이 올바르게 파싱되어 Pydantic 모델 인스턴스로 변환되는가?

## 관련 파일 구조

```
src/
├── core/
│   ├── config.py                 # 환경 변수 설정 (Settings)
│   └── external/
│       └── langchain/
│           └── config.py         # LLM 초기화 (get_llm)
├── domain/
│   └── models/
│       └── nutrition.py          # Pydantic 모델 정의
├── infra/
│   └── langchain/
│       ├── executors/
│       │   └── executor.py       # ainvoke_runnable (재시도 로직)
│       ├── runnables/
│       │   ├── chains.py         # Chain 구성 및 실행 (get_chain, run_chain)
│       │   └── parsers.py        # Parser 등록 (get_parser)
│       └── prompts/
│           ├── __init__.py       # 프롬프트 로딩 (get_prompt)
│           ├── system/
│           │   └── nutrition_estimator.txt
│           └── human/
│               └── nutrition_estimator.txt
└── service/
    └── nutrition_estimate_service.py  # 서비스 레이어
```

## 문제 해결 (Troubleshooting)

### 문제 1: "KeyError" 또는 변수 파싱 에러

**증상**: `ChatPromptTemplate`에서 변수를 찾을 수 없다는 에러

**원인**: Human 프롬프트의 변수명과 `input_variables`의 키가 일치하지 않음

**해결**: Human 프롬프트의 `{variable_name}`과 `input_variables`의 키가 정확히 일치하는지 확인

```python
# Human 프롬프트
"{meal_list}"  # 변수명

# input_variables
input_variables = {
    "meal_list": [...],  # 키가 일치해야 함
}
```

### 문제 2: 파싱 에러 (OutputParserException)

**증상**: LLM 응답이 형식에 맞지 않아 파싱 실패

**원인**:
- LLM이 JSON 형식을 제대로 따르지 않음
- Format instructions가 프롬프트에 제대로 추가되지 않음
- Pydantic 모델 정의와 실제 응답 구조가 다름

**해결**:
- System 프롬프트에서 출력 형식을 명확히 지시
- Format instructions가 System 프롬프트에 포함되었는지 확인
- `parser.get_format_instructions()` 출력값을 확인
- LLM 모델을 더 강력한 모델로 변경 (예: gpt-4-turbo)

### 문제 3: 중괄호 관련 에러

**증상**: `KeyError` 또는 템플릿 파싱 에러

**원인**: Format instructions의 중괄호를 이스케이프하지 않음

**해결**: 반드시 이스케이프 처리

```python
escaped_format = format_instructions.replace("{", "{{").replace("}", "}}")
```

### 문제 4: 타임아웃 에러

**증상**: LLM 응답 시간 초과

**원인**: 네트워크 지연 또는 LLM 응답이 너무 느림

**해결**: `ainvoke_runnable`의 `TIMEOUT_SECONDS` 값을 증가

```python
TIMEOUT_SECONDS = 60.0  # 30초에서 60초로 증가
```

### 문제 5: 재시도 후에도 실패

**증상**: 3번 재시도 후에도 실패

**원인**: API 키 문제, 네트워크 문제, 또는 LLM 서비스 장애

**해결**:
- API 키가 올바른지 확인
- 네트워크 연결 확인
- LLM 서비스 상태 확인
- 에러 메시지를 자세히 확인

## 요약: 핵심 포인트

1. **Pydantic 모델 필수**: 응답 형식을 Pydantic 모델로 정의하고, 모든 필드에 `description` 제공
2. **Parser 등록**: `PydanticOutputParser`를 생성하여 `parser_map`에 등록
3. **중괄호 이스케이프 필수**: Format instructions를 반드시 이스케이프 (`{{`, `}}`)
4. **Chain 순서**: `prompt | llm | parser` 순서로 구성
5. **에러 처리**: 파싱 에러 및 네트워크 에러를 적절히 처리
6. **재시도 로직**: 네트워크 불안정성 대비 재시도 구현 권장

## 추가 리소스

- [LangChain PydanticOutputParser 공식 문서](https://python.langchain.com/docs/modules/model_io/output_parsers/types/pydantic)
- [Pydantic 모델 정의 가이드](https://docs.pydantic.dev/latest/)
- [LangChain 공식 문서](https://python.langchain.com/)
- [LangChain 0.3.x 마이그레이션 가이드](https://python.langchain.com/docs/versions/migrating)

## 버전 정보

이 가이드는 다음 버전을 기준으로 작성되었습니다:

- `langchain==0.3.25`
- `langchain-core==0.3.64`
- `langchain-openai==0.3.21`
- `pydantic==2.11.5`

다른 버전을 사용하는 경우 일부 API가 다를 수 있으니 공식 문서를 참고하세요.
