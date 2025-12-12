# Place MCP Server Documentation

관광지 명을 받아 현재의 밀집 정도를 출력하는 간단한 MCP 서버입니다.

## 구조

```
mcp-hello-py/
├── src/
│   ├── __init__.py       # 패키지 초기화
│   └── server.py         # MCP 서버
├── .env                  # 환경 변수 설정
├── requirements.txt      # 의존성
├── pyproject.toml        # 프로젝트 메타데이터
├── Dockerfile            # Docker 설정
└── README.md             # 이 파일
```

## 주요 기능

- **say_place**: 하나의 관광지를 검색
- **say_place_multiple**: 여러 관광지의 상태를 한번에 검색
- **MCP 프로토콜**: Tools, Resources, Prompts 지원

## 설치

```bash
# 가상 환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

## 환경 변수 설정

`.env` 파일을 생성합니다:

```bash
# .env 파일 내용
PORT=8080
```

## 실행

### Streamable HTTP 모드 (Cloud Run, Web)

```bash
python3 src/server.py --http-stream

# 커스텀 포트 사용
PORT=3000 python3 src/server.py --http-stream
```

## 아키텍처

```
┌─────────────┐       ┌─────────────────┐
│  Postman /  │ ───▶  │  MCP Hello      │
│  MCP Client │       │  Server         │
│             │ ◀───  │  (Python)       │
└─────────────┘       └─────────────────┘
     HTTP                  MCP
   POST /mcp             Protocol
```

## 테스트 (Postman)

### Headers 설정 (모든 요청에 필수)

| Header         | Value              |
| -------------- | ------------------ |
| `Content-Type` | `application/json` |
| `Accept`       | `application/json` |

### 1. MCP 서버 초기화

- **Method**: `POST`
- **URL**: `http://localhost:8080/mcp`
- **Body** (raw JSON):

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "postman", "version": "1.0.0"}
  }
}
```

### 2. Tool 목록 조회

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

### 3. say_place 호출

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "say_place",
    "arguments": {"name": "경복궁"}
  }
}
```

**응답 예시:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "경복궁의 현재 밀집 정도는 여유상태입니다.\n사람이 몰려있을 가능성이 낮고 붐빔은 거의 느껴지지 않아요. 도보 이동이 자유로워요."
      }
    ]
  }
}
```

### 4. say_place_multiple 호출

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "say_place_multiple",
    "arguments": {"names": ["서울역", "이태원", "경복궁"]}
  }
}
```

**응답 예시:**

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "• 서울역의 현재 밀집 정도는 여유상태입니다.\n사람이 몰려있을 가능성이 낮고 붐빔은 거의 느껴지지 않아요. 도보 이동이 자유로워요.\n• 이태원의 현재 밀집 정도는 여유상태입니다.\n사람이 몰려있을 가능성이 낮고 붐빔은 거의 느껴지지 않아요. 도보 이동이 자유로워요.\n• 경복궁의 현재 밀집 정도는 여유상태입니다.\n사람이 몰려있을 가능성이 낮고 붐빔은 거의 느껴지지 않아요. 도보 이동이 자유로워요."
      }
    ]
  }
}
```

## Cloud Run 배포

### 배포된 서버 테스트

배포 URL 예시: `https://mcp-hello-py-xxxxxx.asia-northeast3.run.app/mcp`

Postman에서 URL만 변경하여 동일하게 테스트 가능합니다.

### 환경 변수 설정 (Cloud Run)

| 변수   | 값     | 설명                              |
| ------ | ------ | --------------------------------- |
| `PORT` | `8080` | Cloud Run 기본 포트 (자동 설정됨) |

## MCP Tools

### say_place

하나의 관광지를 검색합니다.

| 파라미터 | 타입   | 필수 | 설명            |
| -------- | ------ | ---- | --------------- |
| `name`   | string | O    | 검색할 관광지명 |

### say_place_multiple

여러 관광지의 상태를 한번에 검색합니다.

| 파라미터 | 타입  | 필수 | 설명            |
| -------- | ----- | ---- | --------------- |
| `names`  | array | O    | 관광지명 리스트 |

## 기술 스택

- **Python**: 3.11+
- **MCP SDK**: 1.23.0+ (FastMCP)
- **Pydantic**: 2.x
- **Uvicorn**: ASGI 서버
- **Docker**: 컨테이너화

## 전송 모드

| 모드            | 사용처                        | 엔드포인트   |
| --------------- | ----------------------------- | ------------ |
| stdio           | Claude Desktop, MCP Inspector | stdin/stdout |
| Streamable HTTP | Cloud Run, Web                | `POST /mcp`  |

## 참고

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP 문서](https://github.com/modelcontextprotocol/python-sdk)

## 라이선스

MIT License
