# 내부 분석 API 계약

프로토타입은 별도 HTTP 서버 대신 Python 함수 계약을 사용한다.

## `src.service.analyze_profile(profile, log_result=False)`

### 입력

```python
profile = {
    "age": 27,
    "monthly_income": 3_000_000,
    "assets": 10_000_000,
    "deposit": 10_000_000,
    "monthly_rent": 650_000,
    "management_fee": 100_000,
    "monthly_debt_payment": 200_000,
    "household_size": 1,
    "region": "서울",
    "is_unemployed": False,
    "car_value": 0,
    "unhoused_status": "예",
    "separate_household_status": "예",
    "unmarried_status": "혼인 중이 아님",
}
```

모든 금액은 원 단위다.

### 출력

- `profile_summary`: 지역 지수와 고지문
- `affordability`: 순수 월 주거비, 주거·부채 통합 고정비, 생활 안정 권장선, 초과·여유 금액
- `model`: 규칙 기반 부담 단계, AI 참고 위험도, 모델 메타데이터
- `policies`: 정책별 판정 상태, 참고 적합도, 충족 조건, 미충족 조건, 추가 확인 조건
- `action_plan`: 다음 행동 3개
- `session_id`: 로그 저장 시 익명 세션 ID
- `disclaimer`: 금융·정책 자격 비확정 고지

### 오류

- 필수 입력 누락: `ValueError`
- 미지원 지역: `ValueError`
- 모델·정책 파일 누락: `FileNotFoundError`
