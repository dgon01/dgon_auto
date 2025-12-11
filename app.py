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

# 로고 이미지를 base64로 인코딩하는 함수
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

# 로고 이미지 경로
LOGO_PATH = os.path.join(APP_ROOT, "KakaoTalk_20250331_180755414_01.jpg")
logo_base64 = get_base64_image(LOGO_PATH)

# 커스텀 CSS 스타일 (DG-ON 브랜드 컬러 적용)
st.markdown(f"""
<style>
    /* 메인 컨테이너 배경 */
    .main {{
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }}
    
    /* 헤더 로고 및 타이틀 */
    .header-container {{
        background: linear-gradient(135deg, #003d82 0%, #0066cc 100%);
        padding: 20px 40px;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0, 61, 130, 0.3);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    
    .logo-title-container {{
        display: flex;
        align-items: center;
        gap: 20px;
    }}
    
    .header-logo {{
        width: 120px;
        height: auto;
        background: white;
        padding: 10px;
        border-radius: 10px;
    }}
    
    .header-title {{
        color: white;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }}
    
    .header-subtitle {{
        color: #ffd700;
        font-size: 1.2rem;
        font-weight: 500;
        margin: 0;
    }}
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: #f0f4f8;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        color: #003d82;
        border: 2px solid transparent;
        transition: all 0.3s;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: #e1e8ed;
        transform: translateY(-2px);
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #003d82 0%, #0066cc 100%);
        color: white;
        border-color: #ffd700;
    }}
    
    /* 버튼 스타일 */
    .stButton > button {{
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s;
        border: 2px solid #0066cc;
        background-color: white;
        color: #003d82;
    }}
    
    .stButton > button:hover {{
        background: linear-gradient(135deg, #003d82 0%, #0066cc 100%);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 102, 204, 0.4);
    }}
    
    /* 다운로드 버튼 */
    .stDownloadButton > button {{
        background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        color: #003d82;
        border: none;
        font-weight: 700;
        border-radius: 10px;
    }}
    
    .stDownloadButton > button:hover {{
        background: linear-gradient(135deg, #ffed4e 0%, #ffd700 100%);
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255, 215, 0, 0.5);
    }}
    
    /* 입력 필드 스타일 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {{
        border-radius: 10px;
        border: 2px solid #e1e8ed;
        background-color: white;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {{
        border-color: #0066cc;
        box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
    }}
    
    /* 컨테이너 스타일 */
    [data-testid="stContainer"] {{
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        border: 1px solid #e1e8ed;
    }}
    
    /* 익스팬더 스타일 */
    .streamlit-expanderHeader {{
        background: linear-gradient(135deg, #f0f4f8 0%, #e1e8ed 100%);
        border-radius: 10px;
        font-weight: 600;
        color: #003d82;
        border: 2px solid #0066cc;
    }}
    
    .streamlit-expanderHeader:hover {{
        background: linear-gradient(135deg, #e1e8ed 0%, #d1dae0 100%);
    }}
    
    /* 메트릭 스타일 */
    [data-testid="stMetricValue"] {{
        font-size: 32px;
        font-weight: 700;
        color: #003d82;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: #0066cc;
        font-weight: 600;
    }}
    
    /* 체크박스 스타일 */
    .stCheckbox {{
        padding: 8px 0;
    }}
    
    /* 제목 스타일 */
    h1, h2, h3 {{
        color: #003d82;
        font-weight: 700;
    }}
    
    /* 구분선 */
    hr {{
        margin: 25px 0;
        border: none;
        border-top: 3px solid #ffd700;
    }}
    
    /* 성공 메시지 */
    .stSuccess {{
        background-color: #d4edda;
        border-left: 5px solid #28a745;
    }}
    
    /* 경고 메시지 */
    .stWarning {{
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
    }}
    
    /* 에러 메시지 */
    .stError {{
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
    }}
    
    /* 정보 메시지 */
    .stInfo {{
        background-color: #d1ecf1;
        border-left: 5px solid #0066cc;
    }}
</style>
""", unsafe_allow_html=True)

# 헤더 섹션
if logo_base64:
    st.markdown(f"""
    <div class="header-container">
        <div class="logo-title-container">
            <img src="data:image/jpeg;base64,{logo_base64}" class="header-logo" alt="DG-ON Logo">
            <div>
                <h1 class="header-title">DG-Form</h1>
                <p class="header-subtitle">등기온 전자설정 자동화 시스템</p>
            </div>
        </div>
        <div style="color: white; text-align: right;">
            <p style="margin: 0; font-size: 1.1rem; font-weight: 600;">법무법인 시화</p>
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.9;">부동산 등기는 등기온</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="header-container">
        <div>
            <h1 class="header-title">🏠 DG-Form</h1>
            <p class="header-subtitle">등기온 전자설정 자동화 시스템</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# 1. 라이브러리 및 환경 설정
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
    from fpdf import FPDF
    LIBS_OK = True
except ImportError:
    LIBS_OK = False

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
    "(주)유노스프레스티지대부 사내이사 한은수": {"addr": "서울특별시 강남구 압구정로28길24, 5층 501호(신사동,디앤씨빌딩)", "corp_num": "110111-4138560", "fee": {"제증명": 20000, "교통비": 0, "원인증서": 0}},
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
def format_date(text):
    if not text: return ""
    numbers = re.sub(r'[^\d]', '', text)
    if len(numbers) == 8: return f"{numbers[:4]}년 {numbers[4:6]}월 {numbers[6:8]}일"
    return text

def format_number_with_comma(num_str):
    if not num_str: return ""
    if isinstance(num_str, int): num_str = str(num_str)
    has_comma = ',' in num_str
    numbers = re.sub(r'[^\d]', '', num_str)
    if not numbers: return ""
    try:
        num_int = int(numbers)
        if num_int > 0 and len(numbers) < 4 and not has_comma:
             numbers = numbers + '000'
             num_int = int(numbers)
        return "{:,}".format(num_int)
    except ValueError:
        return num_str

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
        if match:
            return math.ceil(float(match.group(1)) * 10) / 10 / 100
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

# =============================================================================
# 4. PDF 생성 로직
# =============================================================================

def draw_fit_text(c, text, x, y, max_width, font_name='Korean', max_size=11, min_size=6):
    if not text: return
    current_size = max_size
    text_width = pdfmetrics.stringWidth(text, font_name, current_size)
    while text_width > max_width and current_size > min_size:
        current_size -= 0.5
        text_width = pdfmetrics.stringWidth(text, font_name, current_size)
    c.setFont(font_name, current_size)
    c.drawString(x, y, text)

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
            except: 
                self.set_font('Arial', '', 11)
        else: 
            self.set_font('Arial', '', 11)
    
    def draw_labelframe_box(self, title, content_func):
        self.set_font(self.font_family, 'B', 11)
        start_y = self.get_y(); start_x = self.l_margin
        box_width = self.w - self.l_margin * 2
        self.set_y(start_y + self.line_height)
        content_start_y = self.get_y()
        content_func()
        content_end_y = self.get_y()
        box_height = (content_end_y - content_start_y) + self.line_height + 4
        self.set_draw_color(211, 211, 211)
        self.rect(start_x, start_y + self.font_size / 2, box_width, box_height)
        title_width = self.get_string_width(title)
        self.set_fill_color(255, 255, 255)
        self.rect(start_x + 9, start_y, title_width + 4, self.font_size, 'F')
        self.set_xy(start_x + 11, start_y)
        self.cell(0, self.font_size, title)
        self.set_y(start_y + self.line_height)
        content_func()
        self.set_y(start_y + box_height + 4)
    
    def output_pdf(self, data, save_path):
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
                self.set_font(self.font_family, '', 10)
                items = data['fee_items']
                subtotal = items.get('기본료', 0) + items.get(data['labels']['추가보수_label'], 0) + items.get(data['labels']['기타보수_label'], 0)
                self.set_x(self.l_margin + 5)
                self.cell(self.col_width1, self.line_height, "보수액 소계")
                self.cell(self.col_width2, self.line_height, f"{subtotal:,} 원", ln=1, align="R")
                self.set_x(self.l_margin + 5)
                self.cell(self.col_width1, self.line_height, "할인금액")
                self.cell(self.col_width2, self.line_height, f"{items.get('할인금액', 0):,} 원", ln=1, align="R")
                self.ln(1); self.line(self.get_x() + 5, self.get_y(), self.w - self.r_margin - 5, self.get_y()); self.ln(1)
                self.set_font(self.font_family, 'B', 10); self.set_x(self.l_margin + 5)
                self.cell(self.col_width1, self.line_height, "보수 소계")
                self.cell(self.col_width2, self.line_height, f"{data['fee_totals']['보수총액']:,} 원", ln=1, align="R")
            self.draw_labelframe_box("1. 보수액", fee_content)
        def costs_content():
            self.set_font(self.font_family, '', 10)
            items = data['cost_items']
            for name, val in items.items():
                if val != 0:
                    self.set_x(self.l_margin + 5); self.cell(self.col_width1, self.line_height, name)
                    self.cell(self.col_width2, self.line_height, f"{int(val):,} 원", ln=1, align="R")
            self.ln(1); self.line(self.get_x() + 5, self.get_y(), self.w - self.r_margin - 5, self.get_y()); self.ln(1)
            self.set_font(self.font_family, 'B', 10); self.set_x(self.l_margin + 5)
            self.cell(self.col_width1, self.line_height, "공과금소계")
            self.cell(self.col_width2, self.line_height, f"{data['cost_totals']['공과금 총액']:,} 원", ln=1, align="R")
        self.draw_labelframe_box(data['cost_section_title'], costs_content)
        self.set_font(self.font_family, 'B', 12)
        self.cell(self.col_width1 - 10, 10, "등기비용 합계")
        self.cell(self.col_width2 + 10, 10, f"{data['grand_total']:,} 원", ln=True, align="R")
        self.ln(5)
        def notes_content():
            self.set_font(self.font_family, '', 10); self.set_x(self.l_margin + 5)
            self.cell(0, self.line_height, "• 원활한 확인을 위해 입금자는 소유자명(또는 채무자명)으로 기재해 주세요.", ln=1)
            self.set_x(self.l_margin + 5)
            self.cell(0, self.line_height, "• 입금 완료 후, 메시지를 남겨주시면 더욱 빠르게 처리됩니다.", ln=1)
            self.set_x(self.l_margin + 5)
            self.cell(0, self.line_height, "• 업무는 입금이 확인된 후에 진행됩니다.", ln=1)
        self.draw_labelframe_box("안내사항", notes_content)
        def bank_content():
            self.set_font(self.font_family, '', 10); self.set_x(self.l_margin + 5)
            self.cell(0, self.line_height, "• 신한은행 100-035-852291", ln=1)
            self.set_x(self.l_margin + 5)
            self.cell(0, self.line_height, "• 예금주 : 법무법인 시화", ln=1)
        self.draw_labelframe_box("입금 계좌 정보", bank_content)

        return self.output(dest='S') 

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
    
    output_buffer = BytesIO() 
    
    for page_num in range(min(len(template_pdf.pages), len(overlay_pdf.pages))):
        template_page = template_pdf.pages[page_num]; overlay_page = overlay_pdf.pages[page_num]
        template_page.merge_page(overlay_page); writer.add_page(template_page)
    
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer

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
    
    output_buffer = BytesIO() 
    
    template_page = template_pdf.pages[0]; overlay_page = overlay_pdf.pages[0]
    template_page.merge_page(overlay_page); writer.add_page(template_page)
    
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer

# =============================================================================
# 5. Streamlit UI 및 상태 관리
# =============================================================================

# Streamlit 상태 초기화
if 'calc_data' not in st.session_state:
    st.session_state['calc_data'] = {}
    st.session_state['show_fee'] = True
    st.session_state['addr_change'] = False
    st.session_state['addr_count'] = 1
    st.session_state['input_amount'] = "0"
    st.session_state['input_parcels'] = 1
    st.session_state['input_rate'] = f"{get_rate()*100:.5f}"
    st.session_state['input_debtor'] = ""
    st.session_state['input_creditor'] = list(CREDITORS.keys())[0]
    st.session_state['input_collateral_addr'] = ""
    st.session_state['input_debtor_addr'] = ""
    st.session_state['input_owner'] = ""
    st.session_state['input_owner_addr'] = ""
    st.session_state['guarantee'] = "한정근담보"
    st.session_state['contract_type'] = "개인"
    st.session_state['input_date'] = datetime.now().strftime("%Y년 %m월 %d일")
    st.session_state['estate_text'] = """[토지]\n서울특별시 강남구 대치동 123번지\n대 300㎡\n\n[건물]\n서울특별시 강남구 대치동 123번지\n철근콘크리트조 슬래브지붕 5층 주택\n1층 100㎡\n2층 100㎡"""
    st.session_state['input_debtor_rrn'] = ""
    st.session_state['input_owner_rrn'] = ""

def parse_int_input(text_input):
    try:
        if isinstance(text_input, int): return text_input
        return int(remove_commas(text_input or "0"))
    except ValueError:
        return 0

def handle_creditor_change():
    """금융사 변경 시 수수료 기본값을 세션 상태에 즉시 반영"""
    creditor_key = st.session_state['t1_creditor_select']
    default_fees = CREDITORS.get(creditor_key, {}).get("fee", {"제증명": 50000, "교통비": 100000, "원인증서": 50000})
    
    st.session_state.calc_data['제증명'] = format_number_with_comma(str(default_fees.get("제증명")))
    st.session_state.calc_data['교통비'] = format_number_with_comma(str(default_fees.get("교통비")))
    st.session_state.calc_data['원인증서'] = format_number_with_comma(str(default_fees.get("원인증서")))
    st.session_state.calc_data['creditor_key_check'] = creditor_key
    st.session_state.calc_data['주소변경'] = forma