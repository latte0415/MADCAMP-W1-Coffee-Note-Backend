from fastapi import APIRouter, HTTPException
from service import AIService
from schema import ChatTest, ChatForMapping
from exceptions import ServiceException

router = APIRouter()
ai_service = AIService()

@router.post("/chat")
async def chat_test(request: ChatTest.Request) -> ChatTest.Response:
    """
    API 레이어: HTTP 요청/응답 처리
    Service 레이어의 예외를 HTTPException으로 변환합니다.
    """
    try:
        result = await ai_service.chat(request.message)
        return ChatTest.Response(message=result)
    except ServiceException as e:
        # Service 레이어 예외를 HTTP 예외로 변환 (원래 예외 정보 유지)
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        # 예상치 못한 예외를 안전한 에러 메시지로 변환 (원래 예외 정보 유지)
        raise HTTPException(status_code=500, detail="서비스 처리 중 오류가 발생했습니다.") from e

@router.post("/chat-for-mapping")
async def chat_for_mapping(request: ChatForMapping.Request) -> ChatForMapping.Response:
    """
    API 레이어: HTTP 요청/응답 처리
    Service 레이어의 예외를 HTTPException으로 변환합니다.
    """
    try:
        result = await ai_service.chat_for_mapping(request.message)
        return result
    except ServiceException as e:
        # Service 레이어 예외를 HTTP 예외로 변환 (원래 예외 정보 유지)
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        # 예상치 못한 예외를 안전한 에러 메시지로 변환 (원래 예외 정보 유지)
        raise HTTPException(status_code=500, detail="서비스 처리 중 오류가 발생했습니다.") from e