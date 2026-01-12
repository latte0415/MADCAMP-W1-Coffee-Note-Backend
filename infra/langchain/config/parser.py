from langchain.output_parsers import PydanticOutputParser
from schema import ChatForMapping

parser_map = {
    "mapping": PydanticOutputParser(pydantic_object=ChatForMapping.Response),
}

def get_parser(label: str) -> PydanticOutputParser | None:
    """레이블에 해당하는 파서를 반환합니다. 없으면 None을 반환합니다."""
    return parser_map.get(label)