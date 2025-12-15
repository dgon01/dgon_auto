
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="DG-Form | 등기온",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def reset_all():
    st.session_state.clear()

def sync_from_tab1(prefix):
    st.session_state[f"{prefix}_synced"] = True

st.markdown("""
<style>
.header {
    border: 3px solid #00428B;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 20px;
    font-weight: bold;
    font-size: 22px;
}
</style>
<div class="header">📄 DG-Form 근저당권 자동화</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "📄 근저당권설정 계약서",
    "✍️ 자필서명정보",
    "🧾 비용 계산",
    "🗑️ 말소"
])

with tab1:
    colh = st.columns([8, 2])
    colh[0].markdown("### 📄 근저당권설정 계약서 (원본 유지)")
    if colh[1].button("🔄 초기화", key="reset_tab1"):
        reset_all()
        st.rerun()
    st.text_input("채무자", key="t1_debtor")
    st.text_input("소유자", key="t1_owner")
    st.text_area("부동산의 표시", key="t1_estate")

with tab2:
    colh = st.columns([8, 2])
    colh[0].markdown("### ✍️ 자필서명정보")
    if colh[1].button("🔄 초기화", key="reset_tab2"):
        reset_all()
        st.rerun()
    if st.button("🔄 1탭 정보 가져오기", key="sync_tab2"):
        sync_from_tab1("tab2")
    st.radio("접수구분", ["전자접수", "서면접수"], key="sig_type")
    st.text_input("설정자(단독)", key="sig_debtor")
    st.text_area("부동산 표시", key="sig_estate")

with tab3:
    colh = st.columns([8, 2])
    colh[0].markdown("### 🧾 비용 계산")
    if colh[1].button("🔄 초기화", key="reset_tab3"):
        reset_all()
        st.rerun()
    if st.button("🔄 1탭 정보 가져오기", key="sync_tab3"):
        sync_from_tab1("tab3")
    st.number_input("채권최고액", min_value=0, key="calc_amount")

with tab4:
    colh = st.columns([8, 2])
    colh[0].markdown("### 🗑️ 말소")
    if colh[1].button("🔄 초기화", key="reset_tab4"):
        reset_all()
        st.rerun()
    if st.button("🔄 1탭 정보 가져오기", key="sync_tab4"):
        sync_from_tab1("tab4")
    st.text_input("등기의무자(금융사)", key="malso_bank")
    st.text_input("등기권리자", key="malso_owner")
    st.text_area("부동산 표시", key="malso_estate")
