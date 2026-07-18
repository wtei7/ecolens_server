# 4. REST API 설계

## 공통

- Base path: `/api`
- 인증: `Authorization: Bearer <JWT>` (보호 엔드포인트)
- 응답은 일관된 형식 유지 (성공/에러 래퍼).
- 시간 필드는 ISO 8601 (UTC 권장).
- 좌표는 WGS84 (위도·경도) 기준.

## 응답 형식

성공:

```json
{ "data": { }, "meta": { } }
```

에러:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": { }
  }
}
```

---

## 인증 (auth)

### POST /api/auth/signup

회원가입.

**요청**

```json
{
  "nickname": "string",
  "email": "user@example.com",
  "password": "string (최소 8자)",
  "passwordConfirm": "string"
}
```

**검증**

- 이메일 형식
- 비밀번호 최소 8자
- 비밀번호 일치
- 닉네임 중복 확인

**응답 data**

```json
{
  "id": 1,
  "email": "user@example.com",
  "nickname": "string"
}
```

### POST /api/auth/login

로그인 → JWT 발급.

**요청**

```json
{ "email": "user@example.com", "password": "string" }
```

**응답 data**

```json
{ "accessToken": "string", "tokenType": "bearer" }
```

### GET /api/auth/me

현재 사용자 정보. (인증 필요)

**응답 data**

```json
{
  "id": 1,
  "email": "user@example.com",
  "nickname": "string",
  "totalDistance": 0,
  "totalDuration": 0,
  "totalCleanedCount": 0,
  "totalScore": 0
}
```

---

## 플로깅 세션 (plogging sessions)

### POST /api/plogging/sessions

새 세션 생성. (인증 필요)

**요청**

```json
{
  "startLatitude": 37.5665,
  "startLongitude": 126.9780,
  "startedAt": "2026-07-18T10:00:00Z"
}
```

**응답 data**

```json
{
  "id": 1,
  "status": "active",
  "startedAt": "2026-07-18T10:00:00Z",
  "startLatitude": 37.5665,
  "startLongitude": 126.9780
}
```

### GET /api/plogging/sessions

내 세션 목록 조회.

**쿼리**

- `status` (optional)
- `page`, `size` (페이징)

### GET /api/plogging/sessions/{sessionId}

세션 상세 조회.

### POST /api/plogging/sessions/{sessionId}/pause

세션 일시정지 (`active` → `paused`).

### POST /api/plogging/sessions/{sessionId}/resume

세션 재개 (`paused` → `active`).

### POST /api/plogging/sessions/{sessionId}/finish

세션 종료.

**요청 (선택)**

```json
{
  "endLatitude": 37.5712,
  "endLongitude": 126.9820,
  "endedAt": "2026-07-18T11:30:00Z"
}
```

**서버 동작**

- 위치 추적 종료 처리
- 마지막 경로 데이터 반영
- 이동 거리/활동 시간 계산
- 쓰레기 통계 집계(detected/cleaned/uncollected)
- 점수 합산
- 상태 `completed`

**응답 data**

```json
{
  "id": 1,
  "status": "completed",
  "durationSeconds": 5400,
  "distanceMeters": 1800,
  "detectedCount": 21,
  "cleanedCount": 17,
  "uncollectedCount": 4,
  "totalScore": 102
}
```

---

## 이동 경로 (route points)

### POST /api/plogging/sessions/{sessionId}/route-points

단건 좌표 저장.

**요청**

```json
{
  "latitude": 37.5665,
  "longitude": 126.9780,
  "accuracy": 5.0,
  "recordedAt": "2026-07-18T10:00:05Z"
}
```

서버는 `sequence`를 발급한다. 서비스 계층에서 노이즈 필터링 수행(정확도/속도/점프). 자세한 기준은 [05-policies.md](./05-policies.md) 참고.

### POST /api/plogging/sessions/{sessionId}/route-points/batch

좌표 일괄 저장. 모바일에서 네트워크 요청을 줄이기 위해 사용.

**요청**

```json
{
  "points": [
    { "latitude": 37.5665, "longitude": 126.9780, "accuracy": 5.0, "recordedAt": "2026-07-18T10:00:05Z" },
    { "latitude": 37.5666, "longitude": 126.9781, "accuracy": 4.5, "recordedAt": "2026-07-18T10:00:10Z" }
  ]
}
```

**응답 data**

```json
{ "accepted": 2, "rejected": 0 }
```

### GET /api/plogging/sessions/{sessionId}/route-points

해당 세션의 좌표 목록.

**응답 data**

```json
{
  "points": [
    { "latitude": 37.5665, "longitude": 126.9780, "accuracy": 5.0, "sequence": 1, "recordedAt": "2026-07-18T10:00:05Z" }
  ]
}
```

---

## 쓰레기 탐지 (AI)

### POST /api/ai/detect

이미지를 전송하여 쓰레기 탐지 결과 반환. `AI_MODE=mock`인 경우 테스트용 결과 반환.

**요청**

- `multipart/form-data`
- `image`: 이미지 파일
- (선택) `latitude`, `longitude`: 현재 위치. 탐지 결과 등록에 사용할 수 있음.

**응답 data**

```json
{
  "detections": [
    {
      "type": "plastic_bottle",
      "confidence": 0.92,
      "boundingBox": { "x": 0.31, "y": 0.48, "width": 0.19, "height": 0.23 }
    }
  ],
  "imageWidth": 640,
  "imageHeight": 480
}
```

- `boundingBox`는 0~1 비율.
- `type`은 `can`, `plastic_bottle`, `paper_cup`, `vinyl`, `general`, `glass_bottle`, `bulky`.

### POST /api/ai/verify-cleaning

Before·After 이미지 비교로 정화 여부 판정.

**요청**

- `multipart/form-data`
- `beforeImage`: 탐지 시점 이미지
- `afterImage`: 수거 후 이미지
- `trashType`: 쓰레기 종류

**응답 data**

```json
{
  "result": "cleaned",
  "confidence": 0.88
}
```

- `result`: `cleaned` | `not_cleaned` | `uncertain`
- `cleaned` → 점수 지급, `uncertain` → 재촬영 요청 또는 수동 확인 상태.

---

## 쓰레기 기록 (trash)

### POST /api/plogging/sessions/{sessionId}/trash

탐지 결과를 바탕으로 쓰레기 기록 생성. 서버에서 중복 탐지 검사 수행.

**요청**

```json
{
  "type": "plastic_bottle",
  "confidence": 0.92,
  "latitude": 37.5665,
  "longitude": 126.9780,
  "boundingBox": { "x": 0.31, "y": 0.48, "width": 0.19, "height": 0.23 },
  "beforeImageUrl": "https://cdn.../before.jpg",
  "detectedAt": "2026-07-18T10:05:00Z"
}
```

**중복 검사 조건** (모두 만족 시 기존 레코드 갱신)

- 같은 플로깅 세션
- 같은 쓰레기 종류
- 탐지 시간 차이 ≤ 15초
- 기존 기록과 거리 ≤ 8m

**응답 data (신규 생성)**

```json
{
  "id": 10,
  "status": "detected",
  "detectionCount": 1,
  "duplicate": false
}
```

**응답 data (중복 → 갱신)**

```json
{
  "id": 9,
  "status": "detected",
  "detectionCount": 3,
  "lastDetectedAt": "2026-07-18T10:05:12Z",
  "duplicate": true
}
```

### GET /api/plogging/sessions/{sessionId}/trash

세션 내 쓰레기 목록.

### GET /api/trash/{trashId}

쓰레기 상세.

### PATCH /api/trash/{trashId}

쓰레기 정보 수정(예: 상태/위치 보정).

### POST /api/trash/{trashId}/verify

After 이미지 제출 후 정화 검증 처리.

**요청**

```json
{
  "afterImageUrl": "https://cdn.../after.jpg",
  "aiResult": "cleaned",
  "aiConfidence": 0.88
}
```

**서버 동작**

- 상태 갱신: `cleaned` / `not_cleaned` / `uncertain`
- `cleaned`인 경우 점수 계산 + 저장 + 사용자 누적 점수 갱신

**응답 data**

```json
{
  "id": 10,
  "status": "cleaned",
  "score": 6,
  "cleanedAt": "2026-07-18T10:12:00Z"
}
```

---

## 환경지도 (map)

### GET /api/map/trash

지도 영역 내 쓰레기 목록 조회.

**쿼리 파라미터**

| 파라미터 | 설명 |
| --- | --- |
| `north` | 북쪽(최대 위도) |
| `south` | 남쪽(최소 위도) |
| `east` | 동쪽(최대 경도) |
| `west` | 서쪽(최소 경도) |
| `status` | `detected` / `cleaned` / `verification_pending` 등 |
| `type` | 쓰레기 종류 |
| `startDate` | 조회 시작일(ISO 8601) |
| `endDate` | 조회 종료일(ISO 8601) |

**응답 data**

```json
{
  "items": [
    {
      "id": 10,
      "type": "plastic_bottle",
      "status": "cleaned",
      "latitude": 37.5665,
      "longitude": 126.9780,
      "detectedAt": "2026-07-18T10:05:00Z"
    }
  ]
}
```

### GET /api/map/clusters

마커가 많은 경우 클러스터링 결과 반환. 줌 레벨/그리드 크기 파라미터 권장.

**쿼리 (제안)**

- `north`, `south`, `east`, `west`
- `zoom` (또는 `gridSize`)

**응답 data**

```json
{
  "clusters": [
    { "latitude": 37.566, "longitude": 126.978, "count": 12 }
  ]
}
```

구현 예시(PostGIS `ST_ClusterKMeans` / `ST_SnapToGrid`):

```sql
SELECT ST_NumGeometries(cluster) AS count,
       ST_Centroid(cluster)        AS center
FROM (
  SELECT unnest(ST_ClusterWithin(location, 0.001)) AS cluster
  FROM trash_records
  WHERE location && ST_MakeEnvelope(:west, :south, :east, :north, 4326)
) t;
```

---

## 리포트 (report)

### GET /api/plogging/sessions/{sessionId}/report

활동 리포트.

**응답 data (요약 — 실제 schema는 더 상세)**

```json
{
  "sessionId": 1,
  "date": "2026-07-18",
  "durationSeconds": 5400,
  "distanceMeters": 1800,
  "totalScore": 102,
  "region": "서울특별시 중구",
  "detectedCount": 21,
  "cleanedCount": 17,
  "uncollectedCount": 4,
  "cleanupRate": 0.81,
  "byType": [
    { "type": "plastic_bottle", "count": 10, "cleanedCount": 9, "rate": 0.9 }
  ],
  "mostCleanedType": "plastic_bottle",
  "summary": "오늘은 1.8km를 이동하며 총 21개의 쓰레기를 발견했습니다. 그중 17개를 정화하여 81%의 정화율을 기록했습니다. 가장 많이 발견된 쓰레기는 페트병이며, 공원 입구에서 쓰레기가 집중적으로 탐지되었습니다."
}
```

**정화율**

```text
정화율 = 정화 완료 수 / 발견한 쓰레기 수 × 100
```

**자동 요약 문장**: MVP는 규칙 기반 문장 생성 → 이후 LLM 확장.

### GET /api/users/me/statistics

내 누적 통계.

**응답 data**

```json
{
  "totalDistance": 12500,
  "totalDuration": 16200,
  "totalCleanedCount": 47,
  "totalScore": 285
}
```

---

## HTTP 상태 코드 규칙

| 코드 | 용도 |
| --- | --- |
| 200 | 성공 (GET, 일반 응답) |
| 201 | 생성 성공 (POST로 자원 생성) |
| 204 | 내용 없는 성공 (일부 DELETE/POST) |
| 400 | 잘못된 요청 / 검증 실패 |
| 401 | 인증 필요 / 토큰 없음 |
| 403 | 권한 없음 |
| 404 | 리소스 없음 |
| 409 | 충돌 (중복 이메일/닉네임 등) |
| 422 | Pydantic 검증 실패 (FastAPI 기본) |
| 500 | 서버 오류 |

에러 응답은 공통 에러 래퍼 사용.