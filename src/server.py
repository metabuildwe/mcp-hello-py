#!/usr/bin/env python3
"""
Simple Place MCP Server

관광지 명을 받아 현재의 밀집 정도를 출력하는 MCP 서버를 제공합니다.

주요 기능:
    - 단일 검색: 하나의 관광지 상태를 검색
    - 복수 검색: 여러 관광지들의 상태를 검색
    - MCP 프로토콜: Tools, Resources, Prompts 지원
    - Streamable HTTP 전송: Cloud Run 등 서버리스 환경 지원

사용 예시:
    HTTP 모드 실행:
        $ python src/server.py --http-stream
        -> http://localhost:8080/mcp
    
    stdio 모드 실행:
        $ python src/server.py
    
    도구 호출:
        {"name": "say_place", "arguments": {"name": "경복궁"}}
        -> "경복궁의 현재 밀집 정도는 여유상태입니다.\n사람이 몰려있을 가능성이 낮고 붐빔은 거의 느껴지지 않아요. 도보 이동이 자유로워요."

작성자: MCP Hello Team
버전: 1.0.0
라이선스: MIT
"""

import os

from urllib.parse import quote
from urllib.request import urlopen
import json

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

BASE_URL = "http://openapi.seoul.go.kr:8088/6c5571714773616936314e6c747547/json/citydata_ppltn/1/5/"

# ============================================================================
# FastMCP 서버 생성
# ============================================================================

mcp = FastMCP(
    name="mcp-place",
    instructions="서울시내 주요 관광지 밀집 정도를 출력하는 MCP입니다.",
    stateless_http=True,
    json_response=True,
    host="0.0.0.0",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)


# ============================================================================
# Tools (도구)
# ============================================================================

@mcp.tool()
def say_place(name: str) -> str:
    """
    관광지 명을 받아 현재의 밀집 정도를 출력합니다.
    
    공란이 전달되는 경우 경복궁 정보를 출력합니다.
    
    Args:
        name: 검색할 주요 관광지명(예: 덕수궁, 경복궁, ...)
    
    Returns:
        "{name}의 현재 밀집 정도는 {status}상태입니다.\n{msg}" 형태의 문자열
    
    Examples:
        >>> say_place("경복궁")
        '경복궁의 현재 밀집 정도는 여유상태입니다.\n사람이 몰려있을 가능성이 낮고 붐빔은 거의 느껴지지 않아요. 도보 이동이 자유로워요.'
    """
    if not name or name.strip() == "":
        name = "경복궁"

    with urlopen(BASE_URL + quote(name)) as response:
        json_bytes = response.read()

    json_data = json.loads(json_bytes.decode("utf-8"))

    row = json_data["SeoulRtd.citydata_ppltn"][0]

    area_congest_lvl = row.get("AREA_CONGEST_LVL", "")
    area_congest_msg = row.get("AREA_CONGEST_MSG", "")

    return (
        f"{name}의 현재 밀집 정도는 {area_congest_lvl} 상태입니다.\n{area_congest_msg}"
    )


@mcp.tool()
def say_place_multiple(names: list[str]) -> str:
    """
    여러 장소를 한번에 검색합니다.
    
    장소명 리스트를 받아 각 장소마다 상태를 생성하고,
    불릿 포인트(•)로 구분하여 하나의 문자열로 반환합니다.
    
    Args:
        names: 검색할 장소명의 리스트 (예: ["서울역", "이태원", "경복궁"])
    
    Returns:
        각 장소별 성태가 줄바꿈으로 출력된 목록
    
    Examples:
        >>> say_place_multiple(["김철수", "이영희"])
        '• 안녕하세요, 김철수님!\\n• 안녕하세요, 이영희님!'
    """
    if not names:
        return ""
    
    greetings = []
    for name in names:
        greeting = say_place(name)
        greetings.append(f"• {greeting}")
    
    return "\n".join(greetings)


# ============================================================================
# Resources (리소스)
# ============================================================================

@mcp.resource("docs://hello/readme")
def get_readme() -> str:
    """
    Place MCP 서버 사용 가이드를 제공합니다.
    
    Returns:
        Markdown 형식의 문서
    """
    return """# Place MCP Server Documentation

## 개요
관광지 명을 받아 현재의 밀집 정도를 출력하는 간단한 MCP 서버입니다.

## 사용 가능한 도구

### say_place
하나의 관광지를 검색합니다.

**파라미터:**
- `name` (string, 필수): 검색할 관광지명

**예시:**
```json
{
  "name": "경복궁"
}
```

**결과:**
```
경복궁의 현재 밀집 정도는 여유상태입니다.\n사람이 몰려있을 가능성이 낮고 붐빔은 거의 느껴지지 않아요. 도보 이동이 자유로워요.
```

### say_place_multiple
여러 관광지의 상태를 한번에 검색합니다.

**파라미터:**
- `names` (array, 필수): 검색할 관광지명 목록

**예시:**
```json
{
  "names": ["서울역", "이태원", "경복궁"]
}
```

**결과:**
```
• 서울역의 현재 밀집 정도는 여유상태입니다.\n사람이 몰려있을 가능성이 낮고 붐빔은 거의 느껴지지 않아요. 도보 이동이 자유로워요.
• 이태원의 현재 밀집 정도는 여유상태입니다.\n사람이 몰려있을 가능성이 낮고 붐빔은 거의 느껴지지 않아요. 도보 이동이 자유로워요.
• 경복궁의 현재 밀집 정도는 여유상태입니다.\n사람이 몰려있을 가능성이 낮고 붐빔은 거의 느껴지지 않아요. 도보 이동이 자유로워요.
```

## 사용 방법

1. MCP 클라이언트에서 서버 연결
2. `say_place` 또는 `say_place_multiple` 도구 호출
3. OpenAPI 연결후 결과 출력
4. 상태 출력 결과 확인

## 기술 스택
- Python 3.11+
- MCP Python SDK (FastMCP)
- Pydantic (타입 검증)
- Starlette + Uvicorn (HTTP Stream)
"""


# ============================================================================
# Prompts (프롬프트)
# ============================================================================

@mcp.prompt()
def greeting_message(recipient: str) -> str:
    """
    추가 검색에 대한 템플릿을 제공합니다.
    
    Args:
        recipient: 기존 검색한 장소
    
    Returns:
        AI 어시스턴트를 위한 프롬프트 템플릿
    """
    
    return f"{recipient}이외의 장소에 대하여 알고싶으신가요?"


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """
    MCP 서버의 메인 진입점입니다.
    
    커맨드라인 인자를 통해 전송 모드를 선택합니다:
    - --http-stream: HTTP Stream 모드
    - 기본값: stdio 모드 (표준 입출력)
    
    환경 변수:
        PORT: HTTP 서버 포트 (기본값: 8080)
    
    사용 예시:
        HTTP 모드:
            $ python src/server.py --http-stream
            $ PORT=3000 python src/server.py --http-stream
        
        stdio 모드:
            $ python src/server.py
    """
    import sys
    
    if "--http-stream" in sys.argv:
        port = int(os.environ.get("PORT", 8080))
        mcp.settings.port = port
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
