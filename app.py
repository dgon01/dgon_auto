import streamlit as st
import os
import re
import math
from io import BytesIO
from datetime import datetime
import base64

# 현재 실행 디렉토리를 기준으로 경로 설정
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# 0. 페이지 설정 및 커스텀 디자인
# =============================================================================

st.set_page_config(
    layout="wide", 
    page_title="DG-Form | 등기온 전자설정 자동화",
    page_icon="🏠",
    initial_sidebar_state="collapsed"
)

# 이미지/폰트 경로 설정
LOGO_PATH = os.path.join(APP_ROOT, "my_icon.ico")
QR_PATH = os.path.join(APP_ROOT, "등기온QR.png")
KAKAO_PATH = os.path.join(APP_ROOT, "kakaotalk.png")
FONT_PATH = os.path.join(APP_ROOT, "Malgun.ttf")

# 로고 변환 함수
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

logo_base64 = get_base64_image(LOGO_PATH)

# CSS 스타일
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');
    
    .stApp { font-family: 'Noto Sans KR', sans-serif !important; }
    input, textarea, select, button { font-family: 'Noto Sans KR', sans-serif !important; }
    .main { background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%); }
    
    .header-container {
        background: linear-gradient(135deg, #00428B 0%, #0055b8 100%);
        padding: 20px 40px;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0, 66, 139, 0.3);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .header-title {
        color: #FFFFFF;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.3);
    }
    .header-subtitle { color: #FDD000; font-size: 1.2rem; font-weight: 500; margin: 0; }
    
    /* 숫자 입력창 화살표 제거 */
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; 
        margin: 0; 
    }
</style>
""", unsafe_allow_html=True)

# 헤더 렌더링
if logo_base64:
    st.markdown(f"""
    <div class="header-container">
        <div style="display:flex; gap:20px; align-items:center;">
            <img src="data:image/x-icon;base64,{logo_base64}" style="width:80px; background:white; padding:10px; border-radius:10px;">
            <div>
                <h1 class="header-title">DG-Form</h1>
                <p class="header-subtitle">등기온 전자설정 자동화 시스템</p>
            </div>
        </div>
        <div style="color:white; text-align:right;">
            <p style="margin:0; font-weight:600;">법무법인 시화</p>
            <p style="margin:0; opacity:0.8;">부동산 등기는 등기온</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""<div class="header-container"><h1 class="header-title">🏠 DG-Form</h1></div>""", unsafe_allow_html=True)

# =============================================================================
# 1. 라이브러리 로드
# =============================================================================
try:
    import openpyxl
    from openpyxl.cell.cell import MergedCell
    EXCEL_OK = True
except ImportError:
    EXCEL_OK = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from PyPDF2 import PdfReader, PdfWriter
    from fpdf import FPDF
    LIBS_OK = True
except ImportError:
    LIBS_OK = False

# =============================================================================
# 2. 데이터 및 상수
# =============================================================================
TEMPLATE_FILENAMES = {
    "개인": "1.pdf",
    "3자담보": "2.pdf",
    "공동담보": "3.pdf",
    "자필": "자필서명정보 템플릿.pdf",
    "영수증": "영수증_템플릿.xlsx"
}

if 'template_status' not in st.session_state:
    st.session_state['template_status'] = {}
    missing_files = []
    for key, filename in TEMPLATE_FILENAMES.items():
        path = os.path.join(APP_ROOT, filename)
        st.session_state['template_status'][key] = path if os.path.exists(path) else None
        if not st.session_state['template_status'][key]:
            missing_files.append(filename)
    st.session_state['missing_templates'] = missing_files

CREDITORS = {
    "(주)티플레인대부 대표이사 윤웅원": {"addr": "서울특별시 마포구 삼개로16, 2신관1층103호", "corp_num": "110111-7350161", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}},
    "(주)유노스프레스티지대부 사내이사 한은수": {"addr": "서울특별시 강남구 압구정로28길24", "corp_num": "110111-4138560", "fee": {"제증명": 20000, "교통비": 0, "원인증서": 0, "확인서면": 0, "선순위 말소": 0}},
    "(주)파트너스대부 사내이사 허성": {"addr": "부산광역시 부산진구 서면문화로 43", "corp_num": "180111-1452175", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}},
    "(주)드림앤캐쉬대부 대표이사 김재섭": {"addr": "서울특별시 강남구 압구정로28길24", "corp_num": "110111-4176552", "fee": {"제증명": 20000, "교통비": 0, "원인증서": 0}},
    "(주)마젤란트러스트대부 대표이사 김병수": {"addr": "서울특별시 서초구 강남대로34길 7", "corp_num": "110111-6649979", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}},
    "(주)하이클래스대부 사내이사 성윤호": {"addr": "서울특별시 강남구 도곡로 188", "corp_num": "110111-0933512", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}},
    "직접입력": {"addr": "", "corp_num": "", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000, "확인서면": 0, "선순위 말소": 0}}
}

# =============================================================================
# 3. 유틸리티 함수 (Section 3) - [오류 해결: 함수 정의 위치]
# =============================================================================

def format_number_with_comma(num):
    if not num: return ""
    try:
        if isinstance(num, str): num = int(re.sub(r'[^\d]', '', num))
        return "{:,}".format(num)
    except: return str(num)

def remove_commas(v):
    if not v: return 0
    if isinstance(v, (int, float)): return int(v)
    try: return int(re.sub(r'[^\d]', '', str(v)))
    except: return 0

def parse_float(v):
    try: return float(re.sub(r'[^\d.]', '', str(v)))
    except: return 0.0

def floor_10(v): return math.floor(v / 10) * 10

# [중요] NameError 해결을 위한 lookup_base_fee 정의
def lookup_base_fee(amount):
    # 기준 금액 (이상일 경우)
    LOOKUP_KEYS = [0, 30_000_000, 45_000_000, 60_000_000, 106_500_000, 150_000_000, 225_000_000]
    # 해당 보수료
    LOOKUP_VALS = [150_000, 200_000, 250_000, 300_000, 350_000, 400_000, 450_000]
    
    # 큰 금액부터 비교하여 찾기
    for i in range(len(LOOKUP_KEYS) - 1, -1, -1):
        if amount > LOOKUP_KEYS[i]: 
            return LOOKUP_VALS[i]
    return LOOKUP_VALS[0]

def get_rate():
    try:
        import requests
        url = "https://lawss.co.kr/lawpro/homepage/siga/auto_siga_kjaa.php"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=3)
        response.encoding = 'EUC-KR'
        match = re.search(r"오늘 채권할인율\s*=\s*([\d\.]+) %", response.text)
        if match:
            return math.ceil(float(match.group(1)) * 10) / 10 / 100
    except: pass
    return 0.0913459

def number_to_korean(num_str):
    try: num = remove_commas(num_str)
    except: return ""
    if num == 0: return "영원정"
    units = ['', '만', '억', '조']; digits = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
    result = []; unit_idx = 0
    while num > 0:
        part = num % 10000
        if part > 0:
            p_str = ""
            if part >= 1000: p_str += digits[part//1000] + "천"; part %= 1000
            if part >= 100: p_str += digits[part//100] + "백"; part %= 100
            if part >= 10: p_str += digits[part//10] + "십"; part %= 10
            if part > 0: p_str += digits[part]
            result.append(p_str + units[unit_idx])
        num //= 10000; unit_idx += 1
    return ''.join(reversed(result)) + "원정"

def convert_multiple_amounts_to_korean(amount_input):
    if not amount_input: return ""
    s = str(amount_input)
    if '/' in s: return ', '.join([number_to_korean(x.strip()) for x in s.split('/')])
    return number_to_korean(s)

def extract_address_from_estate(text):
    if not text: return ""
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    if not lines: return ""
    
    # 1. '표시'가 없는 줄 중에서 '시/군/구'가 있는 줄 우선
    for line in lines:
        if ('시 ' in line or '군 ' in line or '구 ' in line) and '표시' not in line:
            return line
    
    # 2. 없으면 그냥 '표시' 제외한 첫 줄
    for line in lines:
        if '표시' not in line and '[' not in line:
            return line
            
    return lines[0]

# =============================================================================
# 4. PDF 생성 클래스 (디자인)
# =============================================================================
class PDFConverter(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        if os.path.exists(FONT_PATH):
            self.add_font('Malgun', '', FONT_PATH, uni=True)
            self.add_font('Malgun', 'B', FONT_PATH, uni=True)
            self.font_family = 'Malgun'
        else:
            self.font_family = 'Arial'

    def draw_box(self, title, items):
        start_y = self.get_y()
        self.set_font(self.font_family, 'B', 11)
        self.cell(0, 8, title, ln=True)
        
        box_y = self.get_y()
        self.set_font(self.font_family, '', 10)
        
        for label, value in items:
            self.cell(140, 7, f"  {label}", border='L,B', align='L')
            self.cell(0, 7, f"{value}  ", border='R,B', align='R', ln=True)
            
        end_y = self.get_y()
        self.line(10, box_y, 200, box_y)
        self.line(10, box_y, 10, end_y)
        self.line(200, box_y, 200, end_y)
        self.ln(5)

    def output_pdf(self, data):
        self.add_page()
        
        # 1. 타이틀
        self.set_font(self.font_family, 'B', 22)
        self.cell(0, 15, "근저당권설정 비용내역", ln=True, align="C")
        self.ln(5)
        
        # 2. 기본 정보
        client = data['client']
        self.set_font(self.font_family, '', 10)
        self.cell(0, 6, f"작성일: {data['date_input']}", ln=True, align="R")
        self.cell(0, 6, f"채권최고액: {client['채권최고액']} 원 | 필지수: {client['필지수']}", ln=True)
        self.cell(0, 6, f"채권자: {client['금융사']}", ln=True)
        self.cell(0, 6, f"채무자: {client['채무자']}", ln=True)
        self.multi_cell(0, 6, f"물건지: {client['물건지']}")
        self.ln(5)
        
        # 3. 보수액 섹션 (박스)
        fee = data['fee_totals']
        fee_items = [
            ("보수액 소계", f"{fee['공급가액']:,} 원"),
            ("부가세", f"{fee['부가세']:,} 원"),
            ("보수 소계", f"{fee['보수총액']:,} 원")
        ]
        self.draw_box("1. 보수액", fee_items)
        
        # 4. 공과금 섹션 (박스)
        cost = data['cost_items']
        cost_list = []
        if cost.get('등록면허세'): cost_list.append(("등록면허세", f"{cost['등록면허세']:,} 원"))
        if cost.get('지방교육세'): cost_list.append(("지방교육세", f"{cost['지방교육세']:,} 원"))
        if cost.get('증지대'): cost_list.append(("증지대", f"{cost['증지대']:,} 원"))
        if cost.get('채권할인금액'): cost_list.append(("국민주택채권매입(할인)", f"{cost['채권할인금액']:,} 원"))
        
        for k in ["제증명", "교통비", "원인증서", "주소변경", "확인서면", "선순위 말소"]:
            val = cost.get(k, 0)
            if val > 0:
                cost_list.append((k, f"{val:,} 원"))
        
        cost_list.append(("공과금 소계", f"{data['cost_totals']['공과금 총액']:,} 원"))
        self.draw_box("2. 공과금", cost_list)
        
        # 5. 합계
        self.set_font(self.font_family, 'B', 14)
        self.cell(140, 12, "등기비용 합계", border='TB', align='C')
        self.cell(0, 12, f"{data['grand_total']:,} 원", border='TB', align='R', ln=True)
        self.ln(10)
        
        # 6. 계좌 정보
        self.set_font(self.font_family, 'B', 11)
        self.cell(0, 8, "입금 계좌 정보", ln=True)
        self.set_font(self.font_family, '', 10)
        self.cell(0, 6, "• 신한은행 100-035-852291", ln=True)
        self.cell(0, 6, "• 예금주: 법무법인 시화", ln=True)
        self.ln(2)
        self.cell(0, 6, "• 입금자는 반드시 소유자(또는 채무자) 성명으로 기재 부탁드립니다.", ln=True)
        self.ln(10)
        
        # 7. 하단 정보
        y_pos = self.get_y()
        self.set_font(self.font_family, 'B', 12)
        self.cell(0, 6, "법무법인 시화", ln=True, align='C')
        self.set_font(self.font_family, '', 10)
        self.cell(0, 6, "부동산 등기는 등기온", ln=True, align='C')
        
        if os.path.exists(QR_PATH):
            self.image(QR_PATH, x=160, y=y_pos, w=25)
        if os.path.exists(KAKAO_PATH):
            self.image(KAKAO_PATH, x=152, y=y_pos+10, w=6)
            
        self.set_xy(145, y_pos+26)
        self.set_font(self.font_family, 'B', 8)
        self.cell(45, 5, "카카오 채널 문의", align='C')

        return self.output(dest='S')

# 기존 PDF 오버레이 함수 (make_pdf)
def draw_fit_text(c, text, x, y, max_width, font_name='Korean', max_size=11, min_size=6):
    if not text: return
    current_size = max_size
    text_width = pdfmetrics.stringWidth(text, font_name, current_size)
    while text_width > max_width and current_size > min_size:
        current_size -= 0.5
        text_width = pdfmetrics.stringWidth(text, font_name, current_size)
    c.setFont(font_name, current_size)
    c.drawString(x, y, text)

def create_overlay_pdf(data, font_path):
    packet = BytesIO(); c = canvas.Canvas(packet, pagesize=A4); width, height = A4
    try: 
        pdfmetrics.registerFont(TTFont('Korean', font_path))
        font_name = 'Korean'
    except: 
        font_name = 'Helvetica'
    
    font_size = 11; c.setFont(font_name, font_size); c.setFillColorRGB(0, 0, 0)
    MAX_TEXT_WIDTH = 380
    
    if data.get("date"): c.drawString(480, height - 85, data["date"])
    if data.get("creditor_name"): c.drawString(157, height - 134, data["creditor_name"])
    if data.get("creditor_addr"): draw_fit_text(c, data["creditor_addr"], 157, height - 150, MAX_TEXT_WIDTH, font_name, font_size)
    if data.get("debtor_name"): c.drawString(157, height - 172, data["debtor_name"])
    if data.get("debtor_addr"): draw_fit_text(c, data["debtor_addr"], 157, height - 190, MAX_TEXT_WIDTH, font_name, font_size)
    if data.get("owner_name"): c.drawString(157, height - 212, data["owner_name"])
    if data.get("owner_addr"): draw_fit_text(c, data["owner_addr"], 157, height - 230, MAX_TEXT_WIDTH, font_name, font_size)
    if data.get("guarantee_type"): c.drawString(65, height - 343, data["guarantee_type"])
    if data.get("claim_amount"): c.drawString(150, height - 535, data["claim_amount"])
    
    c.showPage(); c.setFont(font_name, font_size)
    if data.get("date"): c.drawString(180, height - 270, data["date"])
    
    contract_type = data.get("contract_type", "3자담보")
    if contract_type == "개인":
        if data.get("debtor_name"): c.drawString(450, height - 270, data["debtor_name"])
    elif contract_type == "3자담보":
        if data.get("owner_name"): c.drawString(490, height - 270, data["owner_name"])
    elif contract_type == "공동담보":
        if data.get("debtor_name"): c.drawString(450, height - 270, data["debtor_name"])
        if data.get("owner_name"): c.drawString(490, height - 270, data["owner_name"])
    
    c.showPage(); c.setFont(font_name, font_size)
    base_x = 35; base_y = height - 80; gap = 16
    for i, line in enumerate(data.get("estate_list", [])):
        if line.strip(): c.drawString(base_x, base_y - (i * gap), line)
    
    c.showPage(); c.save(); packet.seek(0)
    return packet

def make_pdf(template_path, data):
    overlay_packet = create_overlay_pdf(data, FONT_PATH)
    overlay_pdf = PdfReader(overlay_packet); template_pdf = PdfReader(template_path); writer = PdfWriter()
    
    for page_num in range(min(len(template_pdf.pages), len(overlay_pdf.pages))):
        template_page = template_pdf.pages[page_num]; overlay_page = overlay_pdf.pages[page_num]
        template_page.merge_page(overlay_page); writer.add_page(template_page)
    
    out_buffer = BytesIO()
    writer.write(out_buffer)
    out_buffer.seek(0)
    return out_buffer

def create_signature_overlay_pdf(data, font_path):
    packet = BytesIO(); c = canvas.Canvas(packet, pagesize=A4); width, height = A4
    try: 
        pdfmetrics.registerFont(TTFont('Korean', font_path))
        font_name = 'Korean'
    except: 
        font_name = 'Helvetica'
    c.setFont(font_name, 10); estate_x = 150; estate_y = height - 170; line_h = 14
    if data.get("estate_text"):
        for i, line in enumerate(data["estate_text"].split("\n")[:17]):
            c.drawString(estate_x, estate_y - (i * line_h), line)
    if data.get("debtor_name"): c.drawString(250, 322, data["debtor_name"])
    if data.get("debtor_rrn"): c.drawString(250, 298, data["debtor_rrn"])
    if data.get("owner_name"): c.drawString(400, 322, data["owner_name"])
    if data.get("owner_rrn"): c.drawString(400, 298, data["owner_rrn"])
    if data.get("date"):
        c.setFont(font_name, 11); text = data["date"]; tw = c.stringWidth(text, font_name, 11)
        c.drawString((width - tw) / 2, 150, text)
    c.showPage(); c.save(); packet.seek(0)
    return packet

def make_signature_pdf(template_path, data):
    overlay_packet = create_signature_overlay_pdf(data, FONT_PATH)
    overlay_pdf = PdfReader(overlay_packet); template_pdf = PdfReader(template_path); writer = PdfWriter()
    template_page = template_pdf.pages[0]; overlay_page = overlay_pdf.pages[0]
    template_page.merge_page(overlay_page); writer.add_page(template_page)
    out_buffer = BytesIO()
    writer.write(out_buffer)
    out_buffer.seek(0)
    return out_buffer

# =============================================================================
# 5. Streamlit UI 및 상태 관리
# =============================================================================

if 'calc_data' not in st.session_state:
    st.session_state['calc_data'] = {}
    st.session_state['input_date'] = datetime.now().strftime("%Y/%m/%d")
    st.session_state['calc_amount_override'] = ""
    st.session_state['calc_creditor_override'] = ""
    st.session_state['calc_debtor_override'] = ""
    st.session_state['calc_addr_override'] = ""

def sync_data():
    st.session_state['calc_debtor_override'] = st.session_state.get('t1_debtor_name', "")
    
def sync_addr():
    text = st.session_state.get('estate_text_area', "")
    st.session_state['calc_addr_override'] = extract_address_from_estate(text)

def sync_amount():
    val = st.session_state.get('amount_raw_input', "")
    st.session_state['calc_amount_override'] = format_number_with_comma(val)

def calculate_all(data):
    amount = remove_commas(data.get('채권최고액'))
    parcels = remove_commas(data.get('필지수'))
    rate = parse_float(data.get('채권할인율', '0')) / 100.0
    
    # [오류해결] lookup_base_fee 함수가 이제 정의되어 있어 호출 가능
    base_fee = lookup_base_fee(amount)
    data['기본료'] = base_fee
    
    fee_total = base_fee 
    
    addr_cnt = st.session_state.get('addr_count_num', 1) if st.session_state.get('addr_change_check') else 0
    
    reg = floor_10(amount * 0.002) + (6000 * addr_cnt)
    edu = floor_10(amount * 0.002 * 0.2) + (1200 * addr_cnt)
    jeungji = (18000 * parcels) + (3000 * addr_cnt)
    
    bond = 0
    if amount >= 20000000: bond = math.ceil(amount * 0.01 / 10000) * 10000
    bond_disc = floor_10(bond * rate)
    
    data.update({
        "등록면허세": reg, "지방교육세": edu, "증지대": jeungji, "채권할인금액": bond_disc
    })
    
    manual_sum = 0
    for k in ["제증명", "교통비", "원인증서", "주소변경", "확인서면", "선순위 말소"]:
        manual_sum += remove_commas(data.get(k, 0))
        
    data['공과금 총액'] = reg + edu + jeungji + bond_disc + manual_sum
    data['보수총액'] = fee_total 
    data['총 합계'] = data['공과금 총액'] + data['보수총액']
    
    data['client'] = {
        '채권최고액': format_number_with_comma(amount),
        '필지수': parcels,
        '금융사': data['금융사'],
        '채무자': data['채무자'],
        '물건지': data['물건지']
    }
    data['fee_totals'] = {'공급가액': base_fee, '부가세': int(base_fee*0.1), '보수총액': int(base_fee*1.1)}
    data['cost_items'] = {k: remove_commas(data.get(k,0)) for k in ["등록면허세", "지방교육세", "증지대", "채권할인금액", "제증명", "교통비", "원인증서", "주소변경", "확인서면", "선순위 말소"]}
    data['cost_totals'] = {'공과금 총액': data['공과금 총액']}
    data['grand_total'] = data['총 합계']
    data['date_input'] = st.session_state['input_date']
    
    return data

# =============================================================================
# UI
# =============================================================================
tab1, tab2, tab3 = st.tabs(["📄 계약서 작성", "✍️ 자필서명", "🧾 비용산출"])

# Tab 1
with tab1:
    col_header = st.columns([5, 1])
    col_header[0].markdown("### 📝 근저당권설정 계약서 작성")
    
    if col_header[1].button("🔄 초기화", key="reset_tab1"):
        st.session_state['input_date'] = datetime.now().strftime("%Y/%m/%d")
        st.session_state['input_creditor'] = list(CREDITORS.keys())[0]
        st.session_state['input_debtor'] = ""
        st.session_state['input_debtor_addr'] = ""
        st.session_state['input_owner'] = ""
        st.session_state['input_owner_addr'] = ""
        st.session_state['contract_type'] = "개인"
        st.session_state['guarantee'] = "한정근담보"
        st.session_state['input_amount'] = ""
        st.session_state['amount_raw_input'] = "" 
        st.session_state['estate_text'] = ""
        st.session_state['input_debtor_rrn'] = ""
        st.session_state['input_owner_rrn'] = ""
        st.session_state['calc_amount_override'] = ""
        st.session_state['calc_creditor_override'] = ""
        st.session_state['calc_debtor_override'] = ""
        st.session_state['calc_addr_override'] = ""
        st.rerun()
    
    st.markdown("---")
    
    with st.expander("📌 기본 정보", expanded=True):
        d = st.date_input("작성일자", value=datetime.now())
        st.session_state['input_date'] = d.strftime("%Y/%m/%d")

    with st.expander("👤 당사자 정보", expanded=True):
        creditor_list = ["직접입력"] + [k for k in CREDITORS.keys() if k != "직접입력"]
        selected_creditor = st.selectbox("채권자 선택", options=creditor_list, key='t1_creditor_select', on_change=handle_creditor_change)
        st.session_state['input_creditor'] = selected_creditor
        
        creditor_info = CREDITORS.get(selected_creditor, {})
        default_corp_num = "" if selected_creditor == "직접입력" else creditor_info.get('corp_num', '')
        default_addr = "" if selected_creditor == "직접입력" else creditor_info.get('addr', '')

        st.text_input("법인번호", value=default_corp_num)
        st.text_area("채권자 주소", value=default_addr)
        
        st.session_state['input_debtor'] = st.text_input("채무자 성명", value=st.session_state.get('input_debtor'), key='t1_debtor_name', on_change=sync_data)
        st.session_state['input_debtor_addr'] = st.text_area("채무자 주소", value=st.session_state.get('input_debtor_addr'), key='t1_debtor_addr', height=100)
        st.session_state['input_owner'] = st.text_input("설정자 성명", value=st.session_state.get('input_owner'), key='t1_owner_name')
        st.session_state['input_owner_addr'] = st.text_area("설정자 주소", value=st.session_state.get('input_owner_addr'), key='t1_owner_addr', height=100)

    with st.expander("🤝 담보 및 계약 정보", expanded=True):
        st.session_state['contract_type'] = st.radio("계약서 유형", options=["개인", "3자담보", "공동담보"], horizontal=True, key='contract_type_radio')
        st.session_state['guarantee'] = st.text_input("피담보채무", value=st.session_state.get('guarantee'))
        
        def format_amount_on_change():
            raw_val = st.session_state.get('amount_raw_input', '')
            formatted = format_number_with_comma(raw_val)
            st.session_state['input_amount'] = formatted
            st.session_state['amount_raw_input'] = formatted
            st.session_state['calc_amount_override'] = formatted
        
        st.text_input("채권최고액", key='amount_raw_input', on_change=format_amount_on_change, placeholder="숫자만 입력 (엔터 입력 시 콤마 적용)")
        
        if st.session_state.get('input_amount') and st.session_state['input_amount'] != "0":
            clean_amt = remove_commas(st.session_state['input_amount'])
            korean_amt = number_to_korean(clean_amt)
            st.info(f"💰 **{korean_amt}** (금액: {st.session_state['input_amount']}원)")
        
        col_addr1, col_addr2 = st.columns([5, 1])
        def copy_debtor_address():
            if st.session_state.get('t1_debtor_addr'):
                st.session_state['collateral_addr_input'] = st.session_state['t1_debtor_addr']
                st.session_state['input_collateral_addr'] = st.session_state['t1_debtor_addr']
        
        with col_addr1:
            st.text_area("물건지 주소 (수기 입력)", key='collateral_addr_input', height=100, label_visibility="collapsed")
            if 'collateral_addr_input' in st.session_state:
                st.session_state['input_collateral_addr'] = st.session_state['collateral_addr_input']
        
        with col_addr2:
            st.write("\n\n"); st.button("📋\n채무자\n주소복사", on_click=copy_debtor_address)

    st.markdown("---")
    st.markdown("### 🏠 부동산의 표시")
    st.caption("※ 등기부등본 내용을 입력하세요")
    
    col_estate, col_pdf = st.columns([3, 1])
    with col_estate:
        st.session_state['estate_text'] = st.text_area("부동산 표시 내용", value=st.session_state.get('estate_text', ''), height=300, key='estate_text_area', on_change=sync_addr)
    
    with col_pdf:
        st.markdown("#### 📑 파일 생성")
        selected_template_path = st.session_state['template_status'].get(st.session_state['contract_type'])
        if selected_template_path: st.success(f"✅ 템플릿 준비완료")
        else: st.warning(f"⚠️ 템플릿 없음")
        
        if st.button("🚀 계약서\nPDF 생성", key="generate_pdf_tab1", disabled=not LIBS_OK, use_container_width=True):
            if LIBS_OK:
                debtor_name = st.session_state.get('input_debtor', "미지정")
                creditor_info = CREDITORS.get(st.session_state.get('input_creditor'), {})
                data = {
                    "date": st.session_state['input_date'], 
                    "creditor_name": st.session_state['input_creditor'], 
                    "creditor_addr": creditor_info.get('addr', ''),
                    "debtor_name": st.session_state['input_debtor'], 
                    "debtor_addr": st.session_state['input_debtor_addr'],
                    "owner_name": st.session_state['input_owner'], 
                    "owner_addr": st.session_state['input_owner_addr'],
                    "guarantee_type": st.session_state['guarantee'], 
                    "claim_amount": convert_multiple_amounts_to_korean(remove_commas(st.session_state['input_amount'])),
                    "estate_list": st.session_state['estate_text'].strip().split("\n"), 
                    "contract_type": st.session_state['contract_type']
                }
                try:
                    pdf_buffer = make_pdf(selected_template_path, data)
                    st.download_button("⬇️ 다운로드", data=pdf_buffer, file_name=f"근저당권설정_{debtor_name}.pdf", mime="application/pdf", use_container_width=True)
                    st.success("✅ 완료!")
                except Exception as e: st.error(f"오류: {e}")

# Tab 2 (자필서명)
with tab2:
    col_header2 = st.columns([5, 1])
    col_header2[0].markdown("### ✍️ 자필서명정보 작성")
    if col_header2[1].button("🔄 초기화", key="reset_tab2"):
        st.session_state['sig_debtor'] = ""
        st.session_state['input_debtor_rrn'] = ""
        st.session_state['sig_owner'] = ""
        st.session_state['input_owner_rrn'] = ""
        st.rerun()
    st.markdown("---")
    col_l2, col_r2 = st.columns(2)
    with col_l2:
        st.session_state['sig_date'] = st.text_input("작성일자", value=st.session_state.get('input_date'), key='sig_date_input', disabled=True)
        st.session_state['sig_debtor'] = st.text_input("설정자(단독/채무자)", value=st.session_state.get('input_debtor'), key='sig_debtor_input')
        st.session_state['input_debtor_rrn'] = st.text_input("주민등록번호(채무자)", value=st.session_state.get('input_debtor_rrn'), key='sig_debtor_rrn_input')
        st.session_state['sig_owner'] = st.text_input("설정자(공동/물상보증인)", value=st.session_state.get('input_owner'), key='sig_owner_input')
        st.session_state['input_owner_rrn'] = st.text_input("주민등록번호(설정자)", value=st.session_state.get('input_owner_rrn'), key='sig_owner_rrn_input')
    with col_r2:
        st.session_state['sig_estate_text'] = st.text_area("부동산 표시 (확인용)", value=st.session_state.get('estate_text'), height=350, key='sig_estate_area', disabled=True)
        sig_template_path = st.session_state['template_status'].get("자필")
        if st.button("📄 자필서명 PDF 생성", key="generate_sig_pdf", disabled=not sig_template_path or not LIBS_OK, use_container_width=True):
            if LIBS_OK:
                debtor_name = st.session_state['sig_debtor'] if st.session_state['sig_debtor'] else "미지정"
                data = {
                    "date": st.session_state['sig_date'], "debtor_name": st.session_state['sig_debtor'], "debtor_rrn": st.session_state['input_debtor_rrn'],
                    "owner_name": st.session_state['sig_owner'], "owner_rrn": st.session_state['input_owner_rrn'], "estate_text": st.session_state['sig_estate_text']
                }
                try:
                    pdf_buffer = make_signature_pdf(sig_template_path, data)
                    st.download_button("⬇️ PDF 다운로드", data=pdf_buffer, file_name=f"자필서명정보_{debtor_name}.pdf", mime="application/pdf", use_container_width=True)
                    st.success("✅ 완료!")
                except Exception as e: st.error(f"오류: {e}")

# Tab 3 (비용산출)
with tab3:
    st.markdown("### 🧾 비용 계산 및 출력")
    if st.button("🔄 초기화", key="reset_tab3"):
        st.session_state['calc_data'] = {}
        st.session_state['addr_change'] = False
        st.session_state['input_parcels'] = 1
        st.session_state['input_rate'] = f"{get_rate()*100:.5f}"
        handle_creditor_change()
        st.rerun()
    st.markdown("---")
    
    # 1탭 연동 데이터 (수정 가능)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("채권최고액", key='calc_amount_override')
        st.text_input("금융사", key='calc_creditor_override')
    with c2:
        parcels = st.text_input("필지수", value=st.session_state.get('input_parcels'), key='calc_parcels_input')
        st.session_state['input_parcels'] = remove_commas(parcels)
        st.text_input("채무자", key='calc_debtor_override')
    with c3:
        rate = st.text_input("채권할인율(%)", value=st.session_state.get('input_rate'), key='calc_rate_input')
        if st.button("🔄 시세 업데이트"):
            st.session_state['input_rate'] = f"{get_rate()*100:.5f}"
            st.rerun()
        st.text_input("물건지", key='calc_addr_override')

    st.markdown("#### 기타 비용 및 공과금")
    cc1, cc2 = st.columns(2)
    with cc1:
        st.text_input("제증명", key="cost_manual_제증명", on_change=lambda: st.session_state.update({'cost_manual_제증명': format_number_with_comma(st.session_state['cost_manual_제증명'])}))
        st.text_input("원인증서", key="cost_manual_원인증서", on_change=lambda: st.session_state.update({'cost_manual_원인증서': format_number_with_comma(st.session_state['cost_manual_원인증서'])}))
        st.text_input("주소변경비용", key="cost_manual_주소변경", on_change=lambda: st.session_state.update({'cost_manual_주소변경': format_number_with_comma(st.session_state['cost_manual_주소변경'])}))
    with cc2:
        st.text_input("교통비", key="cost_manual_교통비", on_change=lambda: st.session_state.update({'cost_manual_교통비': format_number_with_comma(st.session_state['cost_manual_교통비'])}))
        st.text_input("선순위말소", key="cost_manual_선순위 말소", on_change=lambda: st.session_state.update({'cost_manual_선순위 말소': format_number_with_comma(st.session_state['cost_manual_선순위 말소'])}))
        st.text_input("확인서면", key="cost_manual_확인서면", on_change=lambda: st.session_state.update({'cost_manual_확인서면': format_number_with_comma(st.session_state['cost_manual_확인서면'])}))

    # 계산 실행
    calc_input = {
        '채권최고액': st.session_state.get('calc_amount_override'),
        '필지수': st.session_state.get('input_parcels'),
        '채권할인율': st.session_state.get('input_rate'),
        '채무자': st.session_state.get('calc_debtor_override'),
        '물건지': st.session_state.get('calc_addr_override'),
        '금융사': st.session_state.get('calc_creditor_override'),
        '제증명': st.session_state.get('cost_manual_제증명'),
        '교통비': st.session_state.get('cost_manual_교통비'),
        '원인증서': st.session_state.get('cost_manual_원인증서'),
        '주소변경': st.session_state.get('cost_manual_주소변경'),
        '확인서면': st.session_state.get('cost_manual_확인서면'),
        '선순위 말소': st.session_state.get('cost_manual_선순위 말소')
    }
    
    final_data = calculate_all(calc_input)
    st.session_state['calc_data'] = final_data

    st.markdown("---")
    st.metric("총 청구금액", f"{final_data['grand_total']:,} 원")
    
    # 다운로드 영역
    d_col1, d_col2 = st.columns(2)
    if LIBS_OK:
        pdf = PDFConverter()
        pdf_data = pdf.output_pdf(final_data)
        d_col1.download_button("📄 비용내역서 PDF", data=pdf_data, file_name=f"비용내역서_{final_data['채무자']}.pdf", mime="application/pdf", use_container_width=True)
    else: d_col1.error("PDF 라이브러리 미설치")
    
    if EXCEL_OK and st.session_state['template_status'].get("영수증"):
        wb = openpyxl.load_workbook(os.path.join(APP_ROOT, "영수증_템플릿.xlsx"))
        ws = wb.active
        # 매핑
        ws['AH15'] = remove_commas(calc_input['제증명'])
        ws['AH16'] = remove_commas(calc_input['원인증서'])
        ws['AH17'] = remove_commas(calc_input['주소변경'])
        ws['AH18'] = remove_commas(calc_input['선순위 말소'])
        ws['AH19'] = remove_commas(calc_input['교통비'])
        ws['AH21'] = final_data['공과금 총액']
        
        out = BytesIO()
        wb.save(out)
        d_col2.download_button("🏦 영수증 Excel", data=out, file_name=f"영수증_{final_data['채무자']}.xlsx", use_container_width=True)
    else: d_col2.error("Excel 템플릿 없음")

# 푸터
st.markdown("---")
st.markdown("""<div style='text-align: center; color: #6c757d; padding: 20px;'>DG-Form 등기온 전자설정 자동화 시스템 | 법무법인 시화</div>""", unsafe_allow_html=True)