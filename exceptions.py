"""
레이어링 아키텍처 기반 커스텀 예외 클래스

각 레이어별 역할:
- InfrastructureException: Infrastructure 레이어의 예외 (외부 시스템 연동 실패 등)
- ServiceException: Service 레이어의 예외 (비즈니스 로직 예외)
"""


class InfrastructureException(Exception):
    """Infrastructure 레이어에서 발생하는 예외 (외부 시스템 연동 실패 등)"""
    pass


class ServiceException(Exception):
    """Service 레이어에서 발생하는 예외 (비즈니스 로직 예외)"""
    pass


class ChainExecutionException(InfrastructureException):
    """LangChain 체인 실행 중 발생하는 예외"""
    pass
