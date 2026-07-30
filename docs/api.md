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
    "unhoused": True,
    "separate_household": True,
    "unmarried": True,
}
```

모든 금액은 원 단위다.

### 출력

- `profile_summary`: 지역 지수와 고지문
- `affordability`: 월 환산 주거비, 권장 상한, 주거비 비율, 잔여금액
- `model`: 위험 클래스, 확률, 모델 메타데이터
- `policies`: 정책별 상태·점수·통과·실패·수동 확인 항목
- `action_plan`: 다음 행동 3개
- `session_id`: 로그 저장 시 익명 세션 ID
- `disclaimer`: 금융·정책 자격 비확정 고지

### 오류

- 필수 입력 누락: `ValueError`
- 미지원 지역: `ValueError`
- 모델·정책 파일 누락: `FileNotFoundError`
