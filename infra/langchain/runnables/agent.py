"""
Agent 실행 모듈

Infrastructure 레이어: LangChain Agent 실행
"""

from typing import Any
from langchain_core.runnables import Runnable
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain_core.exceptions import OutputParserException
from infra.langchain.config.llm import get_llm
from infra.langchain.config.executor import ainvoke_runnable
from infra.langchain.config.tools import get_web_search_tools
from infra.langchain.config.prompt import get_agent_prompt
from exceptions import InfrastructureException


def handle_parsing_error(error: OutputParserException) -> str:
    """
    파싱 에러 발생 시 LLM의 원본 출력을 반환합니다.
    
    Args:
        error: OutputParserException 객체
    
    Returns:
        LLM의 원본 출력 문자열
    """
    # 에러 객체의 llm_output 속성 확인 시도
    llm_output = getattr(error, 'llm_output', None)
    if llm_output:
        # llm_output이 문자열이면 그대로 반환
        if isinstance(llm_output, str):
            return llm_output
        # 리스트인 경우 첫 번째 요소의 text 속성 확인
        if isinstance(llm_output, list) and len(llm_output) > 0:
            first_output = llm_output[0]
            if hasattr(first_output, 'text'):
                return first_output.text
            if isinstance(first_output, str):
                return first_output
    
    # 에러 메시지에서 LLM 출력 추출 시도
    error_str = str(error)
    if "Could not parse LLM output:" in error_str:
        # 에러 메시지에서 LLM 출력 부분 추출 (백틱 사이의 내용)
        start_idx = error_str.find("`") + 1
        end_idx = error_str.rfind("`")
        if start_idx > 0 and end_idx > start_idx:
            llm_output = error_str[start_idx:end_idx]
            return llm_output
    
    # 추출 실패 시 기본 메시지 반환
    return f"파싱 에러 발생: {error_str}"


def get_agent(web_search: bool = False, label: str = "mapping") -> Runnable:
    """
    Agent를 구성합니다.
    
    Args:
        web_search: 웹 검색 도구 사용 여부
        label: 프롬프트 레이블 (기본값: "mapping")
    
    Returns:
        AgentExecutor (Runnable)
    """
    llm = get_llm()
    tools = []
    
    # web_search가 True이면 웹 검색 도구 추가
    if web_search:
        tools.extend(get_web_search_tools())
    
    # 기본 ReAct 프롬프트 사용
    react_prompt = hub.pull("hwchase17/react")
    
    # Agent 생성
    agent = create_react_agent(llm, tools, react_prompt)
    
    # AgentExecutor 생성 (Runnable이므로 반환 가능)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=handle_parsing_error,
        max_iterations=3,
        max_execution_time=30,
    )
    return agent_executor


async def run_agent(input_prompt: str, web_search: bool = False, label: str = "mapping") -> str:
    """
    Agent를 실행합니다.
    Infrastructure 레이어: 실행 실패 시 InfrastructureException을 발생시킵니다.
    
    Args:
        input_prompt: 사용자 입력 프롬프트
        web_search: 웹 검색 도구 사용 여부
        label: 프롬프트 레이블 (기본값: "mapping")
    
    Returns:
        Agent 실행 결과 (문자열)
    
    Raises:
        InfrastructureException: Agent 실행 실패 시
    """
    try:
        # Agent 생성 (기본 ReAct 프롬프트 사용)
        agent_executor = get_agent(web_search=web_search, label=label)
        
        # prompts/agent/{label}.txt를 읽어서 {input_prompt}를 채운 문자열 생성
        agent_input_prompt = get_agent_prompt(
            name=label,
            input_variables={"input_prompt": input_prompt}
        )
        
        # AgentExecutor는 {"input": "..."} 형식으로 입력받음
        # ReAct 프롬프트의 Question: {input} 부분에 전달됨
        agent_input = {"input": agent_input_prompt}
        
        result = await ainvoke_runnable(
            chain=agent_executor,
            variables=agent_input,
            step_label="agent"
        )
        
        # AgentExecutor의 출력은 {"output": "..."} 형식이므로 output 추출
        if isinstance(result, dict) and "output" in result:
            return result["output"]
        return str(result)
    except Exception as e:
        # 모든 예외를 InfrastructureException으로 변환
        raise InfrastructureException(f"Agent 실행 실패: {e}") from e