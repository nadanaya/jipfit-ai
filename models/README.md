# 모델 안내

## 파일

- `burden_model.joblib`: 학습된 모델과 메타데이터를 함께 저장한 아티팩트

## 생성

```bash
python scripts/bootstrap.py
```

또는 데이터가 이미 있을 때:

```bash
python -m src.train
```

## 입력 특징

- age
- monthly_income
- assets
- deposit
- monthly_rent
- management_fee
- monthly_debt_payment
- household_size
- region_cost_index
- is_unemployed
- car_value

## 출력

- 0: 안정
- 1: 주의
- 2: 위험
- 클래스별 예측확률

## 선택 방식

다수 클래스 기준선, 로지스틱 회귀, 랜덤 포레스트를 같은 분할에서 비교하고 macro F1이 높은 비기준 모델을 저장한다.

## 모델 카드 요약

- 데이터: 코드로 생성한 합성 시나리오 6,000건
- 목적: 주거비 부담 위험분류 흐름 검증
- 금지 용도: 대출 승인, 정책 자격 확정, 신용평가, 자동 계약 거절
- 주요 위험: 현실 분포와 합성 분포 차이, 경계 사례, 지역지수의 가상성
- 다음 검증: 익명 실제 데이터 외부검증, 지역·소득구간별 오류, 시간적 안정성
