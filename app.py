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
    page_icon="🏠",
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
    
    .stTabs [data-baseweb="tab-list"] {{ gap: 10px; background-color: #ffffff; padding: 10px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
    .stTabs [data-baseweb="tab"] {{ background-color: #f8f9fa; border-radius: 8px; padding: 10px 20px; font-weight: 600; color: #495057; border: 1px solid #dee2e6; }}
    .stTabs [aria-selected="true"] {{ background-color: #00428B; color: white; border-color: #00428B; }}

    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > select {{
        border-radius: 6px; border: 1px solid #ced4da; padding: 8px 12px; font-size: 0.95rem;
    }}
    .stTextInput > div > div > input:focus {{ border-color: #00428B; box-shadow: 0 0 0 0.2rem rgba(0, 66, 139, 0.15); }}

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

# (기존 코드 호환) 계약서/자필서명정보 생성 여부 체크에 사용
LIBS_OK = PDF_OK


# =============================================================================
# 2. 상수 및 데이터
# =============================================================================
TEMPLATE_FILENAMES = {
    "개인": "1.pdf",
    "3자담보": "2.pdf",
    "공동담보": "3.pdf",
    "자필": "자필서명정보 템플릿.pdf",
    "영수증": "영수증_템플릿.xlsx"
}

CREDITORS = {
    "(주)티플레인대부 대표이사 윤웅원": {"addr": "서울특별시 마포구 삼개로16, 2신관1층103호(도화동,근신빌딩)", "corp_num": "110111-7350161", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}},
    "(주)유노스프레스티지대부 사내이사 한은수": {"addr": "서울특별시 강남구 압구정로28길24, 5층 501호(신사동,디앤씨빌딩)", "corp_num": "110111-4138560", "fee": {"제증명": 20000, "교통비": 0, "원인증서": 0, "확인서면": 0, "선순위 말소": 0}},
    "(주)파트너스대부 사내이사 허성": {"addr": "부산광역시 부산진구 서면문화로 43, 2층(부전동)", "corp_num": "180111-1452175", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}},
    "(주)드림앤캐쉬대부 대표이사 김재섭": {"addr": "서울특별시 강남구 압구정로28길24, 6층 601호(신사동,디앤씨빌딩)", "corp_num": "110111-4176552", "fee": {"제증명": 20000, "교통비": 0, "원인증서": 0}},
    "(주)마젤란트러스트대부 대표이사 김병수": {"addr": "서울특별시 서초구 강남대로34길 7, 7층(양재동,이안빌딩)", "corp_num": "110111-6649979", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}},
    "(주)하이클래스대부 사내이사 성윤호": {"addr": "서울특별시 강남구 도곡로 188, 3층 4호(도곡동,도곡스퀘어)", "corp_num": "110111-0933512", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000}}
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

# PDF 생성 관련

def draw_fit_text(c, text, x, y, max_width, font_name='Korean', max_size=11, min_size=6):
    """주어진 폭(max_width)에 맞춰 폰트 크기를 줄여가며 텍스트를 출력"""
    if not text or not PDF_OK:
        return
    current_size = max_size
    try:
        text_width = pdfmetrics.stringWidth(text, font_name, current_size)
        while text_width > max_width and current_size > min_size:
            current_size -= 0.5
            text_width = pdfmetrics.stringWidth(text, font_name, current_size)
        c.setFont(font_name, current_size)
        c.drawString(x, y, text)
    except Exception:
        # 폰트 문제 등 발생 시 그냥 기본 출력 시도
        try:
            c.setFont('Helvetica', 10)
            c.drawString(x, y, str(text))
        except Exception:
            pass


# 비용내역 PDF 생성기 (fpdf2 필요)
if FPDF_OK:
    class PDFConverter(FPDF):
        def __init__(self, show_fee=True):
            super().__init__()
            self.show_fee = show_fee
            self.line_height = 6.5
            self.col_width1 = 150
            self.col_width2 = 30

            # 한글 폰트 세팅
            if FONT_PATH and os.path.exists(FONT_PATH):
                try:
                    self.add_font('Malgun', '', FONT_PATH, uni=True)
                    # Bold는 별도 파일이 없으면 동일 파일로 등록 (그래도 대부분 동작)
                    self.add_font('Malgun', 'B', FONT_PATH, uni=True)
                    self.set_font('Malgun', '', 11)
                except Exception:
                    self.set_font('Arial', '', 11)
            else:
                self.set_font('Arial', '', 11)

        def draw_labelframe_box(self, title, content_func):
            self.set_font(self.font_family, 'B', 11)
            start_y = self.get_y()
            start_x = self.l_margin
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
            self.add_page()
            self.set_font(self.font_family, 'B', 20)
            self.cell(0, 12, "근저당권설정 비용내역", ln=True, align="C")
            self.ln(2)

            self.set_font(self.font_family, '', 9)
            self.cell(0, 5, f"작성일: {data['date_input']}", ln=True, align="R")
            self.ln(2)

            self.set_font(self.font_family, '', 10)
            client = data['client']
            self.cell(95, self.line_height, f"채권최고액: {client['채권최고액']} 원")
            self.cell(0, self.line_height, f"|  필지수: {client['필지수']}", ln=True)
            if client.get('금융사'):
                self.cell(0, self.line_height, f"금  융  사: {client['금융사']}", ln=1)
            if client.get('채무자'):
                self.cell(0, self.line_height, f"채  무  자: {client['채무자']}", ln=1)
            if client.get('물건지'):
                self.multi_cell(0, self.line_height, f"물  건  지: {client['물건지']}")

            self.ln(3)

            if self.show_fee:
                def fee_content():
                    self.set_font(self.font_family, '', 10)
                    items = data['fee_items']

                    # 키 호환 (추가보수/기타보수 vs *_val)
                    add_key = data.get('labels', {}).get('추가보수_label', '추가보수')
                    etc_key = data.get('labels', {}).get('기타보수_label', '기타보수')
                    add_val = items.get(add_key, items.get('추가보수_val', 0))
                    etc_val = items.get(etc_key, items.get('기타보수_val', 0))

                    subtotal = items.get('기본료', 0) + add_val + etc_val

                    self.set_x(self.l_margin + 5)
                    self.cell(self.col_width1, self.line_height, "보수액 소계")
                    self.cell(self.col_width2, self.line_height, f"{subtotal:,} 원", ln=1, align="R")

                    self.set_x(self.l_margin + 5)
                    self.cell(self.col_width1, self.line_height, "할인금액")
                    self.cell(self.col_width2, self.line_height, f"{items.get('할인금액', 0):,} 원", ln=1, align="R")

                    self.ln(1)
                    self.line(self.get_x() + 5, self.get_y(), self.w - self.r_margin - 5, self.get_y())
                    self.ln(1)

                    self.set_font(self.font_family, 'B', 10)
                    self.set_x(self.l_margin + 5)
                    self.cell(self.col_width1, self.line_height, "보수 소계")
                    self.cell(self.col_width2, self.line_height, f"{data['fee_totals']['보수총액']:,} 원", ln=1, align="R")

                self.draw_labelframe_box("1. 보수액", fee_content)
                self.ln(5)

            def costs_content():
                self.set_font(self.font_family, '', 10)
                items = data['cost_items']
                for name, val in items.items():
                    if val != 0:
                        self.set_x(self.l_margin + 5)
                        self.cell(self.col_width1, self.line_height, name)
                        self.cell(self.col_width2, self.line_height, f"{int(val):,} 원", ln=1, align="R")

                self.ln(1)
                self.line(self.get_x() + 5, self.get_y(), self.w - self.r_margin - 5, self.get_y())
                self.ln(1)

                self.set_font(self.font_family, 'B', 10)
                self.set_x(self.l_margin + 5)
                self.cell(self.col_width1, self.line_height, "공과금소계")
                self.cell(self.col_width2, self.line_height, f"{data['cost_totals']['공과금 총액']:,} 원", ln=1, align="R")

            self.draw_labelframe_box(data['cost_section_title'], costs_content)
            self.ln(5)

            self.set_font(self.font_family, 'B', 12)
            self.cell(self.col_width1 - 10, 10, "등기비용 합계")
            self.cell(self.col_width2 + 10, 10, f"{data['grand_total']:,} 원", ln=True, align="R")
            self.ln(5)

            def notes_content():
                self.set_font(self.font_family, '', 10)
                self.set_x(self.l_margin + 5)
                self.cell(0, self.line_height, "• 원활한 확인을 위해 입금자는 소유자명(또는 채무자명)으로 기재해 주세요.", ln=1)
                self.set_x(self.l_margin + 5)
                self.cell(0, self.line_height, "• 입금 완료 후, 메시지를 남겨주시면 더욱 빠르게 처리됩니다.", ln=1)
                self.set_x(self.l_margin + 5)
                self.cell(0, self.line_height, "• 업무는 입금이 확인된 후에 진행됩니다.", ln=1)

            self.draw_labelframe_box("안내사항", notes_content)
            self.ln(5)

            def bank_content():
                self.set_font(self.font_family, '', 10)
                self.set_x(self.l_margin + 5)
                self.cell(0, self.line_height, "• 신한은행 100-035-852291", ln=1)
                self.set_x(self.l_margin + 5)
                self.cell(0, self.line_height, "• 예금주 : 법무법인 시화", ln=1)

            self.draw_labelframe_box("입금 계좌 정보", bank_content)

            # BytesIO로 반환
            from io import BytesIO
            pdf_buffer = BytesIO()
            pdf_bytes = self.output(dest='S')
            if isinstance(pdf_bytes, str):
                pdf_buffer.write(pdf_bytes.encode('latin-1'))
            else:
                pdf_buffer.write(pdf_bytes)
            pdf_buffer.seek(0)
            return pdf_buffer
else:
    PDFConverter = None
def create_overlay_pdf(data, font_path):
    packet = BytesIO(); c = canvas.Canvas(packet, pagesize=A4); width, height = A4
    try: 
        pdfmetrics.registerFont(TTFont('Korean', font_path)); font_name = 'Korean'
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
    output_buffer = BytesIO() 
    for page_num in range(min(len(template_pdf.pages), len(overlay_pdf.pages))):
        template_page = template_pdf.pages[page_num]; overlay_page = overlay_pdf.pages[page_num]
        template_page.merge_page(overlay_page); writer.add_page(template_page)
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer

def make_signature_pdf(template_path, data, font_path=FONT_PATH):
    # reportlab/PyPDF2가 없으면 안내
    if not PDF_OK:
        raise RuntimeError("PDF 라이브러리(reportlab/PyPDF2)가 설치되지 않았습니다.")

    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4

    # 폰트 등록 (한글)
    try:
        if font_path and os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Korean', font_path))
            font_name = 'Korean'
        else:
            font_name = 'Helvetica'
    except Exception:
        font_name = 'Helvetica'

    c.setFont(font_name, 10)
    estate_x = 150
    estate_y = height - 170
    line_h = 14

    if data.get("estate_text"):
        for i, line in enumerate(str(data["estate_text"]).split("\n")[:17]):
            c.drawString(estate_x, estate_y - (i * line_h), line)

    if data.get("debtor_name"):
        c.drawString(250, 322, str(data["debtor_name"]))
    if data.get("debtor_rrn"):
        c.drawString(250, 298, str(data["debtor_rrn"]))
    if data.get("owner_name"):
        c.drawString(400, 322, str(data["owner_name"]))
    if data.get("owner_rrn"):
        c.drawString(400, 298, str(data["owner_rrn"]))

    if data.get("date"):
        c.setFont(font_name, 11)
        text_date = str(data["date"])
        tw = c.stringWidth(text_date, font_name, 11)
        c.drawString((width - tw) / 2, 150, text_date)

    c.showPage()
    c.save()
    packet.seek(0)

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

# =============================================================================
# 5. Streamlit UI 및 상태 관리
# =============================================================================

if 'add_fee_val' not in st.session_state: st.session_state['add_fee_val'] = "0"
if 'etc_fee_val' not in st.session_state: st.session_state['etc_fee_val'] = "0"
if 'disc_fee_val' not in st.session_state: st.session_state['disc_fee_val'] = "0"
if 'cost_manual_제증명' not in st.session_state: st.session_state['cost_manual_제증명'] = "0"
if 'cost_manual_교통비' not in st.session_state: st.session_state['cost_manual_교통비'] = "0"
if 'cost_manual_원인증서' not in st.session_state: st.session_state['cost_manual_원인증서'] = "0"
if 'cost_manual_주소변경' not in st.session_state: st.session_state['cost_manual_주소변경'] = "0"
if 'cost_manual_확인서면' not in st.session_state: st.session_state['cost_manual_확인서면'] = "0"
if 'cost_manual_선순위 말소' not in st.session_state: st.session_state['cost_manual_선순위 말소'] = "0"
if 'use_address_change' not in st.session_state: st.session_state['use_address_change'] = False
if 'address_change_count' not in st.session_state: st.session_state['address_change_count'] = 1

# Streamlit 상태 초기화
if 'calc_data' not in st.session_state:
    st.session_state['calc_data'] = {}
    st.session_state['show_fee'] = True
    st.session_state['input_amount'] = ""
    st.session_state['amount_raw_input'] = ""
    st.session_state['input_parcels'] = 1
    st.session_state['input_rate'] = f"{get_rate()*100:.5f}"
    st.session_state['input_debtor'] = ""
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

# 3탭 수기 입력값 초기 상태 설정
manual_keys = ["cost_manual_제증명", "cost_manual_교통비", "cost_manual_원인증서", "cost_manual_확인서면", "cost_manual_선순위 말소"]
for key in manual_keys:
    if key not in st.session_state:
        first_creditor = list(CREDITORS.keys())[0]
        fees = CREDITORS[first_creditor]["fee"]
        if "제증명" in key: val = fees.get("제증명", 50000)
        elif "교통비" in key: val = fees.get("교통비", 100000)
        elif "원인증서" in key: val = fees.get("원인증서", 50000)
        else: val = 0
        st.session_state[key] = format_number_with_comma(str(val))

def parse_int_input(text_input):
    try:
        if isinstance(text_input, int): return text_input
        return int(remove_commas(text_input or "0"))
    except ValueError:
        return 0

def handle_creditor_change():
    creditor_key = st.session_state['t1_creditor_select']
    if creditor_key == "🖊️ 직접입력":
        st.session_state['cost_manual_제증명'] = "0"
        st.session_state['cost_manual_교통비'] = "0"
        st.session_state['cost_manual_원인증서'] = "0"
        st.session_state['cost_manual_주소변경'] = "0"
        st.session_state['cost_manual_확인서면'] = "0"
        st.session_state['cost_manual_선순위 말소'] = "0"
        st.session_state['input_creditor_name'] = ""
        st.session_state['input_creditor_corp_num'] = ""
        st.session_state['input_creditor_addr'] = ""
    else:
        default_fees = CREDITORS.get(creditor_key, {}).get("fee", {"제증명": 50000, "교통비": 100000, "원인증서": 50000})
        st.session_state['cost_manual_제증명'] = format_number_with_comma(str(default_fees.get("제증명", 0)))
        st.session_state['cost_manual_교통비'] = format_number_with_comma(str(default_fees.get("교통비", 0)))
        st.session_state['cost_manual_원인증서'] = format_number_with_comma(str(default_fees.get("원인증서", 0)))
        st.session_state['cost_manual_주소변경'] = "0"
        st.session_state['cost_manual_확인서면'] = format_number_with_comma(str(default_fees.get("확인서면", 0)))
        st.session_state['cost_manual_선순위 말소'] = format_number_with_comma(str(default_fees.get("선순위 말소", 0)))
    st.session_state.calc_data['creditor_key_check'] = creditor_key

MANUAL_COST_NAMES = ["제증명", "교통비", "원인증서", "주소변경", "확인서면", "선순위 말소"]

def calculate_all(data):
    amount = parse_int_input(data.get('채권최고액')) 
    parcels = parse_int_input(data.get('필지수'))
    try: rate = float(remove_commas(data.get('채권할인율', '0'))) / 100
    except ValueError: rate = 0 
    
    # 1. 기본료 계산
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
    
    # 2. 공과금 (주소변경 포함)
    use_addr_change = st.session_state.get('use_address_change', False)
    addr_count = st.session_state.get('address_change_count', 1)
    
    addr_reg = 0; addr_edu = 0; addr_jeungji = 0
    if use_addr_change and addr_count > 0:
        addr_reg = 6000 * addr_count
        addr_edu = 1200 * addr_count
        addr_jeungji = 3000 * addr_count
        
        # [중요] calculate_all 함수에서는 "계산"만 담당하고
        # UI 입력값(st.session_state)을 여기서 직접 바꾸지 않습니다.
        # 입력값 변경은 'on_change' 콜백에서 처리합니다.
    
    # 등록면허세, 지방교육세 등 계산
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
    
    # 수기 입력 항목 합산 (위에서 자동 업데이트된 '주소변경' 포함)
    for k in MANUAL_COST_NAMES:
        cost_total += parse_int_input(st.session_state.get('cost_manual_' + k, 0)) # session_state에서 직접 가져옴
    
    data['공과금 총액'] = cost_total
    data['총 합계'] = fee_total + cost_total
    return data

# =============================================================================
# UI 구현
# =============================================================================

tab1, tab2, tab3 = st.tabs(["📄 근저당권설정 계약서", "✍️ 자필서명정보", "🧾 비용 계산 및 영수증"])

# Tab 1: 근저당권 설정 (입력)
with tab1:
    col_header = st.columns([5, 1])
    col_header[0].markdown("### 📝 근저당권설정 계약서 작성")
    if col_header[1].button("🔄 초기화", type="secondary", key="reset_tab1"):
        st.session_state['input_date'] = datetime.now().date()
        st.session_state['input_creditor'] = list(CREDITORS.keys())[0]
        st.session_state['input_debtor'] = ""
        st.session_state['input_debtor_addr'] = ""
        st.session_state['input_owner'] = ""
        st.session_state['input_owner_addr'] = ""
        st.session_state['contract_type'] = "개인"
        st.session_state['guarantee'] = "한정근담보"
        st.session_state['input_amount'] = ""
        st.session_state['amount_raw_input'] = "" 
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
        
        is_direct_input = (selected_creditor == "🖊️ 직접입력")
        if is_direct_input:
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

        st.session_state['input_debtor'] = st.text_input("채무자 성명", value=st.session_state.get('input_debtor'), key='t1_debtor_name')
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
                debtor_name = st.session_state['input_debtor'] if st.session_state['input_debtor'] else "미지정"
                if st.session_state['input_creditor'] == "🖊️ 직접입력":
                    creditor_name_for_pdf = st.session_state.get('input_creditor_name', '')
                    creditor_addr_for_pdf = st.session_state.get('input_creditor_addr', '')
                else:
                    creditor_name_for_pdf = st.session_state['input_creditor']
                    creditor_addr_for_pdf = creditor_info.get('addr', '')
                data = {
                    "date": format_date_korean(st.session_state['input_date']), "creditor_name": creditor_name_for_pdf, "creditor_addr": creditor_addr_for_pdf,
                    "debtor_name": st.session_state['input_debtor'], "debtor_addr": st.session_state['input_debtor_addr'],
                    "owner_name": st.session_state['input_owner'], "owner_addr": st.session_state['input_owner_addr'],
                    "guarantee_type": st.session_state['guarantee'], "claim_amount": convert_multiple_amounts_to_korean(remove_commas(st.session_state['input_amount'])),
                    "estate_list": st.session_state['estate_text'].strip().split("\n"), "contract_type": st.session_state['contract_type']
                }
                try:
                    pdf_buffer = make_pdf(selected_template_path, data)
                    st.download_button(label="⬇️ 다운로드", data=pdf_buffer, file_name=f"근저당권설정_{debtor_name}.pdf", mime="application/pdf", use_container_width=True)
                    st.success("✅ PDF 생성완료!")
                except Exception as e: st.error(f"오류: {e}")

# Tab 2: 자필서명 정보
with tab2:
    col_header2 = st.columns([5, 1])
    col_header2[0].markdown("### ✍️ 자필서명정보 작성")
    if col_header2[1].button("🔄 초기화", type="secondary", key="reset_tab2"):
        st.session_state['sig_debtor'] = ""; st.session_state['input_debtor_rrn'] = ""
        st.session_state['sig_owner'] = ""; st.session_state['input_owner_rrn'] = ""
        st.rerun()
    st.markdown("---")
    col_l2, col_r2 = st.columns(2)
    with col_l2:
        st.markdown("#### 의무자 정보 입력")
        st.text_input("작성일자", value=format_date_korean(st.session_state.get('input_date')), key='sig_date_input')
        st.session_state['sig_debtor'] = st.text_input("설정자(단독/채무자)", value=st.session_state.get('input_debtor'), key='sig_debtor_input')
        st.session_state['input_debtor_rrn'] = st.text_input("주민등록번호(채무자)", value=st.session_state.get('input_debtor_rrn'), key='sig_debtor_rrn_input')
        st.session_state['sig_owner'] = st.text_input("설정자(공동/물상보증인)", value=st.session_state.get('input_owner'), key='sig_owner_input')
        st.session_state['input_owner_rrn'] = st.text_input("주민등록번호(설정자)", value=st.session_state.get('input_owner_rrn'), key='sig_owner_rrn_input')
    with col_r2:
        st.markdown("#### 🏠 부동산의 표시 (확인용)")
        st.session_state['sig_estate_text'] = st.text_area("부동산 표시 내용", value=st.session_state.get('estate_text'), height=350, key='sig_estate_area')
        sig_template_path = st.session_state['template_status'].get("자필")
        if sig_template_path: is_disabled = False
        else: st.warning("⚠️ 템플릿 파일 없음"); is_disabled = True
        if st.button("📄 자필서명정보 PDF 생성", key="generate_sig_pdf", disabled=is_disabled or not LIBS_OK, use_container_width=True):
            if not LIBS_OK: st.error("PDF 라이브러리 미설치")
            else:
                data = {
                    "date": format_date_korean(st.session_state['input_date']), "debtor_name": st.session_state['sig_debtor'], 
                    "debtor_rrn": st.session_state['input_debtor_rrn'], "owner_name": st.session_state['sig_owner'], 
                    "owner_rrn": st.session_state['input_owner_rrn'], "estate_text": st.session_state['sig_estate_text']
                }
                try:
                    pdf_buffer = make_signature_pdf(sig_template_path, data)
                    st.download_button(label="⬇️ PDF 다운로드", data=pdf_buffer, file_name=f"자필서명정보_{data['debtor_name']}.pdf", mime="application/pdf", use_container_width=True)
                    st.success("✅ 생성 완료!")
                except Exception as e: st.error(f"오류: {e}")

# Tab 3: 비용 계산 및 영수증 (완전 개편)
with tab3:
    col_header3 = st.columns([5, 1])
    col_header3[0].markdown("### 🧾 등기비용 계산기")
    if col_header3[1].button("🔄 초기화", type="secondary", key="reset_tab3"):
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
    # [수정됨] 0. 1탭 데이터 동기화 (Sync Data)
    # 반드시 위젯을 그리기 전에 값을 맞춰줘야 합니다.
    # =========================================================
    if 'input_amount' in st.session_state and st.session_state['input_amount']:
        # 만약 1탭 값(input_amount)과 3탭 값(calc_amount_input)이 다르면, 1탭 값으로 덮어씀
        if st.session_state.get('calc_amount_input') != st.session_state['input_amount']:
            st.session_state['calc_amount_input'] = st.session_state['input_amount']
    
    # =========================================================
    # 1. 통합 기본 정보 섹션 (1탭 데이터 연동)
    # =========================================================
    creditor_display = st.session_state.get('input_creditor', '')
    if creditor_display == "🖊️ 직접입력": creditor_display = st.session_state.get('input_creditor_name', '직접입력')
    
    estate_display = extract_address_from_estate(st.session_state.get('estate_text') or "")
    if st.session_state.get('input_collateral_addr'): estate_display = st.session_state.get('input_collateral_addr')

    # 상단 3단 배열 (채권최고액, 필지수, 할인율)
    row1_c1, row1_c2, row1_c3, row1_c4 = st.columns([2, 0.5, 1, 1.2]) 
    
    with row1_c1:
        # [수정] 3탭에서도 즉시 콤마 적용되도록 on_change 추가
        def on_tab3_amount_change():
            val = st.session_state.get('calc_amount_input', '')
            formatted = format_number_with_comma(val)
            st.session_state['calc_amount_input'] = formatted
            st.session_state['input_amount'] = formatted
        
        st.text_input("채권최고액", value=st.session_state.get('input_amount'), key='calc_amount_input', on_change=on_tab3_amount_change)

    with row1_c3:
        # 필지수 처리
        parcels_val = st.session_state.get('input_parcels', 1)
        new_parcels = st.number_input("필지수", min_value=1, value=int(parcels_val), key='calc_parcels_input')
        st.session_state['input_parcels'] = new_parcels

    with row1_c4:
        # 할인율 처리
        col_rate, col_btn = st.columns([2, 0.5])
        rate_val = st.session_state.get('input_rate', '12.00000')
        new_rate = col_rate.text_input("할인율(%)", value=rate_val, key='calc_rate_input')
        if col_btn.button("🔄", help="갱신"):
            st.session_state['input_rate'] = f"{get_rate()*100:.5f}"
            st.rerun()
        st.session_state['input_rate'] = new_rate

    # 하단 2단 배열 (금융사, 물건지)
    row2_c1, row2_c2 = st.columns([1, 1])
    with row2_c1:
        st.text_input("금융사", value=creditor_display, key="calc_creditor_view", disabled=True)
    with row2_c2:
        st.text_input("채무자", value=st.session_state.get('input_debtor'), key="calc_debtor_view", disabled=True)
        
    st.text_input("물건지", value=estate_display, key="calc_estate_view", disabled=True)
    st.markdown("---")

    # =========================================================
    # 2. 계산 로직 수행
    # =========================================================
    def format_cost_input(key):
        val = st.session_state[key]
        st.session_state[key] = format_number_with_comma(val)

    creditor_for_calc = creditor_display
    calc_input_values = {
        '추가보수_val': st.session_state.get('add_fee_val', "0"),
        '기타보수_val': st.session_state.get('etc_fee_val', "0"),
        '할인금액': st.session_state.get('disc_fee_val', "0"),
    }
    
    calc_input_data = {
        '채권최고액': st.session_state['input_amount'], # 콤마 적용된 최신값 전달
        '필지수': st.session_state['input_parcels'],
        '채권할인율': st.session_state['input_rate'],
        '금융사': creditor_for_calc,
        '채무자': st.session_state['input_debtor'],
        '물건지': estate_display,
        '추가보수_label': "추가보수", 
        '기타보수_label': "기타보수",
    }
    calc_input_data.update(calc_input_values)
    final_data = calculate_all(calc_input_data)
    st.session_state['calc_data'] = final_data 

    # =========================================================
    # 3. 3단 레이아웃 (보수액 / 공과금 / 결제)
    # =========================================================
    
    def make_row(label, value, key, on_change=None, disabled=False):
        c1, c2 = st.columns([1, 1.8])
        with c1: st.markdown(f"<div class='row-label'>{label}</div>", unsafe_allow_html=True)
        with c2:
            if on_change:
                st.text_input(label, value=str(value), key=key, on_change=on_change, args=(key,), label_visibility="collapsed", disabled=disabled)
            else:
                st.text_input(label, value=str(value), key=key, label_visibility="collapsed", disabled=disabled)

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
            c_label.markdown("**공급가액**")
            c_val.markdown(f"<div style='text-align:right; color:#28a745; font-weight:bold;'>{format_number_with_comma(final_data.get('공급가액'))} 원</div>", unsafe_allow_html=True)
            c_label.markdown("**부가세**")
            c_val.markdown(f"<div style='text-align:right; color:#28a745;'>{format_number_with_comma(final_data.get('부가세'))} 원</div>", unsafe_allow_html=True)
            st.markdown("---")
            c_label.markdown("#### 보수 총액")
            c_val.markdown(f"<div style='text-align:right; color:#28a745; font-size:1.2rem; font-weight:bold;'>{format_number_with_comma(final_data.get('보수총액'))} 원</div>", unsafe_allow_html=True)

    # [2] 공과금 (Tax)
    with col_tax:
        st.markdown("<div class='section-header tax-header'>🏛️ 공과금 (Tax)</div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.caption("[자동 계산]")
            make_row("등록면허세", format_number_with_comma(final_data.get("등록면허세")), "disp_reg", disabled=True)
            make_row("지방교육세", format_number_with_comma(final_data.get("지방교육세")), "disp_edu", disabled=True)
            make_row("증지대", format_number_with_comma(final_data.get("증지대")), "disp_stamp", disabled=True)
            make_row("채권할인", format_number_with_comma(final_data.get("채권할인금액")), "disp_bond", disabled=True)
            
            st.markdown("---")
            st.caption("[수기 입력]")
            make_row("제증명", st.session_state['cost_manual_제증명'], "cost_manual_제증명", format_cost_input)
            make_row("교통비", st.session_state['cost_manual_교통비'], "cost_manual_교통비", format_cost_input)
            make_row("원인증서", st.session_state['cost_manual_원인증서'], "cost_manual_원인증서", format_cost_input)
            make_row("주소변경", st.session_state['cost_manual_주소변경'], "cost_manual_주소변경", format_cost_input)
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
            st.markdown(f"""
            <div class='total-box'>
                <div class='total-amount'>{format_number_with_comma(final_data.get('총 합계'))} 원</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            def toggle_show_fee():
                st.session_state['show_fee'] = st.session_state['show_fee_checkbox']
            
            st.checkbox("보수액 포함 표시", value=st.session_state['show_fee'], key='show_fee_checkbox', on_change=toggle_show_fee)
            
            st.markdown("#### ➕ 주소변경 추가")
            st.caption("체크 시 공과금 + 수기비용 자동 합산")
            
            # [수정됨] 주소변경 체크 시 즉시 반영되는 콜백 함수
            def update_address_cost():
                # 체크 상태 확인
                if st.session_state.get('use_address_change', False):
                    # 금융사 이름 가져오기
                    cur_creditor = st.session_state.get('input_creditor', '')
                    if cur_creditor == "🖊️ 직접입력":
                        cur_creditor = st.session_state.get('input_creditor_name', '')
                    
                    count = st.session_state.get('address_change_count', 1)
                    # 유노스/드림앤캐쉬: 20,000 / 그외: 50,000
                    if "유노스" in cur_creditor or "드림" in cur_creditor:
                        fee = 20000 * count
                    else:
                        fee = 50000 * count
                    st.session_state['cost_manual_주소변경'] = format_number_with_comma(fee)
                else:
                    # 체크 해제 시 0원으로 초기화
                    st.session_state['cost_manual_주소변경'] = "0"

            cp1, cp2 = st.columns([1, 1])
            with cp1:
                # on_change에 update_address_cost 함수 연결
                st.checkbox("주소변경 포함", key='use_address_change', on_change=update_address_cost)
            with cp2:
                # 인원수가 바뀌어도 비용 다시 계산
                st.number_input("인원수", min_value=1, value=1, key='address_change_count', label_visibility="collapsed", on_change=update_address_cost)
            
            st.markdown("---")
            st.info("""
            **ℹ️ 참고 기준 (주소변경비용)**
            * 유노스/드림앤캐쉬: 20,000원/인
            * 기타 금융사: 50,000원/인
            * (체크 시 수기입력란에 자동반영)
            """)

    st.markdown("---")
    d_col1, d_col2 = st.columns(2)
    if d_col1.button("📄 비용내역 PDF 다운로드", use_container_width=True):
        if True:
            creditor_for_pdf = creditor_display
            if not FPDF_OK or PDFConverter is None:
                st.error("비용내역 PDF 생성 라이브러리(fpdf2)가 설치되지 않았습니다.")
            else:
                data_for_pdf = {
                    "date_input": format_date_korean(st.session_state['input_date']),
                    "client": {
                        "채권최고액": format_number_with_comma(final_data['채권최고액']),
                        "필지수": final_data['필지수'],
                        "금융사": creditor_for_pdf,
                        "채무자": final_data['채무자'],
                        "물건지": final_data['물건지'],
                    },
                    "fee_items": {
                        "기본료": parse_int_input(final_data.get('기본료')),
                        "추가보수": parse_int_input(final_data.get('추가보수_val')),
                        "기타보수": parse_int_input(final_data.get('기타보수_val')),
                        "할인금액": parse_int_input(final_data.get('할인금액')),
                    },
                    "fee_totals": {
                        "공급가액": final_data['공급가액'],
                        "부가세": final_data['부가세'],
                        "보수총액": final_data['보수총액'],
                    },
                    "cost_items": {
                        "등록면허세": parse_int_input(final_data.get('등록면허세')),
                        "지방교육세": parse_int_input(final_data.get('지방교육세')),
                        "증지대": parse_int_input(final_data.get('증지대')),
                        "채권할인금액": parse_int_input(final_data.get('채권할인금액')),
                        "제증명": parse_int_input(st.session_state.get('cost_manual_제증명', 0)),
                        "교통비": parse_int_input(st.session_state.get('cost_manual_교통비', 0)),
                        "원인증서": parse_int_input(st.session_state.get('cost_manual_원인증서', 0)),
                        "주소변경": parse_int_input(st.session_state.get('cost_manual_주소변경', 0)),
                        "확인서면": parse_int_input(st.session_state.get('cost_manual_확인서면', 0)),
                        "선순위 말소": parse_int_input(st.session_state.get('cost_manual_선순위 말소', 0)),
                    },
                    "cost_totals": {"공과금 총액": final_data['공과금 총액']},
                    "cost_section_title": '2. 공과금' if st.session_state['show_fee'] else '1. 공과금',
                    "grand_total": final_data['총 합계'],
                    "labels": {"추가보수_label": "추가보수", "기타보수_label": "기타보수"},
                }

                try:
                    pdf = PDFConverter(show_fee=st.session_state['show_fee'])
                    pdf_buffer = pdf.output_pdf(data_for_pdf)
                    d_col1.download_button(
                        label="⬇️ PDF 저장",
                        data=pdf_buffer,
                        file_name=f"비용내역_{final_data['채무자']}.pdf",
                        mime="application/pdf",
                        key="dl_pdf_final",
                    )
                except Exception as e:
                    st.error(f"오류: {e}")
        

    if d_col2.button("🏦 영수증 Excel 다운로드", disabled=not EXCEL_OK, use_container_width=True):
        if EXCEL_OK and st.session_state['template_status'].get("영수증"):
            try:
                wb = openpyxl.load_workbook(st.session_state['template_status'].get("영수증"))
                ws = wb.active
                def safe_set(ref, val):
                    try: 
                        c=ws[ref]
                        if isinstance(c, MergedCell): ws[c.coordinate].value=val 
                        else: c.value=val
                    except: pass
                
                date_str = format_date_korean(st.session_state['input_date'])
                claim_amt = parse_int_input(final_data["채권최고액"])
                
                # 사무소용
                safe_set('A24', date_str); safe_set('M5', claim_amt); safe_set('E7', final_data['물건지'])
                safe_set('E11', final_data["공급가액"]); safe_set('E20', final_data["부가세"])
                safe_set('E21', final_data["보수총액"]); safe_set('E22', final_data["총 합계"])
                
                # 고객용
                safe_set('U24', date_str); safe_set('V4', final_data['채무자']); safe_set('AG5', claim_amt); safe_set('Y7', final_data['물건지'])
                safe_set('AH11', final_data["등록면허세"]); safe_set('AH12', final_data["지방교육세"])
                safe_set('AH13', final_data["증지대"]); safe_set('AH14', final_data["채권할인금액"])
                safe_set('AH15', parse_int_input(st.session_state['cost_manual_제증명'])); safe_set('AH16', parse_int_input(st.session_state['cost_manual_원인증서']))
                safe_set('AH17', parse_int_input(st.session_state['cost_manual_주소변경'])); safe_set('AH18', parse_int_input(st.session_state['cost_manual_선순위 말소']))
                safe_set('AH19', parse_int_input(st.session_state['cost_manual_교통비'])); safe_set('AH21', final_data["공과금 총액"]); safe_set('Y22', final_data["공과금 총액"])

                firm_info = ["서울특별시 서초구 법무법인길 6-9, 301호(서초동,법조타운)", "법무법인시화", "214-887-97287", "1833-5482", "신한은행 100-035-852291 예금주: 법무법인 시화"]
                for i, txt in enumerate(firm_info):
                    safe_set(f'D{25+i}', txt); safe_set(f'X{25+i}', txt)

                excel_buffer = BytesIO(); wb.save(excel_buffer); excel_buffer.seek(0)
                d_col2.download_button(label="⬇️ Excel 저장", data=excel_buffer, file_name=f"영수증_{final_data['채무자']}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_excel_final")
            except Exception as e: st.error(f"오류: {e}")

st.markdown("---")
st.markdown("""<div style='text-align: center; color: #6c757d; padding: 20px; background-color: white; border-radius: 10px; border: 2px solid #e1e8ed;'>
    <p style='margin: 0; font-size: 1rem; color: #00428B;'><strong>DG-Form 등기온 전자설정 자동화 시스템 | 법무법인 시화</strong></p>
    <p style='margin: 5px 0 0 0; font-size: 0.85rem; color: #6c757d;'>부동산 등기는 등기온</p></div>""", unsafe_allow_html=True)