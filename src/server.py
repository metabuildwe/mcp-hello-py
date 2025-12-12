#!/usr/bin/env python3
"""
Financial & Life Calculation MCP Server

이 모듈은 연봉 계산, 단순 이자 계산, 대출 상환액 계산과 같은 실생활 재무 계산 기능을 제공합니다.

주요 기능:
    - 월급 및 기간 기반 연봉 및 월 실수령액 계산 (간소화된 모델)
    - 초기 원금 및 기간 기반 단순 이자 계산
    - 대출 상환액 계산
    - MCP 프로토콜: Tools, Resources, Prompts 지원
    - Streamable HTTP 전송: Cloud Run 등 서버리스 환경 지원

작성자: MCP Finance Team
버전: 5.1.0
라이선스: MIT
"""
####################################################################################
import os
import math 
from typing import Dict, Literal, Union

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# 앱 버전과 이름을 정의합니다.
APP_NAME = "mcp-finance-calc"
APP_VERSION = "5.1.0"


# ============================================================================
# FastMCP 서버 생성
# ============================================================================

mcp = FastMCP(
    name=APP_NAME,
    instructions="월급 기반 연봉 계산, 단순 이자 및 대출 상환액 계산 도구를 제공합니다.",
    stateless_http=True,
    json_response=True,
    host="0.0.0.0",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)


# ============================================================================
# Tools (도구) - 사용자 요청 반영
# ============================================================================

@mcp.tool()
def calculate_annual_salary(monthly_salary: float, period_months: int = 12) -> Dict[str, float]:
    """
    월급과 지급 기간(개월)을 입력받아 연봉 및 예상 월 실수령액을 계산합니다.
    
    주의: 이 계산은 간소화된 모델이며, 실제 국가별/개인별 세금 및 공제액과 차이가 있을 수 있습니다.
    
    Args:
        monthly_salary: 세전 월급
        period_months: 월급을 받는 총 기간 (기본값: 12개월)
    
    Returns:
        계산 결과를 담은 딕셔너리
        
    Examples:
        >>> calculate_annual_salary(3000000, 12)
        {'annual_pretax': 36000000.0, 'monthly_deduction': 300000.0, 'monthly_takehome': 2700000.0}
    """
    if monthly_salary <= 0 or period_months <= 0:
        raise ValueError("월급과 기간은 0보다 커야 합니다.")
        
    # 연봉 계산
    annual_pretax = monthly_salary * period_months
    
    # 간이 세액표 등을 고려한 대략적인 공제율 (연봉에 따라 조정)
    if annual_pretax < 40000000:
        deduction_rate = 0.10
    elif annual_pretax < 70000000:
        deduction_rate = 0.15
    else:
        deduction_rate = 0.20
        
    # 월 공제액 (월급 기준)
    monthly_deduction = monthly_salary * (deduction_rate * 0.9) # 연봉 구간에 따른 세전 월급의 약 90%에 공제율 적용 가정
    monthly_takehome = monthly_salary - monthly_deduction
    
    # 소수점 두 자리까지 반올림
    return {
        "annual_pretax": round(annual_pretax, 2),
        "monthly_deduction": round(monthly_deduction, 2),
        "monthly_takehome": round(monthly_takehome, 2),
    }


@mcp.tool()
def calculate_simple_interest(principal: float, annual_rate: float, years: float) -> Dict[str, float]:
    """
    원금, 연 이자율, 기간을 기반으로 **단리(Simple Interest)**를 계산하여 총 이익을 반환합니다.
    
    Args:
        principal: 초기 원금
        annual_rate: 연 이자율 (0.05 = 5%)
        years: 저축 기간 (년)
    
    Returns:
        최종 원리금 합계(total_value)와 총 이자(total_interest)를 담은 딕셔너리
        
    Examples:
        >>> calculate_simple_interest(1000000, 0.05, 1)
        {'total_value': 1050000.0, 'total_interest': 50000.0}
    """
    if principal <= 0 or years < 0:
        raise ValueError("원금은 양수여야 하며, 기간은 음수일 수 없습니다.")
        
    # 공식: I = P * r * t (단순 이자 계산)
    # P: 원금, r: 연 이자율, t: 기간(년)
    
    total_interest = principal * annual_rate * years
    total_value = principal + total_interest
    
    return {
        "total_value": round(total_value, 2),
        "total_interest": round(total_interest, 2),
    }


@mcp.tool()
def calculate_loan_repayment(principal: float, annual_rate: float, months: int) -> Dict[str, float]:
    """
    원금, 연 이자율, 대출 기간(월)을 기반으로 **원리금 균등 상환 방식**의 월 상환액을 계산합니다.
    
    Args:
        principal: 대출 원금
        annual_rate: 연 이자율 (0.05 = 5%)
        months: 총 상환 기간 (월)
    
    Returns:
        월 상환액(monthly_payment)과 총 이자(total_interest)를 담은 딕셔너리
        
    Examples:
        >>> calculate_loan_repayment(100000000, 0.04, 120) # 1억, 4%, 10년
        {'monthly_payment': 1012457.73, 'total_interest': 21495927.9} # 예시 값은 조정될 수 있음
    """
    if principal <= 0 or months <= 0:
        raise ValueError("원금과 기간은 0보다 커야 합니다.")
        
    if annual_rate == 0:
        monthly_payment = principal / months
        total_interest = 0
    else:
        # 월 이자율
        monthly_rate = annual_rate / 12
        
        # 월 상환액 공식 (PMT): P * [ i(1+i)^n / ((1+i)^n - 1) ]
        numerator = monthly_rate * (1 + monthly_rate) ** months
        denominator = (1 + monthly_rate) ** months - 1
        monthly_payment = principal * (numerator / denominator)
        
        # 총 이자 = 월 상환액 * 총 개월 수 - 원금
        total_interest = (monthly_payment * months) - principal
        
    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_interest": round(total_interest, 2),
    }


# ============================================================================
# Resources (리소스) - 업데이트
# ============================================================================

@mcp.resource("docs://finance/readme")
def get_readme() -> str:
    """
    Finance Calculation MCP 서버 사용 가이드를 제공합니다.
    
    Returns:
        Markdown 형식의 문서
    """
    return """# Financial & Life Calculation MCP Server Documentation

## 개요
월급 기반 연봉 계산, 단순 이자 계산, 대출 상환액 계산과 같은 실용적인 재무 분석 기능을 제공합니다.

## 사용 가능한 도구

### calculate_annual_salary
월급과 지급 기간(개월)을 기반으로 연봉 및 예상 월 실수령액을 계산합니다.
**파라미터:** `monthly_salary` (float, 세전 월급), `period_months` (int, 지급 기간, 기본값 12)

### calculate_simple_interest
초기 원금, 연 이자율, 기간(년)을 기반으로 단순 이자를 계산하여 최종 원리금을 예측합니다.
**파라미터:** `principal` (float, 원금), `annual_rate` (float, 연 이자율), `years` (float, 기간)

### calculate_loan_repayment
원리금 균등 상환 방식의 대출에 대한 월 상환액과 총 이자를 계산합니다.
**파라미터:** `principal` (float, 대출 원금), `annual_rate` (float, 연 이자율), `months` (int, 총 기간)

## 사용 방법
... (생략)
"""


# ============================================================================
# Prompts (프롬프트) - 업데이트
# ============================================================================

@mcp.prompt()
def finance_explanation_template(tool_name: str, **kwargs) -> str:
    """
    재무 계산 결과를 설명하는 프롬프트 템플릿을 제공합니다.
    """
    
    try:
        if tool_name == "calculate_annual_salary":
            result = calculate_annual_salary(kwargs['monthly_salary'], kwargs.get('period_months', 12))
            desc = f"월급 {kwargs['monthly_salary']:,}원과 {kwargs.get('period_months', 12)}개월을 기준으로 연봉을 계산했습니다."
        elif tool_name == "calculate_simple_interest":
            result = calculate_simple_interest(kwargs['principal'], kwargs['annual_rate'], kwargs['years'])
            desc = f"원금 {kwargs['principal']:,}원의 단리 이자율을 계산했습니다."
        elif tool_name == "calculate_loan_repayment":
            result = calculate_loan_repayment(kwargs['principal'], kwargs['annual_rate'], kwargs['months'])
            desc = f"대출 원금 {kwargs['principal']:,}원에 대한 월 상환액을 계산했습니다."
        else:
            result = "N/A"
            desc = f"지원되지 않는 금융 연산"
            
    except Exception as e:
        result = f"오류: {e}"
        desc = f"연산 실패"
        
    
    return f"""사용자에게 다음 재무 계산 결과를 명확하고 유익하게 설명하세요.

수행된 연산: {tool_name}
설명: {desc}
입력된 인수: {kwargs}
최종 계산 결과: {result}

메시지에 포함할 내용:
1. 계산의 목적 (예: 월급 예상, 투자 미래 가치, 대출 부담금) 명시
2. 주요 입력 값과 최종 결과 (예: 월 실수령액, 총 이자) 명확히 제시
3. 결과가 사용자에게 주는 재무적 의미 간략하게 해석

톤: 전문적이고 조언하는
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