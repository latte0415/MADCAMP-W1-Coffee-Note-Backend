from infra.langchain.runnables.chain import run_chain
from infra.langchain.runnables.agent import run_agent
from schema import ChatForMapping
from exceptions import ServiceException

class AIService:
    async def chat(self, input_prompt: str) -> str:
        """
        Service 레이어: 비즈니스 로직 처리
        Infrastructure 레이어의 예외를 ServiceException으로 변환합니다.
        
        Args:
            input_prompt: 사용자 입력 프롬프트
        
        Returns:
            AI 응답 메시지
        
        Raises:
            ServiceException: AI 서비스 처리 실패 시
        """
        try:
            result = await run_chain(label="test", input_variables={"input_prompt": input_prompt})
            # LangChain의 응답은 보통 content 속성을 가짐
            if hasattr(result, 'content'):
                return result.content
            return str(result)
        except Exception as e:
            # 모든 예외를 ServiceException으로 변환 (InfrastructureException, ChainExecutionException 포함)
            raise ServiceException(f"AI 서비스 처리 실패: {e}") from e
    
    async def chat_for_mapping(self, input_prompt: str) -> ChatForMapping.Response:
        """
        Service 레이어: 비즈니스 로직 처리
        2단계 처리:
        1. web_search label로 웹 검색 및 정보 수집
        2. 수집한 정보를 바탕으로 mapping label로 구조화된 출력
        
        Args:
            input_prompt: 사용자 입력 프롬프트
        
        Returns:
            매핑된 응답 데이터
        
        Raises:
            ServiceException: AI 서비스 처리 실패 시
        """
        try:
            # 1단계: 웹 검색 및 정보 수집 (Agent 사용)
            web_search_result = await run_agent(
                input_prompt=input_prompt,
                web_search=True
            )
            
            # 웹 검색 결과를 문자열로 변환 (이미 문자열로 반환됨)
            enriched_prompt = str(web_search_result)
            
            # 2단계: 수집한 정보를 바탕으로 구조화된 출력 (Chain 사용)
            result = await run_chain(
                label="mapping", 
                input_variables={"input_prompt": input_prompt, "web_search_result": enriched_prompt}
            )
            return result
        except Exception as e:
            # 모든 예외를 ServiceException으로 변환 (InfrastructureException, ChainExecutionException 포함)
            raise ServiceException(f"AI 매핑 서비스 처리 실패: {e}") from e