# API 명세서

## 기본 정보

- **Base URL**: `https://madcamp-w1-coffee-note-backend-production.up.railway.app`
- **Content-Type**: `application/json`
- **프로토콜**: HTTPS

---

## 엔드포인트

### 1. 헬스체크

서비스의 건강 상태를 확인하는 엔드포인트입니다.

**요청**
```
GET /health
```

**응답**
```json
{
  "status": "ok"
}
```

**상태 코드**
- `200 OK`: 서비스 정상 동작 중

---

### 2. 채팅 (일반)

일반적인 AI 채팅 기능을 제공하는 엔드포인트입니다.

**요청**
```
POST /chat
```

**요청 본문**
```json
{
  "message": "안녕하세요"
}
```

**요청 필드**
| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| message | string | ✅ | 사용자 메시지 |

**응답**
```json
{
  "message": "AI 응답 메시지"
}
```

**응답 필드**
| 필드명 | 타입 | 설명 |
|--------|------|------|
| message | string | AI가 생성한 응답 메시지 |

**상태 코드**
- `200 OK`: 요청 성공
- `500 Internal Server Error`: 서비스 내부 오류

**예시**
```bash
curl -X POST https://madcamp-w1-coffee-note-backend-production.up.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'
```

---

### 3. 채팅 (매핑용)

커피 정보를 추출하여 구조화된 데이터로 반환하는 엔드포인트입니다.

**요청**
```
POST /chat-for-mapping
```

**요청 본문**
```json
{
  "message": "과테말라 워시드 라이트 로스팅 에스프레소로 추출한 커피, 플로럴하고 시트러스한 맛"
}
```

**요청 필드**
| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| message | string | ✅ | 커피 정보가 포함된 사용자 메시지 |

**응답**
```json
{
  "location": "과테말라",
  "variety": "원산지 품종",
  "process": "WASHED",
  "process_text": "워시드",
  "roasting_point": "LIGHT",
  "roasting_point_text": "라이트",
  "method": "ESPRESSO",
  "method_text": "에스프레소",
  "tasting_notes": ["플로럴", "시트러스"]
}
```

**응답 필드**
| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| location | string | ❌ | 국가 및 지역 (예: "과테말라", "에티오피아 예가체프") |
| variety | string | ❌ | 원산지 품종 |
| process | enum | ❌ | 가공 방식의 enum 값 (`WASHED`, `NATURAL`, `PULPED_NATURAL`, `HONEY`, `ETC` 중 하나) |
| process_text | string | ❌ | 가공 방식의 원문 (사용자 입력에 그대로 있던 표현, 예: "워시드", "내추럴") |
| roasting_point | enum | ❌ | 로스팅 지점의 enum 값 (`LIGHT`, `MEDIUM`, `MEDIUM_DARK`, `DARK`, `ETC` 중 하나) |
| roasting_point_text | string | ❌ | 로스팅 지점의 원문 (사용자 입력에 그대로 있던 표현, 예: "라이트", "미디움") |
| method | enum | ❌ | 추출 방법의 enum 값 (`ESPRESSO`, `FILTER`, `COLD_BREW`, `ETC` 중 하나) |
| method_text | string | ❌ | 추출 방법의 원문 (사용자 입력에 그대로 있던 표현, 예: "에스프레소", "필터") |
| tasting_notes | string[] | ✅ | 맛, 향 등 테이스팅 노트 (최대 5개) |

**Enum 값**

**Process (가공 방식)**
- `WASHED`: 워시드
- `NATURAL`: 내추럴
- `PULPED_NATURAL`: 풀프드 내추럴
- `HONEY`: 허니
- `ETC`: 기타

**RoastingPoint (로스팅 지점)**
- `LIGHT`: 라이트
- `MEDIUM`: 미디움
- `MEDIUM_DARK`: 미디움 다크
- `DARK`: 다크
- `ETC`: 기타

**Method (추출 방법)**
- `ESPRESSO`: 에스프레소
- `FILTER`: 필터
- `COLD_BREW`: 콜드브루
- `ETC`: 기타

**상태 코드**
- `200 OK`: 요청 성공
- `500 Internal Server Error`: 서비스 내부 오류

**예시**
```bash
curl -X POST https://madcamp-w1-coffee-note-backend-production.up.railway.app/chat-for-mapping \
  -H "Content-Type: application/json" \
  -d '{
    "message": "과테말라 워시드 라이트 로스팅 에스프레소로 추출한 커피, 플로럴하고 시트러스한 맛"
  }'
```

---

### 4. 채팅 (센서리 가이드용)

커피 정보를 추출하여 구조화된 데이터와 함께 초보자를 위한 센서리 가이드를 제공하는 엔드포인트입니다.

**요청**
```
POST /chat-for-sensory-guide
```

**요청 본문**
```json
{
  "message": "과테말라 워시드 라이트 로스팅 에스프레소로 추출한 커피, 플로럴하고 시트러스한 맛"
}
```

**요청 필드**
| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| message | string | ✅ | 커피 정보가 포함된 사용자 메시지 |

**응답**
```json
{
  "mapping_result": {
    "location": "과테말라",
    "variety": "원산지 품종",
    "process": "WASHED",
    "process_text": "워시드",
    "roasting_point": "LIGHT",
    "roasting_point_text": "라이트",
    "method": "ESPRESSO",
    "method_text": "에스프레소",
    "tasting_notes": ["플로럴", "시트러스"]
  },
  "sensory_guide": "이 커피는 플로럴하고 시트러스한 향이 특징입니다. 처음 마실 때는 꽃향기를 느껴보시고, 입 안에서는 상큼한 시트러스 풍미를 음미해보세요."
}
```

**응답 필드**
| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| mapping_result | object | ✅ | 매핑 결과 (ChatForMapping.Response와 동일한 구조) |
| mapping_result.location | string | ❌ | 국가 및 지역 (예: "과테말라", "에티오피아 예가체프") |
| mapping_result.variety | string | ❌ | 원산지 품종 |
| mapping_result.process | enum | ❌ | 가공 방식의 enum 값 (`WASHED`, `NATURAL`, `PULPED_NATURAL`, `HONEY`, `ETC` 중 하나) |
| mapping_result.process_text | string | ❌ | 가공 방식의 원문 (사용자 입력에 그대로 있던 표현, 예: "워시드", "내추럴") |
| mapping_result.roasting_point | enum | ❌ | 로스팅 지점의 enum 값 (`LIGHT`, `MEDIUM`, `MEDIUM_DARK`, `DARK`, `ETC` 중 하나) |
| mapping_result.roasting_point_text | string | ❌ | 로스팅 지점의 원문 (사용자 입력에 그대로 있던 표현, 예: "라이트", "미디움") |
| mapping_result.method | enum | ❌ | 추출 방법의 enum 값 (`ESPRESSO`, `FILTER`, `COLD_BREW`, `ETC` 중 하나) |
| mapping_result.method_text | string | ❌ | 추출 방법의 원문 (사용자 입력에 그대로 있던 표현, 예: "에스프레소", "필터") |
| mapping_result.tasting_notes | string[] | ✅ | 맛, 향 등 테이스팅 노트 (최대 5개) |
| sensory_guide | string | ✅ | 초보자를 위한 센서리 가이드 메시지 (2~3줄 내외) |

**Enum 값**

매핑 결과의 enum 값은 `/chat-for-mapping` 엔드포인트와 동일합니다.

**상태 코드**
- `200 OK`: 요청 성공
- `500 Internal Server Error`: 서비스 내부 오류

**예시**
```bash
curl -X POST https://madcamp-w1-coffee-note-backend-production.up.railway.app/chat-for-sensory-guide \
  -H "Content-Type: application/json" \
  -d '{
    "message": "과테말라 워시드 라이트 로스팅 에스프레소로 추출한 커피, 플로럴하고 시트러스한 맛"
  }'
```

---

## 에러 처리

### 에러 응답 형식

모든 에러는 다음 형식으로 반환됩니다:

```json
{
  "detail": "에러 메시지"
}
```

### 상태 코드

- `200 OK`: 요청 성공
- `500 Internal Server Error`: 서비스 내부 오류

---

## 주의사항

1. 모든 요청은 HTTPS를 통해 전송되어야 합니다.
2. 요청 본문은 반드시 `Content-Type: application/json` 헤더를 포함해야 합니다.
3. `/chat-for-mapping` 및 `/chat-for-sensory-guide` 엔드포인트의 `tasting_notes` 배열은 최대 5개까지만 포함됩니다.
4. `/chat-for-sensory-guide` 엔드포인트는 웹 검색을 통해 커피 정보를 수집한 후, 매핑 결과와 함께 초보자를 위한 센서리 가이드를 제공합니다.
4. 모든 enum 필드는 대문자로 반환됩니다.

---