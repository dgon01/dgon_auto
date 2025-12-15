import streamlit as st
import os
import re
import math
from io import BytesIO
from datetime import datetime, date
import base64

# =============================================================================
# 0. 기본 설정 및 경로
# =============================================================================
st.set_page_config(
    layout="wide", 
    page_title="DG-Form | 등기온 전자설정 자동화",
    page_icon="🏠",
    initial_sidebar_state="collapsed"
)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    """GitHub 등 환경에서 파일 경로를 절대경로로 변환"""
    return os.path.join(APP_ROOT, relative_path)

# 이미지 및 폰트 경로
LOGO_PATH = resource_path("my_icon.ico")
FONT_PATH = resource_path("Malgun.ttf") 

# 템플릿 파일 경로 정의
TEMPLATE_PATHS = {
    "개인": resource_path("1.pdf"),
    "3자담보": resource_path("2.pdf"),
    "공동담보": resource_path("3.pdf"),
    "자필_전자": resource_path("자필서명정보 템플릿.pdf"),
    "자필_서면": resource_path("자필서명정보_서면_템플릿.pdf"),
    "영수증": resource_path("영수증_템플릿.xlsx")
}

# 로고 로드
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

logo_base64 = get_base64_image(LOGO_PATH)

# =============================================================================
# 1. 라이브러리 로드
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
    PDF_OK = True
except ImportError:
    PDF_OK = False

try:
    from fpdf import FPDF
    FPDF_OK = True
except ImportError:
    FPDF_OK = False

LIBS_OK = PDF_OK

# =============================================================================
# 2. 스타일 및 디자인 (수정된 헤더 적용)
# =============================================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');
    .stApp {{ font-family: 'Noto Sans KR', sans-serif !important; }}
    input, textarea, select, button {{ font-family: 'Noto Sans KR', sans-serif !important; }}
    
    /* 헤더 컨테이너 */
    .header-container {{
        background: white; 
        border-bottom: 3px solid #00428B; 
        padding: 15px 30px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        display: flex; align-items: center; gap: 20px;
    }}
    
    /* 로고 스타일 */
    .header-logo {{ width: 80px; height: auto; }} /* 로고 크기 확대 */
    
    /* 텍스트 레이아웃 */
    .text-content {{ display: flex; flex-direction: column; justify-content: center; }}
    
    /* 제목 스타일 (DG-Form) */
    .header-title {{ 
        margin: 0; 
        font-size: 2.2rem; 
        font-weight: 800; 
        line-height: 1.1; 
        letter-spacing: -1px;
    }}
    
    /* 서브 텍스트 (2줄) */
    .header-desc {{ margin: 0; padding-top: 5px; }}
    .desc-line-1 {{ 
        display: block; 
        font-size: 1rem; 
        font-weight: 500; 
        color: #555; 
        margin-bottom: 2px; 
    }}
    .desc-line-2 {{ 
        display: block; 
        font-size: 0.95rem; 
        font-weight: 700; 
        color: #00428B; /* 브랜드 컬러 강조 */
    }}

    /* 탭 및 기타 스타일 유지 */
    .stTabs [data-baseweb="tab-list"] {{ gap: 10px; background-color: #ffffff; padding: 10px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
    .stTabs [data-baseweb="tab"] {{ background-color: #f8f9fa; border-radius: 8px; padding: 10px 20px; font-weight: 600; color: #495057; border: 1px solid #dee2e6; }}
    .stTabs [aria-selected="true"] {{ background-color: #00428B; color: white; border-color: #00428B; }}
    
    .row-label {{ font-weight: 500; color: #495057; display: flex; align-items: center; height: 100%; font-size: 0.9rem; }}
    .section-header {{ font-size: 1.1rem; font-weight: 700; margin-bottom: 15px; padding-bottom: 5px; border-bottom: 2px solid; }}
    .income-header {{ color: #28a745; border-color: #28a745; }}
    .tax-header {{ color: #fd7e14; border-color: #fd7e14; }}
    .total-header {{ color: #dc3545; border-color: #dc3545; }}
    .total-box {{ background-color: #ff0033; color: white; padding: 20px; text-align: center; border-radius: 8px; margin: 15px 0; }}
    .total-amount {{ font-size: 2rem; font-weight: 800; }}
</style>
""", unsafe_allow_html=True)

# 헤더 HTML 렌더링
header_html = f"""
<div class="header-container">
    {'<img src="data:image/x-icon;base64,' + logo_base64 + '" class="header-logo" alt="DG-ON Logo">' if logo_base64 else ''}
    <div class="text-content">
        <h1 class="header-title">
            <span style="color: #00428B;">DG-</span><span style="color: #FFC000;">Form</span>
        </h1>
        <div class="header-desc">
            <span class="desc-line-1">등기온 전자설정 자동화 시스템 | 법무법인 시화</span>
            <span class="desc-line-2">부동산 등기는 등기온</span>
        </div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)
# =============================================================================
# 3. 데이터 및 유틸리티 함수
# =============================================================================
CREDITORS = {
    "(주)티플레인대부 대표이사 윤웅원": {"addr": "서울특별시 마포구 삼개로16, 2신관1층103호(도화동,근신빌딩)", "corp_num": "110111-7350161", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}},
    "(주)유노스프레스티지대부 사내이사 한은수": {"addr": "서울특별시 강남구 압구정로28길24, 5층 501호(신사동,디앤씨빌딩)", "corp_num": "110111-4138560", "fee": {"제증명": 20000, "교통비": 0, "원인증서": 0, "확인서면": 0, "선순위 말소": 0}},
    "(주)파트너스대부 사내이사 허성": {"addr": "부산광역시 부산진구 서면문화로 43, 2층(부전동)", "corp_num": "180111-1452175", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}},
    "(주)드림앤캐쉬대부 대표이사 김재섭": {"addr": "서울특별시 강남구 압구정로28길24, 6층 601호(신사동,디앤씨빌딩)", "corp_num": "110111-4176552", "fee": {"제증명": 20000, "교통비": 0, "원인증서": 0}},
    "(주)마젤란트러스트대부 대표이사 김병수": {"addr": "서울특별시 서초구 강남대로34길 7, 7층(양재동,이안빌딩)", "corp_num": "110111-6649979", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}},
    "(주)하이클래스대부 사내이사 성윤호": {"addr": "서울특별시 강남구 도곡로 188, 3층 4호(도곡동,도곡스퀘어)", "corp_num": "110111-0933512", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}}
}

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
        response = requests.get(url, headers=headers, timeout=2)
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

def parse_int_input(text_input):
    try:
        if isinstance(text_input, int): return text_input
        return int(remove_commas(text_input or "0"))
    except ValueError: return 0

# 전역 초기화 함수 (콜백용)
def reset_all_data():
    """모든 세션 상태를 초기값으로 리셋"""
    defaults = {
        'input_date': datetime.now().date(),
        't1_creditor_select': list(CREDITORS.keys())[0],
        'input_creditor': list(CREDITORS.keys())[0],
        'input_creditor_name': '', 'input_creditor_corp_num': '', 'input_creditor_addr': '',
        't1_debtor_name': '', 't1_debtor_addr': '',
        't1_owner_name': '', 't1_owner_addr': '',
        'contract_type': '개인', 'guarantee': '한정근담보',
        'amount_raw_input': '', 'input_amount': '',
        'input_collateral_addr': '', 'collateral_addr_input': '',
        'estate_text': """[토지]\n서울특별시 강남구 대치동 123번지\n대 300㎡\n\n[건물]\n서울특별시 강남구 대치동 123번지\n철근콘크리트조 슬래브지붕 5층 주택\n1층 100㎡\n2층 100㎡""",
        
        # 2탭 변수
        't2_date': datetime.now().date(), 't2_cause': '설정계약',
        't2_name1': '', 't2_rrn1': '', 't2_name2': '', 't2_rrn2': '',
        't2_estate': '',
        
        # 3탭 변수
        'calc_amount_input': '', 'input_parcels': 1, 'input_rate': f"{get_rate()*100:.5f}",
        'tab3_creditor_select': list(CREDITORS.keys())[0],
        'tab3_debtor_input': '', 'tab3_estate_input': '',
        'add_fee_val': "0", 'etc_fee_val': "0", 'disc_fee_val': "0",
        'cost_manual_제증명': "0", 'cost_manual_교통비': "0", 'cost_manual_원인증서': "0",
        'cost_manual_주소변경': "0", 'cost_manual_확인서면': "0", 'cost_manual_선순위 말소': "0",
        'use_address_change': False, 'address_change_count': 1,
        
        # 4탭 변수
        'malso_type': '근저당권', 'malso_obligor_corp': '', 'malso_obligor_rep': '',
        'malso_obligor_id': '', 'malso_obligor_addr': '',
        'malso_holder_name': '', 'malso_holder_addr': '',
        'malso_cause_date': datetime.now().date(), 'malso_cause': '해지',
        'malso_estate_detail': '', 'malso_cancel_text': ''
    }
    
    for key, val in defaults.items():
        st.session_state[key] = val

# 초기 상태 설정
if 'estate_text' not in st.session_state:
    reset_all_data()

# =============================================================================
# PDF/Excel 생성 클래스 및 함수
# =============================================================================
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
            self.ln(3)
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
    if not text: return
    words = text.split(); lines = []; current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if canvas_obj.stringWidth(test_line, font_name, font_size) <= max_width: current_line.append(word)
        else:
            if current_line: lines.append(' '.join(current_line))
            current_line = [word]
    if current_line: lines.append(' '.join(current_line))
    for i, line in enumerate(lines): canvas_obj.drawString(x, y - (i * (font_size + 2)), line)

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
    writer.write(output_buffer); output_buffer.seek(0)
    return output_buffer

def make_signature_pdf(template_path, data):
    packet = BytesIO(); c = canvas.Canvas(packet, pagesize=A4); width, height = A4
    try: pdfmetrics.registerFont(TTFont('Korean', FONT_PATH)); font_name = 'Korean'
    except: font_name = 'Helvetica'
    c.setFont(font_name, 10); estate_x = 150; estate_y = height - 170; line_h = 14
    
    if data.get("estate_text"):
        for i, line in enumerate(str(data["estate_text"]).split("\n")[:17]):
            c.drawString(estate_x, estate_y - (i * line_h), line)
    
    if data.get("name1"): c.drawString(250, 322, str(data["name1"]))
    if data.get("rrn1"): c.drawString(250, 298, str(data["rrn1"]))
    
    if data.get("name2"): c.drawString(400, 322, str(data["name2"]))
    if data.get("rrn2"): c.drawString(400, 298, str(data["rrn2"]))
    
    if data.get("date"):
        c.setFont(font_name, 11); text = str(data["date"]); tw = c.stringWidth(text, font_name, 11)
        c.drawString((width - tw) / 2, 150, text)
        
    c.showPage(); c.save(); packet.seek(0)
    overlay_pdf = PdfReader(packet); template_pdf = PdfReader(template_path); writer = PdfWriter()
    output_buffer = BytesIO()
    if len(template_pdf.pages) > 0:
        template_page = template_pdf.pages[0]; overlay_page = overlay_pdf.pages[0]
        template_page.merge_page(overlay_page); writer.add_page(template_page)
    writer.write(output_buffer); output_buffer.seek(0)
    return output_buffer

def calculate_all(data):
    amount = parse_int_input(data.get('채권최고액')) 
    parcels = parse_int_input(data.get('필지수'))
    try: rate = float(remove_commas(data.get('채권할인율', '0'))) / 100
    except ValueError: rate = 0 
    
    data['input_amount'] = data.get('채권최고액', '')
    base_fee = lookup_base_fee(amount)
    data['기본료'] = base_fee
    
    add_fee = parse_int_input(data.get('추가보수_val'))
    etc_fee = parse_int_input(data.get('기타보수_val'))
    disc_fee = parse_int_input(data.get('할인금액'))

    fee_total = 0
    if st.session_state.get('show_fee', True):
        supply_val = base_fee + add_fee + etc_fee - disc_fee
        vat = math.floor(max(0, supply_val) * 0.1)
        fee_total = supply_val + vat
        data['공급가액'] = supply_val; data['부가세'] = vat; data['보수총액'] = fee_total
    else:
        data['공급가액'] = 0; data['부가세'] = 0; data['보수총액'] = 0
    
    use_addr_change = st.session_state.get('use_address_change', False)
    addr_count = st.session_state.get('address_change_count', 1)
    
    addr_reg = 0; addr_edu = 0; addr_jeungji = 0
    if use_addr_change and addr_count > 0:
        addr_reg = 6000 * addr_count; addr_edu = 1200 * addr_count; addr_jeungji = 3000 * addr_count
    
    basic_reg = floor_10(amount * 0.002); basic_edu = floor_10(basic_reg * 0.2)
    final_reg = basic_reg + addr_reg; final_edu = basic_edu + addr_edu
    jeungji = (18000 * parcels) + addr_jeungji 

    bond = 0
    if amount >= 20_000_000: bond = math.ceil(amount * 0.01 / 10000) * 10000
    bond_disc = floor_10(bond * rate)
    
    data["등록면허세"] = final_reg; data["지방교육세"] = final_edu
    data["증지대"] = jeungji; data["채권할인금액"] = bond_disc
    
    cost_total = final_reg + final_edu + jeungji + bond_disc
    MANUAL_COST_NAMES = ["제증명", "교통비", "원인증서", "주소변경", "확인서면", "선순위 말소"]
    for k in MANUAL_COST_NAMES: cost_total += parse_int_input(st.session_state.get('cost_manual_' + k, 0))
    
    data['공과금 총액'] = cost_total
    data['총 합계'] = fee_total + cost_total
    return data

def create_receipt_excel(data, template_path=None):
    if not EXCEL_OK: return None
    if template_path and os.path.exists(template_path):
        try:
            workbook = openpyxl.load_workbook(template_path)
            ws = workbook.active
            client = data.get('client', {})
            date_str = data.get('date_input', '')
            if date_str: ws['AG2'] = date_str
            ws['B4'] = client.get('금융사', ''); ws['V4'] = client.get('채무자', '')
            amount_str = client.get('채권최고액', '0')
            ws['AG5'] = int(re.sub(r'[^\d]', '', amount_str)) if amount_str else 0
            ws['Y7'] = client.get('물건지', '')
            cost_items = data.get('cost_items', {})
            ws['AH11'] = int(cost_items.get('등록면허세', 0)); ws['AH12'] = int(cost_items.get('지방교육세', 0))
            ws['AH13'] = int(cost_items.get('증지대', 0)); ws['AH14'] = int(cost_items.get('채권할인', 0))
            ws['AH15'] = int(cost_items.get('제증명', 0)); ws['AH16'] = int(cost_items.get('원인증서', 0))
            ws['AH17'] = int(cost_items.get('주소변경', 0)); ws['AH18'] = int(cost_items.get('선순위말소', 0))
            traffic_fee = int(cost_items.get('교통비', 0))
            if traffic_fee > 0: ws['AD19'] = '교통비'; ws['AH19'] = traffic_fee
            else: ws['AD19'] = None; ws['AH19'] = None
            confirm_fee = int(cost_items.get('확인서면', 0))
            if confirm_fee > 0: ws['AD20'] = '확인서면'; ws['AH20'] = confirm_fee
            else: ws['AD20'] = None; ws['AH20'] = None
            ws['AH21'] = '=SUM(AH11:AH20)'; ws['Y22'] = '=AH21'
        except Exception:
            workbook = openpyxl.Workbook(); ws = workbook.active; ws.title = "영수증"
            _create_simple_receipt(ws, data)
    else:
        workbook = openpyxl.Workbook(); ws = workbook.active; ws.title = "영수증"
        _create_simple_receipt(ws, data)
    output = BytesIO(); workbook.save(output); output.seek(0)
    return output

def _create_simple_receipt(sheet, data):
    from openpyxl.styles import Font, Alignment
    sheet['A1'] = '근저당권설정 영수증'; sheet['A1'].font = Font(size=16, bold=True)
    sheet['A1'].alignment = Alignment(horizontal='center'); sheet.merge_cells('A1:C1')
    sheet['A3'] = '작성일:'; sheet['B3'] = data.get('date_input', '')
    client = data.get('client', {})
    sheet['A5'] = '채무자:'; sheet['B5'] = client.get('채무자', '')
    sheet['A6'] = '물건지:'; sheet['B6'] = client.get('물건지', '')
    sheet['A7'] = '채권최고액:'; sheet['B7'] = client.get('채권최고액', '')
    row = 9
    sheet[f'A{row}'] = '항목'; sheet[f'B{row}'] = '금액'
    row += 1
    cost_items = data.get('cost_items', {})
    for name, value in cost_items.items():
        if value != 0: sheet[f'A{row}'] = name; sheet[f'B{row}'] = f"{int(value):,} 원"; row += 1
    row += 1; sheet[f'A{row}'] = '총 합계'; sheet[f'B{row}'] = f"{data.get('grand_total', 0):,} 원"

# =============================================================================
# UI 구현
# =============================================================================

tab1, tab2, tab3, tab4 = st.tabs(["📄 근저당권설정 계약서", "✍️ 자필서명정보", "🧾 비용 계산 및 영수증", "🗑️ 말소 문서"])

# -----------------------------------------------------------------------------
# Tab 1: 근저당권 설정
# -----------------------------------------------------------------------------
with tab1:
    col_header = st.columns([5, 1])
    col_header[0].markdown("### 📝 근저당권설정 계약서 작성")
    col_header[1].button("🔄 전체 초기화", type="secondary", key="reset_all_t1", on_click=reset_all_data)
    st.markdown("---")
    
    with st.expander("📌 기본 정보", expanded=True):
        st.session_state['input_date'] = st.date_input("작성일자", value=st.session_state['input_date'], key='date_picker')

    def handle_creditor_change():
        creditor_key = st.session_state.get('t1_creditor_select')
        if creditor_key == "🖊️ 직접입력":
            st.session_state['input_creditor'] = "🖊️ 직접입력"
            st.session_state['input_creditor_name'] = ""
            st.session_state['input_creditor_corp_num'] = ""
            st.session_state['input_creditor_addr'] = ""
        else:
            st.session_state['input_creditor'] = creditor_key
            info = CREDITORS[creditor_key]
            st.session_state['input_creditor_name'] = creditor_key
            st.session_state['input_creditor_corp_num'] = info['corp_num']
            st.session_state['input_creditor_addr'] = info['addr']

    with st.expander("👤 당사자 정보", expanded=True):
        creditor_list = list(CREDITORS.keys()) + ["🖊️ 직접입력"]
        st.selectbox("채권자 선택", options=creditor_list, key='t1_creditor_select', on_change=handle_creditor_change)
        
        if st.session_state['t1_creditor_select'] == "🖊️ 직접입력":
            st.text_input("채권자 성명/상호", key='input_creditor_name')
            st.text_input("법인번호", key='input_creditor_corp_num')
            st.text_area("채권자 주소", key='input_creditor_addr', height=100)
        else:
            info = CREDITORS[st.session_state['t1_creditor_select']]
            st.text_input("법인번호", value=info['corp_num'], disabled=True)
            st.text_area("채권자 주소", value=info['addr'], disabled=True)

        st.text_input("채무자 성명", key='t1_debtor_name')
        st.text_area("채무자 주소", key='t1_debtor_addr', height=100)
        st.text_input("설정자 성명", key='t1_owner_name')
        st.text_area("설정자 주소", key='t1_owner_addr', height=100)

    with st.expander("🤝 담보 및 계약 정보", expanded=True):
        st.radio("계약서 유형", options=["개인", "3자담보", "공동담보"], horizontal=True, key='contract_type')
        st.text_input("피담보채무", key='guarantee')
        
        def format_amount_on_change():
            raw = st.session_state['amount_raw_input']
            fmt = format_number_with_comma(raw)
            st.session_state['input_amount'] = fmt
            st.session_state['amount_raw_input'] = fmt
        
        st.text_input("채권최고액", key='amount_raw_input', on_change=format_amount_on_change, placeholder="숫자만 입력")
        if st.session_state['input_amount'] and st.session_state['input_amount'] != "0":
            st.info(f"💰 **{number_to_korean(remove_commas(st.session_state['input_amount']))}**")
        
        col_addr1, col_addr2 = st.columns([5, 1])
        def copy_debtor_address():
            st.session_state['collateral_addr_input'] = st.session_state['t1_debtor_addr']
            st.session_state['input_collateral_addr'] = st.session_state['t1_debtor_addr']
        with col_addr1:
            st.text_area("물건지 주소 (수기 입력)", key='collateral_addr_input', height=100)
            st.session_state['input_collateral_addr'] = st.session_state['collateral_addr_input']
        with col_addr2:
            st.write(""); st.write("")
            st.button("📋\n채무자\n주소복사", on_click=copy_debtor_address, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🏠 부동산의 표시"); st.caption("※ 등기부등본 내용을 입력하세요")
    col_estate, col_pdf = st.columns([3, 1])
    with col_estate:
        st.text_area("부동산 표시 내용", key='estate_text', height=300, label_visibility="collapsed")
    with col_pdf:
        st.markdown("#### 📑 파일 생성")
        template_path = TEMPLATE_PATHS.get(st.session_state['contract_type'])
        if template_path and os.path.exists(template_path): 
            st.success(f"✅ 템플릿 준비완료"); is_disabled = False
        else: 
            st.warning(f"⚠️ 템플릿 없음"); is_disabled = True
        
        if st.button("🚀 계약서\nPDF 생성", disabled=is_disabled or not LIBS_OK, use_container_width=True):
            data = {
                "date": format_date_korean(st.session_state['input_date']), 
                "creditor_name": st.session_state['input_creditor_name'], "creditor_addr": st.session_state['input_creditor_addr'],
                "debtor_name": st.session_state['t1_debtor_name'], "debtor_addr": st.session_state['t1_debtor_addr'],
                "owner_name": st.session_state['t1_owner_name'], "owner_addr": st.session_state['t1_owner_addr'],
                "guarantee_type": st.session_state['guarantee'], "claim_amount": convert_multiple_amounts_to_korean(remove_commas(st.session_state['input_amount'])),
                "estate_list": st.session_state['estate_text'].strip().split("\n"), "contract_type": st.session_state['contract_type']
            }
            try:
                pdf_buffer = make_pdf(template_path, data)
                st.download_button(label="⬇️ 다운로드", data=pdf_buffer, file_name=f"근저당권설정_{data['debtor_name']}.pdf", mime="application/pdf", use_container_width=True)
            except Exception as e: st.error(f"오류: {e}")

# -----------------------------------------------------------------------------
# Tab 2: 자필서명 정보
# -----------------------------------------------------------------------------
with tab2:
    col_h2 = st.columns([5, 1])
    col_h2[0].markdown("### ✍️ 자필서명정보 작성")
    col_h2[1].button("🔄 전체 초기화", type="secondary", key="reset_all_t2", on_click=reset_all_data)
    st.markdown("---")

    def sync_tab2_from_tab1():
        st.session_state['t2_date'] = st.session_state['input_date']
        c_type = st.session_state.get('contract_type', '개인')
        debtor = st.session_state.get('t1_debtor_name', '')
        owner = st.session_state.get('t1_owner_name', '')
        st.session_state['t2_estate'] = st.session_state.get('estate_text', '')

        if c_type == "3자담보":
            st.session_state['t2_name1'] = owner
            st.session_state['t2_name2'] = ""
        else:
            st.session_state['t2_name1'] = debtor
            st.session_state['t2_name2'] = owner

    if st.button("🔄 1탭 정보 가져오기", key="sync_tab2"):
        sync_tab2_from_tab1()

    sign_type = st.radio("접수 유형", ["전자접수", "서면접수"], horizontal=True)
    st.info(f"현재 선택: **{sign_type}**")

    col_t2_1, col_t2_2 = st.columns(2)
    with col_t2_1:
        st.markdown("#### 📅 기본 정보")
        st.date_input("작성일자", key='t2_date')
        st.text_input("등기원인", value="설정계약", key='t2_cause')
    
    st.markdown("#### 👤 등기의무자 정보")
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        with st.container(border=True):
            st.markdown("**의무자 1 (채무자/소유자)**")
            st.text_input("성명", key='t2_name1', placeholder="성명 입력")
            st.text_input("주민(법인)등록번호", key='t2_rrn1', placeholder="000000-0000000")
    with c_p2:
        with st.container(border=True):
            st.markdown("**의무자 2 (소유자)**")
            st.text_input("성명", key='t2_name2', placeholder="성명 입력 (필요시)")
            st.text_input("주민(법인)등록번호", key='t2_rrn2', placeholder="000000-0000000")
            
    st.markdown("#### 🏠 부동산의 표시")
    st.text_area("부동산 표시 내용", key='t2_estate', height=150)

    st.markdown("---")
    template_key = "자필_전자" if sign_type == "전자접수" else "자필_서면"
    t_path = TEMPLATE_PATHS.get(template_key)
    
    if t_path and os.path.exists(t_path):
        if st.button("🚀 자필서명 PDF 생성", key="gen_sign_pdf", use_container_width=True):
            data = {
                "date": format_date_korean(st.session_state['t2_date']),
                "cause": st.session_state['t2_cause'],
                "name1": st.session_state['t2_name1'], "rrn1": st.session_state['t2_rrn1'],
                "name2": st.session_state['t2_name2'], "rrn2": st.session_state['t2_rrn2'],
                "estate_text": st.session_state['t2_estate']
            }
            try:
                pdf_buffer = make_signature_pdf(t_path, data)
                st.download_button("⬇️ 다운로드", data=pdf_buffer, file_name=f"자필서명정보_{data['name1']}.pdf", mime="application/pdf", use_container_width=True)
                st.success("✅ PDF 생성완료!")
            except Exception as e: st.error(f"오류: {e}")
    else:
        st.warning(f"⚠️ 템플릿 파일이 없습니다: {t_path}")

# -----------------------------------------------------------------------------
# Tab 3: 비용 계산 및 영수증
# -----------------------------------------------------------------------------
with tab3:
    col_header3 = st.columns([5, 1])
    col_header3[0].markdown("### 🧾 등기비용 계산기")
    col_header3[1].button("🔄 전체 초기화", type="secondary", key="reset_all_t3", on_click=reset_all_data)
    st.markdown("---")

    def sync_tab3_from_tab1():
        st.session_state['calc_amount_input'] = st.session_state.get('input_amount', '')
        st.session_state['tab3_debtor_input'] = st.session_state.get('t1_debtor_name', '')
        estate_val = st.session_state.get('input_collateral_addr', '')
        if not estate_val: estate_val = extract_address_from_estate(st.session_state.get('estate_text', ''))
        st.session_state['tab3_estate_input'] = estate_val
        st.session_state['tab3_creditor_select'] = st.session_state.get('t1_creditor_select', list(CREDITORS.keys())[0])

    if st.button("🔄 1탭 정보 가져오기", key="sync_tab3"):
        sync_tab3_from_tab1()

    row1_c1, row1_c2, row1_c3, row1_c4 = st.columns([2, 0.5, 1, 1.2]) 
    with row1_c1:
        def on_amount_change():
            st.session_state['calc_amount_input'] = format_number_with_comma(st.session_state['calc_amount_input'])
        st.text_input("채권최고액", key='calc_amount_input', on_change=on_amount_change)
    with row1_c3:
        st.number_input("필지수", min_value=1, key='input_parcels')
    with row1_c4:
        def update_rate():
            st.session_state['input_rate'] = f"{get_rate()*100:.5f}"
        c_rate, c_btn = st.columns([2, 1])
        with c_rate: st.text_input("할인율(%)", key='input_rate')
        with c_btn:
            st.write(""); st.write("") 
            st.button("🔄", help="할인율 갱신", on_click=update_rate, key='btn_refresh_rate')

    row2_c1, row2_c2 = st.columns([1, 1])
    with row2_c1:
        c_list = list(CREDITORS.keys()) + ["🖊️ 직접입력"]
        def on_creditor_select_change():
            sel = st.session_state['tab3_creditor_select']
            if "유노스" in sel: st.session_state['cost_manual_제증명'] = "20,000"
            elif sel != "🖊️ 직접입력": st.session_state['cost_manual_제증명'] = "50,000"
            else: st.session_state['cost_manual_제증명'] = "0"
        st.selectbox("금융사", options=c_list, key='tab3_creditor_select', on_change=on_creditor_select_change)
    with row2_c2:
        st.text_input("채무자", key='tab3_debtor_input')
    
    st.text_area("물건지", key='tab3_estate_input', height=80)
    st.markdown("---")

    creditor_name = st.session_state['tab3_creditor_select']
    if creditor_name == "🖊️ 직접입력": creditor_name = st.session_state.get('input_creditor_name', '직접입력')
    
    calc_data = {
        '채권최고액': st.session_state['calc_amount_input'], 
        '필지수': st.session_state['input_parcels'],
        '채권할인율': st.session_state['input_rate'],
        '금융사': creditor_name,
        '채무자': st.session_state['tab3_debtor_input'],
        '물건지': st.session_state['tab3_estate_input'],
        '추가보수_val': st.session_state['add_fee_val'],
        '기타보수_val': st.session_state['etc_fee_val'],
        '할인금액': st.session_state['disc_fee_val']
    }
    final_data = calculate_all(calc_data)

    def make_row(label, value, key, on_change=None, disabled=False):
        c1, c2 = st.columns([1, 1.8])
        with c1: st.markdown(f"<div class='row-label'>{label}</div>", unsafe_allow_html=True)
        with c2:
            st.text_input(label, value=str(value), key=key, label_visibility="collapsed", disabled=disabled, on_change=on_change, args=(key,) if on_change else None)
    def fmt_cost(k): st.session_state[k] = format_number_with_comma(st.session_state[k])

    col_income, col_tax, col_payment = st.columns([1, 1, 1])
    with col_income:
        st.markdown("<div class='section-header income-header'>💰 보수액 (Income)</div>", unsafe_allow_html=True)
        with st.container(border=True):
            make_row("기본료", format_number_with_comma(final_data.get('기본료')), "disp_base", disabled=True)
            make_row("추가보수", st.session_state['add_fee_val'], "add_fee_val", fmt_cost)
            make_row("기타보수", st.session_state['etc_fee_val'], "etc_fee_val", fmt_cost)
            make_row("할인금액", st.session_state['disc_fee_val'], "disc_fee_val", fmt_cost)
            st.markdown("---")
            c1, c2 = st.columns([1, 1]); c1.markdown("**공급가액**"); c2.markdown(f"<div style='text-align:right; color:#28a745; font-weight:bold;'>{format_number_with_comma(final_data['공급가액'])} 원</div>", unsafe_allow_html=True)
            c1.markdown("**부가세**"); c2.markdown(f"<div style='text-align:right; color:#28a745;'>{format_number_with_comma(final_data['부가세'])} 원</div>", unsafe_allow_html=True)
            st.markdown("---")
            c1.markdown("#### 보수 총액"); c2.markdown(f"<div style='text-align:right; color:#28a745; font-size:1.2rem; font-weight:bold;'>{format_number_with_comma(final_data['보수총액'])} 원</div>", unsafe_allow_html=True)

    with col_tax:
        st.markdown("<div class='section-header tax-header'>🏛️ 공과금 (Tax)</div>", unsafe_allow_html=True)
        with st.container(border=True):
            make_row("등록면허세", format_number_with_comma(final_data['등록면허세']), "d_reg", disabled=True)
            make_row("지방교육세", format_number_with_comma(final_data['지방교육세']), "d_edu", disabled=True)
            make_row("증지대", format_number_with_comma(final_data['증지대']), "d_stamp", disabled=True)
            make_row("채권할인", format_number_with_comma(final_data['채권할인금액']), "d_bond", disabled=True)
            st.markdown("---")
            make_row("제증명", st.session_state['cost_manual_제증명'], "cost_manual_제증명", fmt_cost)
            make_row("교통비", st.session_state['cost_manual_교통비'], "cost_manual_교통비", fmt_cost)
            make_row("원인증서", st.session_state['cost_manual_원인증서'], "cost_manual_원인증서", fmt_cost)
            make_row("주소변경", st.session_state['cost_manual_주소변경'], "cost_manual_주소변경", disabled=True)
            make_row("확인서면", st.session_state['cost_manual_확인서면'], "cost_manual_확인서면", fmt_cost)
            make_row("선순위말소", st.session_state['cost_manual_선순위 말소'], "cost_manual_선순위 말소", fmt_cost)
            st.markdown("---")
            c1, c2 = st.columns([1, 1]); c1.markdown("#### 공과금 소계"); c2.markdown(f"<div style='text-align:right; color:#fd7e14; font-size:1.2rem; font-weight:bold;'>{format_number_with_comma(final_data['공과금 총액'])} 원</div>", unsafe_allow_html=True)

    with col_payment:
        st.markdown("<div class='section-header total-header'>🧾 결제 및 청구</div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### 총 청구금액")
            st.markdown(f"<div class='total-box'><div class='total-amount'>{format_number_with_comma(final_data['총 합계'])} 원</div></div>", unsafe_allow_html=True)
            st.markdown("---")
            if 'show_fee' not in st.session_state: st.session_state['show_fee'] = True
            st.checkbox("보수액 포함 표시", key='show_fee')
            
            def update_addr_cost():
                if st.session_state['use_address_change']:
                    sel_c = st.session_state.get('tab3_creditor_select', '')
                    unit_cost = 20000 if "유노스" in sel_c else 50000
                    cost = unit_cost * st.session_state['address_change_count']
                    st.session_state['cost_manual_주소변경'] = format_number_with_comma(cost)
                else: st.session_state['cost_manual_주소변경'] = "0"
            
            c1, c2 = st.columns([1, 1])
            with c1: st.checkbox("주소변경 포함", key='use_address_change', on_change=update_addr_cost)
            with c2: st.number_input("인원수", min_value=1, key='address_change_count', label_visibility="collapsed", on_change=update_addr_cost)
            
            if "유노스" in st.session_state.get('tab3_creditor_select', ''): st.caption("ℹ️ 유노스 적용: 주소변경 20,000원/인")
            else: st.caption("ℹ️ 일반 적용: 주소변경 50,000원/인")

    st.markdown("---")
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        if st.button("📄 비용내역 PDF 다운로드", disabled=not FPDF_OK, use_container_width=True):
            if FPDF_OK:
                pdf_data = {
                    'date_input': format_date_korean(st.session_state['input_date']),
                    'client': final_data,
                    'fee_items': {'기본료': final_data['기본료'], '추가보수': parse_int_input(st.session_state['add_fee_val']), '기타보수': parse_int_input(st.session_state['etc_fee_val']), '할인금액': parse_int_input(st.session_state['disc_fee_val'])},
                    'fee_totals': {'보수총액': final_data['보수총액']},
                    'cost_items': {'등록면허세': final_data['등록면허세'], '지방교육세': final_data['지방교육세'], '증지대': final_data['증지대'], '채권할인': final_data['채권할인금액'], '제증명': parse_int_input(st.session_state['cost_manual_제증명']), '교통비': parse_int_input(st.session_state['cost_manual_교통비']), '원인증서': parse_int_input(st.session_state['cost_manual_원인증서']), '주소변경': parse_int_input(st.session_state['cost_manual_주소변경']), '확인서면': parse_int_input(st.session_state['cost_manual_확인서면']), '선순위 말소': parse_int_input(st.session_state['cost_manual_선순위 말소'])},
                    'cost_totals': {'공과금 총액': final_data['공과금 총액']},
                    'cost_section_title': '2. 공과금' if st.session_state['show_fee'] else '1. 공과금',
                    'grand_total': final_data['총 합계']
                }
                pdf_bytes = PDFConverter(show_fee=st.session_state['show_fee']).output_pdf(pdf_data)
                st.download_button("⬇️ PDF 다운로드", pdf_bytes, f"비용내역_{final_data['채무자']}.pdf", "application/pdf", use_container_width=True)

    with d_col2:
        if st.button("🏦 영수증 Excel 다운로드", disabled=not EXCEL_OK, use_container_width=True):
            if EXCEL_OK:
                final_data['cost_items'] = {
                    '등록면허세': final_data['등록면허세'], '지방교육세': final_data['지방교육세'], '증지대': final_data['증지대'], '채권할인': final_data['채권할인금액'],
                    '제증명': parse_int_input(st.session_state['cost_manual_제증명']), '교통비': parse_int_input(st.session_state['cost_manual_교통비']),
                    '원인증서': parse_int_input(st.session_state['cost_manual_원인증서']), '주소변경': parse_int_input(st.session_state['cost_manual_주소변경']),
                    '선순위말소': parse_int_input(st.session_state['cost_manual_선순위 말소']), '확인서면': parse_int_input(st.session_state['cost_manual_확인서면'])
                }
                final_data['date_input'] = format_date_korean(st.session_state['input_date'])
                final_data['client'] = {'금융사': creditor_name, '채무자': final_data['채무자'], '물건지': final_data['물건지'], '채권최고액': final_data['채권최고액']}
                
                excel_buffer = create_receipt_excel(final_data, TEMPLATE_PATHS['영수증'])
                if excel_buffer:
                    st.download_button("⬇️ Excel 다운로드", excel_buffer, f"영수증_{final_data['채무자']}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# -----------------------------------------------------------------------------
# Tab 4: 말소 문서
# -----------------------------------------------------------------------------
with tab4:
    col_h4 = st.columns([5, 1])
    col_h4[0].markdown("### 🗑️ 말소 문서 작성")
    col_h4[1].button("🔄 전체 초기화", type="secondary", key="reset_all_t4", on_click=reset_all_data)
    st.markdown("---")

    def sync_malso_from_tab1():
        st.session_state['malso_obligor_corp'] = "" 
        st.session_state['malso_obligor_rep'] = ""
        st.session_state['malso_obligor_id'] = ""
        st.session_state['malso_obligor_addr'] = ""
        
        c_type = st.session_state.get('contract_type', '개인')
        owner = st.session_state.get('t1_owner_name', '')
        owner_addr = st.session_state.get('t1_owner_addr', '')
        st.session_state['malso_holder_name'] = owner
        st.session_state['malso_holder_addr'] = owner_addr
        st.session_state['malso_estate_detail'] = st.session_state.get('estate_text', '')

    if st.button("🔄 1탭 정보 가져오기", key="sync_malso"):
        sync_malso_from_tab1()

    m_cols = st.columns(3)
    types = ["근저당권", "질권", "전세권"]
    for i, t in enumerate(types):
        if m_cols[i].button(t, type="primary" if st.session_state['malso_type'] == t else "secondary", key=f"btn_m_{t}"):
            st.session_state['malso_type'] = t
            st.rerun()
    st.info(f"선택된 유형: **{st.session_state['malso_type']}말소**")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 1️⃣ 등기의무자 (금융사)")
        with st.container(border=True):
            st.text_input("법인명", key="malso_obligor_corp", placeholder="직접 입력")
            st.text_input("대표이사", key="malso_obligor_rep")
            st.text_input("법인등록번호", key="malso_obligor_id")
            st.text_area("주소", key="malso_obligor_addr", height=80)
    with c2:
        st.markdown("#### 2️⃣ 등기권리자 (소유자)")
        with st.container(border=True):
            st.text_input("성명", key="malso_holder_name")
            st.text_area("주소", key="malso_holder_addr", height=100)
    
    st.markdown("---")
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### 3️⃣ 원인 및 목적")
        st.date_input("등기원인일", key="malso_cause_date")
        st.text_input("등기원인", key="malso_cause")
        st.text_input("등기목적", value=f"{st.session_state['malso_type']}말소", disabled=True)
    with c4:
        st.markdown("#### 4️⃣ 말소할 등기")
        st.text_input("접수번호 등", key="malso_cancel_text", placeholder="202X년X월X일 접수 제1234호")

    st.markdown("#### 5️⃣ 부동산의 표시")
    st.text_area("부동산 상세", key="malso_estate_detail", height=150)
    
    st.markdown("---")
    st.markdown("### 📥 문서 생성 (PDF)")
    
    down_cols = st.columns(4)
    with down_cols[0]: st.button("해지증서 PDF", use_container_width=True)
    with down_cols[1]: st.button("위임장 PDF", use_container_width=True)
    with down_cols[2]: st.button("자필서명 PDF", use_container_width=True)
    with down_cols[3]: st.button("이관증명서 PDF", use_container_width=True)
    
    st.caption("※ PDF 생성 기능은 현재 UI 데모입니다.")

st.markdown("---")
st.markdown("""<div style='text-align: center; color: #6c757d; padding: 20px; background-color: white; border-radius: 10px; border: 2px solid #e1e8ed;'>
    <p style='margin: 0; font-size: 1rem; color: #00428B;'><strong>DG-Form 등기온 전자설정 자동화 시스템 | 법무법인 시화</strong></p>
    <p style='margin: 5px 0 0 0; font-size: 0.85rem; color: #6c757d;'>부동산 등기는 등기온</p></div>""", unsafe_allow_html=True)