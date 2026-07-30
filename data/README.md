# 데이터 안내

## 폴더 원칙

- `raw/`: 원본을 수정하지 않고 보관하는 위치
- `processed/`: 코드로 다시 만들 수 있는 가공 데이터
- `data-dictionary.csv`: 열 의미·타입·단위
- `jipfit_demo.db`: SQLite 데모 DB

## 포함 데이터

### `processed/synthetic_housing_scenarios.csv`

- 행 수: 6,000
- 생성 코드: `src/data_generation.py`
- 랜덤 시드: 42
- 실제 개인·계좌·신용 데이터 없음
- 목적: 모델 학습·평가·앱 연결의 기술 검증

재생성:

```bash
python -m src.data_generation --rows 6000 --seed 42
```

### `processed/policy_catalog.csv`

공식 MyHome 페이지에서 확인한 정책명·분류·출처·확인일을 기록한다. 일부 공개 조건은 `src/policy_engine.py`에서 단순화 사전진단에 사용한다. 실제 자격 확정은 공식 기관이 수행한다.

### `processed/regional_cost_index.csv`

17개 시도의 상대 주거비 차이를 표현하기 위한 데모 지수다. 실거래 시세나 공공 통계가 아니며, 실제 버전에서는 검증된 임대료 데이터로 교체해야 한다.

## 품질 점검

`python scripts/bootstrap.py` 실행 시 `reports/data-quality.json`에 다음을 기록한다.

- 행·열 수
- 결측 셀 수
- 중복 행 수
- 클래스 분포
- 주요 수치 범위

## 이용 주의

정책·금융 정보는 변경될 수 있다. 데이터 파일의 `verified_at`과 공식 페이지를 함께 확인한다.
