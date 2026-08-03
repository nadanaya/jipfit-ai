"""Streamlit entry point for JipFit AI."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import altair as alt

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
    .brand-card {padding: 1.2rem 1.4rem; border-radius: 8px; background: #fffaf0; border: 1px solid #ead99f; margin-bottom: 1rem;}
    .brand-title {font-size: 2.05rem; font-weight: 800; letter-spacing: 0; margin-bottom: .2rem;}
    .brand-sub {color: #45515f; font-size: 1.02rem;}
    .result-card {padding: 1rem 1.1rem; border-radius: 8px; border: 1px solid #e4e8ee; background: white; min-height: 145px;}
    .risk-0 {border-left: 7px solid #1c8c5c;}
    .risk-1 {border-left: 7px solid #e6a700;}
    .risk-2 {border-left: 7px solid #d94343;}
    .small-note {font-size: .9rem; color: #4f5b68;}
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
    "월세·관리비·보증금의 월 환산비용과 부채상환액을 함께 계산해 **순수 주거비**, "
    "**부채 포함 통합 고정비**, **부담 단계**, **정책 사전진단 결과**를 보여주는 "
    "주거 금융 사전진단 프로토타입입니다."
)
st.caption(
    "생활 안정 권장선은 월소득의 30%를 기준으로 한 참고선입니다. "
    "금융기관의 공식 대출 심사 기준이나 정책 수급 자격 확정 기준이 아닙니다."
)

regions = list(load_region_index().keys())

has_saved_result = "last_profile" in st.session_state
with st.expander("1. 조건 입력", expanded=not has_saved_result):
    if has_saved_result:
        saved = st.session_state["last_profile"]
        st.caption(
            f"{saved['age']}세 · {saved['region']} · 월소득 {saved['monthly_income'] / 10_000:,.0f}만 원 · "
            f"월세 {saved['monthly_rent'] / 10_000:,.0f}만 원"
        )
    with st.form("profile_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            age = st.number_input("나이", min_value=19, max_value=60, value=27, step=1)
            monthly_income_man = st.number_input("월 소득 (만원)", min_value=50, max_value=2000, value=300, step=10)
            assets_man = st.number_input("총자산 (만원)", min_value=0, max_value=100000, value=1000, step=100)
            car_value_man = st.number_input("자동차 가액 (만원)", min_value=0, max_value=20000, value=0, step=100)
        with c2:
            region = st.selectbox("거주 지역", regions, index=0)
            household_size = st.number_input("청년가구 가구원수", min_value=1, max_value=8, value=1, step=1)
            employment = st.selectbox("고용 상태", ["재직·소득 있음", "미취업·소득 불안정"], index=0)
            monthly_debt_man = st.number_input("월 부채상환액 (만원)", min_value=0, max_value=1000, value=20, step=5)
        with c3:
            deposit_man = st.number_input("임차보증금 (만원)", min_value=0, max_value=100000, value=1000, step=100)
            rent_man = st.number_input("월세 (만원)", min_value=0, max_value=1000, value=65, step=5)
            management_man = st.number_input("관리비 (만원)", min_value=0, max_value=300, value=10, step=1)

        st.markdown("**정책 사전진단 확인 항목**")
        st.caption("본인 또는 정책별 세대 범위 내 구성원이 주택·분양권·입주권을 보유하면 ‘아니오’를 선택하세요.")
        p1, p2, p3 = st.columns(3)
        with p1:
            unhoused_status = st.radio("무주택 여부", ["예", "아니오", "잘 모르겠음"], horizontal=True)
        with p2:
            separate_household_status = st.radio("부모와 별도 거주", ["예", "아니오", "잘 모르겠음"], horizontal=True)
        with p3:
            unmarried_status = st.radio("혼인 상태", ["혼인 중이 아님", "혼인 중", "잘 모르겠음"], horizontal=True)

        submitted = st.form_submit_button("주거 선택 분석하기", type="primary", use_container_width=True)

current_profile = {
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
    "unhoused": unhoused_status == "예",
    "separate_household": separate_household_status == "예",
    "unmarried": unmarried_status == "혼인 중이 아님",
    "unhoused_status": unhoused_status,
    "separate_household_status": separate_household_status,
    "unmarried_status": unmarried_status,
}

if submitted:
    st.session_state["last_profile"] = current_profile
    st.session_state["last_employment"] = employment
    st.rerun()

if not submitted and "last_profile" not in st.session_state:
    st.info("기본값은 서울 거주를 검토하는 27세 1인 가구 예시입니다. 값을 바꾸고 분석 버튼을 눌러 보세요.")
    flow = pd.DataFrame(
        {
            "단계": ["① 조건 입력", "② 부담 분석", "③ 정책 사전진단", "④ 실행 계획"],
            "결과": ["소득·자산·주거비", "순수 주거비·통합 고정비", "적합도·확인 필요 조건", "다음 행동 3개"],
        }
    )
    st.dataframe(flow, hide_index=True, use_container_width=True)
    st.stop()

profile = st.session_state.get("last_profile", current_profile)
employment = st.session_state.get("last_employment", employment)

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
st.markdown("## 2. 주거비 진단 결과")

pure_gap = afford["monthly_gap_to_recommendation"] / 10_000
total_gap = afford["monthly_gap_to_total_recommendation"] / 10_000
monthly_income_display = profile["monthly_income"] / 10_000
remaining_cash = max(0, afford["disposable_after_housing_and_debt"]) / 10_000
housing_cost_man = afford["monthly_housing_cost"] / 10_000
total_fixed_man = afford["total_fixed_cost_with_debt"] / 10_000
recommended_man = afford["recommended_max_housing_cost"] / 10_000
deposit_equiv_man = afford["deposit_monthly_equivalent"] / 10_000
rent_man_value = profile["monthly_rent"] / 10_000
management_man_value = profile["management_fee"] / 10_000
debt_man_value = profile["monthly_debt_payment"] / 10_000
rule_label = model["rule_label"]
ai_reference_score = float(model["ai_reference_score"])
ai_score_label = "0.01 미만" if ai_reference_score < 0.01 else f"{ai_reference_score:.2f}"
if ai_reference_score < 0.40:
    ai_zone = "안정 구간"
elif ai_reference_score < 0.60:
    ai_zone = "주의 구간"
elif ai_reference_score < 0.70:
    ai_zone = "주의 구간 상단"
else:
    ai_zone = "위험 구간"

if total_gap < 0:
    headline = f"월 고정비가 생활 안정 권장선보다 {abs(total_gap):,.1f}만 원 높습니다"
    summary = (
        f"현재 주거비와 부채상환을 합친 월 고정비는 {total_fixed_man:,.1f}만 원이며, "
        f"생활 안정 참고선보다 {abs(total_gap):,.1f}만 원 높습니다."
    )
else:
    headline = f"월 고정비가 생활 안정 권장선보다 {total_gap:,.1f}만 원 낮습니다"
    summary = (
        f"현재 주거비와 부채상환을 합친 월 고정비는 {total_fixed_man:,.1f}만 원이며, "
        f"생활 안정 참고선보다 {total_gap:,.1f}만 원 여유가 있습니다."
    )

st.markdown(
    f"""
    <div class="result-card risk-{risk_class}">
      <div class="small-note">종합 판정 · {rule_label}</div>
      <h2 style="margin:.25rem 0 .45rem 0;">{headline}</h2>
      <div>{summary}</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("규칙 기반 진단은 소득 대비 주거비와 부채 포함 통합 고정비를 우선 보고, AI 점수는 합성 데이터 기반 참고값으로만 사용합니다.")

st.markdown("**판정 이유**")
r1, r2, r3 = st.columns(3)
with r1:
    st.metric("순수 월 주거비", f"{housing_cost_man:,.1f}만 원")
    st.caption(f"소득 대비 {afford['affordability_ratio'] * 100:.1f}%")
    st.caption(f"월세 {rent_man_value:,.1f} + 관리비 {management_man_value:,.1f} + 보증금 환산 {deposit_equiv_man:,.1f}")
with r2:
    st.metric("부채 포함 통합 고정비", f"{total_fixed_man:,.1f}만 원")
    st.caption(f"권장선 대비 {abs(total_gap):,.1f}만 원 {'초과' if total_gap < 0 else '여유'}")
    st.caption(f"순수 주거비 {housing_cost_man:,.1f} + 부채상환 {debt_man_value:,.1f}")
with r3:
    st.metric("AI 참고 위험도", f"{ai_score_label} · {ai_zone}")
    if ai_zone == "주의 구간 상단":
        st.caption("위험 구간에 가까워 월 고정비 조정이 권장됩니다.")
    else:
        st.caption("합성 데이터 기반 모델이 산출한 참고용 위험도입니다.")

st.markdown("**생활 안정 참고선과 통합 고정비 비교**")
comparison_frame = pd.DataFrame(
    [
        {"구분": "권장선", "만원": recommended_man, "표시": f"권장선 {recommended_man:,.1f}만 원"},
        {"구분": "현재", "만원": total_fixed_man, "표시": f"현재 {total_fixed_man:,.1f}만 원"},
    ]
)
bar_layer = (
    alt.Chart(comparison_frame)
    .mark_bar(size=38)
    .encode(
        x=alt.X("만원:Q", scale=alt.Scale(domain=[0, max(recommended_man, total_fixed_man) * 1.22]), axis=None, title=None),
        y=alt.Y("구분:N", title=None, axis=None, sort=["권장선", "현재"]),
        color=alt.Color("구분:N", legend=None, scale=alt.Scale(range=["#5b7cfa", "#e6a700"])),
        tooltip=["표시", alt.Tooltip("만원:Q", format=",.1f")],
    )
)
text_layer = (
    alt.Chart(comparison_frame)
    .mark_text(align="left", baseline="middle", dx=8, fontSize=15, fontWeight="bold", color="#243041")
    .encode(
        x=alt.X("만원:Q"),
        y=alt.Y("구분:N", sort=["권장선", "현재"]),
        text="표시:N",
    )
)
comparison_chart = (bar_layer + text_layer).properties(height=118)
overage_text = f"+{abs(total_gap):,.1f}만 원" if total_gap < 0 else f"{total_gap:,.1f}만 원 여유"
st.caption(
    f"생활 안정 참고선 {recommended_man:,.1f}만 원 · 현재 {total_fixed_man:,.1f}만 원 · {overage_text}"
)
st.altair_chart(comparison_chart, use_container_width=True)
label_cols = st.columns(3)
label_cols[0].metric("생활 안정 참고선", f"{recommended_man:,.1f}만 원")
label_cols[1].metric("주거·부채 통합 고정비", f"{total_fixed_man:,.1f}만 원")
label_cols[2].metric("초과액", f"{abs(total_gap):,.1f}만 원" if total_gap < 0 else "0.0만 원")
cash_cols = st.columns(5)
cash_items = [
    ("월세", rent_man_value),
    ("관리비", management_man_value),
    ("보증금 월 환산", deposit_equiv_man),
    ("부채상환", debt_man_value),
    ("주거·부채 차감 후 잔액", remaining_cash),
]
for col, (label, value) in zip(cash_cols, cash_items, strict=True):
    col.metric(label, f"{value:,.1f}만 원")
st.write(f"**주거·부채 차감 후 잔액 {remaining_cash:,.1f}만 원**")
st.caption(
    "보증금은 연 4% 기회비용을 월 단위로 환산한 데모 가정입니다. "
    "잔액은 세금, 보험료, 식비, 교통비 등 기타 지출을 차감하기 전 금액입니다."
)

st.subheader("3. 정책 사전진단 결과")
if all(item["status"] == "핵심요건 미충족" for item in result["policies"][:3]):
    st.warning("현재 입력에서는 주요 정책의 핵심요건을 충족하지 못했습니다. 아래 미충족 조건을 확인한 후 다시 진단하세요.")
else:
    st.caption(
        "적합도는 입력값 기반 우선순위 신호입니다. 실제 자격·대출 가능 여부·수급 가능성을 확정하지 않습니다."
    )

for rank, item in enumerate(result["policies"][:3], start=1):
    if item["failed_checks"]:
        reason = item["failed_checks"][0]
    elif item["passed_checks"]:
        reason = item["passed_checks"][0]
    else:
        reason = item.get("priority_note", "입력 조건을 기준으로 우선순위를 계산했습니다.")
    if item["status"] == "핵심요건 미충족":
        recommendation_label = "핵심요건 미충족"
    else:
        recommendation_label = "추천도 높음" if rank == 1 else "추천도 보통"
    st.markdown(
        f"""
        <div class="result-card">
          <div class="small-note">{recommendation_label}</div>
          <div class="policy-title">{item['name']}</div>
          <div style="margin-top:.45rem;">{"진단 중단 · 핵심요건 미충족" if item["status"] == "핵심요건 미충족" else f"적합도 {item['score']}점 · {item['status']}"}</div>
          <div style="margin-top:.45rem;">{reason}</div>
          <div class="small-note" style="margin-top:.45rem;">기준 확인일 {item['verified_at']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button("자격 조건 확인", item["official_url"], use_container_width=True)

with st.expander("전체 정책 후보 보기"):
    for item in result["policies"]:
        st.markdown(f"**{item['status']} · {item['name']}**")
        if item["status"] != "핵심요건 미충족":
            st.caption(f"참고 적합도 {item['score']}점")
        st.write(item["description"])
        if item["passed_checks"]:
            st.markdown("**입력상 충족 조건**")
            for message in item["passed_checks"]:
                st.write(f"- {message}")
        st.markdown("**점수 산정 근거**")
        st.dataframe(pd.DataFrame(item["score_breakdown"]), hide_index=True, use_container_width=True)
        if item["failed_checks"]:
            st.markdown("**우선순위가 낮아진 이유**")
            for message in item["failed_checks"]:
                st.write(f"- {message}")
            st.write(item["priority_note"])
        elif item.get("priority_note"):
            st.markdown("**우선순위 판단**")
            st.write(item["priority_note"])
        if item["manual_checks"]:
            st.markdown("**추가 확인 조건**")
            for message in item["manual_checks"]:
                st.write(f"- {message}")
        st.link_button("자격 조건 확인", item["official_url"])
        st.caption(f"기준 확인일 {item['verified_at']} · {item['source_note']}")
        st.divider()

st.subheader("4. 지금 할 일")
for index, action in enumerate(result["action_plan"], start=1):
    st.write(f"**{index}.** {action}")

st.subheader("5. 입력값 및 산정 기준")
with st.expander("이번 결과에 사용된 입력 조건", expanded=False):
    condition_frame = pd.DataFrame(
        [
            {"항목": "나이", "입력": f"{profile['age']}세"},
            {"항목": "월소득", "입력": f"{profile['monthly_income'] / 10_000:,.0f}만 원"},
            {"항목": "총자산", "입력": f"{profile['assets'] / 10_000:,.0f}만 원"},
            {"항목": "자동차 가액", "입력": f"{profile['car_value'] / 10_000:,.0f}만 원"},
            {"항목": "거주 지역", "입력": profile["region"]},
            {"항목": "가구원 수", "입력": f"{profile['household_size']}명"},
            {"항목": "고용 상태", "입력": employment},
            {"항목": "무주택 여부", "입력": profile.get("unhoused_status", "예" if profile["unhoused"] else "아니오")},
            {"항목": "부모와 별도 거주", "입력": profile.get("separate_household_status", "예" if profile["separate_household"] else "아니오")},
            {"항목": "혼인 상태", "입력": profile.get("unmarried_status", "혼인 중이 아님" if profile["unmarried"] else "혼인 중")},
            {"항목": "보증금", "입력": f"{profile['deposit'] / 10_000:,.0f}만 원"},
            {"항목": "월세", "입력": f"{profile['monthly_rent'] / 10_000:,.0f}만 원"},
            {"항목": "관리비", "입력": f"{profile['management_fee'] / 10_000:,.0f}만 원"},
            {"항목": "월 부채상환액", "입력": f"{profile['monthly_debt_payment'] / 10_000:,.0f}만 원"},
        ]
    )
    st.dataframe(condition_frame, hide_index=True, use_container_width=True)

with st.expander("모델과 데이터의 한계"):
    st.write(
        "AI 분류 모델은 서비스 흐름을 검증하기 위해 만든 합성 데이터로 학습했습니다. "
        "현재 결과는 실제 금융 위험 예측이 아니라 입력 현금흐름을 바탕으로 한 사전 안내입니다."
    )
    st.write(f"사용 모델: `{model['model_name']}`")
    st.write(model["data_notice"])

st.warning(result["disclaimer"])
st.caption(f"{TEAM_NAME} · {SERVICE_NAME}")
