import streamlit as st
import os
import re
import math
from io import BytesIO
from datetime import datetime
import sys

# 현재 실행 디렉토리를 기준으로 경로 설정 (Streamlit 환경에 최적화)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# 0. 라이브러리 및 환경 설정
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
# 1. 상수 및 데이터
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

# 템플릿 파일 경로를 앱 루트 기준으로 설정
def resource_path(relative_path):
    return os.path.join(APP_ROOT, relative_path)

# 폰트 경로 설정
FONT_PATH = resource_path("Malgun.ttf") 

# 템플릿 파일 상태 확인 (세션 상태에 저장)
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
# 2. 유틸리티 및 계산 로직
# =============================================================================
def format_date(text):
    if not text: return ""
    numbers = re.sub(r'[^\d]', '', text)
    if len(numbers) == 8: return f"{numbers[:4]}년 {numbers[4:6]}월 {numbers[6:8]}일"
    return text

# 💡 [수정] 천 단위 입력 보정 로직 강화 및 타입 안전성 확보
def format_number_with_comma(num_str):
    if not num_str: return ""
    
    # 입력이 int 타입일 경우 문자열로 강제 변환
    if isinstance(num_str, int):
        num_str = str(num_str)
    
    # 원본에 콤마가 있었는지 체크
    has_comma = ',' in num_str
    
    # 숫자만 추출
    numbers = re.sub(r'[^\d]', '', num_str)
    if not numbers: return ""
    
    try:
        num_int = int(numbers)
        
        # 💡 천 단위 생략 보정: 콤마가 없고 3자리 이하인 경우에만 ,000 추가
        if num_int > 0 and len(numbers) < 4 and not has_comma:
             numbers = numbers + '000'
             num_int = int(numbers)
             
        return "{:,}".format(num_int)
    except ValueError:
        return num_str

def remove_commas(v):
    # 입력값이 None이나 숫자가 아닌 경우를 대비
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
# 3. PDF 생성 로직 (Streamlit 출력에 맞게 수정)
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
        if client.get('물건지'): self.cell(0, self.line_height, f"물  건  지: {client['물건지']}", ln=1)
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
# 4. Streamlit UI 및 상태 관리
# =============================================================================

# Streamlit 상태 초기화
if 'calc_data' not in st.session_state:
    st.session_state['calc_data'] = {}
    st.session_state['show_fee'] = True
    st.session_state['addr_change'] = False
    st.session_state['addr_count'] = 1
    # 초기 계산을 위한 기본값 설정
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
    
# 금액을 커마 포맷으로 입력받기 위한 헬퍼 함수
def parse_int_input(text_input):
    try:
        if isinstance(text_input, int): return text_input
        return int(remove_commas(text_input or "0"))
    except ValueError:
        return 0
    
# 💡 [추가] 금융사 변경 시 콜백 함수
def handle_creditor_change():
    """금융사 변경 시 수수료 기본값을 세션 상태에 즉시 반영"""
    creditor_key = st.session_state['t1_creditor_select']
    default_fees = CREDITORS.get(creditor_key, {}).get("fee", {"제증명": 50000, "교통비": 100000, "원인증서": 50000})
    
    # calc_data의 수기 입력 항목에 새 기본값을 설정 (str() 변환 필수)
    st.session_state.calc_data['제증명'] = format_number_with_comma(str(default_fees.get("제증명")))
    st.session_state.calc_data['교통비'] = format_number_with_comma(str(default_fees.get("교통비")))
    st.session_state.calc_data['원인증서'] = format_number_with_comma(str(default_fees.get("원인증서")))
    
    # 상태 갱신 마커 초기화
    st.session_state.calc_data['creditor_key_check'] = creditor_key
    
    # 기타 수기 비용 0으로 초기화
    st.session_state.calc_data['주소변경'] = format_number_with_comma("0")
    st.session_state.calc_data['확인서면'] = format_number_with_comma("0")
    st.session_state.calc_data['선순위 말소'] = format_number_with_comma("0")

# 계산 로직 통합 함수
def calculate_all(data):
    amount = parse_int_input(data['채권최고액']) 
    parcels = parse_int_input(data['필지수'])
    try:
        rate = float(remove_commas(data['채권할인율'])) / 100
    except ValueError:
        rate = 0 
    
    # 2. 보수료 계산
    base_fee = lookup_base_fee(amount)
    data['기본료'] = base_fee
    
    add_fee = parse_int_input(data['추가보수_val'])
    etc_fee = parse_int_input(data['기타보수_val'])
    disc_fee = parse_int_input(data['할인금액'])

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
    
    # 3. 공과금 계산
    reg = floor_10(amount * 0.002)
    edu = floor_10(reg * 0.2)
    jeungji = 18000 * parcels
    
    # 주소변경 로직
    if st.session_state['addr_change']:
        count = st.session_state['addr_count']
        reg += 6000 * count
        edu += 1200 * count
        jeungji += 3000 * count
        data['주소변경'] = 20000 * count
    else:
        data['주소변경'] = st.session_state.calc_data.get('주소변경', "0")
    
    # 채권 계산
    bond = 0
    if amount >= 20_000_000: bond = math.ceil(amount * 0.01 / 10000) * 10000
    bond_disc = floor_10(bond * rate)
    
    data["등록면허세"] = reg
    data["지방교육세"] = edu
    data["증지대"] = jeungji
    data["채권할인금액"] = bond_disc
    
    cost_total = reg + edu + jeungji + bond_disc
    
    manual_cost_keys = ["제증명", "교통비", "원인증서", "주소변경", "확인서면", "선순위 말소"]
    for k in manual_cost_keys:
        cost_total += parse_int_input(data.get(k, 0))
    
    for i in range(1, 7):
        label_key = f'custom_label_{i}'
        value_key = f'custom_value_{i}'
        if data.get(label_key):
            cost_total += parse_int_input(data.get(value_key, 0))

    data['공과금 총액'] = cost_total
    data['총 합계'] = fee_total + cost_total
    
    st.session_state['calc_data'] = data
    return data

# Streamlit 앱 시작
st.set_page_config(layout="wide", page_title="근저당권설정 자동화 웹 앱")

st.title("📄 근저당권설정 자동화 웹 앱")

# 탭 구현
tab1, tab2, tab3 = st.tabs(["📄 근저당권설정", "✍️ 자필서명정보", "🧾 비용 계산 및 영수증"])

# =============================================================================
# Tab 1: 근저당권 설정 (입력)
# =============================================================================
with tab1:
    col_l, col_r = st.columns([7, 3])
    
    with col_l:
        # 💡 초기화 버튼 추가
        st.header("입력 정보")
        
        if st.button("🔄 전체 초기화", type="secondary", help="모든 입력값을 초기 상태로 되돌립니다"):
            # 모든 입력 필드 초기화
            st.session_state['input_date'] = datetime.now().strftime("%Y년 %m월 %d일")
            st.session_state['input_creditor'] = list(CREDITORS.keys())[0]
            st.session_state['input_debtor'] = ""
            st.session_state['input_debtor_addr'] = ""
            st.session_state['input_owner'] = ""
            st.session_state['input_owner_addr'] = ""
            st.session_state['contract_type'] = "개인"
            st.session_state['guarantee'] = "한정근담보"
            st.session_state['input_amount'] = "0"
            st.session_state['_amount_temp'] = "0"
            st.session_state['input_collateral_addr'] = ""
            st.session_state['estate_text'] = """[토지]\n서울특별시 강남구 대치동 123번지\n대 300㎡\n\n[건물]\n서울특별시 강남구 대치동 123번지\n철근콘크리트조 슬래브지붕 5층 주택\n1층 100㎡\n2층 100㎡"""
            st.session_state['input_debtor_rrn'] = ""
            st.session_state['input_owner_rrn'] = ""
            st.rerun()
        
        # 1. 기본 정보
        with st.expander("📌 기본 정보", expanded=True):
            date_raw = st.text_input("작성일자", value=st.session_state.get('input_date'), help="YYYYMMDD 형식 입력 후 포맷 자동 변환")
            st.session_state['input_date'] = format_date(date_raw)

        # 2. 당사자 정보
        with st.expander("👤 당사자 정보", expanded=True):
            creditor_list = list(CREDITORS.keys())
            selected_creditor = st.selectbox(
                "채권자 선택", 
                options=creditor_list, 
                index=creditor_list.index(st.session_state.get('input_creditor')) if st.session_state.get('input_creditor') in creditor_list else 0,
                key='t1_creditor_select', 
                on_change=handle_creditor_change
            )
            st.session_state['input_creditor'] = selected_creditor
            
            creditor_info = CREDITORS.get(selected_creditor, {})
            st.text_input("법인번호", value=creditor_info.get('corp_num', ''), disabled=True)
            st.text_area("채권자 주소", value=creditor_info.get('addr', ''), disabled=True)
            st.session_state['input_debtor'] = st.text_input("채무자 성명", value=st.session_state.get('input_debtor'), key='t1_debtor_name')
            st.session_state['input_debtor_addr'] = st.text_area("채무자 주소", value=st.session_state.get('input_debtor_addr'), key='t1_debtor_addr')
            st.session_state['input_owner'] = st.text_input("설정자 성명", value=st.session_state.get('input_owner'), key='t1_owner_name')
            st.session_state['input_owner_addr'] = st.text_area("설정자 주소", value=st.session_state.get('input_owner_addr'), key='t1_owner_addr')

        # 3. 담보 및 계약 정보
        with st.expander("🤝 담보 및 계약 정보", expanded=True):
            st.session_state['contract_type'] = st.radio("계약서 유형", options=["개인", "3자담보", "공동담보"], horizontal=True, key='contract_type_radio')
            st.session_state['guarantee'] = st.text_input("피담보채무", value=st.session_state.get('guarantee'))
            
            # 💡 채권최고액 입력 콜백 함수
            def format_amount_input():
                """입력값을 자동으로 콤마 포맷팅"""
                raw_value = st.session_state['_amount_temp']
                st.session_state['input_amount'] = format_number_with_comma(raw_value)
            
            # 초기값 설정
            if '_amount_temp' not in st.session_state:
                st.session_state['_amount_temp'] = st.session_state.get('input_amount', "0")
            
            # 채권최고액 입력
            st.text_input(
                "채권최고액 (콤마 포함 입력)", 
                value=st.session_state.get('input_amount', "0"),
                key='_amount_temp',
                on_change=format_amount_input,
                help="숫자 입력 후 Enter 또는 다른 필드 클릭 시 자동으로 콤마가 추가됩니다"
            )
            
            # 물건지 주소 복사 버튼
            col_addr1, col_addr2 = st.columns([4, 1])
            with col_addr1:
                collateral_addr_input = st.text_input(
                    "물건지 주소 (수기 입력)", 
                    value=st.session_state.get('input_collateral_addr', ""), 
                    key='t1_collateral_addr_input'
                )
                st.session_state['input_collateral_addr'] = collateral_addr_input
            
            with col_addr2:
                st.write("")
                st.write("")
                if st.button("📋 복사", help="채무자 주소를 물건지 주소로 복사", key='copy_addr_btn'):
                    st.session_state['input_collateral_addr'] = st.session_state.get('input_debtor_addr', "")
                    st.rerun()

    with col_r:
        st.header("🏠 부동산의 표시")
        st.caption("※ 등기부등본 내용 입력")
        st.session_state['estate_text'] = st.text_area("부동산 표시 내용", value=st.session_state['estate_text'], height=400, key='estate_text_area')
        
        st.subheader("파일 생성")
        
        selected_template_path = st.session_state['template_status'].get(st.session_state['contract_type'])
        
        if selected_template_path:
            st.success(f"✅ {st.session_state['contract_type']} 템플릿 준비 완료")
            is_disabled = False
        else:
            st.warning(f"⚠️ {st.session_state['contract_type']} 템플릿 파일이 없습니다.")
            is_disabled = True
        
        if st.button("🚀 계약서 PDF 생성", key="generate_pdf_tab1", disabled=is_disabled or not LIBS_OK):
            if not LIBS_OK: 
                st.error("PDF 생성 라이브러리(reportlab/pypdf2/fpdf)가 설치되지 않았습니다.")
            else:
                debtor_name = st.session_state['input_debtor'] if st.session_state['input_debtor'] else "미지정"
                
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
                    st.download_button(
                        label="⬇️ PDF 다운로드 (클릭)",
                        data=pdf_buffer,
                        file_name=f"근저당권설정계약서_{debtor_name}.pdf",
                        mime="application/pdf"
                    )
                    st.success("PDF 파일 생성이 완료되었습니다. 다운로드 버튼을 클릭하세요.")
                except Exception as e:
                    st.error(f"PDF 생성 중 오류 발생: {e}")
                    st.exception(e)

# =============================================================================
# Tab 2: 자필서명 정보
# =============================================================================
with tab2:
    col_l2, col_r2 = st.columns(2)
    
    with col_l2:
        st.header("✍️ 의무자 정보 입력")
        st.session_state['sig_date'] = st.text_input("작성일자", value=st.session_state.get('input_date'), key='sig_date_input', disabled=True)
        st.session_state['sig_debtor'] = st.text_input("설정자(단독/채무자)", value=st.session_state.get('input_debtor'), key='sig_debtor_input')
        st.session_state['input_debtor_rrn'] = st.text_input("주민등록번호(채무자)", value=st.session_state.get('input_debtor_rrn'), key='sig_debtor_rrn_input')
        st.session_state['sig_owner'] = st.text_input("설정자(공동/물상보증인)", value=st.session_state.get('input_owner'), key='sig_owner_input')
        st.session_state['input_owner_rrn'] = st.text_input("주민등록번호(설정자)", value=st.session_state.get('input_owner_rrn'), key='sig_owner_rrn_input')

    with col_r2:
        st.header("🏠 부동산의 표시 (확인용)")
        
        st.session_state['sig_estate_text'] = st.text_area("부동산 표시 내용", value=st.session_state.get('estate_text'), height=350, key='sig_estate_area', disabled=True)
        st.info("내용은 1번 탭의 '부동산의 표시'와 동기화됩니다.")
        
        sig_template_path = st.session_state['template_status'].get("자필")

        if sig_template_path:
            st.success("✅ 자필서명 템플릿 준비 완료")
            is_disabled = False
        else:
            st.warning("⚠️ 자필서명정보 템플릿 파일이 없습니다.")
            is_disabled = True
        
        if st.button("📄 자필서명정보 PDF 생성", key="generate_sig_pdf", disabled=is_disabled or not LIBS_OK):
            if not LIBS_OK: 
                st.error("PDF 생성 라이브러리가 설치되지 않았습니다.")
            else:
                debtor_name = st.session_state['sig_debtor'] if st.session_state['sig_debtor'] else "미지정"
                
                data = {
                    "date": st.session_state['sig_date'], 
                    "debtor_name": st.session_state['sig_debtor'], 
                    "debtor_rrn": st.session_state['input_debtor_rrn'],
                    "owner_name": st.session_state['sig_owner'], 
                    "owner_rrn": st.session_state['input_owner_rrn'], 
                    "estate_text": st.session_state['sig_estate_text']
                }
                
                try:
                    pdf_buffer = make_signature_pdf(sig_template_path, data)
                    st.download_button(
                        label="⬇️ PDF 다운로드 (클릭)",
                        data=pdf_buffer,
                        file_name=f"자필서명정보_{debtor_name}.pdf",
                        mime="application/pdf"
                    )
                    st.success("PDF 파일 생성이 완료되었습니다. 다운로드 버튼을 클릭하세요.")
                except Exception as e:
                    st.error(f"자필서명 PDF 생성 중 오류 발생: {e}")
                    st.exception(e)


# =============================================================================
# Tab 3: 비용 계산 및 영수증
# =============================================================================
with tab3:
    st.header("🧾 등기비용 계산기")
    
    # -------------------
    # 1. 기초 정보 입력 (1번 탭과 동기화)
    # -------------------
    with st.expander("📌 기초 계산 정보 (1번 탭과 연동)", expanded=True):
        col_c1, col_c2, col_c3 = st.columns([2, 1, 2])
        
        col_c1.text_input("채권최고액", value=st.session_state.get('input_amount'), disabled=True)
        
        parcels = col_c2.text_input("필지수", value=st.session_state.get('input_parcels'), key='calc_parcels_input')
        try: 
            st.session_state['input_parcels'] = int(remove_commas(parcels))
        except: 
            st.session_state['input_parcels'] = 1
        
        rate_cols = col_c3.columns([3, 1])
        st.session_state['input_rate'] = rate_cols[0].text_input("채권할인율(%)", value=st.session_state.get('input_rate'), key='calc_rate_input')
        if rate_cols[1].button("🔄", help="현재 채권할인율로 업데이트"):
            st.session_state['input_rate'] = f"{get_rate()*100:.5f}"
            st.rerun()
            
        st.text_input("금융사", value=st.session_state.get('input_creditor'), disabled=True)
        st.text_input("채무자", value=st.session_state.get('input_debtor'), disabled=True)
        st.text_input("물건지", value=extract_address_from_estate(st.session_state.get('estate_text') or "") if not st.session_state.get('input_collateral_addr') else st.session_state.get('input_collateral_addr'), disabled=True)
    
    
    # 💡 금융사 변경 감지 및 초기값 설정
    creditor_key = st.session_state['input_creditor']
    default_fees = CREDITORS.get(creditor_key, {}).get("fee", {"제증명": 50000, "교통비": 100000, "원인증서": 50000})

    # 초기화 마커가 없거나 금융사가 변경된 경우, 계산 데이터 초기값 설정
    if st.session_state.calc_data.get('creditor_key_check') != creditor_key:
        st.session_state.calc_data['제증명'] = format_number_with_comma(str(default_fees.get("제증명")))
        st.session_state.calc_data['교통비'] = format_number_with_comma(str(default_fees.get("교통비")))
        st.session_state.calc_data['원인증서'] = format_number_with_comma(str(default_fees.get("원인증서")))
        st.session_state.calc_data['주소변경'] = format_number_with_comma("0")
        st.session_state.calc_data['확인서면'] = format_number_with_comma("0")
        st.session_state.calc_data['선순위 말소'] = format_number_with_comma("0")
        st.session_state.calc_data['creditor_key_check'] = creditor_key
        
    calc_data = {
        '채권최고액': st.session_state['input_amount'],
        '필지수': st.session_state['input_parcels'],
        '채권할인율': st.session_state['input_rate'],
        '금융사': st.session_state['input_creditor'],
        '채무자': st.session_state['input_debtor'],
        '물건지': extract_address_from_estate(st.session_state.get('estate_text') or "") if not st.session_state.get('input_collateral_addr') else st.session_state.get('input_collateral_addr'),
        '추가보수_label': "추가보수", 
        '기타보수_label': "기타보수",
        '추가보수_val': st.session_state.calc_data.get('추가보수_val', "0"),
        '기타보수_val': st.session_state.calc_data.get('기타보수_val', "0"),
        '할인금액': st.session_state.calc_data.get('할인금액', "0"),
        '제증명': st.session_state.calc_data.get('제증명', "0"),
        '교통비': st.session_state.calc_data.get('교통비', "0"),
        '원인증서': st.session_state.calc_data.get('원인증서', "0"),
        '주소변경': st.session_state.calc_data.get('주소변경', "0"),
        '확인서면': st.session_state.calc_data.get('확인서면', "0"),
        '선순위 말소': st.session_state.calc_data.get('선순위 말소', "0"),
    }
    
    for i in range(1, 7):
        calc_data[f'custom_label_{i}'] = st.session_state.calc_data.get(f'custom_label_{i}', "")
        calc_data[f'custom_value_{i}'] = st.session_state.calc_data.get(f'custom_value_{i}', "0")

    # 계산 실행
    st.session_state['calc_data'] = calculate_all(calc_data)
    current_data = st.session_state['calc_data']


    # -------------------
    # 2. 보수액 / 공과금 / 총계
    # -------------------
    col_f, col_c, col_t = st.columns(3)
    
    # 2-1. 보수액
    with col_f:
        with st.container(border=True):
            st.subheader("💰 보수액 (Income)")
            
            st.session_state.calc_data['추가보수_val'] = st.text_input("추가보수", value=current_data.get('추가보수_val'), key='add_fee_val')
            st.session_state.calc_data['기타보수_val'] = st.text_input("기타보수", value=current_data.get('기타보수_val'), key='etc_fee_val')
            st.session_state.calc_data['할인금액'] = st.text_input("할인금액", value=current_data.get('할인금액'), key='disc_fee_val')
            
            st.divider()
            st.metric("기본료", format_number_with_comma(current_data.get('기본료')))
            st.metric("공급가액", format_number_with_comma(current_data.get('공급가액')))
            st.metric("부가세", format_number_with_comma(current_data.get('부가세')))
            st.markdown(f"**총 보수액:** <h3 style='color:green;'>{format_number_with_comma(current_data.get('보수총액'))} 원</h3>", unsafe_allow_html=True)


    # 2-2. 공과금
    with col_c:
        with st.container(border=True):
            st.subheader("🏛️ 공과금 (Tax)")
            
            st.markdown("##### 자동 계산 (ReadOnly)")
            st.text_input("등록면허세", value=format_number_with_comma(current_data.get('등록면허세')), disabled=True)
            st.text_input("지방교육세", value=format_number_with_comma(current_data.get('지방교육세')), disabled=True)
            st.text_input("증지대", value=format_number_with_comma(current_data.get('증지대')), disabled=True)
            st.text_input("채권할인금액", value=format_number_with_comma(current_data.get('채권할인금액')), disabled=True)
            
            st.divider()
            
            st.markdown("##### 수기 입력")
            
            for k in ["제증명", "교통비", "원인증서", "확인서면", "선순위 말소"]:
                st.session_state.calc_data[k] = st.text_input(k, value=current_data.get(k), key=f'cost_manual_{k}')
            
            st.session_state.calc_data['주소변경'] = st.text_input("주소변경 (보수료)", value=current_data.get('주소변경'), key='cost_addr_change')
            
            st.divider()
            st.markdown(f"**총 공과금:** <h3 style='color:orange;'>{format_number_with_comma(current_data.get('공과금 총액'))} 원</h3>", unsafe_allow_html=True)


    # 2-3. 최종 결제 및 옵션
    with col_t:
        with st.container(border=True):
            st.subheader("🧾 최종 결제 및 옵션")
            st.markdown(f"## 총 청구금액: <span style='color:red;'>{format_number_with_comma(current_data.get('총 합계'))} 원</span>", unsafe_allow_html=True)
            st.divider()

            # 💡 옵션 설정 - on_change로 즉시 반영
            def toggle_show_fee():
                st.session_state['show_fee'] = st.session_state['show_fee_checkbox']
            
            def toggle_addr_change():
                st.session_state['addr_change'] = st.session_state['addr_change_checkbox']
            
            st.checkbox(
                "보수액 포함 표시", 
                value=st.session_state['show_fee'],
                key='show_fee_checkbox',
                on_change=toggle_show_fee
            )
            
            addr_cols = st.columns([3, 1])
            addr_cols[0].checkbox(
                "주소변경 포함 (공과금 및 보수료)", 
                value=st.session_state['addr_change'],
                key='addr_change_checkbox',
                on_change=toggle_addr_change
            )
            st.session_state['addr_count'] = addr_cols[1].number_input("인원수", min_value=1, max_value=10, value=st.session_state['addr_count'], step=1)

            # 영수증/비용내역 다운로드 버튼
            download_cols = st.columns(2)
            
            # 비용내역 PDF 다운로드
            if download_cols[0].button("📄 고객용 비용내역 PDF"):
                if LIBS_OK:
                    pdf_data = st.session_state.calc_data 
                    data_for_pdf = {
                        "date_input": st.session_state['input_date'], 
                        'client': {
                            '채권최고액': format_number_with_comma(pdf_data['채권최고액']), 
                            '필지수': pdf_data['필지수'],
                            '금융사': pdf_data['금융사'], 
                            '채무자': pdf_data['채무자'], 
                            '물건지': pdf_data['물건지']
                        },
                        'fee_items': {
                            k: parse_int_input(pdf_data.get(k)) 
                            for k in ['기본료', '추가보수_val', '기타보수_val', '할인금액']
                        },
                        'fee_totals': {
                            '공급가액': pdf_data['공급가액'], 
                            '부가세': pdf_data['부가세'], 
                            '보수총액': pdf_data['보수총액']
                        },
                        'cost_items': {
                            k: parse_int_input(pdf_data.get(k)) 
                            for k in ["등록면허세", "지방교육세", "증지대", "채권할인금액", 
                                      "제증명", "교통비", "원인증서", "주소변경", "확인서면", "선순위 말소"]
                        },
                        'cost_totals': {'공과금 총액': pdf_data['공과금 총액']},
                        'cost_section_title': '2. 공과금' if st.session_state['show_fee'] else '1. 공과금',
                        'grand_total': pdf_data['총 합계'],
                        'labels': {'추가보수_label': "추가보수", '기타보수_label': "기타보수"}
                    }
                    
                    try:
                        pdf = PDFConverter(show_fee=st.session_state['show_fee'])
                        pdf_buffer = pdf.output_pdf(data_for_pdf, None) 
                        
                        download_cols[0].download_button(
                            label="⬇️ 다운로드 (클릭)",
                            data=pdf_buffer,
                            file_name=f"비용내역_{pdf_data['채무자'] or '근저당권설정'}.pdf",
                            mime="application/pdf",
                            key="dl_client_pdf"
                        )
                    except Exception as e:
                        st.error(f"PDF 생성 중 오류 발생: {e}")
                        st.exception(e)
                else:
                    st.error("PDF 라이브러리 미설치")

            # 대부업 영수증 (Excel) 다운로드
            excel_template_path = st.session_state['template_status'].get("영수증")
            if download_cols[1].button("🏦 대부업 영수증 Excel", disabled=not EXCEL_OK or not excel_template_path):
                if not EXCEL_OK:
                    st.error("Excel 라이브러리(openpyxl)가 설치되지 않았습니다.")
                elif not excel_template_path:
                    st.error("영수증 템플릿 파일이 준비되지 않았습니다.")
                else:
                    try:
                        import openpyxl
                        from openpyxl.cell.cell import MergedCell
                        
                        wb = openpyxl.load_workbook(excel_template_path)
                        ws = wb.active
                        
                        # 💡 병합된 셀 안전하게 처리하는 함수
                        def safe_set_value(sheet, cell_ref, value):
                            """병합된 셀의 경우 왼쪽 상단 셀에 값 설정"""
                            try:
                                cell = sheet[cell_ref]
                                
                                # MergedCell인 경우 병합 범위의 시작 셀 찾기
                                if isinstance(cell, MergedCell):
                                    for merged_range in sheet.merged_cells.ranges:
                                        if cell.coordinate in merged_range:
                                            # 병합 범위의 시작 셀(왼쪽 상단)에 값 설정
                                            start_cell = merged_range.start_cell
                                            sheet[start_cell.coordinate].value = value
                                            return
                                else:
                                    # 일반 셀은 그냥 값 설정
                                    cell.value = value
                            except Exception as e:
                                st.warning(f"셀 {cell_ref} 설정 실패: {e}")
                        
                        # 대부업 영수증 (Excel) 다운로드
            excel_template_path = st.session_state['template_status'].get("영수증")
            if download_cols[1].button("🏦 대부업 영수증 Excel", disabled=not EXCEL_OK or not excel_template_path):
                if not EXCEL_OK:
                    st.error("Excel 라이브러리(openpyxl)가 설치되지 않았습니다.")
                elif not excel_template_path:
                    st.error("영수증 템플릿 파일이 준비되지 않았습니다.")
                else:
                    try:
                        import openpyxl
                        from openpyxl.cell.cell import MergedCell
                        
                        wb = openpyxl.load_workbook(excel_template_path)
                        ws = wb.active
                        
                        # 💡 병합된 셀 안전하게 처리하는 함수
                        def safe_set_value(sheet, cell_ref, value):
                            """병합된 셀의 경우 왼쪽 상단 셀에 값 설정"""
                            try:
                                cell = sheet[cell_ref]
                                
                                # MergedCell인 경우 병합 범위의 시작 셀 찾기
                                if isinstance(cell, MergedCell):
                                    for merged_range in sheet.merged_cells.ranges:
                                        if cell.coordinate in merged_range:
                                            # 병합 범위의 시작 셀(왼쪽 상단)에 값 설정
                                            start_cell = merged_range.start_cell
                                            sheet[start_cell.coordinate].value = value
                                            return
                                else:
                                    # 일반 셀은 그냥 값 설정
                                    cell.value = value
                            except Exception as e:
                                st.warning(f"셀 {cell_ref} 설정 실패: {e}")
                        
                        # 💡 공통 정보
                        date_str = st.session_state['input_date']
                        creditor = current_data['금융사']
                        debtor = current_data['채무자']
                        claim_amount = parse_int_input(current_data["채권최고액"])
                        collateral_addr = current_data['물건지']
                        
                        # 💡 좌측 (사무소 보관용) 데이터 입력
                        safe_set_value(ws, 'A24', date_str)  # 작성일
                        safe_set_value(ws, 'M5', claim_amount)  # 채권최고액
                        safe_set_value(ws, 'E7', collateral_addr)  # 물건지
                        
                        # 좌측 보수액 영역
                        safe_set_value(ws, 'C11', current_data["공급가액"])  # 기본료/공급가액
                        safe_set_value(ws, 'C20', current_data["부가세"])  # 부가가치세
                        safe_set_value(ws, 'C21', current_data["보수총액"])  # 보수 소계
                        
                        # 좌측 총계 (보수 + 공과금)
                        safe_set_value(ws, 'C22', current_data["총 합계"])
                        
                        # 💡 우측 (고객 보관용) 데이터 입력
                        safe_set_value(ws, 'U24', date_str)  # 작성일
                        safe_set_value(ws, 'AG5', claim_amount)  # 채권최고액
                        safe_set_value(ws, 'Y7', collateral_addr)  # 물건지
                        
                        # 💡 우측 공과금 항목 (AH열)
                        safe_set_value(ws, 'AH11', current_data["등록면허세"])
                        safe_set_value(ws, 'AH12', current_data["지방교육세"])
                        safe_set_value(ws, 'AH13', current_data["증지대"])
                        safe_set_value(ws, 'AH14', current_data["채권할인금액"])
                        safe_set_value(ws, 'AH15', parse_int_input(current_data["제증명"]))
                        safe_set_value(ws, 'AH16', parse_int_input(current_data["교통비"]))
                        safe_set_value(ws, 'AH17', parse_int_input(current_data["원인증서"]))
                        safe_set_value(ws, 'AH18', parse_int_input(current_data["주소변경"]))
                        safe_set_value(ws, 'AH19', parse_int_input(current_data["확인서면"]))
                        safe_set_value(ws, 'AH20', parse_int_input(current_data["선순위 말소"]))
                        
                        # 💡 우측 공과금 소계 (AH21)
                        safe_set_value(ws, 'AH21', current_data["공과금 총액"])
                        
                        # 💡 우측 총계 (Y22) - 고객용은 공과금만 표시하므로 소계와 동일
                        safe_set_value(ws, 'Y22', current_data["공과금 총액"])
                        
                        # 💡 하단 사무소 정보
                        firm_name = "법무법인 시화"
                        firm_addr = "서울특별시 서초구 법무법인길 6-9, 301호(서초동,법조타운)"
                        firm_ceo = "법무법인시화"
                        firm_business_num = "214-887-97287"
                        firm_corp_num = "1833-5482"
                        firm_bank = "신한은행 100-035-852291"
                        firm_depositor = "예금주: 법무법인 시화"
                        
                        # 💡 좌측 사무소 정보
                        safe_set_value(ws, 'D25', firm_addr)
                        safe_set_value(ws, 'D26', firm_ceo)
                        safe_set_value(ws, 'D27', firm_business_num)
                        safe_set_value(ws, 'D28', firm_corp_num)
                        safe_set_value(ws, 'D29', firm_bank + " " + firm_depositor)
                        
                        # 💡 우측 사무소 정보
                        safe_set_value(ws, 'X25', firm_addr)
                        safe_set_value(ws, 'X26', firm_ceo)
                        safe_set_value(ws, 'X27', firm_business_num)
                        safe_set_value(ws, 'X28', firm_corp_num)
                        safe_set_value(ws, 'X29', firm_bank + " " + firm_depositor)

                        # Excel 파일 저장
                        excel_buffer = BytesIO()
                        wb.save(excel_buffer)
                        excel_buffer.seek(0)
                        
                        download_cols[1].download_button(
                            label=⬇️ Excel 다운로드 (클릭)",
                            data=excel_buffer,
                            file_name=f"영수증_{current_data['채무자']}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="dl_loan_excel"
                        )
                        st.success("✅ Excel 파일이 생성되었습니다!")
                        
                    except Exception as e:
                        st.error(f"Excel 생성 중 오류 발생: {e}")
                        st.exception(e)
                        import traceback
                        st.code(traceback.format_exc())

            st.markdown("---")
            if st.session_state['missing_templates']:
                 st.error(f"⚠️ **다음 템플릿 파일이 누락되었습니다:** {', '.join(st.session_state['missing_templates'])}")
            st.caption("ℹ️ 참고: 웹 환경에서는 Excel을 PDF로 자동 변환하는 기능(win32com)은 지원하지 않습니다. Excel 파일로 다운로드됩니다.")