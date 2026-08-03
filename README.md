# 집핏 AI (JipFit AI)

> **내 소득에 맞는 집, 받을 수 있는 지원까지**

- 팀명: **원루프랩 (OneRoof Lab)**
- 참가 형태: 1인 팀
- 대회 주제: 청년 주거 금융 도우미
- 구현 형태: Streamlit 웹앱 + 설명 가능한 정책 엔진 + ML 부담 위험 분류

집핏 AI는 청년이 소득·자산·희망 지역과 검토 중인 집의 보증금·월세·관리비를 입력하면 다음을 한 화면에 보여주는 주거 금융 사전진단 프로토타입이다.

1. 월세·관리비·보증금 월 환산액을 합친 **순수 월 주거비**
2. 부채상환까지 포함한 **주거·부채 통합 고정비**
3. 월소득 30% 기준 **생활 안정 권장선과 초과·여유 금액**
4. 합성 데이터 기반 **AI 참고 위험도**
5. 핵심요건 미충족·확인 필요를 구분하는 **정책 사전진단 결과**
6. 사용자가 바로 실행할 **다음 행동 3개**

> 이 결과는 참고용 사전 안내이며 실제 대출 승인이나 정책 수급 자격을 확정하지 않는다. 실제 신청 전 공식 기관의 최신 기준과 심사 절차를 확인해야 한다.

---

## 1. 빠른 실행

### Windows — 가장 쉬운 방법

프로젝트 폴더에서 다음 파일을 순서대로 실행한다.

```text
1. setup_windows.bat
2. run_app.bat
```

`setup_windows.bat`은 가상환경 생성, 패키지 설치, 합성 데이터·DB·모델 생성, 테스트를 한 번에 수행한다.

### Windows PowerShell / macOS / Linux

```bash
# 프로젝트 루트에서 실행
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/bootstrap.py
python scripts/validate_project.py
streamlit run app.py
```

정상 실행 시 브라우저에서 집핏 AI 입력 화면이 열린다.

### 웹 화면 없이 CLI 데모

```bash
python scripts/run_demo.py
```

---

## 2. 데모 입력과 예상 결과

기본 예시:

- 27세, 월소득 300만원, 자산 1,000만원
- 서울, 보증금 1,000만원
- 월세 65만원, 관리비 10만원
- 월 부채상환 20만원

현재 포함된 모델과 규칙에서는 다음과 같은 결과가 생성된다.

- 순수 월 주거비: 약 78.3만 원
- 주거·부채 통합 고정비: 약 98.3만 원
- 생활 안정 권장선: 90.0만 원
- 권장선 대비 초과액: 약 8.3만 원
- AI 참고 위험도: 합성 데이터 기반 보조 지표
- 우선 확인 정책: 행복주택 청년계층, 청년전용 보증부월세대출, 청년 보증료 지원

전체 예시 JSON은 `assets/demo_result.json`에 있다.

---

## 3. 왜 하이브리드 AI인가

```text
정확한 금액 계산              다변수 위험 패턴              정책 조건 설명
규칙 기반 Affordability  +  ML Classifier          +  Policy Engine
```

- **생활 안정 권장선**은 월소득의 30% 기준으로 표시해 사용자가 계산 근거를 바로 확인할 수 있게 한다.
- **규칙 기반 부담 단계**는 순수 주거비와 부채 포함 통합 고정비를 우선 반영한다.
- **AI 참고 위험도**는 소득, 자산, 보증금, 월세, 관리비, 부채, 가구원수, 고용 상태, 지역지수의 결합 패턴을 보조 지표로 제시한다.
- **정책 사전진단**은 핵심요건 미충족, 확인 필요, 높은 적합도를 구분해 과도한 자동 추천을 피한다.

---

## 4. 모델 결과

`python scripts/bootstrap.py`가 6,000개의 재현 가능한 합성 시나리오를 생성하고 세 모델을 비교한다.

| 모델 | 정확도 | Macro F1 |
|---|---:|---:|
| 다수 클래스 기준선 | 0.6617 | 0.2655 |
| 로지스틱 회귀 | **0.9375** | **0.9185** |
| 랜덤 포레스트 | 0.9050 | 0.8600 |

선택 모델: **로지스틱 회귀**

이 수치는 합성 테스트셋에서 파이프라인이 정상 작동한다는 기술 검증값이다. 실제 청년의 금융·주거 결과에 대한 성능을 의미하지 않는다. 상세 지표와 혼동행렬은 `reports/metrics.json`, 오류 사례는 `reports/error-analysis.md`에 있다.

---

## 5. 정책 사전진단 원칙

정책 카탈로그는 다음 항목을 포함한다.

- 청년월세 지원사업
- 행복주택 청년계층
- 청년버팀목전세자금
- 청년전용 보증부월세대출
- 청년 보증료 지원

공개 조건이 명확한 항목만 자동 확인한다. 원가구 소득·재산, 중복 수혜, 세대 범위, 최신 모집공고, 대출한도와 금리는 `공식 확인 필요`로 남긴다. 출처와 확인일은 `docs/source-notes.md`와 `data/processed/policy_catalog.csv`에 기록했다.

---

## 6. 파일 구조

```text
jipfit-ai/
├─ app.py                         # Streamlit 발표용 앱
├─ README.md
├─ requirements.txt
├─ pyproject.toml
├─ setup_windows.bat              # Windows 최초 설정
├─ run_app.bat                    # Windows 앱 실행
├─ project_state.json
├─ assets/
│  ├─ logo.svg
│  └─ demo_result.json
├─ data/
│  ├─ README.md
│  ├─ data-dictionary.csv
│  ├─ jipfit_demo.db              # 생성된 SQLite 데모 DB
│  ├─ raw/
│  └─ processed/
│     ├─ policy_catalog.csv
│     ├─ regional_cost_index.csv
│     └─ synthetic_housing_scenarios.csv
├─ design/
│  ├─ user-flow.md
│  ├─ figma-handoff.md
│  └─ design-tokens.json
├─ docs/
│  ├─ brief.md
│  ├─ competition-fit.md
│  ├─ architecture.md
│  ├─ api.md
│  ├─ privacy.md
│  ├─ source-notes.md
│  ├─ demo-script.md
│  ├─ pitch-outline.md
│  ├─ judge-qna.md
│  ├─ 4-day-plan.md
│  ├─ testing.md
│  └─ submission-checklist.md
├─ models/
│  ├─ burden_model.joblib
│  └─ README.md
├─ notebooks/
│  └─ 01_eda.ipynb
├─ reports/
│  ├─ metrics.json
│  ├─ data-quality.json
│  ├─ error-analysis.md
│  └─ project-validation.json      # 검증 실행 후 생성
├─ scripts/
│  ├─ bootstrap.py
│  ├─ run_demo.py
│  ├─ validate_sqlite.py
│  ├─ validate_project.py
│  └─ package_submission.py
├─ sql/
│  ├─ schema.sql
│  ├─ seed.sql
│  ├─ queries.sql
│  ├─ tests.sql
│  └─ validation-report.json       # 검증 실행 후 생성
├─ src/
│  ├─ affordability.py
│  ├─ data_generation.py
│  ├─ train.py
│  ├─ predict.py
│  ├─ policy_engine.py
│  ├─ database.py
│  └─ service.py
├─ submission/
│  └─ one-page-summary.md
└─ tests/
   ├─ test_affordability.py
   ├─ test_policy_engine.py
   ├─ test_database.py
   └─ test_model_and_service.py
```

---

## 7. 재현 명령

### 데이터·DB·모델 다시 생성

```bash
python scripts/bootstrap.py
```

생성 결과:

- `data/processed/synthetic_housing_scenarios.csv`
- `data/jipfit_demo.db`
- `models/burden_model.joblib`
- `reports/metrics.json`
- `reports/data-quality.json`
- `assets/demo_result.json`

### 전체 검증

```bash
python scripts/validate_project.py
```

검증 항목:

- 필수 파일
- Python 문법
- SQLite 스키마·시드·쿼리·무결성
- Pytest 단위·통합 테스트
- CLI 전체 흐름
- 모델 성능 기준선 비교

### 제출 ZIP 만들기

```bash
python scripts/package_submission.py
```

---

## 8. 발표 준비

- 3분 데모: `docs/demo-script.md`
- 7장 발표 구성: `docs/pitch-outline.md`
- 예상 질문: `docs/judge-qna.md`
- 4일 계획: `docs/4-day-plan.md`
- 제출 점검: `docs/submission-checklist.md`
- 한 장 요약: `submission/one-page-summary.md`

---

## 9. 한계와 다음 단계

현재 지역지수와 학습 데이터는 데모용이다. 실제 서비스로 확장하려면 다음이 필요하다.

1. 국토교통부 실거래 임대료·관리비 등 실제 지역 데이터 연결
2. 정책 조건의 구조화된 자동 갱신과 변경 감지
3. 사용자 동의 기반 익명 현금흐름 데이터로 외부 검증
4. 지역·소득구간별 오류와 공정성 점검
5. 금융기관 상담·보증·정책 신청 단계와 안전한 연결

---

## Team

**원루프랩 (OneRoof Lab)** — 한 사람이어도, 한 지붕 아래의 더 나은 선택을 끝까지 만든다.
