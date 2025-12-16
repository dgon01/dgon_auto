import streamlit as st
import os
import re
import math
from io import BytesIO
from datetime import datetime, date
import base64

# 현재 실행 디렉토리를 기준으로 경로 설정
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# 0. 페이지 설정 및 커스텀 디자인
# =============================================================================

st.set_page_config(
    layout="wide", 
    page_title="DG-Form | 등기온 전자설정 자동화",
    page_icon=os.path.join(APP_ROOT, "my_icon.ico"),
    initial_sidebar_state="collapsed"
)

# 로고 이미지를 base64로 인코딩하는 함수
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

# 로고 이미지 경로
LOGO_PATH = os.path.join(APP_ROOT, "my_icon.ico")
logo_base64 = get_base64_image(LOGO_PATH)

# 💡 등기온 공식 브랜드 컬러 및 스타일 적용
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');
    .stApp {{ font-family: 'Noto Sans KR', sans-serif !important; }}
    input, textarea, select, button {{ font-family: 'Noto Sans KR', sans-serif !important; }}
    
    .header-container {{
        background: white; border: 3px solid #00428B; padding: 20px 40px;
        border-radius: 15px; margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 66, 139, 0.2);
        display: flex; align-items: center; justify-content: space-between;
    }}
    .logo-title-container {{ display: flex; align-items: center; gap: 20px; }}
    .header-logo {{ width: 120px; height: auto; }}
    .header-title {{ margin: 0; font-size: 2.5rem; font-weight: 700; }}
    .title-dg {{ color: #00428B; }}
    .title-form {{ color: #FDD000; }}
    .header-subtitle {{ color: #00428B; font-size: 1.2rem; font-weight: 500; margin: 0; }}
    
    /* 📱 반응형 CSS - 모바일 대응 */
    @media (max-width: 768px) {{
        .header-container {{ 
            padding: 15px 20px !important; 
            flex-direction: column !important; 
            gap: 10px !important;
        }}
        .logo-title-container {{ flex-direction: column !important; text-align: center !important; }}
        .header-logo {{ width: 80px !important; }}
        .header-title {{ font-size: 1.8rem !important; }}
        .header-subtitle {{ font-size: 0.9rem !important; }}
        .header-right p {{ font-size: 0.85rem !important; }}
        h3 {{ font-size: 1.2rem !important; }}
        .total-amount {{ font-size: 1.5rem !important; }}
    }}
    
    .stTabs [data-baseweb="tab-list"] {{ gap: 10px; background-color: #ffffff; padding: 10px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
    .stTabs [data-baseweb="tab"] {{ background-color: #f8f9fa; border-radius: 8px; padding: 10px 20px; font-weight: 600; color: #495057; border: 1px solid #dee2e6; }}
    .stTabs [aria-selected="true"] {{ background-color: #00428B; color: white; border-color: #00428B; }}

    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > select {{
        border-radius: 6px; border: 1px solid #ced4da; padding: 8px 12px; font-size: 0.95rem;
    }}
    .stTextInput > div > div > input:focus {{ border-color: #00428B; box-shadow: 0 0 0 0.2rem rgba(0, 66, 139, 0.15); }}

    /* 헤더 버튼 스타일 */
    .header-btn-container {{
        display: flex;
        gap: 8px;
        flex-wrap: nowrap;
        white-space: nowrap;
    }}
    
    /* 3탭 커스텀 레이아웃 */
    .section-header {{ font-size: 1.1rem; font-weight: 700; margin-bottom: 15px; padding-bottom: 5px; border-bottom: 2px solid; }}
    .income-header {{ color: #28a745; border-color: #28a745; }}
    .tax-header {{ color: #fd7e14; border-color: #fd7e14; }}
    .total-header {{ color: #dc3545; border-color: #dc3545; }}
    .row-label {{ font-weight: 500; color: #495057; display: flex; align-items: center; height: 100%; font-size: 0.9rem; }}
    .total-box {{ background-color: #ff0033; color: white; padding: 20px; text-align: center; border-radius: 8px; margin: 15px 0; box-shadow: 0 4px 6px rgba(220, 53, 69, 0.3); }}
    .total-amount {{ font-size: 2rem; font-weight: 800; }}
    [data-testid="stContainer"] {{ background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border: 1px solid #e9ecef; }}
</style>
""", unsafe_allow_html=True)

# 헤더 섹션
if logo_base64:
    st.markdown(f"""
    <div class="header-container">
        <div class="logo-title-container">
            <img src="data:image/x-icon;base64,{logo_base64}" class="header-logo" alt="DG-ON Logo">
            <div>
                <h1 class="header-title"><span class="title-dg">DG</span><span class="title-form">-Form</span></h1>
                <p class="header-subtitle">등기온 전자설정 자동화 시스템 | 법무법인 시화</p>
            </div>
        </div>
        <div class="header-right">
            <p style="margin: 0; font-size: 1.1rem; font-weight: 600;">부동산 등기는 등기온</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="header-container">
        <div>
            <h1 class="header-title">🏠 <span class="title-dg">DG</span><span class="title-form">-Form</span></h1>
            <p class="header-subtitle">등기온 전자설정 자동화 시스템 | 법무법인 시화</p>
        </div>
        <div class="header-right">
            <p style="margin: 0; font-size: 1.1rem; font-weight: 600;">부동산 등기는 등기온</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# 1. 라이브러리 및 환경 설정
# =============================================================================

# Excel (영수증)
try:
    import openpyxl
    from openpyxl.cell.cell import MergedCell
    EXCEL_OK = True
except Exception:
    openpyxl = None
    MergedCell = None
    EXCEL_OK = False

# 계약서/자필서명정보 PDF (템플릿 위에 오버레이)
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from PyPDF2 import PdfReader, PdfWriter
    PDF_OK = True
except Exception:
    canvas = None
    A4 = None
    pdfmetrics = None
    TTFont = None
    PdfReader = None
    PdfWriter = None
    PDF_OK = False

# 비용내역 PDF (FPDF)
try:
    from fpdf import FPDF
    FPDF_OK = True
except Exception:
    FPDF = None
    FPDF_OK = False

LIBS_OK = PDF_OK

# =============================================================================
# 2. 상수 및 데이터
# =============================================================================
TEMPLATE_FILENAMES = {
    "개인": "1.pdf",
    "3자담보": "2.pdf",
    "공동담보": "3.pdf",
    "자필": "자필서명정보 템플릿.pdf",
    "영수증": "receipt_template.xlsx"
}

CREDITORS = {
    "(주)티플레인대부 대표이사 윤웅원": {"addr": "서울특별시 마포구 삼개로16, 2신관1층103호(도화동,근신빌딩)", "corp_num": "110111-7350161", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}},
    "(주)유노스프레스티지대부 사내이사 한은수": {"addr": "서울특별시 강남구 압구정로28길24, 5층 501호(신사동,디앤씨빌딩)", "corp_num": "110111-4138560", "fee": {"제증명": 20000, "교통비": 0, "원인증서": 0, "확인서면": 0, "선순위 말소": 0}},
    "(주)파트너스대부 사내이사 허성": {"addr": "부산광역시 부산진구 서면문화로 43, 2층(부전동)", "corp_num": "180111-1452175", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}},
    "(주)드림앤캐쉬대부 대표이사 김재섭": {"addr": "서울특별시 강남구 압구정로28길24, 6층 601호(신사동,디앤씨빌딩)", "corp_num": "110111-4176552", "fee": {"제증명": 20000, "교통비": 0, "원인증서": 0}},
    "(주)마젤란트러스트대부 대표이사 김병수": {"addr": "서울특별시 서초구 강남대로34길 7, 7층(양재동,이안빌딩)", "corp_num": "110111-6649979", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}},
    "(주)하이클래스대부 사내이사 성윤호": {"addr": "서울특별시 강남구 도곡로 188, 3층 4호(도곡동,도곡스퀘어)", "corp_num": "110111-0933512", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}},
    "㈜엘하비스트대부 대표이사 김상수": {"addr": "서울특별시 중구 무교로 15, 16층(무교동,남강건설회관빌딩)", "corp_num": "110111-3648627", "fee": {"제증명": 20000, "교통비": 0, "원인증서": 0}}
}

def resource_path(relative_path):
    return os.path.join(APP_ROOT, relative_path)

FONT_PATH = resource_path("Malgun.ttf") 

# 템플릿 파일 상태 확인
if 'template_status' not in st.session_state:
    st.session_state['template_status'] = {}
    missing_files = []
    for key, filename in TEMPLATE_FILENAMES.items():
        path = resource_path(filename)
        st.session_state['template_status'][key] = path if os.path.exists(path) else None
        if not st.session_state['template_status'][key]:
            missing_files.append(filename)
    st.session_state['missing_templates'] = missing_files

# =============================================================================
# 3. 유틸리티 및 계산 로직
# =============================================================================
def format_date_korean(date_obj):
    if isinstance(date_obj, date): return f"{date_obj.year}년 {date_obj.month:02d}월 {date_obj.day:02d}일"
    return str(date_obj)

def format_number_with_comma(num_str):
    if num_str is None: return ""
    if isinstance(num_str, (int, float)): return "{:,}".format(int(num_str))
    numbers = re.sub(r'[^\d]', '', str(num_str))
    if not numbers: return ""
    try: return "{:,}".format(int(numbers))
    except ValueError: return num_str

def remove_commas(v):
    if v is None: return ""
    if isinstance(v, (int, float)): return str(int(v))
    return v.replace(',', '') if isinstance(v, str) else str(v)

def floor_10(v): return math.floor(v / 10) * 10

def lookup_base_fee(amount):
    LOOKUP_KEYS = [0, 30_000_000, 45_000_000, 60_000_000, 106_500_000, 150_000_000, 225_000_000]
    LOOKUP_VALS = [150_000, 200_000, 250_000, 300_000, 350_000, 400_000, 450_000]
    for i in range(len(LOOKUP_KEYS) - 1, -1, -1):
        if amount > LOOKUP_KEYS[i]: return LOOKUP_VALS[i]
    return LOOKUP_VALS[0]

def get_rate():
    try:
        import requests
        url = "https://lawss.co.kr/lawpro/homepage/siga/auto_siga_kjaa.php"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=3)
        response.encoding = 'EUC-KR'
        match = re.search(r"오늘 채권할인율\s*=\s*([\d\.]+) %", response.text)
        if match: return math.ceil(float(match.group(1)) * 10) / 10 / 100
    except: pass
    return 0.0913459

def number_to_korean(num_str):
    if not num_str: return ""
    try: num = int(re.sub(r'[^\d]', '', num_str))
    except: return ""
    units = ['', '만', '억', '조']; digits = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
    if num == 0: return "영원정"
    result = []; unit_idx = 0
    while num > 0:
        part = num % 10000
        if part > 0:
            part_str = ""
            if part >= 1000: part_str += digits[part // 1000] + "천"; part %= 1000
            if part >= 100: part_str += digits[part // 100] + "백"; part %= 100
            if part >= 10: part_str += digits[part // 10] + "십"; part %= 10
            if part > 0: part_str += digits[part]
            result.append(part_str + units[unit_idx])
        num //= 10000; unit_idx += 1
    return ''.join(reversed(result)) + "원정"

def convert_multiple_amounts_to_korean(amount_str):
    if not amount_str: return ""
    if '/' in amount_str:
        return ', '.join([number_to_korean(p.strip()) for p in amount_str.split('/') if number_to_korean(p.strip())])
    return number_to_korean(amount_str)

def extract_address_from_estate(estate_text):
    if not estate_text: return ""
    lines = [line.strip() for line in estate_text.strip().split('\n')]
    for line in lines:
        if "1동의 건물의 표시" in line or "건물의 표시" in line: continue
        if any(region in line for region in ['특별시', '광역시', '시 ', '군 ', '구 ']):
            if '대 ' not in line and '도로명주소' not in line and '[' not in line:
                return line.strip()
    return ""

# PDF 관련 클래스 및 함수 생략 (위와 동일)
if FPDF_OK:
    class PDFConverter(FPDF):
        def __init__(self, show_fee=True):
            super().__init__()
            self.show_fee = show_fee
            self.line_height = 6.5
            self.col_width1 = 150; self.col_width2 = 30
            if FONT_PATH and os.path.exists(FONT_PATH):
                try:
                    self.add_font('Malgun', '', FONT_PATH, uni=True)
                    self.add_font('Malgun', 'B', FONT_PATH, uni=True)
                    self.set_font('Malgun', '', 11)
                except: self.set_font('Arial', '', 11)
            else: self.set_font('Arial', '', 11)
        
        def draw_labelframe_box(self, title, content_func):
            self.set_font(self.font_family, 'B', 11)
            start_y = self.get_y(); start_x = self.l_margin
            box_width = self.w - self.l_margin * 2
            self.set_y(start_y + self.line_height)
            content_func()
            content_end_y = self.get_y()
            box_height = (content_end_y - start_y) + self.line_height + 4
            self.set_draw_color(211, 211, 211)
            self.rect(start_x, start_y + self.font_size / 2, box_width, box_height)
            title_width = self.get_string_width(title)
            self.set_fill_color(255, 255, 255)
            self.rect(start_x + 9, start_y, title_width + 4, self.font_size, 'F')
            self.set_xy(start_x + 11, start_y)
            self.cell(0, self.font_size, title)
            self.set_y(content_end_y + 4)
            
        def output_pdf(self, data):
            self.add_page(); self.set_font(self.font_family, 'B', 20)
            self.cell(0, 12, "근저당권설정 비용내역", ln=True, align="C"); self.ln(2)
            self.set_font(self.font_family, '', 9)
            self.cell(0, 5, f"작성일: {data['date_input']}", ln=True, align="R"); self.ln(2)
            self.set_font(self.font_family, '', 10)
            client = data['client']
            self.cell(95, self.line_height, f"채권최고액: {client['채권최고액']} 원")
            self.cell(0, self.line_height, f"|  필지수: {client['필지수']}", ln=True)
            if client.get('금융사'): self.cell(0, self.line_height, f"금  융  사: {client['금융사']}", ln=1)
            if client.get('채무자'): self.cell(0, self.line_height, f"채  무  자: {client['채무자']}", ln=1)
            if client.get('물건지'): self.multi_cell(0, self.line_height, f"물  건  지: {client['물건지']}")
            self.ln(3)
            if self.show_fee:
                def fee_content():
                    self.set_font(self.font_family, '', 10); items = data['fee_items']
                    subtotal = items.get('기본료', 0) + items.get('추가보수', 0) + items.get('기타보수', 0)
                    self.set_x(self.l_margin + 5); self.cell(self.col_width1, self.line_height, "보수액 소계"); self.cell(self.col_width2, self.line_height, f"{subtotal:,} 원", ln=1, align="R")
                    self.set_x(self.l_margin + 5); self.cell(self.col_width1, self.line_height, "할인금액"); self.cell(self.col_width2, self.line_height, f"{items.get('할인금액', 0):,} 원", ln=1, align="R")
                    self.ln(1); self.line(self.get_x() + 5, self.get_y(), self.w - self.r_margin - 5, self.get_y()); self.ln(1)
                    self.set_font(self.font_family, 'B', 10); self.set_x(self.l_margin + 5); self.cell(self.col_width1, self.line_height, "보수 소계"); self.cell(self.col_width2, self.line_height, f"{data['fee_totals']['보수총액']:,} 원", ln=1, align="R")
                self.draw_labelframe_box("1. 보수액", fee_content); self.ln(5)
            def costs_content():
                self.set_font(self.font_family, '', 10); items = data['cost_items']
                for name, val in items.items():
                    if val != 0: self.set_x(self.l_margin + 5); self.cell(self.col_width1, self.line_height, name); self.cell(self.col_width2, self.line_height, f"{int(val):,} 원", ln=1, align="R")
                self.ln(1); self.line(self.get_x() + 5, self.get_y(), self.w - self.r_margin - 5, self.get_y()); self.ln(1)
                self.set_font(self.font_family, 'B', 10); self.set_x(self.l_margin + 5); self.cell(self.col_width1, self.line_height, "공과금소계"); self.cell(self.col_width2, self.line_height, f"{data['cost_totals']['공과금 총액']:,} 원", ln=1, align="R")
            self.draw_labelframe_box(data['cost_section_title'], costs_content); self.ln(5)
            self.ln(3)  # 등기비용 합계를 더 아래로 이동
            self.set_font(self.font_family, 'B', 12); self.cell(self.col_width1 - 10, 10, "등기비용 합계"); self.cell(self.col_width2 + 10, 10, f"{data['grand_total']:,} 원", ln=True, align="R"); self.ln(5)
            def notes_content():
                self.set_font(self.font_family, '', 10); self.set_x(self.l_margin + 5); self.cell(0, self.line_height, "• 원활한 확인을 위해 입금자는 소유자명(또는 채무자명)으로 기재해 주세요.", ln=1)
                self.set_x(self.l_margin + 5); self.cell(0, self.line_height, "• 입금 완료 후, 메시지를 남겨주시면 더욱 빠르게 처리됩니다.", ln=1)
                self.set_x(self.l_margin + 5); self.cell(0, self.line_height, "• 업무는 입금이 확인된 후에 진행됩니다.", ln=1)
            self.draw_labelframe_box("안내사항", notes_content); self.ln(5)
            def bank_content():
                self.set_font(self.font_family, '', 10)
                self.set_x(self.l_margin + 5)
                self.cell(0, self.line_height, "• 신한은행 100-035-852291", ln=1)
                self.set_x(self.l_margin + 5)
                self.cell(0, self.line_height, "• 예금주 : 법무법인 시화", ln=1)
            self.draw_labelframe_box("입금 계좌 정보", bank_content)
            pdf_buffer = BytesIO(); pdf_bytes = self.output(dest='S')
            if isinstance(pdf_bytes, str): pdf_buffer.write(pdf_bytes.encode('latin-1'))
            else: pdf_buffer.write(pdf_bytes)
            pdf_buffer.seek(0); return pdf_buffer
else: PDFConverter = None

def draw_fit_text(canvas_obj, text, x, y, max_width, font_name, font_size):
    """긴 텍스트를 max_width에 맞춰 여러 줄로 나눠 그리기"""
    if not text:
        return
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if canvas_obj.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    for i, line in enumerate(lines):
        canvas_obj.drawString(x, y - (i * (font_size + 2)), line)

def create_overlay_pdf(data, font_path):
    packet = BytesIO(); c = canvas.Canvas(packet, pagesize=A4); width, height = A4
    try: pdfmetrics.registerFont(TTFont('Korean', font_path)); font_name = 'Korean'
    except: font_name = 'Helvetica'
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
    output_buffer = BytesIO() 
    for page_num in range(min(len(template_pdf.pages), len(overlay_pdf.pages))):
        template_page = template_pdf.pages[page_num]; overlay_page = overlay_pdf.pages[page_num]
        template_page.merge_page(overlay_page); writer.add_page(template_page)
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer

def make_signature_pdf(template_path, data):
    packet = BytesIO(); c = canvas.Canvas(packet, pagesize=A4); width, height = A4
    try: pdfmetrics.registerFont(TTFont('Korean', FONT_PATH)); font_name = 'Korean'
    except: font_name = 'Helvetica'
    c.setFont(font_name, 10); estate_x = 150; estate_y = height - 170; line_h = 14
    if data.get("estate_text"):
        for i, line in enumerate(str(data["estate_text"]).split("\n")[:17]):
            c.drawString(estate_x, estate_y - (i * line_h), line)
    if data.get("debtor_name"): c.drawString(250, 322, str(data["debtor_name"]))
    if data.get("debtor_rrn"): c.drawString(250, 298, str(data["debtor_rrn"]))
    if data.get("owner_name"): c.drawString(400, 322, str(data["owner_name"]))
    if data.get("owner_rrn"): c.drawString(400, 298, str(data["owner_rrn"]))
    if data.get("date"):
        c.setFont(font_name, 11); text = str(data["date"]); tw = c.stringWidth(text, font_name, 11)
        c.drawString((width - tw) / 2, 150, text)
    c.showPage(); c.save(); packet.seek(0)
    overlay_pdf = PdfReader(packet); template_pdf = PdfReader(template_path); writer = PdfWriter()
    output_buffer = BytesIO()
    template_page = template_pdf.pages[0]; overlay_page = overlay_pdf.pages[0]
    template_page.merge_page(overlay_page); writer.add_page(template_page)
    writer.write(output_buffer); output_buffer.seek(0)
    return output_buffer

# =============================================================================
# 말소 문서 PDF 생성 함수들
# =============================================================================

def make_malso_signature_pdf(template_path, data):
    """말소용 자필서명정보 PDF 생성 (탭2와 유사)"""
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    
    try:
        pdfmetrics.registerFont(TTFont('Korean', FONT_PATH))
        font_name = 'Korean'
    except:
        font_name = 'Helvetica'
    
    c.setFont(font_name, 10)
    
    # 부동산 표시
    estate_x = 150
    estate_y = height - 170
    line_h = 14
    estate_list = data.get('estate_list', [])
    for i, line in enumerate(estate_list[:17]):
        if line.strip():
            c.drawString(estate_x, estate_y - (i * line_h), line)
    
    # 권리자 정보 (최대 2명)
    holders = data.get('holders', [])
    if len(holders) >= 1:
        c.drawString(250, 322, str(holders[0].get('name', '')))
        c.drawString(250, 298, str(holders[0].get('rrn', '')))
    if len(holders) >= 2:
        c.drawString(400, 322, str(holders[1].get('name', '')))
        c.drawString(400, 298, str(holders[1].get('rrn', '')))
    
    # 날짜 (중앙)
    if data.get("date"):
        c.setFont(font_name, 11)
        text = str(data["date"])
        tw = c.stringWidth(text, font_name, 11)
        c.drawString((width - tw) / 2, 150, text)
    
    c.showPage()
    c.save()
    packet.seek(0)
    
    # 템플릿과 병합
    overlay_pdf = PdfReader(packet)
    template_pdf = PdfReader(template_path)
    writer = PdfWriter()
    output_buffer = BytesIO()
    
    template_page = template_pdf.pages[0]
    overlay_page = overlay_pdf.pages[0]
    template_page.merge_page(overlay_page)
    writer.add_page(template_page)
    
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer

def make_malso_power_pdf(template_path, data):
    """위임장 PDF 생성 (템플릿 오버레이)"""
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    
    try:
        pdfmetrics.registerFont(TTFont('Korean', FONT_PATH))
        font_name = 'Korean'
    except:
        font_name = 'Helvetica'
    
    # 위임장 좌표 (분석 결과 기반)
    # 부동산 표시: (102.9, 93.1) ~ (529.7, 344.6), RL Y: 497.4 ~ 748.9
    # 등기원인/목적: X=172.0, RL Y: 450~491
    # 말소할 사항: (172.0, 397.1) ~ (530.3, 455.4), RL Y: 386.6 ~ 444.9
    # 의무자/권리자: (65.1, 590.3) ~ (415.4, 778.9), RL Y: 63.1 ~ 251.7
    
    c.setFont(font_name, 9)
    
    # 부동산 표시 (Box 1)
    estate_x = 105
    estate_y = 745
    line_h = 12
    estate_lines = data.get('estate_text', '').split('\n')
    for i, line in enumerate(estate_lines[:20]):
        if line.strip():
            c.drawString(estate_x, estate_y - (i * line_h), line)
    
    # 등기원인과 그 년월일 (Box 2) - 상하 중앙정렬, RL Y: 470.6 ~ 491.1, 중앙 480.85
    cause_date = data.get('date', '')
    c.drawString(175, 478, f"{cause_date} 해지")
    
    # 등기목적 (Box 3) - 상하 중앙정렬, RL Y: 450.6 ~ 471.1, 중앙 460.85
    malso_type = data.get('malso_type', '근저당권')
    c.drawString(175, 458, f"{malso_type}말소")
    
    # 말소할 사항 (Box 4) - 상하 중앙정렬, RL Y: 386.6 ~ 444.9, 중앙 415.75
    cancel_text = data.get('cancel_text', '')
    c.setFont(font_name, 8)
    # 긴 텍스트 줄바꿈 처리 (폭 넓힘)
    if len(cancel_text) > 75:
        c.drawString(175, 422, cancel_text[:75])
        c.drawString(175, 410, cancel_text[75:])
    else:
        c.drawString(175, 416, cancel_text)
    
    c.setFont(font_name, 9)
    
    # 의무자 (소유자) - 왼쪽 상단 (Box 5 영역), RL Y: 63.1 ~ 251.7
    holder1_name = data.get('holder1_name', '')
    holder1_addr = data.get('holder1_addr', '')
    holder2_name = data.get('holder2_name', '')
    holder2_addr = data.get('holder2_addr', '')
    
    # 등기의무자 라벨
    c.setFont(font_name, 8)
    c.drawString(70, 248, "등기의무자")
    c.setFont(font_name, 9)
    
    # 의무자 내용
    c.drawString(70, 232, holder1_name)
    # 주소 (여러 줄 처리)
    addr_lines = holder1_addr.split('\n') if holder1_addr else []
    for i, line in enumerate(addr_lines[:2]):
        c.drawString(70, 217 - (i * 12), line)
    
    if holder2_name:
        c.drawString(70, 180, holder2_name)
        addr2_lines = holder2_addr.split('\n') if holder2_addr else []
        for i, line in enumerate(addr2_lines[:2]):
            c.drawString(70, 165 - (i * 12), line)
    
    # 권리자 (채권자) - 하단
    obligor_name = data.get('obligor_name', '')
    obligor_id = data.get('obligor_id', '')
    obligor_addr = data.get('obligor_addr', '')
    obligor_rep = data.get('obligor_rep', '')
    
    # 등기권리자 라벨
    c.setFont(font_name, 8)
    c.drawString(70, 118, "등기권리자")
    c.setFont(font_name, 9)
    
    # 법인 형식: 주식회사티플레인대부(110111-7350161)
    if obligor_id:
        obligor_display = f"{obligor_name}({obligor_id})"
    else:
        obligor_display = obligor_name
    
    c.drawString(70, 102, obligor_display)
    c.drawString(70, 87, obligor_addr)
    if obligor_rep:
        c.drawString(70, 72, f"(대표이사){obligor_rep}")
    
    c.showPage()
    c.save()
    packet.seek(0)
    
    # 템플릿과 병합 (1페이지만)
    overlay_pdf = PdfReader(packet)
    template_pdf = PdfReader(template_path)
    writer = PdfWriter()
    output_buffer = BytesIO()
    
    template_page = template_pdf.pages[0]
    overlay_page = overlay_pdf.pages[0]
    template_page.merge_page(overlay_page)
    writer.add_page(template_page)
    
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer

def make_malso_termination_pdf(data):
    """해지증서 PDF 생성 (백지에서 생성)"""
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    
    try:
        pdfmetrics.registerFont(TTFont('Korean', FONT_PATH))
        font_name = 'Korean'
    except:
        font_name = 'Helvetica'
    
    # 페이지 설정: 좌측 X=50, 우측 X=545 (여백 줄임)
    left_x = 50
    right_x = 545
    center_x = (left_x + right_x) / 2
    content_width = right_x - left_x
    
    # 제목: 해 지 증 서 (중앙, 상단)
    c.setFont(font_name, 18)
    title = "해 지 증 서"
    title_width = c.stringWidth(title, font_name, 18)
    c.drawString(center_x - title_width/2, 750, title)
    
    # 부제목: (부동산의표시) (중앙, 2줄)
    c.setFont(font_name, 11)
    subtitle = "(부동산의표시)"
    subtitle_width = c.stringWidth(subtitle, font_name, 11)
    c.drawString(center_x - subtitle_width/2, 720, subtitle)
    
    # 부동산 표시 내용
    c.setFont(font_name, 10)
    estate_text = data.get('estate_text', '')
    estate_lines = estate_text.split('\n')
    estate_y = 695
    line_h = 13
    for i, line in enumerate(estate_lines[:22]):
        if line.strip():
            c.drawString(left_x, estate_y - (i * line_h), line)
    
    # 내용 영역
    c.setFont(font_name, 10)
    cancel_text = data.get('cancel_text', '')
    content_y = 395
    
    # 전체 내용 한 문장으로 구성
    full_content = f"위 부동산에 관하여 {cancel_text} (을)를 해지한다."
    
    # 폭 기반 줄바꿈 (약 90자 또는 폭 495pt 기준)
    max_chars = 90
    if len(full_content) > max_chars:
        # 첫 줄
        c.drawString(left_x, content_y, full_content[:max_chars])
        # 두번째 줄
        c.drawString(left_x, content_y - 16, full_content[max_chars:])
    else:
        c.drawString(left_x, content_y, full_content)
    
    # 작성일자 (중앙)
    date_text = data.get('date', '')
    c.setFont(font_name, 11)
    date_width = c.stringWidth(date_text, font_name, 11)
    c.drawString(center_x - date_width/2, 320, date_text)
    
    # 의무자 영역 - 중앙정렬, 라벨 좌측
    obligor_label = data.get('obligor_label', '근저당권자')
    obligor_name = data.get('obligor_name', '')
    obligor_id = data.get('obligor_id', '')
    obligor_addr = data.get('obligor_addr', '')
    obligor_rep = data.get('obligor_rep', '')
    
    # 라벨 (좌측)
    c.setFont(font_name, 10)
    c.drawString(left_x, 280, obligor_label)
    
    # 내용 (중앙)
    c.setFont(font_name, 10)
    if obligor_id:
        obligor_display = f"{obligor_name}({obligor_id})"
    else:
        obligor_display = obligor_name
    
    text_width = c.stringWidth(obligor_display, font_name, 10)
    c.drawString(center_x - text_width/2, 260, obligor_display)
    
    c.setFont(font_name, 9)
    addr_width = c.stringWidth(obligor_addr, font_name, 9)
    c.drawString(center_x - addr_width/2, 245, obligor_addr)
    
    if obligor_rep:
        rep_text = f"(대표이사){obligor_rep}"
        rep_width = c.stringWidth(rep_text, font_name, 10)
        c.setFont(font_name, 10)
        c.drawString(center_x - rep_width/2, 225, rep_text)
    
    # 권리자 (우측정렬)
    holder1_name = data.get('holder1_name', '')
    holder2_name = data.get('holder2_name', '')
    
    c.setFont(font_name, 10)
    if holder2_name:
        holder_text = f"{holder1_name},{holder2_name} 귀하"
    else:
        holder_text = f"{holder1_name} 귀하"
    
    holder_width = c.stringWidth(holder_text, font_name, 10)
    c.drawString(right_x - holder_width, 160, holder_text)
    
    c.showPage()
    c.save()
    packet.seek(0)
    return packet

def make_malso_transfer_pdf(data):
    """이관증명서 PDF 생성 (백지에서 생성)"""
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    
    try:
        pdfmetrics.registerFont(TTFont('Korean', FONT_PATH))
        font_name = 'Korean'
    except:
        font_name = 'Helvetica'
    
    # 페이지 설정: 좌측 X=50, 우측 X=545 (여백 줄임)
    left_x = 50
    right_x = 545
    center_x = (left_x + right_x) / 2
    
    # 제목: 이 관 증 명 서 (중앙)
    c.setFont(font_name, 18)
    title = "이 관 증 명 서"
    title_width = c.stringWidth(title, font_name, 18)
    c.drawString(center_x - title_width/2, 750, title)
    
    # 부제목
    c.setFont(font_name, 11)
    subtitle = "(부동산의표시)"
    subtitle_width = c.stringWidth(subtitle, font_name, 11)
    c.drawString(center_x - subtitle_width/2, 720, subtitle)
    
    # 부동산 표시
    c.setFont(font_name, 10)
    estate_text = data.get('estate_text', '')
    estate_lines = estate_text.split('\n')
    estate_y = 695
    line_h = 13
    for i, line in enumerate(estate_lines[:22]):
        if line.strip():
            c.drawString(left_x, estate_y - (i * line_h), line)
    
    # 내용
    c.setFont(font_name, 10)
    cancel_text = data.get('cancel_text', '')
    from_branch = data.get('from_branch', '')
    to_branch = data.get('to_branch', '')
    
    content_y = 395
    
    # 전체 내용
    full_content1 = f"위 부동산에 관하여 {cancel_text}"
    full_content2 = f"업무일체가 {from_branch}에서 {to_branch}(으)로 이관되었음을 확인합니다."
    
    # 폭 기반 줄바꿈 (약 90자 기준)
    max_chars = 90
    if len(full_content1) > max_chars:
        c.drawString(left_x, content_y, full_content1[:max_chars])
        c.drawString(left_x, content_y - 16, full_content1[max_chars:])
        c.drawString(left_x, content_y - 32, full_content2)
    else:
        c.drawString(left_x, content_y, full_content1)
        c.drawString(left_x, content_y - 16, full_content2)
    
    # 작성일자 (중앙)
    date_text = data.get('date', '')
    c.setFont(font_name, 11)
    date_width = c.stringWidth(date_text, font_name, 11)
    c.drawString(center_x - date_width/2, 320, date_text)
    
    # 의무자 (중앙, 라벨 좌측)
    obligor_label = data.get('obligor_label', '근저당권자')
    obligor_name = data.get('obligor_name', '')
    obligor_id = data.get('obligor_id', '')
    obligor_addr = data.get('obligor_addr', '')
    obligor_rep = data.get('obligor_rep', '')
    
    c.setFont(font_name, 10)
    c.drawString(left_x, 280, obligor_label)
    
    if obligor_id:
        obligor_display = f"{obligor_name}({obligor_id})"
    else:
        obligor_display = obligor_name
    
    text_width = c.stringWidth(obligor_display, font_name, 10)
    c.drawString(center_x - text_width/2, 260, obligor_display)
    
    c.setFont(font_name, 9)
    addr_width = c.stringWidth(obligor_addr, font_name, 9)
    c.drawString(center_x - addr_width/2, 245, obligor_addr)
    
    if obligor_rep:
        rep_text = f"(대표이사){obligor_rep}"
        rep_width = c.stringWidth(rep_text, font_name, 10)
        c.setFont(font_name, 10)
        c.drawString(center_x - rep_width/2, 225, rep_text)
    
    c.showPage()
    c.save()
    packet.seek(0)
    return packet

# =============================================================================
# 5. Streamlit UI 및 상태 관리
# =============================================================================

# 상태 변수 초기화
keys_to_init = [
    'add_fee_val', 'etc_fee_val', 'disc_fee_val', 
    'cost_manual_제증명', 'cost_manual_교통비', 'cost_manual_원인증서', 
    'cost_manual_주소변경', 'cost_manual_확인서면', 'cost_manual_선순위 말소'
]
for k in keys_to_init:
    if k not in st.session_state: st.session_state[k] = "0"

if 'use_address_change' not in st.session_state: st.session_state['use_address_change'] = False
if 'address_change_count' not in st.session_state: st.session_state['address_change_count'] = 1

if 'calc_data' not in st.session_state:
    st.session_state['calc_data'] = {}
    st.session_state['show_fee'] = True
    st.session_state['input_amount'] = ""
    st.session_state['amount_raw_input'] = ""
    st.session_state['input_parcels'] = 1
    st.session_state['input_rate'] = f"{get_rate()*100:.5f}"
    st.session_state['input_debtor'] = "" # Tab 1과 동기화 위해 존재하지만 초기값은 빈값
    st.session_state['input_creditor'] = list(CREDITORS.keys())[0]
    st.session_state['input_creditor_name'] = ""
    st.session_state['input_creditor_corp_num'] = ""
    st.session_state['input_creditor_addr'] = ""
    st.session_state['input_collateral_addr'] = ""
    st.session_state['input_debtor_addr'] = ""
    st.session_state['input_owner'] = ""
    st.session_state['input_owner_addr'] = ""
    st.session_state['guarantee'] = "한정근담보"
    st.session_state['contract_type'] = "개인"
    st.session_state['input_date'] = datetime.now().date()
    st.session_state['estate_text'] = """[토지]\n서울특별시 강남구 대치동 123번지\n대 300㎡\n\n[건물]\n서울특별시 강남구 대치동 123번지\n철근콘크리트조 슬래브지붕 5층 주택\n1층 100㎡\n2층 100㎡"""
    st.session_state['input_debtor_rrn'] = ""
    st.session_state['input_owner_rrn'] = ""

# 3탭 수기 입력값 초기 상태 (금융사 기본값 로드)
manual_keys = ["cost_manual_제증명", "cost_manual_교통비", "cost_manual_원인증서", "cost_manual_확인서면", "cost_manual_선순위 말소"]
for key in manual_keys:
    if key not in st.session_state:
        # 이미 0으로 초기화했지만 금융사 변경 시 값 덮어쓰기 위해 여기서 체크
        pass # 아래 handle_creditor_change 등에서 처리

def parse_int_input(text_input):
    try:
        if isinstance(text_input, int): return text_input
        return int(remove_commas(text_input or "0"))
    except ValueError: return 0

def handle_creditor_change():
    creditor_key = st.session_state.get('t1_creditor_select', list(CREDITORS.keys())[0])
    if creditor_key == "🖊️ 직접입력":
        # 수기입력 항목들 0으로 초기화
        for k in manual_keys: st.session_state[k] = "0"
        st.session_state['cost_manual_주소변경'] = "0"
        st.session_state['input_creditor_name'] = ""
        st.session_state['input_creditor_corp_num'] = ""
        st.session_state['input_creditor_addr'] = ""
    else:
        # 유노스프레스티지일 경우만 제증명 20,000원, 나머지는 모두 0원
        if "유노스프레스티지" in creditor_key:
            st.session_state['cost_manual_제증명'] = format_number_with_comma("20000")
            st.session_state['cost_manual_교통비'] = "0"
            st.session_state['cost_manual_원인증서'] = "0"
            st.session_state['cost_manual_확인서면'] = "0"
            st.session_state['cost_manual_선순위 말소'] = "0"
        else:
            # 유노스프레스티지가 아닌 경우 모두 0원
            st.session_state['cost_manual_제증명'] = "0"
            st.session_state['cost_manual_교통비'] = "0"
            st.session_state['cost_manual_원인증서'] = "0"
            st.session_state['cost_manual_확인서면'] = "0"
            st.session_state['cost_manual_선순위 말소'] = "0"
        st.session_state['cost_manual_주소변경'] = "0" # 주소변경은 체크박스로만 제어
    st.session_state.calc_data['creditor_key_check'] = creditor_key

MANUAL_COST_NAMES = ["제증명", "교통비", "원인증서", "주소변경", "확인서면", "선순위 말소"]

def calculate_all(data):
    amount = parse_int_input(data.get('채권최고액')) 
    parcels = parse_int_input(data.get('필지수'))
    try: rate = float(remove_commas(data.get('채권할인율', '0'))) / 100
    except ValueError: rate = 0 
    
    # 원본 데이터 보존
    data['input_amount'] = data.get('채권최고액', '')
    
    # 기본료
    base_fee = lookup_base_fee(amount)
    data['기본료'] = base_fee
    
    add_fee = parse_int_input(data.get('추가보수_val'))
    etc_fee = parse_int_input(data.get('기타보수_val'))
    disc_fee = parse_int_input(data.get('할인금액'))

    fee_total = 0
    if st.session_state['show_fee']:
        supply_val = base_fee + add_fee + etc_fee - disc_fee
        vat = math.floor(max(0, supply_val) * 0.1)
        fee_total = supply_val + vat
        data['공급가액'] = supply_val
        data['부가세'] = vat
        data['보수총액'] = fee_total
    else:
        data['공급가액'] = 0; data['부가세'] = 0; data['보수총액'] = 0
    
    # 공과금 계산
    # (주소변경 체크 시 비용 계산 로직은 UI 콜백에서 선행 처리됨)
    use_addr_change = st.session_state.get('use_address_change', False)
    addr_count = st.session_state.get('address_change_count', 1)
    
    addr_reg = 0; addr_edu = 0; addr_jeungji = 0
    if use_addr_change and addr_count > 0:
        addr_reg = 6000 * addr_count
        addr_edu = 1200 * addr_count
        addr_jeungji = 3000 * addr_count
    
    basic_reg = floor_10(amount * 0.002)
    basic_edu = floor_10(basic_reg * 0.2)
    final_reg = basic_reg + addr_reg
    final_edu = basic_edu + addr_edu
    jeungji = (18000 * parcels) + addr_jeungji 

    bond = 0
    if amount >= 20_000_000: bond = math.ceil(amount * 0.01 / 10000) * 10000
    bond_disc = floor_10(bond * rate)
    
    data["등록면허세"] = final_reg
    data["지방교육세"] = final_edu
    data["증지대"] = jeungji
    data["채권할인금액"] = bond_disc
    
    cost_total = final_reg + final_edu + jeungji + bond_disc
    for k in MANUAL_COST_NAMES:
        cost_total += parse_int_input(st.session_state.get('cost_manual_' + k, 0))
    
    data['공과금 총액'] = cost_total
    data['총 합계'] = fee_total + cost_total
    return data

def create_receipt_excel(data, template_path=None):
    """영수증 Excel 파일 생성 - 템플릿 기반"""
    if not EXCEL_OK:
        return None
    
    # 템플릿이 있으면 사용, 없으면 새로 생성
    if template_path and os.path.exists(template_path):
        try:
            workbook = openpyxl.load_workbook(template_path)
            ws = workbook.active
            
            # 기본 정보 입력
            client = data.get('client', {})
            
            # 금융사명에서 회사명만 추출 (대표이사/사내이사 앞까지)
            full_creditor = client.get('금융사', '')
            if '대표이사' in full_creditor:
                company_name = full_creditor.split('대표이사')[0].strip()
            elif '사내이사' in full_creditor:
                company_name = full_creditor.split('사내이사')[0].strip()
            else:
                company_name = full_creditor
            
            # ===== 좌측 영수증 =====
            ws['B4'] = company_name                      # 금융사 (회사명만)
            
            # 채권최고액 (숫자만 추출)
            amount_str = client.get('채권최고액', '0')
            amount_val = int(re.sub(r'[^\d]', '', amount_str)) if amount_str else 0
            ws['M5'] = amount_val                        # 좌측 채권최고액
            
            ws['E7'] = client.get('물건지', '')           # 좌측 물건지
            
            # ===== 우측 영수증 =====
            ws['V4'] = client.get('채무자', '')           # 채무자
            ws['AG5'] = amount_val                       # 우측 채권최고액
            ws['Y7'] = client.get('물건지', '')           # 우측 물건지
            
            # ===== 작성일자 (좌/우 둘 다) =====
            date_str = data.get('date_input', '')
            ws['A24'] = date_str                         # 좌측 날짜
            ws['U24'] = date_str                         # 우측 날짜
            
            # ===== 공과금 항목 입력 (웹에서 계산된 값 직접 입력) =====
            cost_items = data.get('cost_items', {})
            
            # AH11~AH18: 고정 항목
            ws['AH11'] = int(cost_items.get('등록면허세', 0))
            ws['AH12'] = int(cost_items.get('지방교육세', 0))
            ws['AH13'] = int(cost_items.get('증지대', 0))          # 등기신청수수료
            ws['AH14'] = int(cost_items.get('채권할인', 0))        # 채권할인액
            ws['AH15'] = int(cost_items.get('제증명', 0))          # 등본/제증명
            ws['AH16'] = int(cost_items.get('원인증서', 0))
            ws['AH17'] = int(cost_items.get('주소변경', 0))
            ws['AH18'] = int(cost_items.get('선순위말소', 0))      # 선순위 말소
            
            # AD19/AH19: 교통비 (값이 있을 때만 라벨+금액 입력)
            traffic_fee = int(cost_items.get('교통비', 0))
            if traffic_fee > 0:
                ws['AD19'] = '교통비'
                ws['AH19'] = traffic_fee
            else:
                ws['AD19'] = None
                ws['AH19'] = None
            
            # AD20/AH20: 확인서면 (값이 있을 때만 라벨+금액 입력)
            confirm_fee = int(cost_items.get('확인서면', 0))
            if confirm_fee > 0:
                ws['AD20'] = '확인서면'
                ws['AH20'] = confirm_fee
            else:
                ws['AD20'] = None
                ws['AH20'] = None
            
            # ===== 소계/총계 (웹에서 계산된 값 직접 입력) =====
            cost_total = int(data.get('cost_totals', {}).get('공과금 총액', 0))
            ws['AH21'] = cost_total                      # 우측 공과금 소계
            ws['Y22'] = cost_total                       # 우측 총계
            
        except Exception as e:
            # 템플릿 사용 실패 시 새로 생성
            workbook = openpyxl.Workbook()
            ws = workbook.active
            ws.title = "영수증"
            _create_simple_receipt(ws, data)
    else:
        # 템플릿 없이 새로 생성
        workbook = openpyxl.Workbook()
        ws = workbook.active
        ws.title = "영수증"
        _create_simple_receipt(ws, data)
    
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output

def _create_simple_receipt(sheet, data):
    """간단한 영수증 시트 생성"""
    from openpyxl.styles import Font, Alignment, Border, Side
    
    # 제목
    sheet['A1'] = '근저당권설정 영수증'
    sheet['A1'].font = Font(size=16, bold=True)
    sheet['A1'].alignment = Alignment(horizontal='center')
    sheet.merge_cells('A1:C1')
    
    # 날짜
    sheet['A3'] = '작성일:'
    sheet['B3'] = data.get('date_input', '')
    
    # 고객 정보
    client = data.get('client', {})
    sheet['A5'] = '채무자:'
    sheet['B5'] = client.get('채무자', '')
    sheet['A6'] = '물건지:'
    sheet['B6'] = client.get('물건지', '')
    sheet['A7'] = '채권최고액:'
    sheet['B7'] = client.get('채권최고액', '')
    
    # 비용 항목
    row = 9
    sheet[f'A{row}'] = '항목'
    sheet[f'B{row}'] = '금액'
    sheet[f'A{row}'].font = Font(bold=True)
    sheet[f'B{row}'].font = Font(bold=True)
    
    row += 1
    cost_items = data.get('cost_items', {})
    for name, value in cost_items.items():
        if value != 0:
            sheet[f'A{row}'] = name
            sheet[f'B{row}'] = f"{int(value):,} 원"
            row += 1
    
    # 합계
    row += 1
    sheet[f'A{row}'] = '총 합계'
    sheet[f'B{row}'] = f"{data.get('grand_total', 0):,} 원"
    sheet[f'A{row}'].font = Font(bold=True, size=12)
    sheet[f'B{row}'].font = Font(bold=True, size=12)
    
    # 열 너비 조정
    sheet.column_dimensions['A'].width = 20
    sheet.column_dimensions['B'].width = 30
    sheet.column_dimensions['C'].width = 15


# =============================================================================
# UI 구현
# =============================================================================

tab1, tab2, tab3, tab4 = st.tabs(["📄 근저당권설정 계약서", "✍️ 자필서명정보", "🧾 비용 계산 및 영수증", "🗑️ 말소 문서"])

# Tab 1: 근저당권 설정 (입력)
with tab1:
    col_header = st.columns([6, 1])
    col_header[0].markdown("### 📝 근저당권설정 계약서 작성")
    with col_header[1]:
        if st.button("🔄 초기화", type="secondary", key="reset_tab1", use_container_width=True, help="모든 입력 초기화"):
            st.session_state['input_date'] = datetime.now().date()
            st.session_state['t1_debtor_name'] = "" # 키 초기화
            st.session_state['t1_debtor_addr'] = ""
            st.session_state['t1_debtor_rrn'] = ""
            st.session_state['t1_owner_name'] = ""
            st.session_state['t1_owner_addr'] = ""
            st.session_state['t1_owner_rrn'] = ""
            st.session_state['contract_type'] = "개인"
            st.session_state['guarantee'] = "한정근담보"
            st.session_state['amount_raw_input'] = ""
            st.session_state['input_amount'] = ""
            st.session_state['input_collateral_addr'] = ""
            st.session_state['collateral_addr_input'] = ""
            st.session_state['estate_text'] = """[토지]\n서울특별시 강남구 대치동 123번지\n대 300㎡\n\n[건물]\n서울특별시 강남구 대치동 123번지\n철근콘크리트조 슬래브지붕 5층 주택\n1층 100㎡\n2층 100㎡"""
            st.session_state['input_debtor_rrn'] = ""
            st.session_state['input_owner_rrn'] = ""
            st.rerun()
    st.markdown("---")
    
    with st.expander("📌 기본 정보", expanded=True):
        current_date = st.session_state.get('input_date')
        if not isinstance(current_date, date): current_date = datetime.now().date()
        st.session_state['input_date'] = st.date_input("작성일자", value=current_date, key='date_picker')

    with st.expander("👤 당사자 정보", expanded=True):
        creditor_list = list(CREDITORS.keys()) + ["🖊️ 직접입력"]
        current_creditor = st.session_state.get('input_creditor', creditor_list[0])
        default_index = creditor_list.index(current_creditor) if current_creditor in creditor_list else 0
        selected_creditor = st.selectbox("채권자 선택", options=creditor_list, index=default_index, key='t1_creditor_select', on_change=handle_creditor_change)
        st.session_state['input_creditor'] = selected_creditor
        
        if selected_creditor == "🖊️ 직접입력":
            st.session_state['input_creditor_name'] = st.text_input("채권자 성명/상호", value=st.session_state.get('input_creditor_name', ''), key='direct_creditor_name')
            st.session_state['input_creditor_corp_num'] = st.text_input("법인번호", value=st.session_state.get('input_creditor_corp_num', ''), key='direct_corp_num')
            st.session_state['input_creditor_addr'] = st.text_area("채권자 주소", value=st.session_state.get('input_creditor_addr', ''), key='direct_creditor_addr', height=100)
        else:
            creditor_info = CREDITORS.get(selected_creditor, {})
            st.text_input("법인번호", value=creditor_info.get('corp_num', ''), disabled=False)
            st.text_area("채권자 주소", value=creditor_info.get('addr', ''), disabled=False)
            st.session_state['input_creditor_name'] = selected_creditor
            st.session_state['input_creditor_corp_num'] = creditor_info.get('corp_num', '')
            st.session_state['input_creditor_addr'] = creditor_info.get('addr', '')

        # 주민번호 자동 하이픈 삽입 함수
        def auto_format_rrn_input(key):
            """6자리 입력 시 자동으로 '-' 삽입"""
            if key in st.session_state:
                val = st.session_state[key]
                # 숫자만 추출
                clean_val = re.sub(r'[^0-9]', '', str(val))
                # 6자리 이상이면 하이픈 삽입
                if len(clean_val) >= 6 and '-' not in val:
                    st.session_state[key] = f"{clean_val[:6]}-{clean_val[6:13]}"
                elif len(clean_val) > 13:
                    st.session_state[key] = f"{clean_val[:6]}-{clean_val[6:13]}"
        
        # 채무자 정보
        st.markdown("**채무자**")
        debtor_col1, debtor_col2 = st.columns([2, 1])
        with debtor_col1:
            st.text_input("채무자 성명", value=st.session_state.get('t1_debtor_name', ''), key='t1_debtor_name')
        with debtor_col2:
            st.text_input("주민등록번호", value=st.session_state.get('t1_debtor_rrn', ''), key='t1_debtor_rrn', placeholder="000000-0000000", on_change=auto_format_rrn_input, args=('t1_debtor_rrn',))
        st.text_area("채무자 주소", value=st.session_state.get('t1_debtor_addr', ''), key='t1_debtor_addr', height=100)
        
        # 설정자(소유자) 정보
        st.markdown("**설정자(소유자)**")
        owner_col1, owner_col2 = st.columns([2, 1])
        with owner_col1:
            st.text_input("설정자 성명", value=st.session_state.get('t1_owner_name', ''), key='t1_owner_name')
        with owner_col2:
            st.text_input("주민등록번호", value=st.session_state.get('t1_owner_rrn', ''), key='t1_owner_rrn', placeholder="000000-0000000", on_change=auto_format_rrn_input, args=('t1_owner_rrn',))
        st.text_area("설정자 주소", value=st.session_state.get('t1_owner_addr', ''), key='t1_owner_addr', height=100)

    with st.expander("🤝 담보 및 계약 정보", expanded=True):
        st.session_state['contract_type'] = st.radio("계약서 유형", options=["개인", "3자담보", "공동담보"], horizontal=True, key='contract_type_radio')
        
        # 피담보채무 버튼 선택
        st.write("**피담보채무**")
        col_guarantee1, col_guarantee2 = st.columns(2)
        if 'guarantee' not in st.session_state:
            st.session_state['guarantee'] = "한정근담보"
        
        with col_guarantee1:
            if st.button("한정근담보", type="primary" if st.session_state['guarantee']=="한정근담보" else "secondary", use_container_width=True, key="btn_guarantee_1"):
                st.session_state['guarantee'] = "한정근담보"
                st.rerun()
        with col_guarantee2:
            if st.button("포괄근담보", type="primary" if st.session_state['guarantee']=="포괄근담보" else "secondary", use_container_width=True, key="btn_guarantee_2"):
                st.session_state['guarantee'] = "포괄근담보"
                st.rerun()
        
        def format_amount_on_change():
            raw_val = st.session_state.get('amount_raw_input', '')
            formatted = format_number_with_comma(raw_val)
            st.session_state['input_amount'] = formatted # 3탭에서 이 변수를 참조함
            st.session_state['amount_raw_input'] = formatted
        
        st.text_input("채권최고액", key='amount_raw_input', on_change=format_amount_on_change, placeholder="숫자만 입력")
        if st.session_state.get('input_amount') and st.session_state['input_amount'] != "0":
            st.info(f"💰 **{number_to_korean(remove_commas(st.session_state['input_amount']))}**")
        
        col_addr1, col_addr2 = st.columns([5, 1])
        def copy_debtor_address():
            if st.session_state.get('t1_debtor_addr'):
                st.session_state['collateral_addr_input'] = st.session_state['t1_debtor_addr']
                st.session_state['input_collateral_addr'] = st.session_state['t1_debtor_addr']
        with col_addr1:
            st.text_area("물건지 주소 (수기 입력)", key='collateral_addr_input', height=100)
            if 'collateral_addr_input' in st.session_state: st.session_state['input_collateral_addr'] = st.session_state['collateral_addr_input']
        with col_addr2:
            st.write(""); st.write("")
            st.button("📋\n채무자\n주소복사", key='copy_debtor_addr_btn', on_click=copy_debtor_address, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🏠 부동산의 표시"); st.caption("※ 등기부등본 내용을 입력하세요")
    col_estate, col_pdf = st.columns([3, 1])
    with col_estate:
        st.session_state['estate_text'] = st.text_area("부동산 표시 내용", value=st.session_state['estate_text'], height=300, key='estate_text_area', label_visibility="collapsed")
    with col_pdf:
        st.markdown("#### 📑 파일 생성")
        selected_template_path = st.session_state['template_status'].get(st.session_state['contract_type'])
        if selected_template_path: st.success(f"✅ 템플릿 준비완료"); is_disabled = False
        else: st.warning(f"⚠️ 템플릿 없음"); is_disabled = True
        
        if st.button("🚀 계약서\nPDF 생성", key="generate_pdf_tab1", disabled=is_disabled or not LIBS_OK, use_container_width=True):
            if not LIBS_OK: st.error("PDF 라이브러리 미설치")
            else:
                creditor_name_for_pdf = st.session_state['input_creditor'] if st.session_state['input_creditor'] != "🖊️ 직접입력" else st.session_state.get('input_creditor_name', '')
                creditor_addr_for_pdf = CREDITORS.get(st.session_state['input_creditor'], {}).get('addr', '') if st.session_state['input_creditor'] != "🖊️ 직접입력" else st.session_state.get('input_creditor_addr', '')
                
                data = {
                    "date": format_date_korean(st.session_state['input_date']), "creditor_name": creditor_name_for_pdf, "creditor_addr": creditor_addr_for_pdf,
                    "debtor_name": st.session_state.get('t1_debtor_name', ''), "debtor_addr": st.session_state.get('t1_debtor_addr', ''),
                    "owner_name": st.session_state.get('t1_owner_name', ''), "owner_addr": st.session_state.get('t1_owner_addr', ''),
                    "guarantee_type": st.session_state['guarantee'], "claim_amount": convert_multiple_amounts_to_korean(remove_commas(st.session_state['input_amount'])),
                    "estate_list": st.session_state['estate_text'].strip().split("\n"), "contract_type": st.session_state['contract_type']
                }
                try:
                    pdf_buffer = make_pdf(selected_template_path, data)
                    st.download_button(label="⬇️ 다운로드", data=pdf_buffer, file_name=f"근저당권설정_{data['debtor_name']}.pdf", mime="application/pdf", use_container_width=True)
                    st.success("✅ PDF 생성완료!")
                except Exception as e: st.error(f"오류: {e}")

# =============================================================================
# Tab 2: 자필서명정보 작성
# =============================================================================
with tab2:
    # [추가됨] 주민/법인번호 자동 포맷팅 함수 (13자리 숫자 입력 시 '-' 자동 삽입)
    def auto_format_rrn(key):
        if key in st.session_state:
            val = st.session_state[key]
            # 숫자만 추출
            clean_val = re.sub(r'[^0-9]', '', str(val))
            # 13자리(법인/주민)인 경우 6-7 포맷 적용
            if len(clean_val) == 13:
                st.session_state[key] = f"{clean_val[:6]}-{clean_val[6:]}"

    # 헤더
    col_header = st.columns([6, 1, 1])
    with col_header[0]:
        st.markdown("### ✍️ 자필서명정보 작성")
    
    # [수정됨] 1탭 가져오기 로직 (위젯 Key 강제 동기화 적용)
    with col_header[1]:
        if st.button("📥 1탭 가져오기", type="primary", use_container_width=True, key="sync_tab2", help="1탭 정보 불러오기"):
            # 1. 1탭 데이터 확보 (위젯 Key 기준)
            contract_type = st.session_state.get('contract_type', '개인')
            debtor_name = st.session_state.get('t1_debtor_name', '')
            owner_name = st.session_state.get('t1_owner_name', '')
            # 1탭 부동산표시 위젯의 값을 가져옵니다
            estate_info = st.session_state.get('estate_text_area', '') 
            
            # 주민번호는 1탭에 입력란이 없으므로, 기존 저장값 사용
            debtor_rrn = st.session_state.get('input_debtor_rrn', '')
            owner_rrn = st.session_state.get('input_owner_rrn', '')
            date_val = st.session_state.get('input_date', datetime.now().date())

            # 2. 계약 유형별 할당 데이터 준비
            o1_name, o1_rrn = "", ""
            o2_name, o2_rrn = "", ""

            if contract_type == "개인":
                # 단독: 채무자만
                o1_name, o1_rrn = debtor_name, debtor_rrn
            elif contract_type == "3자담보":
                # 3자: 소유자만
                o1_name, o1_rrn = owner_name, owner_rrn
            elif contract_type == "공동담보":
                # 공동: 채무자 + 소유자
                o1_name, o1_rrn = debtor_name, debtor_rrn
                o2_name, o2_rrn = owner_name, owner_rrn

            # 3. [핵심] Tab 2 위젯 Key(_input)와 Value 변수를 동시에 업데이트
            
            # 등기의무자 1
            st.session_state['tab2_owner1_name_input'] = o1_name
            st.session_state['tab2_owner1_name'] = o1_name
            
            st.session_state['tab2_owner1_rrn_input'] = o1_rrn
            st.session_state['tab2_owner1_rrn'] = o1_rrn

            # 등기의무자 2
            st.session_state['tab2_owner2_name_input'] = o2_name
            st.session_state['tab2_owner2_name'] = o2_name
            
            st.session_state['tab2_owner2_rrn_input'] = o2_rrn
            st.session_state['tab2_owner2_rrn'] = o2_rrn
            
            # 부동산 표시
            st.session_state['tab2_estate_input'] = estate_info
            st.session_state['tab2_estate'] = estate_info
            
            # 작성일자
            st.session_state['tab2_date_input'] = date_val
            st.session_state['tab2_date'] = date_val
            
            st.success("✅ 1탭 정보를 불러왔습니다!")
            st.rerun()
    
    with col_header[2]:
        if st.button("🔄 초기화", type="secondary", use_container_width=True, key="reset_tab2", help="모든 입력 초기화"):
            st.session_state['tab2_owner1_name'] = ''
            st.session_state['tab2_owner1_rrn'] = ''
            st.session_state['tab2_owner2_name'] = ''
            st.session_state['tab2_owner2_rrn'] = ''
            st.session_state['tab2_estate'] = ''
            st.session_state['tab2_date'] = datetime.now().date()
            st.session_state['tab2_receipt_type'] = '전자신청'
            st.success("✅ 초기화되었습니다!")
            st.rerun()
    
    st.markdown("---")
    
    # 신청서 구분
    st.markdown("#### 📋 신청서 구분")
    if 'tab2_receipt_type' not in st.session_state:
        st.session_state['tab2_receipt_type'] = '전자신청'
    
    col_receipt1, col_receipt2 = st.columns(2)
    with col_receipt1:
        if st.button("전자신청", 
                     type="primary" if st.session_state['tab2_receipt_type']=="전자신청" else "secondary",
                     use_container_width=True,
                     key="btn_receipt_1"):
            st.session_state['tab2_receipt_type'] = "전자신청"
            st.rerun()
    with col_receipt2:
        if st.button("서면신청",
                     type="primary" if st.session_state['tab2_receipt_type']=="서면신청" else "secondary",
                     use_container_width=True,
                     key="btn_receipt_2"):
            st.session_state['tab2_receipt_type'] = "서면신청"
            st.rerun()
    
    # 템플릿 파일 선택
    if st.session_state['tab2_receipt_type'] == "전자신청":
        template_filename = "자필서명정보_템플릿.pdf"
    else:
        template_filename = "자필서명정보_서면_템플릿.pdf"
    
    template_path = resource_path(template_filename)
    
    if os.path.exists(template_path):
        st.success(f"✅ {st.session_state['tab2_receipt_type']} 템플릿 준비완료")
    else:
        st.error(f"⚠️ {template_filename} 파일이 없습니다.")
    
    st.markdown("---")
    
    # 입력 정보
    with st.expander("📝 자필서명정보 입력", expanded=True):
        # 작성일자
        st.markdown("#### 📅 작성일자")
        if 'tab2_date' not in st.session_state:
            st.session_state['tab2_date'] = datetime.now().date()
        tab2_date = st.date_input(
            "작성일자",
            value=st.session_state.get('tab2_date', datetime.now().date()),
            key='tab2_date_input'
        )
        
        st.markdown("---")
        
        # 등기의무자 정보
        st.markdown("#### 👤 등기의무자 정보")
        st.caption("※ 1탭 가져오기: 단독(채무자), 3자(소유자), 공동(채무자+소유자)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**등기의무자 1**")
            tab2_owner1_name = st.text_input(
                "성명(법인명 직함 성명)",
                value=st.session_state.get('tab2_owner1_name', ''),
                key='tab2_owner1_name_input',
                placeholder="주식회사대한민국 대표이사 홍길동"
            )
            
            # [수정] 붉은색 강조 라벨 (마진 조정)
            st.markdown("""
                <div style='color: #FF4B4B; font-weight: 600; font-size: 0.9rem; margin-top: 10px; margin-bottom: 5px;'>
                    ⚠️ 주민(법인)등록번호 <span style='font-size: 0.8rem; opacity: 0.8;'>(수기입력 필수)</span>
                </div>
            """, unsafe_allow_html=True)
            
            # [수정] on_change 추가 (자동 하이픈)
            tab2_owner1_rrn = st.text_input(
                "주민(법인)등록번호_라벨숨김1",
                value=st.session_state.get('tab2_owner1_rrn', ''),
                key='tab2_owner1_rrn_input',
                placeholder="숫자 13자리 입력 후 엔터 (자동 '-' 입력)",
                label_visibility="collapsed",
                on_change=auto_format_rrn,
                args=('tab2_owner1_rrn_input',)
            )
        
        with col2:
            st.markdown("**등기의무자 2** (공동명의인 경우)")
            tab2_owner2_name = st.text_input(
                "성명(법인명 직함 성명)",
                value=st.session_state.get('tab2_owner2_name', ''),
                key='tab2_owner2_name_input',
                placeholder="(선택사항)"
            )
            
            # [수정] 붉은색 강조 라벨 (마진 조정)
            st.markdown("""
                <div style='color: #FF4B4B; font-weight: 600; font-size: 0.9rem; margin-top: 10px; margin-bottom: 5px;'>
                    ⚠️ 주민(법인)등록번호 <span style='font-size: 0.8rem; opacity: 0.8;'>(수기입력 필수)</span>
                </div>
            """, unsafe_allow_html=True)
            
            # [수정] on_change 추가 (자동 하이픈)
            tab2_owner2_rrn = st.text_input(
                "주민(법인)등록번호_라벨숨김2",
                value=st.session_state.get('tab2_owner2_rrn', ''),
                key='tab2_owner2_rrn_input',
                placeholder="(선택사항) 숫자 13자리 입력 후 엔터",
                label_visibility="collapsed",
                on_change=auto_format_rrn,
                args=('tab2_owner2_rrn_input',)
            )
        
        st.markdown("---")
        
        # 부동산 표시
        st.markdown("#### 🏠 부동산의 표시")
        tab2_estate = st.text_area(
            "부동산 표시",
            value=st.session_state.get('tab2_estate', ''),
            height=170,
            key='tab2_estate_input',
            placeholder="[토지]\n서울특별시 강남구 대치동 123번지\n대 300㎡"
        )
    
    st.markdown("---")
    
    # PDF 생성
    st.markdown("#### 📄 PDF 생성")
    
    if st.button("🚀 자필서명정보 PDF 생성", type="primary", use_container_width=True, key="generate_signature_pdf"):
        if not LIBS_OK:
            st.error("PDF 라이브러리가 설치되지 않았습니다.")
        elif not os.path.exists(template_path):
            st.error(f"{template_filename} 파일이 없습니다.")
        else:
            try:
                # 자필서명정보 PDF 데이터 준비
                signature_data = {
                    "date": format_date_korean(tab2_date),
                    "debtor_name": tab2_owner1_name or "[등기의무자1]",
                    "debtor_rrn": tab2_owner1_rrn or "[주민번호1]",
                    "owner_name": tab2_owner2_name or "",
                    "owner_rrn": tab2_owner2_rrn or "",
                    "estate_text": tab2_estate or "[부동산 표시]"
                }
                
                # make_signature_pdf 함수 사용
                pdf_buffer = make_signature_pdf(template_path, signature_data)
                
                st.download_button(
                    label="⬇️ 자필서명정보 다운로드",
                    data=pdf_buffer,
                    file_name=f"자필서명정보_{tab2_owner1_name or '고객'}_{st.session_state['tab2_receipt_type']}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.success("✅ PDF 생성 완료!")
                
            except Exception as e:
                st.error(f"PDF 생성 오류: {e}")
    
    st.info("💡 **사용 방법**: '📥 1탭 가져오기' 버튼을 눌러 계약 유형에 따라 정보를 자동으로 불러올 수 있습니다.")


# Tab 3: 비용 계산 및 영수증 (완전 개편)
with tab3:
    # 헤더: 가져오기 + 초기화 버튼
    col_header3 = st.columns([6, 1, 1])
    with col_header3[0]:
        st.markdown("### 🧾 등기비용 계산기")
    with col_header3[1]:
        if st.button("📥 1탭 가져오기", type="primary", use_container_width=True, key="sync_tab3", help="1탭 정보 불러오기"):
            st.success("✅ 1탭 정보가 동기화되었습니다!")
            st.rerun()
    with col_header3[2]:
        if st.button("🔄 초기화", type="secondary", use_container_width=True, key="reset_tab3", help="모든 입력 초기화"):
            st.session_state['calc_data'] = {}
            st.session_state['show_fee'] = True
            st.session_state['input_parcels'] = 1
            st.session_state['input_rate'] = f"{get_rate()*100:.5f}"
            st.session_state['use_address_change'] = False
            st.session_state['address_change_count'] = 1
            handle_creditor_change()
            st.rerun()
    st.markdown("---")

    # =========================================================
    # [수정됨] 0. 1탭 데이터 강제 동기화 (Source of Truth)
    # =========================================================
    # 3탭이 렌더링될 때마다 1탭 데이터를 무조건 가져옴
    
    # 1탭 데이터 가져오기
    debtor_from_tab1 = st.session_state.get('t1_debtor_name', '')
    creditor_from_tab1 = st.session_state.get('input_creditor', '')
    amount_from_tab1 = st.session_state.get('input_amount', '')
    estate_from_tab1 = st.session_state.get('input_collateral_addr', '')
    
    # 물건지 처리
    if not estate_from_tab1:
        estate_from_tab1 = extract_address_from_estate(st.session_state.get('estate_text') or "")
    
    # 채권최고액 동기화 (무조건)
    st.session_state['calc_amount_input'] = amount_from_tab1
    
    # 채무자 동기화 (무조건 1탭 값으로 덮어쓰기)
    st.session_state['input_debtor'] = debtor_from_tab1
    st.session_state['calc_debtor_view'] = debtor_from_tab1
    st.session_state['tab3_debtor_input'] = debtor_from_tab1
    
    # 채권자 동기화 (무조건 1탭 값으로 덮어쓰기)
    st.session_state['input_creditor'] = creditor_from_tab1
    st.session_state['calc_creditor_view'] = creditor_from_tab1
    st.session_state['tab3_creditor_select'] = creditor_from_tab1
    
    # 물건지 동기화 (무조건 1탭 값으로 덮어쓰기)
    st.session_state['input_collateral_addr'] = estate_from_tab1
    st.session_state['calc_estate_view'] = estate_from_tab1
    st.session_state['tab3_estate_input'] = estate_from_tab1
    
    # =========================================================
    # 1. 통합 기본 정보 섹션
    # =========================================================
    creditor_display = creditor_from_tab1
    if creditor_display == "🖊️ 직접입력": 
        creditor_display = st.session_state.get('input_creditor_name', '직접입력')
    
    estate_display = estate_from_tab1

    row1_c1, row1_c2, row1_c3, row1_c4 = st.columns([2, 0.5, 1, 1.2]) 
    
    with row1_c1:
        def on_tab3_amount_change():
            val = st.session_state.get('calc_amount_input', '')
            formatted = format_number_with_comma(val)
            st.session_state['calc_amount_input'] = formatted
            st.session_state['input_amount'] = formatted
        st.text_input("채권최고액", value=st.session_state.get('calc_amount_input', ''), key='calc_amount_input', on_change=on_tab3_amount_change)

    with row1_c3:
        parcels_val = st.session_state.get('input_parcels', 1)
        new_parcels = st.number_input("필지수", min_value=1, value=int(parcels_val), key='calc_parcels_input')
        st.session_state['input_parcels'] = new_parcels

    with row1_c4:
        col_rate, col_btn = st.columns([2, 0.5])
        rate_val = st.session_state.get('input_rate', '12.00000')
        new_rate = col_rate.text_input("할인율(%)", value=rate_val, key='calc_rate_input')
        if col_btn.button("🔄", help="갱신"):
            st.session_state['input_rate'] = f"{get_rate()*100:.5f}"
            st.rerun()
        st.session_state['input_rate'] = new_rate

    row2_c1, row2_c2 = st.columns([1, 1])
    
    # 금융사 선택 (1탭 값 기준)
    with row2_c1:
        creditor_list = list(CREDITORS.keys()) + ["🖊️ 직접입력"]
        
        # 1탭 값을 우선 사용
        current_creditor = creditor_from_tab1 if creditor_from_tab1 else creditor_list[0]
        if current_creditor not in creditor_list:
            current_creditor = creditor_list[0]
        default_index = creditor_list.index(current_creditor)
        
        def on_tab3_creditor_change():
            selected = st.session_state.get('tab3_creditor_select')
            st.session_state['calc_creditor_view'] = selected
            st.session_state['input_creditor'] = selected
            st.session_state['t1_creditor_select'] = selected  # 이 줄 추가!
            # 금융사 변경 시 수기입력 기본값 적용
            handle_creditor_change()
        
        st.selectbox("금융사", options=creditor_list, index=default_index, key='tab3_creditor_select', on_change=on_tab3_creditor_change)
    
    # 채무자 입력
    with row2_c2:
        def on_tab3_debtor_change():
            st.session_state['input_debtor'] = st.session_state.get('tab3_debtor_input', '')
            st.session_state['calc_debtor_view'] = st.session_state.get('tab3_debtor_input', '')
        
        st.text_input("채무자", key='tab3_debtor_input', on_change=on_tab3_debtor_change)
    
    # 물건지 입력
    def on_tab3_estate_change():
        st.session_state['input_collateral_addr'] = st.session_state.get('tab3_estate_input', '')
        st.session_state['calc_estate_view'] = st.session_state.get('tab3_estate_input', '')
    
    st.text_area("물건지", key='tab3_estate_input', on_change=on_tab3_estate_change, height=80)
    st.markdown("---")

    # =========================================================
    # 2. 계산 로직 수행
    # =========================================================
    # 3탭 위젯 값 사용 (사용자가 수정한 경우 그 값 반영)
    creditor_for_calc = st.session_state.get('tab3_creditor_select', creditor_from_tab1)
    if creditor_for_calc == "🖊️ 직접입력":
        creditor_for_calc = st.session_state.get('input_creditor_name', '직접입력')
    
    calc_input_data = {
        '채권최고액': st.session_state.get('calc_amount_input', amount_from_tab1), 
        '필지수': st.session_state['input_parcels'],
        '채권할인율': st.session_state['input_rate'],
        '금융사': creditor_for_calc,
        '채무자': st.session_state.get('tab3_debtor_input', debtor_from_tab1),
        '물건지': st.session_state.get('tab3_estate_input', estate_from_tab1),
        '추가보수_val': st.session_state.get('add_fee_val', "0"),
        '기타보수_val': st.session_state.get('etc_fee_val', "0"),
        '할인금액': st.session_state.get('disc_fee_val', "0"),
    }
    
    final_data = calculate_all(calc_input_data)
    st.session_state['calc_data'] = final_data 

    # =========================================================
    # 3. 3단 레이아웃 (보수액 / 공과금 / 결제)
    # =========================================================
    
    # [수정] 결과 표시용 함수: disabled=True인 경우 state를 강제 갱신하여 0원 표시 방지
    def make_row(label, value, key, on_change=None, disabled=False):
        c1, c2 = st.columns([1, 1.8])
        with c1: st.markdown(f"<div class='row-label'>{label}</div>", unsafe_allow_html=True)
        with c2:
            formatted_val = str(value)
            
            # disabled(수정불가) 항목은 계산된 값을 강제로 session_state에 주입
            if disabled and key:
                st.session_state[key] = formatted_val
            
            if on_change:
                st.text_input(label, value=formatted_val, key=key, on_change=on_change, args=(key,), label_visibility="collapsed", disabled=disabled)
            else:
                if disabled and key:
                    st.text_input(label, key=key, label_visibility="collapsed", disabled=disabled)
                else:
                    st.text_input(label, value=formatted_val, key=key, label_visibility="collapsed", disabled=disabled)

    def format_cost_input(key):
        val = st.session_state[key]
        st.session_state[key] = format_number_with_comma(val)

    col_income, col_tax, col_payment = st.columns([1, 1, 1])

    # [1] 보수액 (Income)
    with col_income:
        st.markdown("<div class='section-header income-header'>💰 보수액 (Income)</div>", unsafe_allow_html=True)
        with st.container(border=True):
            make_row("기본료", format_number_with_comma(final_data.get('기본료')), "disp_base", disabled=True)
            make_row("추가보수", st.session_state['add_fee_val'], "add_fee_val", format_cost_input)
            make_row("기타보수", st.session_state['etc_fee_val'], "etc_fee_val", format_cost_input)
            make_row("할인금액", st.session_state['disc_fee_val'], "disc_fee_val", format_cost_input)
            st.markdown("---")
            c_label, c_val = st.columns([1, 1])
            c_label.markdown("**공급가액**"); c_val.markdown(f"<div style='text-align:right; color:#28a745; font-weight:bold;'>{format_number_with_comma(final_data.get('공급가액'))} 원</div>", unsafe_allow_html=True)
            c_label.markdown("**부가세**"); c_val.markdown(f"<div style='text-align:right; color:#28a745;'>{format_number_with_comma(final_data.get('부가세'))} 원</div>", unsafe_allow_html=True)
            st.markdown("---")
            c_label.markdown("#### 보수 총액"); c_val.markdown(f"<div style='text-align:right; color:#28a745; font-size:1.2rem; font-weight:bold;'>{format_number_with_comma(final_data.get('보수총액'))} 원</div>", unsafe_allow_html=True)

    # [2] 공과금 (Tax)
    with col_tax:
        st.markdown("<div class='section-header tax-header'>🏛️ 공과금 (Tax)</div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.caption("[자동 계산]")
            
            # 세부내역을 확실하게 표시
            tax_col1, tax_col2 = st.columns([1.5, 1])
            
            # 등록면허세
            with tax_col1:
                st.markdown("<div class='row-label'>등록면허세</div>", unsafe_allow_html=True)
            with tax_col2:
                reg_tax = final_data.get("등록면허세", 0)
                st.markdown(f"<div style='text-align:right; padding:8px;'>{format_number_with_comma(reg_tax)} 원</div>", unsafe_allow_html=True)
            
            # 지방교육세
            tax_col1, tax_col2 = st.columns([1.5, 1])
            with tax_col1:
                st.markdown("<div class='row-label'>지방교육세</div>", unsafe_allow_html=True)
            with tax_col2:
                edu_tax = final_data.get("지방교육세", 0)
                st.markdown(f"<div style='text-align:right; padding:8px;'>{format_number_with_comma(edu_tax)} 원</div>", unsafe_allow_html=True)
            
            # 증지대
            tax_col1, tax_col2 = st.columns([1.5, 1])
            with tax_col1:
                st.markdown("<div class='row-label'>증지대</div>", unsafe_allow_html=True)
            with tax_col2:
                stamp = final_data.get("증지대", 0)
                st.markdown(f"<div style='text-align:right; padding:8px;'>{format_number_with_comma(stamp)} 원</div>", unsafe_allow_html=True)
            
            # 채권할인
            tax_col1, tax_col2 = st.columns([1.5, 1])
            with tax_col1:
                st.markdown("<div class='row-label'>채권할인</div>", unsafe_allow_html=True)
            with tax_col2:
                bond = final_data.get("채권할인금액", 0)
                st.markdown(f"<div style='text-align:right; padding:8px;'>{format_number_with_comma(bond)} 원</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.caption("[수기 입력]")
            
            # 수기 입력 항목들
            make_row("제증명", st.session_state['cost_manual_제증명'], "cost_manual_제증명", format_cost_input)
            make_row("교통비", st.session_state['cost_manual_교통비'], "cost_manual_교통비", format_cost_input)
            make_row("원인증서", st.session_state['cost_manual_원인증서'], "cost_manual_원인증서", format_cost_input)
            make_row("주소변경", st.session_state['cost_manual_주소변경'], "cost_manual_주소변경", disabled=True)
            make_row("확인서면", st.session_state['cost_manual_확인서면'], "cost_manual_확인서면", format_cost_input)
            make_row("선순위말소", st.session_state['cost_manual_선순위 말소'], "cost_manual_선순위 말소", format_cost_input)
            
            st.markdown("---")
            c_label, c_val = st.columns([1, 1])
            c_label.markdown("#### 공과금 소계")
            c_val.markdown(f"<div style='text-align:right; color:#fd7e14; font-size:1.2rem; font-weight:bold;'>{format_number_with_comma(final_data.get('공과금 총액'))} 원</div>", unsafe_allow_html=True)

    # [3] 결제 및 청구
    with col_payment:
        st.markdown("<div class='section-header total-header'>🧾 결제 및 청구</div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### 총 청구금액")
            st.markdown(f"<div class='total-box'><div class='total-amount'>{format_number_with_comma(final_data.get('총 합계'))} 원</div></div>", unsafe_allow_html=True)
            st.markdown("---")
            
            def toggle_show_fee(): st.session_state['show_fee'] = st.session_state['show_fee_checkbox']
            st.checkbox("보수액 포함 표시", value=st.session_state['show_fee'], key='show_fee_checkbox', on_change=toggle_show_fee)
            
            st.markdown("#### ➕ 주소변경 추가")
            st.caption("체크 시 공과금 + 수기비용 자동 합산")
            
            def update_address_cost():
                if st.session_state.get('use_address_change', False):
                    # 3탭 위젯 값 사용
                    cur_creditor = st.session_state.get('tab3_creditor_select', creditor_from_tab1)
                    if cur_creditor == "🖊️ 직접입력": 
                        cur_creditor = st.session_state.get('input_creditor_name', '')
                    count = st.session_state.get('address_change_count', 1)
                    fee = (20000 if ("유노스" in cur_creditor or "드림" in cur_creditor) else 50000) * count
                    st.session_state['cost_manual_주소변경'] = format_number_with_comma(fee)
                else:
                    st.session_state['cost_manual_주소변경'] = "0"

            cp1, cp2 = st.columns([1, 1])
            with cp1: st.checkbox("주소변경 포함", key='use_address_change', on_change=update_address_cost)
            with cp2: st.number_input("인원수", min_value=1, value=1, key='address_change_count', label_visibility="collapsed", on_change=update_address_cost)
            
            st.markdown("---")
            st.info("**ℹ️ 참고 기준 (주소변경비용)**\n* 유노스/드림앤캐쉬: 20,000원/인\n* 기타 금융사: 50,000원/인\n* (체크 시 수기입력란에 자동반영)")


    st.markdown("---")
    d_col1, d_col2 = st.columns(2)
    
    # [1] 비용내역 PDF 다운로드
    with d_col1:
        if st.button("📄 비용내역 PDF 다운로드", disabled=not FPDF_OK, use_container_width=True, key="btn_pdf_download"):
            st.session_state['generate_pdf'] = True
        
        if st.session_state.get('generate_pdf', False):
            if not FPDF_OK:
                st.error("FPDF 라이브러리가 설치되지 않았습니다.")
                st.session_state['generate_pdf'] = False
            else:
                try:
                    # PDF 데이터 준비 (3탭 위젯 값 사용)
                    pdf_creditor = st.session_state.get('tab3_creditor_select', creditor_from_tab1)
                    if pdf_creditor == "🖊️ 직접입력":
                        pdf_creditor = st.session_state.get('input_creditor_name', '직접입력')
                    
                    pdf_data = {
                        'date_input': format_date_korean(st.session_state.get('input_date', datetime.now().date())),
                        'client': {
                            '채권최고액': format_number_with_comma(final_data.get('input_amount', st.session_state.get('input_amount', ''))),
                            '필지수': str(st.session_state.get('input_parcels', 1)),
                            '금융사': pdf_creditor,
                            '채무자': st.session_state.get('tab3_debtor_input', debtor_from_tab1),
                            '물건지': st.session_state.get('tab3_estate_input', estate_from_tab1)
                        },
                        'fee_items': {
                            '기본료': parse_int_input(final_data.get('기본료', 0)),
                            '추가보수': parse_int_input(st.session_state.get('add_fee_val', 0)),
                            '기타보수': parse_int_input(st.session_state.get('etc_fee_val', 0)),
                            '할인금액': parse_int_input(st.session_state.get('disc_fee_val', 0))
                        },
                        'fee_totals': {
                            '보수총액': final_data.get('보수총액', 0)
                        },
                        'cost_items': {
                            '등록면허세': final_data.get('등록면허세', 0),
                            '지방교육세': final_data.get('지방교육세', 0),
                            '증지대': final_data.get('증지대', 0),
                            '채권할인': final_data.get('채권할인금액', 0),
                            '제증명': parse_int_input(st.session_state.get('cost_manual_제증명', 0)),
                            '교통비': parse_int_input(st.session_state.get('cost_manual_교통비', 0)),
                            '원인증서': parse_int_input(st.session_state.get('cost_manual_원인증서', 0)),
                            '주소변경': parse_int_input(st.session_state.get('cost_manual_주소변경', 0)),
                            '확인서면': parse_int_input(st.session_state.get('cost_manual_확인서면', 0)),
                            '선순위 말소': parse_int_input(st.session_state.get('cost_manual_선순위 말소', 0))
                        },
                        'cost_totals': {
                            '공과금 총액': final_data.get('공과금 총액', 0)
                        },
                        'cost_section_title': '2. 공과금' if st.session_state.get('show_fee', True) else '1. 공과금',
                        'grand_total': final_data.get('총 합계', 0)
                    }
                    
                    # PDF 생성
                    pdf_converter = PDFConverter(show_fee=st.session_state.get('show_fee', True))
                    pdf_buffer = pdf_converter.output_pdf(pdf_data)
                    
                    # 다운로드 버튼 (3탭 위젯 값 사용)
                    debtor_name = st.session_state.get('tab3_debtor_input', debtor_from_tab1)
                    if not debtor_name or debtor_name.strip() == '':
                        debtor_name = '고객'
                    
                    def clear_pdf_flag():
                        st.session_state['generate_pdf'] = False
                    
                    st.download_button(
                        label="⬇️ PDF 파일 다운로드",
                        data=pdf_buffer,
                        file_name=f"근저당설정_비용내역_{debtor_name}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        on_click=clear_pdf_flag
                    )
                    st.success("✅ PDF 생성 완료!")
                except Exception as e:
                    st.error(f"PDF 생성 오류: {e}")
                    st.session_state['generate_pdf'] = False
    
    # [2] 영수증 Excel 다운로드
    with d_col2:
        if st.button("🏦 영수증 Excel 다운로드", disabled=not EXCEL_OK, use_container_width=True, key="btn_excel_download"):
            st.session_state['generate_excel'] = True
        
        if st.session_state.get('generate_excel', False):
            if not EXCEL_OK:
                st.error("openpyxl 라이브러리가 설치되지 않았습니다.")
                st.session_state['generate_excel'] = False
            else:
                try:
                    # Excel 데이터 준비 (3탭 위젯 값 사용)
                    receipt_template = st.session_state['template_status'].get('영수증')
                    
                    excel_creditor = st.session_state.get('tab3_creditor_select', creditor_from_tab1)
                    if excel_creditor == "🖊️ 직접입력":
                        excel_creditor = st.session_state.get('input_creditor_name', '직접입력')
                    
                    excel_data = {
                        'date_input': format_date_korean(st.session_state.get('input_date', datetime.now().date())),
                        'client': {
                            '금융사': excel_creditor,
                            '채무자': st.session_state.get('tab3_debtor_input', debtor_from_tab1),
                            '물건지': st.session_state.get('tab3_estate_input', estate_from_tab1),
                            '채권최고액': format_number_with_comma(st.session_state.get('input_amount', ''))
                        },
                        'cost_items': {
                            '등록면허세': final_data.get('등록면허세', 0),
                            '지방교육세': final_data.get('지방교육세', 0),
                            '증지대': final_data.get('증지대', 0),
                            '채권할인': final_data.get('채권할인금액', 0),
                            '제증명': parse_int_input(st.session_state.get('cost_manual_제증명', 0)),
                            '교통비': parse_int_input(st.session_state.get('cost_manual_교통비', 0)),
                            '원인증서': parse_int_input(st.session_state.get('cost_manual_원인증서', 0)),
                            '주소변경': parse_int_input(st.session_state.get('cost_manual_주소변경', 0)),
                            '확인서면': parse_int_input(st.session_state.get('cost_manual_확인서면', 0)),
                            '선순위말소': parse_int_input(st.session_state.get('cost_manual_선순위 말소', 0))
                        },
                        'cost_totals': {
                            '공과금 총액': final_data.get('공과금 총액', 0)
                        },
                        'grand_total': final_data.get('총 합계', 0)
                    }
                    
                    # Excel 생성 (템플릿 있으면 사용, 없으면 새로 생성)
                    excel_buffer = create_receipt_excel(excel_data, receipt_template)
                    
                    if excel_buffer:
                        # 다운로드 버튼 (3탭 위젯 값 사용)
                        debtor_name = st.session_state.get('tab3_debtor_input', debtor_from_tab1)
                        if not debtor_name or debtor_name.strip() == '':
                            debtor_name = '고객'
                        
                        def clear_excel_flag():
                            st.session_state['generate_excel'] = False
                        
                        st.download_button(
                            label="⬇️ Excel 파일 다운로드",
                            data=excel_buffer,
                            file_name=f"영수증_{debtor_name}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            on_click=clear_excel_flag
                        )
                        st.success("✅ Excel 생성 완료!")
                    else:
                        st.error("Excel 생성에 실패했습니다.")
                        st.session_state['generate_excel'] = False
                except Exception as e:
                    st.error(f"Excel 생성 오류: {e}")
                    st.session_state['generate_excel'] = False

# =============================================================================
# Tab 4: 말소 문서 작성
# =============================================================================
with tab4:
    # 헤더
    col_header = st.columns([6, 1, 1])
    with col_header[0]:
        st.markdown("### 🗑️ 말소 문서 작성")
    with col_header[1]:
        if st.button("📥 1탭 가져오기", type="primary", use_container_width=True, key="sync_tab4", help="1탭 정보 불러오기"):
            # 1탭 데이터 동기화
            contract_type = st.session_state.get('contract_type', '개인')
            
            # 등기권리자 (소유자) - 3자담보면 소유자, 아니면 채무자
            if contract_type == "3자담보":
                st.session_state['malso_holder1_name'] = st.session_state.get('t1_owner_name', '')
                st.session_state['malso_holder1_rrn'] = st.session_state.get('t1_owner_rrn', '')
                st.session_state['malso_holder1_addr'] = st.session_state.get('t1_owner_addr', '')
            else:
                st.session_state['malso_holder1_name'] = st.session_state.get('t1_debtor_name', '')
                st.session_state['malso_holder1_rrn'] = st.session_state.get('t1_debtor_rrn', '')
                st.session_state['malso_holder1_addr'] = st.session_state.get('t1_debtor_addr', '')
            
            # 등기의무자 (채권자)
            creditor = st.session_state.get('input_creditor', '')
            if creditor and creditor != "🖊️ 직접입력":
                creditor_info = CREDITORS.get(creditor, {})
                # 금융사명에서 회사명과 대표자 분리
                if '대표이사' in creditor:
                    parts = creditor.split('대표이사')
                    st.session_state['malso_obligor_name'] = parts[0].strip()
                    st.session_state['malso_obligor_rep'] = parts[1].strip() if len(parts) > 1 else ''
                elif '사내이사' in creditor:
                    parts = creditor.split('사내이사')
                    st.session_state['malso_obligor_name'] = parts[0].strip()
                    st.session_state['malso_obligor_rep'] = parts[1].strip() if len(parts) > 1 else ''
                else:
                    st.session_state['malso_obligor_name'] = creditor
                    st.session_state['malso_obligor_rep'] = ''
                st.session_state['malso_obligor_id'] = creditor_info.get('corp_num', '')
                st.session_state['malso_obligor_addr'] = creditor_info.get('addr', '')
            
            # 부동산 표시
            st.session_state['malso_estate_detail'] = st.session_state.get('estate_text', '')
            
            st.success("✅ 1탭 정보를 불러왔습니다!")
            st.rerun()
    with col_header[2]:
        if st.button("🔄 초기화", type="secondary", use_container_width=True, key="reset_tab4", help="모든 입력 초기화"):
            for key in ['malso_type', 'malso_obligor_name', 'malso_obligor_id', 'malso_obligor_addr', 
                       'malso_obligor_rep', 'malso_holder1_name', 'malso_holder1_rrn', 'malso_holder1_addr',
                       'malso_holder2_name', 'malso_holder2_rrn', 'malso_holder2_addr',
                       'malso_estate_detail', 'malso_cancel_text', 'malso_from_branch', 'malso_to_branch']:
                st.session_state[key] = ''
            st.session_state['malso_type'] = "근저당권"
            st.session_state['malso_cause_date'] = datetime.now().date()
            st.success("✅ 초기화되었습니다!")
            st.rerun()
    
    st.markdown("---")
    
    # 1. 말소 유형 선택
    st.markdown("#### 📋 말소 유형 선택")
    
    if 'malso_type' not in st.session_state:
        st.session_state['malso_type'] = "근저당권"
    
    malso_type_cols = st.columns(3)
    with malso_type_cols[0]:
        if st.button("근저당권", 
                     type="primary" if st.session_state['malso_type']=="근저당권" else "secondary",
                     use_container_width=True,
                     key="btn_malso_type_1"):
            st.session_state['malso_type'] = "근저당권"
            st.rerun()
    with malso_type_cols[1]:
        if st.button("질권",
                     type="primary" if st.session_state['malso_type']=="질권" else "secondary",
                     use_container_width=True,
                     key="btn_malso_type_2"):
            st.session_state['malso_type'] = "질권"
            st.rerun()
    with malso_type_cols[2]:
        if st.button("전세권",
                     type="primary" if st.session_state['malso_type']=="전세권" else "secondary",
                     use_container_width=True,
                     key="btn_malso_type_3"):
            st.session_state['malso_type'] = "전세권"
            st.rerun()
    
    # 권리자 라벨 설정
    malso_type = st.session_state.get('malso_type', '근저당권')
    if malso_type == "근저당권":
        obligor_label = "근저당권자"
    elif malso_type == "질권":
        obligor_label = "질권자"
    else:
        obligor_label = "전세권자"
    
    st.info(f"✅ 선택된 유형: **{malso_type}말소** ({obligor_label})")
    st.markdown("---")
    
    # 2. 등기의무자 / 등기권리자 입력
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        st.markdown(f"#### 1️⃣ 등기의무자 ({obligor_label})")
        with st.container(border=True):
            st.text_input("성명(법인명)", key="malso_obligor_name", placeholder="주식회사티플레인대부")
            st.text_input("주민(법인)등록번호", key="malso_obligor_id", placeholder="110111-7350161")
            st.text_area("주소", key="malso_obligor_addr", height=80,
                        placeholder="서울특별시 마포구 삼개로 16, 2신관 1층 103호")
            st.text_input("대표자 성명 (법인인 경우)", key="malso_obligor_rep", placeholder="윤웅원")
    
    with col_input2:
        st.markdown("#### 2️⃣ 등기권리자 (소유자)")
        with st.container(border=True):
            st.markdown("**권리자 1**")
            h1_col1, h1_col2 = st.columns([2, 1])
            with h1_col1:
                st.text_input("성명", key="malso_holder1_name", placeholder="홍길동")
            with h1_col2:
                st.text_input("주민등록번호", key="malso_holder1_rrn", placeholder="000000-0000000")
            st.text_area("주소", key="malso_holder1_addr", height=60, placeholder="서울특별시 송파구...")
            
            st.markdown("**권리자 2** (있는 경우)")
            h2_col1, h2_col2 = st.columns([2, 1])
            with h2_col1:
                st.text_input("성명", key="malso_holder2_name", placeholder="김철수", label_visibility="collapsed")
            with h2_col2:
                st.text_input("주민등록번호", key="malso_holder2_rrn", placeholder="000000-0000000", label_visibility="collapsed")
            st.text_area("주소", key="malso_holder2_addr", height=60, placeholder="", label_visibility="collapsed")
    
    st.markdown("---")
    
    # 3. 등기원인 및 부동산 정보
    col_info = st.columns(2)
    with col_info[0]:
        st.markdown("#### 3️⃣ 등기원인과 그 년월일")
        if 'malso_cause_date' not in st.session_state:
            st.session_state['malso_cause_date'] = datetime.now().date()
        st.date_input("등기원인일", value=st.session_state['malso_cause_date'], key="malso_cause_date_input")
        st.session_state['malso_cause_date'] = st.session_state.get('malso_cause_date_input', datetime.now().date())
    
    with col_info[1]:
        st.markdown("#### 4️⃣ 등기목적")
        malso_purpose = f"{malso_type}말소"
        st.text_input("등기목적", value=malso_purpose, disabled=True, key="malso_purpose_display")
    
    st.markdown("#### 5️⃣ 부동산의 표시")
    with st.container(border=True):
        st.text_area(
            "부동산 상세 (등기부등본에서 복사)",
            key="malso_estate_detail",
            height=200,
            placeholder="1동의 건물의 표시\n서울특별시 송파구 문정동 150\n..."
        )
    
    st.markdown("#### 6️⃣ 말소할 등기")
    st.text_input(
        "말소할 등기 (접수번호 등)",
        key="malso_cancel_text",
        placeholder="2025년09월30일 접수 제5201489호(으)로 경료한 근저당권설정"
    )
    
    st.markdown("---")
    
    # 4. 이관 정보 (이관증명서용)
    st.markdown("#### 🏦 이관 정보 (이관증명서용)")
    col_transfer = st.columns(2)
    with col_transfer[0]:
        st.text_input("이관 전", key="malso_from_branch", placeholder="취급지점명")
    with col_transfer[1]:
        st.text_input("이관 후", key="malso_to_branch", placeholder="본점")
    
    st.markdown("---")
    
    # 5. PDF 생성 - 체크박스 선택 후 한번에 출력
    st.markdown("### 📥 문서 생성")
    
    # 체크박스로 문서 선택
    col_chk = st.columns(4)
    with col_chk[0]:
        chk_sig = st.checkbox("📄 자필서명정보", value=True, key="chk_malso_sig")
    with col_chk[1]:
        chk_power = st.checkbox("📄 위임장", value=True, key="chk_malso_power")
    with col_chk[2]:
        chk_term = st.checkbox("📄 해지증서", value=True, key="chk_malso_term")
    with col_chk[3]:
        chk_transfer = st.checkbox("📄 이관증명서", value=False, key="chk_malso_transfer")
    
    # 생성 버튼
    if st.button("🚀 선택한 문서 생성", type="primary", use_container_width=True, key="generate_malso_docs"):
        if not any([chk_sig, chk_power, chk_term, chk_transfer]):
            st.warning("⚠️ 생성할 문서를 선택해주세요.")
        else:
            st.session_state['generate_malso_sig'] = chk_sig
            st.session_state['generate_malso_power'] = chk_power
            st.session_state['generate_malso_term'] = chk_term
            st.session_state['generate_malso_transfer'] = chk_transfer
    
    # PDF 생성 처리
    if st.session_state.get('generate_malso_sig', False):
        try:
            # 자필서명정보 생성 - 서면 템플릿 사용
            sig_template = resource_path("자필서명정보_서면_템플릿.pdf")
            if os.path.exists(sig_template) and PDF_OK:
                # 권리자 목록 생성
                holders = []
                if st.session_state.get('malso_holder1_name'):
                    holders.append({
                        'name': st.session_state.get('malso_holder1_name', ''),
                        'rrn': st.session_state.get('malso_holder1_rrn', ''),
                        'addr': st.session_state.get('malso_holder1_addr', '')
                    })
                if st.session_state.get('malso_holder2_name'):
                    holders.append({
                        'name': st.session_state.get('malso_holder2_name', ''),
                        'rrn': st.session_state.get('malso_holder2_rrn', ''),
                        'addr': st.session_state.get('malso_holder2_addr', '')
                    })
                
                sig_data = {
                    'date': format_date_korean(st.session_state.get('malso_cause_date', datetime.now().date())),
                    'estate_list': st.session_state.get('malso_estate_detail', '').strip().split('\n'),
                    'holders': holders
                }
                
                # 말소타입 약어
                malso_prefix = {"근저당권": "근말", "질권": "질말", "전세권": "전말"}.get(malso_type, "말소")
                holder_name = st.session_state.get('malso_holder1_name', '고객')
                
                pdf_buffer = make_malso_signature_pdf(sig_template, sig_data)
                st.download_button(
                    label="⬇️ 자필서명정보 다운로드",
                    data=pdf_buffer,
                    file_name=f"{malso_prefix}_{holder_name}_자필서명정보.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ 자필서명정보 생성 완료!")
            else:
                st.error("자필서명정보 템플릿(자필서명정보_서면_템플릿.pdf)이 없거나 PDF 라이브러리가 설치되지 않았습니다.")
        except Exception as e:
            st.error(f"생성 오류: {e}")
        st.session_state['generate_malso_sig'] = False
    
    if st.session_state.get('generate_malso_power', False):
        try:
            if PDF_OK:
                power_data = {
                    'date': format_date_korean(st.session_state.get('malso_cause_date', datetime.now().date())),
                    'malso_type': malso_type,
                    'obligor_label': obligor_label,
                    'obligor_name': st.session_state.get('malso_obligor_name', ''),
                    'obligor_id': st.session_state.get('malso_obligor_id', ''),
                    'obligor_addr': st.session_state.get('malso_obligor_addr', ''),
                    'obligor_rep': st.session_state.get('malso_obligor_rep', ''),
                    'holder1_name': st.session_state.get('malso_holder1_name', ''),
                    'holder1_addr': st.session_state.get('malso_holder1_addr', ''),
                    'holder2_name': st.session_state.get('malso_holder2_name', ''),
                    'holder2_addr': st.session_state.get('malso_holder2_addr', ''),
                    'estate_text': st.session_state.get('malso_estate_detail', ''),
                    'cancel_text': st.session_state.get('malso_cancel_text', '')
                }
                
                # 말소타입 약어
                malso_prefix = {"근저당권": "근말", "질권": "질말", "전세권": "전말"}.get(malso_type, "말소")
                holder_name = st.session_state.get('malso_holder1_name', '고객')
                
                # 위임장 템플릿 사용
                power_template_path = resource_path("말소_위임장.pdf")
                if os.path.exists(power_template_path):
                    pdf_buffer = make_malso_power_pdf(power_template_path, power_data)
                    st.download_button(
                        label="⬇️ 위임장 다운로드",
                        data=pdf_buffer,
                        file_name=f"{malso_prefix}_{holder_name}_위임장.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("✅ 위임장 생성 완료!")
                else:
                    st.error("위임장 템플릿 파일이 없습니다. (말소_위임장.pdf)")
            else:
                st.error("PDF 라이브러리가 설치되지 않았습니다.")
        except Exception as e:
            st.error(f"생성 오류: {e}")
        st.session_state['generate_malso_power'] = False
    
    if st.session_state.get('generate_malso_term', False):
        try:
            if PDF_OK:
                term_data = {
                    'date': format_date_korean(st.session_state.get('malso_cause_date', datetime.now().date())),
                    'malso_type': malso_type,
                    'obligor_label': obligor_label,
                    'obligor_name': st.session_state.get('malso_obligor_name', ''),
                    'obligor_id': st.session_state.get('malso_obligor_id', ''),
                    'obligor_addr': st.session_state.get('malso_obligor_addr', ''),
                    'obligor_rep': st.session_state.get('malso_obligor_rep', ''),
                    'holder1_name': st.session_state.get('malso_holder1_name', ''),
                    'holder2_name': st.session_state.get('malso_holder2_name', ''),
                    'estate_text': st.session_state.get('malso_estate_detail', ''),
                    'cancel_text': st.session_state.get('malso_cancel_text', '')
                }
                
                # 말소타입 약어
                malso_prefix = {"근저당권": "근말", "질권": "질말", "전세권": "전말"}.get(malso_type, "말소")
                holder_name = st.session_state.get('malso_holder1_name', '고객')
                
                pdf_buffer = make_malso_termination_pdf(term_data)
                st.download_button(
                    label="⬇️ 해지증서 다운로드",
                    data=pdf_buffer,
                    file_name=f"{malso_prefix}_{holder_name}_해지증서.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ 해지증서 생성 완료!")
            else:
                st.error("PDF 라이브러리가 설치되지 않았습니다.")
        except Exception as e:
            st.error(f"생성 오류: {e}")
        st.session_state['generate_malso_term'] = False
    
    if st.session_state.get('generate_malso_transfer', False):
        try:
            if PDF_OK:
                transfer_data = {
                    'date': format_date_korean(st.session_state.get('malso_cause_date', datetime.now().date())),
                    'malso_type': malso_type,
                    'obligor_label': obligor_label,
                    'obligor_name': st.session_state.get('malso_obligor_name', ''),
                    'obligor_id': st.session_state.get('malso_obligor_id', ''),
                    'obligor_addr': st.session_state.get('malso_obligor_addr', ''),
                    'obligor_rep': st.session_state.get('malso_obligor_rep', ''),
                    'estate_text': st.session_state.get('malso_estate_detail', ''),
                    'cancel_text': st.session_state.get('malso_cancel_text', ''),
                    'from_branch': st.session_state.get('malso_from_branch', ''),
                    'to_branch': st.session_state.get('malso_to_branch', '')
                }
                
                # 말소타입 약어
                malso_prefix = {"근저당권": "근말", "질권": "질말", "전세권": "전말"}.get(malso_type, "말소")
                holder_name = st.session_state.get('malso_holder1_name', '고객')
                
                pdf_buffer = make_malso_transfer_pdf(transfer_data)
                st.download_button(
                    label="⬇️ 이관증명서 다운로드",
                    data=pdf_buffer,
                    file_name=f"{malso_prefix}_{holder_name}_이관증명서.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ 이관증명서 생성 완료!")
            else:
                st.error("PDF 라이브러리가 설치되지 않았습니다.")
        except Exception as e:
            st.error(f"생성 오류: {e}")
        st.session_state['generate_malso_transfer'] = False
    
    # 안내 메시지
    st.info("💡 **사용 방법**: '📥 1탭 가져오기' 버튼을 눌러 소유자 정보와 부동산 표시를 자동으로 불러올 수 있습니다.")

# =============================================================================
# 하단 푸터
# =============================================================================
st.markdown("---")
st.markdown("""<div style='text-align: center; color: #6c757d; padding: 20px; background-color: white; border-radius: 10px; border: 2px solid #e1e8ed;'>
    <p style='margin: 0; font-size: 1rem; color: #00428B;'><strong>DG-Form 등기온 전자설정 자동화 시스템 | 법무법인 시화</strong></p>
    <p style='margin: 5px 0 0 0; font-size: 0.85rem; color: #6c757d;'>부동산 등기는 등기온</p></div>""", unsafe_allow_html=True)