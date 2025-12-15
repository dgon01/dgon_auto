import streamlit as st
import os
import re
import math
from io import BytesIO
from datetime import datetime, date

# =============================================================================
# 0. 설정 및 라이브러리 로드
# =============================================================================
try:
    import openpyxl
    EXCEL_OK = True
except ImportError:
    EXCEL_OK = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from PyPDF2 import PdfReader, PdfWriter
    LIBS_OK = True
except ImportError:
    LIBS_OK = False

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
st.set_page_config(layout="wide", page_title="DG-Form | 등기온 전자설정", page_icon="🏠")

# 폰트 설정
FONT_PATH = os.path.join(APP_ROOT, "Malgun.ttf")
if not os.path.exists(FONT_PATH):
    # 로컬에 폰트 없을 경우 윈도우 기본 폰트
    candidates = ["C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/gulim.ttf"]
    for c in candidates:
        if os.path.exists(c):
            FONT_PATH = c; break

# 스타일
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    .stApp { font-family: 'Noto Sans KR', sans-serif !important; }
    .header-title { font-size: 2rem; font-weight: 700; color: #00428B; margin-bottom: 0; }
    .header-subtitle { color: #666; font-size: 1rem; margin-top: 5px; }
    .stTextInput>div>div>input { font-weight: 500; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div>
    <h1 class="header-title">🏠 DG-Form Automation</h1>
    <p class="header-subtitle">등기온 전자설정 자동화 시스템 | 법무법인 시화</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# 1. 데이터 및 상수
# =============================================================================
CREDITORS = {
    "(주)티플레인대부 대표이사 윤웅원": {"addr": "서울특별시 마포구 삼개로16, 2신관1층103호(도화동,근신빌딩)", "corp_num": "110111-7350161"},
    "(주)유노스프레스티지대부 사내이사 한은수": {"addr": "서울특별시 강남구 압구정로28길24, 5층 501호(신사동,디앤씨빌딩)", "corp_num": "110111-4138560"},
    "(주)파트너스대부 사내이사 허성": {"addr": "부산광역시 부산진구 서면문화로 43, 2층(부전동)", "corp_num": "180111-1452175"},
    "(주)드림앤캐쉬대부 대표이사 김재섭": {"addr": "서울특별시 강남구 압구정로28길24, 6층 601호(신사동,디앤씨빌딩)", "corp_num": "110111-4176552"},
    "(주)마젤란트러스트대부 대표이사 김병수": {"addr": "서울특별시 서초구 강남대로34길 7, 7층(양재동,이안빌딩)", "corp_num": "110111-6649979"},
    "(주)하이클래스대부 사내이사 성윤호": {"addr": "서울특별시 강남구 도곡로 188, 3층 4호(도곡동,도곡스퀘어)", "corp_num": "110111-0933512"}
}

TEMPLATE_FILENAMES = {
    "개인": "1.pdf", "3자담보": "2.pdf", "공동담보": "3.pdf",
    "자필": "자필서명정보 템플릿.pdf", "영수증": "영수증_템플릿.xlsx"
}
MALSO_TEMPLATES = {
    "자필서명정보": "자필서명정보_말소_템플릿.pdf", "위임장": "위임장_말소_템플릿.pdf",
    "해지증서": "해지증서_템플릿.pdf", "이관증명서": "이관증명서_템플릿.pdf"
}

def resource_path(relative_path):
    return os.path.join(APP_ROOT, relative_path)

# =============================================================================
# 2. 유틸리티 함수
# =============================================================================
def format_date_korean(d):
    return f"{d.year}년 {d.month:02d}월 {d.day:02d}일" if isinstance(d, date) else str(d)

def remove_commas(v):
    return str(v).replace(',', '').replace('원', '').strip() if v else ""

def get_int_val(v):
    try: return int(remove_commas(v))
    except: return 0

def format_comma(v):
    return "{:,}".format(get_int_val(v)) if v else ""

def convert_money_to_korean(amount_str):
    if not amount_str: return ""
    try: num = int(re.sub(r'[^\d]', '', str(amount_str)))
    except: return ""
    units = ['', '만', '억', '조']; digits = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
    if num == 0: return "영원정"
    res = []; idx = 0
    while num > 0:
        part = num % 10000
        if part > 0:
            s = ""
            if part >= 1000: s += digits[part // 1000] + "천"; part %= 1000
            if part >= 100: s += digits[part // 100] + "백"; part %= 100
            if part >= 10: s += digits[part // 10] + "십"; part %= 10
            if part > 0: s += digits[part]
            res.append(s + units[idx])
        num //= 10000; idx += 1
    return ''.join(reversed(res)) + "원정"

def extract_address(text):
    if not text: return ""
    for line in text.split('\n'):
        line = line.strip()
        if "건물의 표시" in line: continue
        if any(x in line for x in ['시 ', '군 ', '구 ']) and '도로명' not in line:
            return line
    return ""

# =============================================================================
# 3. PDF 생성 (DG-Form 좌표 적용)
# =============================================================================
def get_canvas(packet):
    c = canvas.Canvas(packet, pagesize=A4)
    try: pdfmetrics.registerFont(TTFont('Korean', FONT_PATH)); c.setFont('Korean', 11)
    except: c.setFont('Helvetica', 11)
    return c

def create_contract_overlay(data): # 1탭 계약서
    packet = BytesIO(); c = get_canvas(packet); w, h = A4
    
    # 상단 정보
    if data.get("date"): c.drawString(480, h - 85, data["date"])
    if data.get("creditor_name"): c.drawString(157, h - 134, data["creditor_name"])
    if data.get("creditor_addr"): c.drawString(157, h - 150, data["creditor_addr"])
    if data.get("debtor_name"): c.drawString(157, h - 172, data["debtor_name"])
    if data.get("debtor_addr"): c.drawString(157, h - 190, data["debtor_addr"])
    if data.get("owner_name"): c.drawString(157, h - 212, data["owner_name"])
    if data.get("owner_addr"): c.drawString(157, h - 230, data["owner_addr"])
    if data.get("guarantee"): c.drawString(65, h - 343, data["guarantee"])
    if data.get("amount"): c.drawString(150, h - 535, data["amount"])

    # 서명란 (2페이지)
    c.showPage(); c.setFont('Korean', 11)
    if data.get("date"): c.drawString(180, h - 270, data["date"])
    ctype = data.get("type", "3자담보")
    if ctype == "개인": c.drawString(450, h - 270, data.get("debtor_name",""))
    elif ctype == "3자담보": c.drawString(490, h - 270, data.get("owner_name",""))
    elif ctype == "공동담보":
        c.drawString(450, h - 270, data.get("debtor_name",""))
        c.drawString(490, h - 270, data.get("owner_name",""))

    # 별지 (3페이지)
    c.showPage(); c.setFont('Korean', 11)
    bx, by = 35, h - 80
    for i, line in enumerate(data.get("estate", [])):
        if line.strip(): c.drawString(bx, by - (i * 16), line)
    
    c.save(); packet.seek(0)
    return packet

def create_signature_overlay(data): # 2탭 & 4탭 공용
    packet = BytesIO(); c = get_canvas(packet); w, h = A4
    c.setFont('Korean', 10)

    # 부동산 표시 (x=150, y=h-170)
    ex, ey = 150, h - 170
    lines = data.get("estate", [])
    if isinstance(lines, str): lines = lines.split('\n')
    for i, line in enumerate(lines[:17]):
        c.drawString(ex, ey - (i * 14), line)

    # 당사자 (채무자=좌, 소유자=우)
    if data.get("d_name"): c.drawString(250, 322, data["d_name"])
    if data.get("d_rrn"): c.drawString(250, 298, data["d_rrn"])
    if data.get("o_name"): c.drawString(400, 322, data["o_name"])
    if data.get("o_rrn"): c.drawString(400, 298, data["o_rrn"])

    # 날짜
    if data.get("date"):
        c.setFont('Korean', 11)
        tw = c.stringWidth(data["date"], 'Korean', 11)
        c.drawString((w - tw) / 2, 150, data["date"])

    c.save(); packet.seek(0)
    return packet

def make_pdf(template, data):
    if not LIBS_OK: return None
    overlay = create_contract_overlay(data) if data.get("is_contract") else create_signature_overlay(data)
    
    ov = PdfReader(overlay); tmpl = PdfReader(template); writer = PdfWriter()
    for i in range(len(tmpl.pages)):
        p = tmpl.pages[i]
        if i < len(ov.pages): p.merge_page(ov.pages[i])
        writer.add_page(p)
    
    out = BytesIO(); writer.write(out); out.seek(0)
    return out

# =============================================================================
# 4. 엑셀 영수증 (DG-Form 좌표)
# =============================================================================
def create_receipt(data, template):
    if not EXCEL_OK: return None
    try:
        wb = openpyxl.load_workbook(template); ws = wb.active
        c = data['client']; cost = data['cost']

        ws['B4'] = c.get('creditor', '')
        ws['V4'] = c.get('debtor', '')
        ws['AG5'] = get_int_val(c.get('amount', 0))
        ws['Y7'] = c.get('estate', '')

        ws['AH11'] = get_int_val(cost.get('reg', 0))
        ws['AH12'] = get_int_val(cost.get('edu', 0))
        ws['AH13'] = get_int_val(cost.get('stamp', 0))
        ws['AH14'] = get_int_val(cost.get('bond', 0))
        ws['AH15'] = get_int_val(cost.get('cert', 0))
        ws['AH16'] = get_int_val(cost.get('orig', 0))
        ws['AH17'] = get_int_val(cost.get('addr', 0))
        ws['AH18'] = get_int_val(cost.get('malso', 0))

        total = data.get('total', 0)
        ws['AH21'] = total; ws['Y22'] = total
        
        out = BytesIO(); wb.save(out); out.seek(0)
        return out
    except Exception as e:
        print(e); return None

# =============================================================================
# 5. 세션 초기화
# =============================================================================
def init_session():
    # Tab 1 defaults
    if 't1_date' not in st.session_state: st.session_state['t1_date'] = datetime.now().date()
    if 't1_creditor' not in st.session_state: st.session_state['t1_creditor'] = list(CREDITORS.keys())[0]
    if 't1_debtor' not in st.session_state: st.session_state['t1_debtor'] = ''
    if 't1_debtor_addr' not in st.session_state: st.session_state['t1_debtor_addr'] = ''
    if 't1_owner' not in st.session_state: st.session_state['t1_owner'] = ''
    if 't1_owner_addr' not in st.session_state: st.session_state['t1_owner_addr'] = ''
    if 't1_amount' not in st.session_state: st.session_state['t1_amount'] = ''
    if 't1_estate' not in st.session_state: st.session_state['t1_estate'] = ''
    # Tab 4 reset
    if 'malso_type' not in st.session_state: st.session_state['malso_type'] = '근저당권'

init_session()

# =============================================================================
# 메인 UI
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["📄 근저당권설정", "✍️ 자필서명정보", "🧾 영수증/비용", "🗑️ 말소 문서"])

# [Tab 1] 근저당권설정 (데이터 원본)
with tab1:
    h1, h2 = st.columns([5,1])
    h1.markdown("### 📝 근저당권설정 계약서")
    if h2.button("🔄 전체 초기화"): st.session_state.clear(); st.rerun()

    with st.expander("기본 정보", expanded=True):
        st.session_state['t1_date'] = st.date_input("작성일자", value=st.session_state['t1_date'])
        
        # 채권자
        cr_list = list(CREDITORS.keys()) + ["직접입력"]
        curr = st.session_state['t1_creditor']
        idx = cr_list.index(curr) if curr in cr_list else 0
        st.session_state['t1_creditor'] = st.selectbox("채권자", cr_list, index=idx)
        
        # 채권자 정보 추출
        if st.session_state['t1_creditor'] == "직접입력":
            cr_name = st.text_input("채권자명(직접입력)")
            cr_addr = st.text_input("채권자 주소")
        else:
            cr_name = st.session_state['t1_creditor']
            cr_addr = CREDITORS[cr_name]['addr']

        c1, c2 = st.columns(2)
        with c1:
            st.session_state['t1_debtor'] = st.text_input("채무자 성명", value=st.session_state['t1_debtor'])
            st.session_state['t1_debtor_addr'] = st.text_area("채무자 주소", value=st.session_state['t1_debtor_addr'], height=80)
        with c2:
            st.session_state['t1_owner'] = st.text_input("설정자(소유자) 성명", value=st.session_state['t1_owner'])
            st.session_state['t1_owner_addr'] = st.text_area("설정자 주소", value=st.session_state['t1_owner_addr'], height=80)
        
        st.session_state['t1_amount'] = st.text_input("채권최고액 (숫자만)", value=st.session_state['t1_amount'])
        if st.session_state['t1_amount']: st.caption(convert_money_to_korean(st.session_state['t1_amount']))

    st.markdown("#### 🏠 부동산의 표시")
    st.session_state['t1_estate'] = st.text_area("등기부 내용 복사", value=st.session_state['t1_estate'], height=150)

    # 계약서 생성
    ctype = st.radio("계약서 유형", ["개인", "3자담보", "공동담보"], horizontal=True)
    t_path = resource_path(TEMPLATE_FILENAMES.get(ctype))
    if st.button("계약서 PDF 다운로드", disabled=not (LIBS_OK and os.path.exists(t_path))):
        data = {
            "is_contract": True, "type": ctype,
            "date": format_date_korean(st.session_state['t1_date']),
            "creditor_name": cr_name, "creditor_addr": cr_addr,
            "debtor_name": st.session_state['t1_debtor'], "debtor_addr": st.session_state['t1_debtor_addr'],
            "owner_name": st.session_state['t1_owner'], "owner_addr": st.session_state['t1_owner_addr'],
            "guarantee": "한정근담보", "amount": convert_money_to_korean(st.session_state['t1_amount']),
            "estate": st.session_state['t1_estate'].split('\n')
        }
        st.download_button("⬇️ 저장", make_pdf(t_path, data), f"근저당_{st.session_state['t1_debtor']}.pdf", "application/pdf")

# [Tab 2] 자필서명정보 (1탭 연동)
with tab2:
    st.markdown("### ✍️ 자필서명정보")
    st.caption("※ 1탭 정보를 기본으로 합니다.")
    
    # 주민등록번호만 여기서 입력
    c2_1, c2_2 = st.columns(2)
    with c2_1:
        t2_d_name = st.text_input("채무자", value=st.session_state['t1_debtor'], key="t2d")
        t2_d_rrn = st.text_input("채무자 주민번호", key="t2d_rrn")
    with c2_2:
        t2_o_name = st.text_input("소유자", value=st.session_state['t1_owner'], key="t2o")
        t2_o_rrn = st.text_input("소유자 주민번호", key="t2o_rrn")
    
    st.markdown("---")
    t2_estate = st.text_area("부동산 표시 (수정가능)", value=st.session_state['t1_estate'], height=100, key="t2_est")
    
    t_path = resource_path(TEMPLATE_FILENAMES["자필"])
    if st.button("자필서명 PDF 생성", key="btn_japil", disabled=not (LIBS_OK and os.path.exists(t_path))):
        data = {
            "date": format_date_korean(st.session_state['t1_date']),
            "d_name": t2_d_name, "d_rrn": t2_d_rrn,
            "o_name": t2_o_name, "o_rrn": t2_o_rrn,
            "estate": t2_estate.split('\n')
        }
        st.download_button("⬇️ 저장", make_pdf(t_path, data), "자필서명정보.pdf", "application/pdf")

# [Tab 3] 영수증 (1탭 연동 심플 버전)
with tab3:
    st.markdown("### 🧾 영수증 (1탭 정보 자동 연동)")
    
    # 1. 1탭 정보 자동 Load
    def_creditor = st.session_state['t1_creditor'] if st.session_state['t1_creditor'] != "직접입력" else "채권자직접입력"
    def_addr = extract_address(st.session_state['t1_estate'])
    
    col3_1, col3_2 = st.columns(2)
    with col3_1:
        t3_amt = st.text_input("채권최고액", value=st.session_state['t1_amount'], key="t3_amt")
        t3_debtor = st.text_input("채무자", value=st.session_state['t1_debtor'], key="t3_deb")
    with col3_2:
        t3_creditor = st.text_input("금융사(채권자)", value=def_creditor, key="t3_cred")
        t3_estate = st.text_input("물건지 주소", value=def_addr, key="t3_est")
        
    st.markdown("#### 비용 상세")
    with st.expander("비용 입력 (펼치기)", expanded=True):
        ec1, ec2 = st.columns(2)
        with ec1:
            c_reg = st.number_input("등록면허세", value=0)
            c_edu = st.number_input("지방교육세", value=0)
            c_stamp = st.number_input("증지대", value=15000)
            c_bond = st.number_input("채권할인", value=0)
        with ec2:
            c_cert = st.number_input("제증명", value=50000)
            c_orig = st.number_input("원인증서", value=50000)
            c_addr = st.number_input("주소변경", value=0)
            c_malso = st.number_input("선순위 말소", value=0)

    total = c_reg + c_edu + c_stamp + c_bond + c_cert + c_orig + c_addr + c_malso
    st.info(f"💰 공과금 총액: {format_comma(total)} 원")
    
    t_path = resource_path(TEMPLATE_FILENAMES["영수증"])
    if st.button("🏦 영수증 Excel 생성", disabled=not (EXCEL_OK and os.path.exists(t_path))):
        data = {
            'client': {'creditor': t3_creditor, 'debtor': t3_debtor, 'amount': t3_amt, 'estate': t3_estate},
            'cost': {'reg':c_reg, 'edu':c_edu, 'stamp':c_stamp, 'bond':c_bond, 'cert':c_cert, 'orig':c_orig, 'addr':c_addr, 'malso':c_malso},
            'total': total
        }
        st.download_button("⬇️ Excel 다운로드", create_receipt(data, t_path), f"영수증_{t3_debtor}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# [Tab 4] 말소 문서 (소유자 중심 & 초기화)
with tab4:
    h4_1, h4_2 = st.columns([5,1])
    h4_1.markdown("### 🗑️ 말소 문서 작성")
    if h4_2.button("🔄 4탭 초기화"):
        # 4탭 관련 상태만 삭제
        for k in list(st.session_state.keys()):
            if k.startswith("malso_"): del st.session_state[k]
        st.rerun()

    # 말소 유형
    b1, b2, b3 = st.columns(3)
    if b1.button("근저당권", use_container_width=True): st.session_state['malso_type'] = "근저당권"
    if b2.button("질권", use_container_width=True): st.session_state['malso_type'] = "질권"
    if b3.button("전세권", use_container_width=True): st.session_state['malso_type'] = "전세권"
    
    # 당사자 (의무자=공란, 권리자=소유자)
    c4_1, c4_2 = st.columns(2)
    with c4_1:
        st.markdown("**등기의무자 (금융사/채권자)**")
        st.caption("※ 직접 입력")
        m_ob_corp = st.text_input("법인명", key="malso_ob_corp")
        m_ob_rep = st.text_input("대표자", key="malso_ob_rep")
        m_ob_addr = st.text_area("주소", height=80, key="malso_ob_addr")
    with c4_2:
        st.markdown("**등기권리자 (소유자)**")
        st.caption("※ 1탭 소유자 정보 자동 로드")
        m_ow_name = st.text_input("성명", value=st.session_state['t1_owner'], key="malso_ow_name")
        m_ow_addr = st.text_area("주소", value=st.session_state['t1_owner_addr'], height=80, key="malso_ow_addr")

    st.markdown("---")
    # 등기 정보
    cd1, cd2 = st.columns(2)
    with cd1:
        m_date = st.date_input("원인일자", value=st.session_state['t1_date'], key="malso_date")
        m_cause = st.text_input("등기원인", value="해지", key="malso_cause")
    with cd2:
        m_purpose = st.text_input("등기목적", value=f"{st.session_state['malso_type']}말소", key="malso_purp")
    
    m_estate = st.text_area("부동산 표시", value=st.session_state['t1_estate'], height=150, key="malso_est")
    m_cancel = st.text_input("말소할 등기 (접수번호 등)", key="malso_cancel")
    
    with st.expander("이관 정보"):
        cm1, cm2 = st.columns(2)
        m_from = cm1.text_input("이관 전", key="malso_fr")
        m_to = cm2.text_input("이관 후", key="malso_to")

    # 다운로드
    st.markdown("### 📥 문서 다운로드")
    docs = ["자필서명정보", "위임장", "해지증서", "이관증명서"]
    cd = st.columns(4)
    for i, doc in enumerate(docs):
        with cd[i]:
            t_path = resource_path(MALSO_TEMPLATES.get(doc))
            if st.button(doc, key=f"btn_{doc}", disabled=not (LIBS_OK and os.path.exists(t_path)), use_container_width=True):
                # 말소용 데이터 매핑
                # 템플릿의 'debtor' 위치 -> 소유자(권리자)
                # 템플릿의 'owner' 위치 -> 금융사(의무자)
                data = {
                    "date": format_date_korean(m_date),
                    "d_name": m_ow_name, "d_rrn": "", # 소유자 -> debtor 위치
                    "o_name": m_ob_corp, "o_rrn": "", # 금융사 -> owner 위치
                    "estate": m_estate.split('\n')
                }
                st.download_button("⬇️ 저장", make_pdf(t_path, data), f"{doc}.pdf", "application/pdf", key=f"dn_{doc}")