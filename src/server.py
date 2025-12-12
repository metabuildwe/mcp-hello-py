#!/usr/bin/env python3
"""
Hybrid Data & Text Utility MCP Server

이 모듈은 텍스트 요약, 유사도 분석, 로그 계산과 같은 다양한 유틸리티 기능을 제공합니다.

주요 기능:
    - 텍스트 파일 내용 요약
    - 슬래시 구분 단어의 유사도 분석
    - 로그 값 계산
    - MCP 프로토콜: Tools, Resources, Prompts 지원
    - Streamable HTTP 전송: Cloud Run 등 서버리스 환경 지원

작성자: MCP Hybrid Team
버전: 4.0.0
라이선스: MIT
"""
####################################################################################
import os
import math # 로그 계산을 위해 math 모듈 추가
from typing import Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# 앱 버전과 이름을 정의합니다.
APP_NAME = "mcp-hybrid-utility"
APP_VERSION = "4.0.0"


# ============================================================================
# FastMCP 서버 생성
# ============================================================================

mcp = FastMCP(
    name=APP_NAME,
    instructions="텍스트 요약, 유사도 분석 및 수학적 로그 계산을 수행하는 하이브리드 유틸리티 도구를 제공합니다.",
    stateless_http=True,
    json_response=True,
    host="0.0.0.0",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)


# ============================================================================
# Tools (도구) - 요청된 3가지 신규 툴
# ============================================================================

@mcp.tool()
def summarize_text_file(file_content: str, summary_length: Literal["short", "medium", "long"] = "medium") -> str:
    """
    텍스트 파일의 전체 내용을 받아 지정된 길이로 요약하여 반환합니다.
    
    주의: 이 함수는 실제 AI 모델 없이 단순한 휴리스틱 (첫 문장 추출 등)을 사용하며,
    실제 AI 서비스는 아닙니다.
    
    Args:
        file_content: 요약할 텍스트 파일의 전체 내용 문자열
        summary_length: 원하는 요약 길이 ("short": 1-2문장, "medium": 3-5문장, "long": 6-10문장)
    
    Returns:
        요약된 텍스트 문자열
    
    Examples:
        >>> summarize_text_file("첫 문장. 둘째 문장. 셋째 문장.", "short")
        '첫 문장. 둘째 문장.'
    """
    sentences = [s.strip() for s in file_content.split('.') if s.strip()]
    
    if summary_length == "short":
        num_sentences = min(2, len(sentences))
    elif summary_length == "medium":
        num_sentences = min(5, len(sentences))
    else: # long
        num_sentences = min(10, len(sentences))
        
    summary = ". ".join(sentences[:num_sentences])
    if summary:
        return summary + "."
    return "요약할 내용이 충분하지 않습니다."


@mcp.tool()
def calculate_slash_similarity(slash_input: str) -> float:
    """
    슬래시(/)로 구분된 두 단어의 유사도를 Jaccard 유사도를 사용하여 계산합니다.
    
    Args:
        slash_input: '단어1/단어2' 형태로 슬래시로 구분된 문자열
    
    Returns:
        두 단어의 유사도 점수 (float, 0.0 ~ 1.0)
    
    Examples:
        >>> calculate_slash_similarity("사과/오렌지")
        0.0  # (공통 단어가 없음)
        >>> calculate_slash_similarity("데이터분석/데이터처리")
        0.5  # (데이터라는 공통 단어 기반)
    """
    if '/' not in slash_input:
        raise ValueError("입력은 '단어1/단어2' 형태로 슬래시(/)를 포함해야 합니다.")
        
    parts = slash_input.split('/')
    if len(parts) != 2:
        # 슬래시가 여러 개인 경우 처리
        raise ValueError("두 단어만 슬래시로 구분해야 합니다.")
        
    word1 = parts[0].strip().lower()
    word2 = parts[1].strip().lower()
    
    # 각 단어를 구성하는 문자로 집합 생성 (문자 기반 유사도)
    set1 = set(word1)
    set2 = set(word2)
    
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
        
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union


@mcp.tool()
def calculate_logarithm(number: float, base: Literal[2, 10, 'e'] = 'e') -> float:
    """
    입력된 숫자의 로그 값(Logarithm)을 지정된 밑(Base)에 대해 계산하여 반환합니다.
    
    Args:
        number: 로그를 계산할 숫자 (양수여야 함)
        base: 로그의 밑. 2 (이진 로그), 10 (상용 로그), 'e' (자연 로그) 중 하나
    
    Returns:
        로그 계산 결과 (float)
        
    Examples:
        >>> calculate_logarithm(100, 10)
        2.0
        >>> calculate_logarithm(2.71828, 'e')
        1.0
    """
    if number <= 0:
        raise ValueError("로그를 계산할 숫자는 양수여야 합니다.")
        
    if base == 2:
        return math.log2(number)
    elif base == 10:
        return math.log10(number)
    elif base == 'e':
        return math.log(number) # math.log는 자연 로그(ln)를 계산
    else:
        raise ValueError("지원하는 밑(base)은 2, 10, 'e' 중 하나여야 합니다.")


# ============================================================================
# Resources (리소스) - 업데이트
# ============================================================================

@mcp.resource("docs://hybrid/readme")
def get_readme() -> str:
    """
    Hybrid Utility MCP 서버 사용 가이드를 제공합니다.
    
    Returns:
        Markdown 형식의 문서
    """
    return """# Hybrid Utility MCP Server Documentation

## 개요
텍스트 요약, 유사도 분석 및 로그 계산을 위한 다양한 유틸리티 도구를 제공합니다.

## 사용 가능한 도구

### summarize_text_file
텍스트 파일의 내용을 지정된 길이로 요약합니다.
**파라미터:** `file_content` (string), `summary_length` (string: "short", "medium", "long")

### calculate_slash_similarity
'단어1/단어2' 형태로 입력된 두 단어의 문자 기반 유사도를 계산합니다.
**파라미터:** `slash_input` (string)
**결과:** 0.0 ~ 1.0 사이의 유사도 점수

### calculate_logarithm
입력된 숫자의 로그 값을 계산합니다. 

[Image of logarithm formula]

**파라미터:** `number` (float, 양수), `base` (Literal: 2, 10, 'e')

## 사용 방법

1. MCP 클라이언트에서 서버 연결
2. 필요한 유틸리티 도구를 호출
3. 결과 확인
"""


# ============================================================================
# Prompts (프롬프트) - 업데이트
# ============================================================================

@mcp.prompt()
def analysis_explanation_template(tool_name: str, **kwargs) -> str:
    """
    연산 결과를 설명하는 프롬프트 템플릿을 제공합니다.
    """
    
    try:
        if tool_name == "summarize_text_file":
            result = summarize_text_file(kwargs['file_content'], kwargs['summary_length'])
            desc = f"입력된 텍스트 파일을 {kwargs['summary_length']} 길이로 요약했습니다."
        elif tool_name == "calculate_slash_similarity":
            result = calculate_slash_similarity(kwargs['slash_input'])
            desc = f"'{kwargs['slash_input']}'의 슬래시로 구분된 두 단어의 유사도를 계산했습니다."
        elif tool_name == "calculate_logarithm":
            result = calculate_logarithm(kwargs['number'], kwargs['base'])
            desc = f"숫자 {kwargs['number']}의 밑이 {kwargs['base']}인 로그 값을 계산했습니다."
        else:
            result = "N/A"
            desc = f"지원되지 않는 연산"
            
    except Exception as e:
        result = f"오류: {e}"
        desc = f"연산 실패"
        
    
    return f"""사용자에게 다음 연산 결과를 명확하고 적절하게 설명하세요.

수행된 연산: {tool_name}
설명: {desc}
입력된 인수: {kwargs}
최종 변환 결과: {result}

메시지에 포함할 내용:
1. 수행된 연산의 목적과 입력 값 명시
2. 계산된 최종 결과
3. (유사도나 로그의 경우) 결과 해석에 대한 간략한 설명 제공

톤: 정보 제공 및 전문성
길이: 3-5 문장
"""


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """
    MCP 서버의 메인 진입점입니다.
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