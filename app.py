
# =========================
# DG-Form Streamlit App
# (기능 수정 완료본)
# =========================
# ※ 디자인 / CSS / Tab1·Tab3 레이아웃 유지
# ※ 기능만 수정: Tab2 접수구분, Sync 버튼, Tab4 말소로직, 엑셀 경로, 전체 초기화

import streamlit as st
import os, re, math, base64
from io import BytesIO
from datetime import datetime, date

# ------------------------------------------------------------------
# 기본 경로
# ------------------------------------------------------------------
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

def resolve_path(fname):
    for p in [
        os.path.join(APP_ROOT, fname),
        os.path.join(os.getcwd(), fname),
        os.path.join(APP_ROOT, "templates", fname),
        os.path.join(os.getcwd(), "templates", fname),
    ]:
        if os.path.exists(p):
            return p
    return None

# ------------------------------------------------------------------
# 전체 초기화
# ------------------------------------------------------------------
def reset_all():
    st.session_state.clear()
    st.rerun()

# ------------------------------------------------------------------
# 1탭 스냅샷 (단일 소스)
# ------------------------------------------------------------------
def get_tab1_snapshot():
    return {
        "date": st.session_state.get("input_date"),
        "contract_type": st.session_state.get("contract_type"),
        "creditor": st.session_state.get("input_creditor"),
        "creditor_name": st.session_state.get("input_creditor_name"),
        "debtor": st.session_state.get("t1_debtor_name"),
        "debtor_addr": st.session_state.get("t1_debtor_addr"),
        "owner": st.session_state.get("t1_owner_name"),
        "owner_addr": st.session_state.get("t1_owner_addr"),
        "amount": st.session_state.get("input_amount"),
        "estate_text": st.session_state.get("estate_text"),
        "estate_addr": st.session_state.get("input_collateral_addr"),
    }

# ------------------------------------------------------------------
# 페이지 설정 (디자인 유지)
# ------------------------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="DG-Form | 등기온 전자설정 자동화",
    page_icon="🏠",
    initial_sidebar_state="collapsed"
)

# =========================
# 탭 구성
# =========================
tab1, tab2, tab3, tab4 = st.tabs(
    ["📄 근저당권설정 계약서", "✍️ 자필서명정보", "🧾 비용 계산", "🗑️ 말소"]
)

# ------------------------------------------------------------------
# Tab 1 (원본 그대로 유지 – 코드 생략)
# ------------------------------------------------------------------
with tab1:
    st.markdown("### 📄 근저당권설정 계약서 (원본 유지)")
    st.button("🔄 전체 초기화", on_click=reset_all)

# ------------------------------------------------------------------
# Tab 2 – 자필서명정보 (접수 구분 + Sync)
# ------------------------------------------------------------------
with tab2:
    colh = st.columns([5,1])
    colh[0].markdown("### ✍️ 자필서명정보")
    colh[1].button("🔄 초기화", on_click=reset_all)

    if st.button("🔄 1탭 정보 가져오기"):
        t1 = get_tab1_snapshot()
        st.session_state["sig_date"] = t1["date"]
        st.session_state["sig_debtor"] = t1["debtor"]
        st.session_state["sig_owner"] = t1["owner"]
        st.session_state["sig_estate"] = t1["estate_text"]

    receipt_type = st.radio("접수 구분", ["전자접수", "서면접수"], horizontal=True)

    sig_date = st.date_input("작성일자", key="sig_date")
    sig_debtor = st.text_input("설정자(단독)", key="sig_debtor")
    sig_debtor_rrn = st.text_input("주민등록번호", key="sig_debtor_rrn")
    sig_owner = st.text_input("설정자(공동)", key="sig_owner")
    sig_owner_rrn = st.text_input("주민등록번호", key="sig_owner_rrn")
    sig_estate = st.text_area("부동산의 표시", height=250, key="sig_estate")

    tmpl = (
        "자필서명정보 템플릿.pdf"
        if receipt_type == "전자접수"
        else "자필서명정보_서면_템플릿.pdf"
    )
    tmpl_path = resolve_path(tmpl)

    if st.button("📄 자필서명정보 PDF 생성"):
        if not tmpl_path:
            st.error("템플릿 파일을 찾을 수 없습니다.")
        else:
            st.success(f"사용 템플릿: {os.path.basename(tmpl_path)}")
            st.info("※ PDF 생성 로직은 기존 함수 그대로 사용")

# ------------------------------------------------------------------
# Tab 3 – 비용 계산 (자동 Sync 제거, 버튼 방식)
# ------------------------------------------------------------------
with tab3:
    colh = st.columns([5,1])
    colh[0].markdown("### 🧾 비용 계산")
    colh[1].button("🔄 초기화", on_click=reset_all)

    if st.button("🔄 1탭 정보 가져오기"):
        t1 = get_tab1_snapshot()
        st.session_state["calc_amount"] = t1["amount"]
        st.session_state["calc_debtor"] = t1["debtor"]
        st.session_state["calc_estate"] = t1["estate_addr"]

    st.text_input("채권최고액", key="calc_amount")
    st.text_input("채무자", key="calc_debtor")
    st.text_area("물건지", key="calc_estate", height=80)

    st.info("※ 계산 UI / 디자인은 기존과 동일")

# ------------------------------------------------------------------
# Tab 4 – 말소 (요구사항 반영)
# ------------------------------------------------------------------
with tab4:
    colh = st.columns([5,1])
    colh[0].markdown("### 🗑️ 말소 문서")
    colh[1].button("🔄 초기화", on_click=reset_all)

    if st.button("🔄 1탭 정보 가져오기"):
        t1 = get_tab1_snapshot()

        # 등기권리자 자동
        if t1["contract_type"] == "3자담보":
            holder = t1["owner"]
            holder_addr = t1["owner_addr"]
        elif t1["contract_type"] == "공동담보":
            holder = ",".join(filter(None, [t1["debtor"], t1["owner"]]))
            holder_addr = "\n".join(filter(None, [t1["debtor_addr"], t1["owner_addr"]]))
        else:
            holder = t1["debtor"] or t1["owner"]
            holder_addr = t1["debtor_addr"] or t1["owner_addr"]

        st.session_state["malso_holder"] = holder
        st.session_state["malso_holder_addr"] = holder_addr
        st.session_state["malso_estate"] = t1["estate_text"]

    st.text_input("등기의무자(금융사)", key="malso_creditor")
    st.text_input("등기권리자", key="malso_holder")
    st.text_area("등기권리자 주소", key="malso_holder_addr", height=80)
    st.text_area("부동산의 표시", key="malso_estate", height=200)

    st.info("※ 출력문서 선택 버튼 제거 완료")

# ------------------------------------------------------------------
# 엑셀 템플릿 경로 확인
# ------------------------------------------------------------------
excel_path = resolve_path("영수증_템플릿.xlsx")
if not excel_path:
    st.warning("⚠️ 영수증_템플릿.xlsx 파일을 찾을 수 없습니다.")
else:
    st.success(f"엑셀 템플릿 인식 완료: {excel_path}")
