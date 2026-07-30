"""Streamlit entry point for JipFit AI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import RISK_LABELS
from src.service import analyze_profile, load_region_index

TEAM_NAME = "원루프랩"
SERVICE_NAME = "집핏 AI"
TAGLINE = "내 소득에 맞는 집, 받을 수 있는 지원까지"

st.set_page_config(
    page_title=f"{SERVICE_NAME} | {TEAM_NAME}",
    page_icon="🏠",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1180px; padding-top: 1.6rem; padding-bottom: 3rem;}
    .brand-card {padding: 1.2rem 1.4rem; border-radius: 18px; background: linear-gradient(120deg,#fff7cc,#f8fbff); border: 1px solid #e7e1b8; margin-bottom: 1rem;}
    .brand-title {font-size: 2.05rem; font-weight: 800; letter-spacing: -0.04em; margin-bottom: .2rem;}
    .brand-sub {color: #45515f; font-size: 1.02rem;}
    .result-card {padding: 1rem 1.1rem; border-radius: 16px; border: 1px solid #e4e8ee; background: white; min-height: 145px;}
    .risk-0 {border-left: 7px solid #1c8c5c;}
    .risk-1 {border-left: 7px solid #e6a700;}
    .risk-2 {border-left: 7px solid #d94343;}
    .small-note {font-size: .84rem; color: #68717d;}
    .policy-title {font-weight: 750; font-size: 1.05rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="brand-card">
      <div class="brand-title">🏠 {SERVICE_NAME}</div>
      <div class="brand-sub">{TAGLINE} · {TEAM_NAME}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write(
    "월세·관리비·보증금의 월 환산비용과 부채상환액을 함께 계산해 **권장 주거비**, "
    "**AI 부담 위험**, **청년 주거정책 후보**를 한 번에 보여주는 주거 금융 사전진단 프로토타입입니다."
)

regions = list(load_region_index().keys())

with st.form("profile_form"):
    st.subheader("1. 내 조건과 검토 중인 집 입력")
    c1, c2, c3 = st.columns(3)
    with c1:
        age = st.number_input("나이", min_value=19, max_value=60, value=27, step=1)
        monthly_income_man = st.number_input("월 소득 (만원)", min_value=50, max_value=2000, value=300, step=10)
        assets_man = st.number_input("총자산 (만원)", min_value=0, max_value=100000, value=1000, step=100)
        car_value_man = st.number_input("자동차 가액 (만원)", min_value=0, max_value=20000, value=0, step=100)
    with c2:
        region = st.selectbox("희망 거주 지역", regions, index=0)
        household_size = st.number_input("청년가구 가구원수", min_value=1, max_value=8, value=1, step=1)
        employment = st.selectbox("고용 상태", ["재직·소득 있음", "미취업·소득 불안정"], index=0)
        monthly_debt_man = st.number_input("월 부채상환액 (만원)", min_value=0, max_value=1000, value=20, step=5)
    with c3:
        deposit_man = st.number_input("임차보증금 (만원)", min_value=0, max_value=100000, value=1000, step=100)
        rent_man = st.number_input("월세 (만원)", min_value=0, max_value=1000, value=65, step=5)
        management_man = st.number_input("관리비 (만원)", min_value=0, max_value=300, value=10, step=1)

    st.markdown("**정책 사전진단 확인 항목**")
    p1, p2, p3 = st.columns(3)
    with p1:
        unhoused = st.checkbox("무주택", value=True)
    with p2:
        separate_household = st.checkbox("부모와 별도 거주", value=True)
    with p3:
        unmarried = st.checkbox("현재 미혼", value=True)

    submitted = st.form_submit_button("내 주거 선택 분석하기", type="primary", use_container_width=True)

if not submitted:
    st.info("기본값은 서울 거주를 검토하는 27세 1인 가구 예시입니다. 값을 바꾸고 분석 버튼을 눌러 보세요.")
    flow = pd.DataFrame(
        {
            "단계": ["① 조건 입력", "② 부담 분석", "③ 정책 후보", "④ 실행 계획"],
            "결과": ["소득·자산·주거비", "권장 상한·AI 위험", "통과/확인/불일치 이유", "다음 행동 3개"],
        }
    )
    st.dataframe(flow, hide_index=True, use_container_width=True)
    st.stop()

profile = {
    "age": int(age),
    "monthly_income": int(monthly_income_man * 10_000),
    "assets": int(assets_man * 10_000),
    "deposit": int(deposit_man * 10_000),
    "monthly_rent": int(rent_man * 10_000),
    "management_fee": int(management_man * 10_000),
    "monthly_debt_payment": int(monthly_debt_man * 10_000),
    "household_size": int(household_size),
    "region": region,
    "is_unemployed": employment == "미취업·소득 불안정",
    "car_value": int(car_value_man * 10_000),
    "unhoused": bool(unhoused),
    "separate_household": bool(separate_household),
    "unmarried": bool(unmarried),
}

try:
    result = analyze_profile(profile, log_result=True)
except Exception as error:  # pragma: no cover - Streamlit presentation path
    st.error(f"분석을 완료하지 못했습니다: {error}")
    st.code("python scripts/bootstrap.py", language="bash")
    st.stop()

afford = result["affordability"]
model = result["model"]
risk_class = int(model["class_id"])

st.divider()
st.subheader("2. 주거비 진단 결과")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("실제 월 주거비", f"{afford['monthly_housing_cost'] / 10_000:,.1f}만원")
with m2:
    st.metric("권장 주거비", f"{afford['recommended_max_housing_cost'] / 10_000:,.1f}만원")
with m3:
    st.metric("소득 대비 비율", f"{afford['affordability_ratio'] * 100:.1f}%")
with m4:
    delta = afford["monthly_gap_to_recommendation"] / 10_000
    st.metric(
        "권장 주거비 대비 여유",
        f"{abs(delta):,.1f}만원",
        delta=(f"+{delta:,.1f}만원 여유" if delta >= 0 else f"-{abs(delta):,.1f}만원 초과"),
        delta_color="normal",
    )

left, right = st.columns([1.05, 1])
with left:
    st.markdown(
        f"""
        <div class="result-card risk-{risk_class}">
          <div class="small-note">AI 주거비 부담 위험</div>
          <h2 style="margin:.25rem 0 .45rem 0;">{model['label']}</h2>
          <div>{model['description']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if model["probabilities"]:
        prob_frame = pd.DataFrame(
            {
                "등급": list(model["probabilities"].keys()),
                "확률": list(model["probabilities"].values()),
            }
        ).set_index("등급")
        st.bar_chart(prob_frame)
with right:
    budget_frame = pd.DataFrame(
        {
            "항목": ["월세", "관리비", "보증금 월 환산", "부채상환", "주거·부채 제외 잔액"],
            "만원": [
                profile["monthly_rent"] / 10_000,
                profile["management_fee"] / 10_000,
                afford["deposit_monthly_equivalent"] / 10_000,
                profile["monthly_debt_payment"] / 10_000,
                max(0, afford["disposable_after_housing_and_debt"]) / 10_000,
            ],
        }
    ).set_index("항목")
    st.caption("월 현금흐름 구성")
    st.bar_chart(budget_frame)
    st.caption(
        "보증금은 연 4%의 기회비용을 월 단위로 환산한 데모 가정입니다. "
        "지역지수도 실거래 시세가 아닌 데모 상대지수입니다."
    )

st.subheader("3. 청년 주거정책 후보")
st.caption("사전진단 통과는 공식 승인이나 수급 확정을 뜻하지 않습니다. 표시된 수동 확인 항목까지 공식 페이지에서 검토해야 합니다.")

policy_table = pd.DataFrame(
    [
        {
            "정책": item["name"],
            "분류": item["category"],
            "상태": item["status"],
            "적합도": item["score"],
            "기준 확인일": item["verified_at"],
        }
        for item in result["policies"]
    ]
)
st.dataframe(policy_table, hide_index=True, use_container_width=True)

for item in result["policies"]:
    with st.expander(f"{item['status']} · {item['name']} ({item['score']}점)"):
        st.write(item["description"])
        if item["passed_checks"]:
            st.markdown("**입력상 맞는 조건**")
            for message in item["passed_checks"]:
                st.write(f"✅ {message}")
        if item["failed_checks"]:
            st.markdown("**현재 입력과 맞지 않는 조건**")
            for message in item["failed_checks"]:
                st.write(f"⚠️ {message}")
        if item["manual_checks"]:
            st.markdown("**공식 페이지에서 추가 확인**")
            for message in item["manual_checks"]:
                st.write(f"🔎 {message}")
        st.link_button("공식 정보 확인", item["official_url"])
        st.caption(f"기준 확인일 {item['verified_at']} · {item['source_note']}")

st.subheader("4. 지금 할 일")
for index, action in enumerate(result["action_plan"], start=1):
    st.write(f"**{index}.** {action}")

with st.expander("모델과 데이터의 한계"):
    st.write(
        "AI 분류 모델은 서비스 흐름을 검증하기 위해 만든 합성 데이터로 학습했습니다. "
        "현실 배포 전에는 익명화된 실제 현금흐름·임대료 데이터로 외부 검증, 편향 점검, 정책 기준 자동 갱신이 필요합니다."
    )
    st.write(f"사용 모델: `{model['model_name']}`")
    st.write(model["data_notice"])

st.warning(result["disclaimer"])
st.caption(f"{TEAM_NAME} · {SERVICE_NAME}")
