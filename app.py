import streamlit as st
import os
import re
import math
import base64
from io import BytesIO
from datetime import datetime, date

# =============================================================================
# 0. 라이브러리 및 환경 설정
# =============================================================================
# Excel (영수증)
try:
    import openpyxl
    EXCEL_OK = True
except ImportError:
    EXCEL_OK = False

# PDF (계약서 오버레이)
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from PyPDF2 import PdfReader, PdfWriter
    LIBS_OK = True
except ImportError:
    LIBS_OK = False

# PDF (비용내역서 FPDF)
try:
    from fpdf import FPDF
    FPDF_OK = True
except ImportError:
    FPDF_OK = False

# 경로 설정
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
st.set_page_config(layout="wide", page_title="DG-Form | 등기온 전자설정", page_icon="🏠")

# 폰트 설정
FONT_PATH = os.path.join(APP_ROOT, "Malgun.ttf")
if not os.path.exists(FONT_PATH):
    FONT_PATH = "C:/Windows/Fonts/malgun.ttf"

# -----------------------------------------------------------------------------
# 스타일 및 로고 (클로드 디자인 유지)
# -----------------------------------------------------------------------------
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f: data = f.read()
        return base64.b64encode(data).decode()
    except: return None

logo_base64 = get_base64_image(os.path.join(APP_ROOT, "my_icon.ico"))

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Noto Sans KR', sans-serif !important; }
    .header-container {
        background: white; border: 3px solid #00428B; padding: 20px 40px;
        border-radius: 15px; margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 66, 139, 0.2);
        display: flex; align-items: center; justify-content: space-between;
    }
    .header-title { margin: 0; font-size: 2.5rem; font-weight: 700; color: #00428B; }
    .header-subtitle { color: #00428B; font-size: 1.2rem; font-weight: 500; margin: 0; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f8f9fa; border-radius: 8px; padding: 10px 20px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #00428B; color: white; }
    .stTextInput > div > div > input { border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

if logo_base64:
    st.markdown(f"""
    <div class="header-container">
        <div style="display:flex; align-items:center; gap:20px;">
            <img src="data:image/x-icon;base64,{logo_base64}" style="width:80px;">
            <div>
                <h1 class="header-title">DG-Form</h1>
                <p class="header-subtitle">등기온 전자설정 자동화 시스템 | 법무법인 시화</p>
            </div>
        </div>
        <p style="margin:0; font-weight:600;">부동산 등기는 등기온</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""<div class="header-container"><div><h1 class="header-title">🏠 DG-Form</h1><p class="header-subtitle">등기온 전자설정 자동화 시스템</p></div></div>""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. 상수 및 데이터
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 2. 유틸리티 함수
# -----------------------------------------------------------------------------
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

def lookup_base_fee(amount):
    keys = [0, 30000000, 45000000, 60000000, 106500000, 150000000, 225000000]
    vals = [150000, 200000, 250000, 300000, 350000, 400000, 450000]
    for i in range(len(keys)-1, -1, -1):
        if amount > keys[i]: return vals[i]
    return vals[0]

def get_rate():
    try:
        import requests
        url = "https://lawss.co.kr/lawpro/homepage/siga/auto_siga_kjaa.php"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=2)
        res.encoding = 'EUC-KR'
        match = re.search(r"오늘 채권할인율\s*=\s*([\d\.]+) %", res.text)
        if match: return math.ceil(float(match.group(1))*10)/1000
    except: pass
    return 0.0913459

# -----------------------------------------------------------------------------
# 3. PDF 생성 로직 (ReportLab - 오버레이)
# -----------------------------------------------------------------------------
def get_canvas(packet):
    c = canvas.Canvas(packet, pagesize=A4)
    try: pdfmetrics.registerFont(TTFont('Korean', FONT_PATH)); c.setFont('Korean', 11)
    except: c.setFont('Helvetica', 11)
    return c

def draw_fit_text(c, text, x, y, max_w, font, size):
    # 간단한 줄바꿈 로직
    c.setFont(font, size)
    c.drawString(x, y, text)

# 1탭 계약서용 오버레이
def create_contract_overlay(data):
    packet = BytesIO(); c = get_canvas(packet); w, h = A4
    font = 'Korean' if 'Korean' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    
    if data.get("date"): c.drawString(480, h-85, data["date"])
    if data.get("creditor_name"): c.drawString(157, h-134, data["creditor_name"])
    if data.get("creditor_addr"): c.drawString(157, h-150, data["creditor_addr"])
    if data.get("debtor_name"): c.drawString(157, h-172, data["debtor_name"])
    if data.get("debtor_addr"): c.drawString(157, h-190, data["debtor_addr"])
    if data.get("owner_name"): c.drawString(157, h-212, data["owner_name"])
    if data.get("owner_addr"): c.drawString(157, h-230, data["owner_addr"])
    if data.get("guarantee"): c.drawString(65, h-343, data["guarantee"])
    if data.get("amount"): c.drawString(150, h-535, data["amount"])

    c.showPage(); c.setFont(font, 11)
    if data.get("date"): c.drawString(180, h-270, data["date"])
    
    ctype = data.get("type", "3자담보")
    if ctype == "개인": c.drawString(450, h-270, data.get("debtor_name",""))
    elif ctype == "3자담보": c.drawString(490, h-270, data.get("owner_name",""))
    elif ctype == "공동담보":
        c.drawString(450, h-270, data.get("debtor_name",""))
        c.drawString(490, h-270, data.get("owner_name",""))

    c.showPage(); c.setFont(font, 11)
    bx, by = 35, h-80
    for i, line in enumerate(data.get("estate", [])):
        if line.strip(): c.drawString(bx, by - (i*16), line)
    
    c.save(); packet.seek(0)
    return packet

# 2탭 & 4탭 공용 오버레이 (부동산+당사자)
def create_signature_overlay(data):
    packet = BytesIO(); c = get_canvas(packet); w, h = A4
    font = 'Korean' if 'Korean' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    c.setFont(font, 10)

    # 부동산 표시 (DG-Form 좌표)
    ex, ey = 150, h - 170
    lines = data.get("estate", [])
    if isinstance(lines, str): lines = lines.split('\n')
    for i, line in enumerate(lines[:17]):
        c.drawString(ex, ey - (i * 14), line)

    # 당사자 (좌: 채무자/소유자, 우: 소유자/금융사 - 호출 시 매핑됨)
    if data.get("d_name"): c.drawString(250, 322, data["d_name"])
    if data.get("d_rrn"): c.drawString(250, 298, data["d_rrn"])
    if data.get("o_name"): c.drawString(400, 322, data["o_name"])
    if data.get("o_rrn"): c.drawString(400, 298, data["o_rrn"])

    # 날짜
    if data.get("date"):
        c.setFont(font, 11)
        tw = c.stringWidth(data["date"], font, 11)
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

# -----------------------------------------------------------------------------
# 4. 엑셀 영수증 생성 (DG-Form 좌표)
# -----------------------------------------------------------------------------
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
        
        # 교통비, 확인서면 (템플릿에 공간 있으면)
        if cost.get('traffic'): ws['AH19'] = get_int_val(cost.get('traffic', 0))
        if cost.get('confirm'): ws['AH20'] = get_int_val(cost.get('confirm', 0))

        total = data.get('total', 0)
        ws['AH21'] = total; ws['Y22'] = total
        
        out = BytesIO(); wb.save(out); out.seek(0)
        return out
    except Exception as e:
        print(f"Excel Error: {e}")
        return None

# -----------------------------------------------------------------------------
# 5. 세션 초기화
# -----------------------------------------------------------------------------
def init_session():
    # Tab 1
    if 't1_date' not in st.session_state: st.session_state['t1_date'] = datetime.now().date()
    if 't1_creditor' not in st.session_state: st.session_state['t1_creditor'] = list(CREDITORS.keys())[0]
    if 't1_debtor' not in st.session_state: st.session_state['t1_debtor'] = ''
    if 't1_debtor_addr' not in st.session_state: st.session_state['t1_debtor_addr'] = ''
    if 't1_owner' not in st.session_state: st.session_state['t1_owner'] = ''
    if 't1_owner_addr' not in st.session_state: st.session_state['t1_owner_addr'] = ''
    if 't1_amount' not in st.session_state: st.session_state['t1_amount'] = ''
    if 't1_estate' not in st.session_state: st.session_state['t1_estate'] = """[토지]\n\n[건물]"""
    # Tab 3
    if 't3_parcels' not in st.session_state: st.session_state['t3_parcels'] = 1
    if 't3_rate' not in st.session_state: st.session_state['t3_rate'] = '12.000'
    # Tab 4
    if 'malso_type' not in st.session_state: st.session_state['malso_type'] = '근저당권'

init_session()

# =============================================================================
# 메인 UI 구조
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["📄 근저당권설정", "✍️ 자필서명정보", "🧾 영수증/비용", "🗑️ 말소 문서"])

# -----------------------------------------------------------------------------
# Tab 1: 근저당권설정 (데이터 원본)
# -----------------------------------------------------------------------------
with tab1:
    col_h1, col_h2 = st.columns([5, 1])
    col_h1.markdown("### 📝 근저당권설정 계약서")
    if col_h2.button("🔄 초기화", key="reset_tab1"):
        st.session_state.clear(); st.rerun()
    
    with st.expander("📌 기본 정보", expanded=True):
        st.session_state['t1_date'] = st.date_input("작성일자", value=st.session_state['t1_date'])
        
        # 채권자
        cr_list = list(CREDITORS.keys()) + ["직접입력"]
        curr_cr = st.session_state['t1_creditor']
        idx = cr_list.index(curr_cr) if curr_cr in cr_list else 0
        st.session_state['t1_creditor'] = st.selectbox("채권자 선택", cr_list, index=idx)
        
        # 채권자 상세
        if st.session_state['t1_creditor'] == "직접입력":
            cr_name_val = st.text_input("채권자명")
            cr_addr_val = st.text_input("채권자 주소")
        else:
            cr_name_val = st.session_state['t1_creditor']
            cr_info = CREDITORS.get(cr_name_val, {})
            st.text_input("법인번호", value=cr_info.get('corp_num',''), disabled=True)
            cr_addr_val = st.text_area("채권자 주소", value=cr_info.get('addr',''), disabled=True)

        c1, c2 = st.columns(2)
        with c1:
            st.session_state['t1_debtor'] = st.text_input("채무자 성명", value=st.session_state['t1_debtor'])
            st.session_state['t1_debtor_addr'] = st.text_area("채무자 주소", value=st.session_state['t1_debtor_addr'], height=80)
        with c2:
            st.session_state['t1_owner'] = st.text_input("설정자(소유자) 성명", value=st.session_state['t1_owner'])
            st.session_state['t1_owner_addr'] = st.text_area("설정자 주소", value=st.session_state['t1_owner_addr'], height=80)
            
        st.session_state['t1_amount'] = st.text_input("채권최고액 (숫자만)", value=st.session_state['t1_amount'])
        if st.session_state['t1_amount']:
            st.caption(f"💡 {convert_money_to_korean(st.session_state['t1_amount'])}")

    st.markdown("#### 🏠 부동산 표시")
    st.session_state['t1_estate'] = st.text_area("등기부 내용 입력", value=st.session_state['t1_estate'], height=200)

    # 계약서 생성
    ctype = st.radio("계약서 유형", ["개인", "3자담보", "공동담보"], horizontal=True)
    t_path = resource_path(TEMPLATE_FILENAMES.get(ctype))
    
    if st.button("🚀 계약서 PDF 생성", disabled=not (LIBS_OK and os.path.exists(t_path)), use_container_width=True):
        data = {
            "is_contract": True, "type": ctype,
            "date": format_date_korean(st.session_state['t1_date']),
            "creditor_name": cr_name_val, "creditor_addr": cr_addr_val,
            "debtor_name": st.session_state['t1_debtor'], "debtor_addr": st.session_state['t1_debtor_addr'],
            "owner_name": st.session_state['t1_owner'], "owner_addr": st.session_state['t1_owner_addr'],
            "guarantee": "한정근담보", "amount": convert_money_to_korean(st.session_state['t1_amount']),
            "estate": st.session_state['t1_estate'].split('\n')
        }
        pdf = make_pdf(t_path, data)
        st.download_button("⬇️ 다운로드", pdf, f"근저당권설정_{st.session_state['t1_debtor']}.pdf", "application/pdf", use_container_width=True)

# -----------------------------------------------------------------------------
# Tab 2: 자필서명정보 (Tab 1 데이터 연동)
# -----------------------------------------------------------------------------
with tab2:
    st.markdown("### ✍️ 자필서명정보")
    st.caption("※ 1탭 정보를 불러오며, 주민번호는 여기서 입력합니다.")
    
    c2_1, c2_2 = st.columns(2)
    with c2_1:
        t2_d_name = st.text_input("채무자", value=st.session_state['t1_debtor'], key="t2d")
        t2_d_rrn = st.text_input("채무자 주민번호", key="t2d_rrn")
    with c2_2:
        t2_o_name = st.text_input("소유자", value=st.session_state['t1_owner'], key="t2o")
        t2_o_rrn = st.text_input("소유자 주민번호", key="t2o_rrn")
        
    t2_estate = st.text_area("부동산 표시 (수정 가능)", value=st.session_state['t1_estate'], height=150, key="t2_est")
    
    t_path = resource_path(TEMPLATE_FILENAMES["자필"])
    if st.button("📄 자필서명 PDF 생성", disabled=not (LIBS_OK and os.path.exists(t_path)), use_container_width=True):
        data = {
            "date": format_date_korean(st.session_state['t1_date']),
            "d_name": t2_d_name, "d_rrn": t2_d_rrn,
            "o_name": t2_o_name, "o_rrn": t2_o_rrn,
            "estate": t2_estate.split('\n')
        }
        pdf = make_pdf(t_path, data)
        st.download_button("⬇️ 다운로드", pdf, "자필서명정보.pdf", "application/pdf", use_container_width=True)

# -----------------------------------------------------------------------------
# Tab 3: 영수증/비용 (1탭 연동, 엑셀 출력)
# -----------------------------------------------------------------------------
with tab3:
    st.markdown("### 🧾 영수증 및 비용 (Excel)")
    
    # 1. 1탭 데이터 자동 Load
    def_cred = st.session_state['t1_creditor'] if st.session_state['t1_creditor'] != "직접입력" else "채권자"
    def_addr = extract_address(st.session_state['t1_estate'])
    
    col3_1, col3_2, col3_3 = st.columns(3)
    with col3_1:
        t3_amt = st.text_input("채권최고액", value=st.session_state['t1_amount'], key="t3_amt")
    with col3_2:
        t3_parcels = st.number_input("필지수", min_value=1, value=st.session_state['t3_parcels'], key="t3_parcels")
    with col3_3:
        t3_rate = st.text_input("할인율(%)", value=st.session_state['t3_rate'], key="t3_rate")

    st.markdown("#### 상세 정보 (1탭 연동)")
    c3_a, c3_b = st.columns(2)
    with c3_a: t3_debtor = st.text_input("채무자", value=st.session_state['t1_debtor'], key="t3_deb")
    with c3_b: t3_creditor = st.text_input("금융사", value=def_cred, key="t3_cred")
    t3_estate = st.text_input("물건지", value=def_addr, key="t3_est")

    with st.expander("비용 상세 입력 (자동계산 + 수기)", expanded=True):
        # 기본 자동 계산값
        amt_val = get_int_val(t3_amt)
        base_reg = math.floor(amt_val * 0.002 / 10) * 10
        base_edu = math.floor(base_reg * 0.2 / 10) * 10
        
        ec1, ec2 = st.columns(2)
        with ec1:
            c_reg = st.number_input("등록면허세", value=base_reg)
            c_edu = st.number_input("지방교육세", value=base_edu)
            c_stamp = st.number_input("증지대", value=15000 * t3_parcels)
            c_bond = st.number_input("채권할인", value=0)
        with ec2:
            c_cert = st.number_input("제증명", value=50000)
            c_orig = st.number_input("원인증서", value=50000)
            c_addr = st.number_input("주소변경", value=0)
            c_malso = st.number_input("선순위 말소", value=0)
            c_traffic = st.number_input("교통비", value=0)
            c_confirm = st.number_input("확인서면", value=0)

    total_cost = c_reg + c_edu + c_stamp + c_bond + c_cert + c_orig + c_addr + c_malso + c_traffic + c_confirm
    st.success(f"💰 공과금 합계: {format_comma(total_cost)} 원")
    
    t_path = resource_path(TEMPLATE_FILENAMES["영수증"])
    if st.button("🏦 영수증 Excel 생성", disabled=not (EXCEL_OK and os.path.exists(t_path)), use_container_width=True):
        data = {
            'client': {'creditor': t3_creditor, 'debtor': t3_debtor, 'amount': t3_amt, 'estate': t3_estate},
            'cost': {
                'reg':c_reg, 'edu':c_edu, 'stamp':c_stamp, 'bond':c_bond, 
                'cert':c_cert, 'orig':c_orig, 'addr':c_addr, 'malso':c_malso,
                'traffic': c_traffic, 'confirm': c_confirm
            },
            'total': total_cost
        }
        xlsx = create_receipt(data, t_path)
        if xlsx:
            st.download_button("⬇️ Excel 다운로드", xlsx, f"영수증_{t3_debtor}.xlsx", 
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        else:
            st.error("엑셀 생성 실패")

# -----------------------------------------------------------------------------
# Tab 4: 말소 문서 (체크박스 제거 & 소유자 중심)
# -----------------------------------------------------------------------------
with tab4:
    c4_h1, c4_h2 = st.columns([5, 1])
    c4_h1.markdown("### 🗑️ 말소 문서 작성")
    if c4_h2.button("🔄 4탭 초기화", key="reset_tab4"):
        for k in list(st.session_state.keys()):
            if k.startswith("malso_"): del st.session_state[k]
        st.rerun()

    # 말소 유형
    st.markdown("#### 1. 말소 유형")
    b1, b2, b3 = st.columns(3)
    if b1.button("근저당권", use_container_width=True): st.session_state['malso_type'] = "근저당권"
    if b2.button("질권", use_container_width=True): st.session_state['malso_type'] = "질권"
    if b3.button("전세권", use_container_width=True): st.session_state['malso_type'] = "전세권"
    st.info(f"선택됨: {st.session_state.get('malso_type', '근저당권')}")

    # 당사자 (의무자=공란, 권리자=소유자)
    c4_in1, c4_in2 = st.columns(2)
    with c4_in1:
        st.markdown("**등기의무자 (금융사/채권자)**")
        st.caption("※ 직접 입력하세요.")
        m_ob_corp = st.text_input("법인명(성명)", key="malso_ob_corp")
        m_ob_rep = st.text_input("대표자", key="malso_ob_rep")
        m_ob_addr = st.text_area("주소", height=80, key="malso_ob_addr")
            
    with c4_in2:
        st.markdown("**등기권리자 (소유자)**")
        st.caption("※ 1탭 소유자 정보가 자동 입력됩니다.")
        # 1탭 소유자 정보
        def_owner = st.session_state.get('t1_owner', '')
        def_addr = st.session_state.get('t1_owner_addr', '')
        m_ow_name = st.text_input("성명", value=def_owner, key="malso_ow_name")
        m_ow_addr = st.text_area("주소", value=def_addr, height=80, key="malso_ow_addr")

    st.markdown("---")
    
    # 등기 정보
    cd1, cd2 = st.columns(2)
    with cd1:
        m_date = st.date_input("원인일자", value=st.session_state['t1_date'], key="malso_date")
        m_cause = st.text_input("등기원인", value="해지", key="malso_cause")
    with cd2:
        def_purpose = f"{st.session_state['malso_type']}말소"
        m_purpose = st.text_input("등기목적", value=def_purpose, key="malso_purp")
        
    m_estate = st.text_area("부동산 표시 (수정 가능)", value=st.session_state['t1_estate'], height=150, key="malso_est")
    m_cancel = st.text_input("말소할 등기 (접수번호 등)", key="malso_cancel")

    with st.expander("이관 정보 (이관증명서용)", expanded=True):
        cm1, cm2 = st.columns(2)
        m_from = cm1.text_input("이관 전 (지점)", key="malso_fr")
        m_to = cm2.text_input("이관 후 (본점)", key="malso_to")
        
    st.markdown("### 📥 문서 다운로드")
    docs = ["자필서명정보", "위임장", "해지증서", "이관증명서"]
    cd = st.columns(4)
    
    for i, doc in enumerate(docs):
        with cd[i]:
            t_path = resource_path(MALSO_TEMPLATES.get(doc))
            if st.button(f"📄 {doc}", key=f"btn_{doc}", disabled=not (LIBS_OK and os.path.exists(t_path)), use_container_width=True):
                # 말소용 매핑: PDF의 'debtor' 위치 -> 화면의 소유자(권리자), 'owner' -> 금융사(의무자)
                data = {
                    "date": format_date_korean(m_date),
                    "d_name": m_ow_name, "d_rrn": "", # 소유자 -> debtor 위치
                    "o_name": m_ob_corp, "o_rrn": "", # 금융사 -> owner 위치
                    "estate": m_estate.split('\n')
                }
                pdf = make_pdf(t_path, data)
                st.download_button("⬇️ 저장", pdf, f"{doc}_{m_ob_corp}.pdf", "application/pdf", key=f"dn_{doc}", use_container_width=True)

st.markdown("---")
st.markdown("""<div style='text-align: center; color: #6c757d; padding: 20px;'>
    <p style='margin: 0; font-size: 0.9rem;'><strong>DG-Form 등기온 전자설정 자동화 시스템</strong> | 법무법인 시화</p>
</div>""", unsafe_allow_html=True)