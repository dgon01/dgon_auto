import streamlit as st
import os
import re
import math
from io import BytesIO
from datetime import datetime, date
import base64

# =============================================================================
# 0. 기본 설정 및 경로 (경로 문제 해결)
# =============================================================================

# 현재 실행 디렉토리를 기준으로 절대 경로 설정
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    """실행 파일 위치 기준 절대 경로 반환"""
    return os.path.join(APP_ROOT, relative_path)

st.set_page_config(
    layout="wide", 
    page_title="DG-Form | 등기온 전자설정 자동화",
    page_icon="🏠",
    initial_sidebar_state="collapsed"
)

# 로고 및 아이콘 설정
LOGO_PATH = resource_path("my_icon.ico")
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f: data = f.read()
        return base64.b64encode(data).decode()
    except: return None
logo_base64 = get_base64_image(LOGO_PATH)

# =============================================================================
# 1. 스타일 (디자인 100% 유지)
# =============================================================================
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

# 헤더 섹션 렌더링
header_html = f"""
<div class="header-container">
    <div class="logo-title-container">
        {'<img src="data:image/x-icon;base64,' + logo_base64 + '" class="header-logo" alt="DG-ON Logo">' if logo_base64 else ''}
        <div>
            <h1 class="header-title"><span class="title-dg">DG</span><span class="title-form">-Form</span></h1>
            <p class="header-subtitle">등기온 전자설정 자동화 시스템 | 법무법인 시화</p>
        </div>
    </div>
    <div class="header-right">
        <p style="margin: 0; font-size: 1.1rem; font-weight: 600;">부동산 등기는 등기온</p>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# =============================================================================
# 2. 라이브러리 및 파일 설정
# =============================================================================

# Excel (영수증)
try:
    import openpyxl
    EXCEL_OK = True
except Exception:
    EXCEL_OK = False

# PDF 라이브러리
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from PyPDF2 import PdfReader, PdfWriter
    from fpdf import FPDF
    LIBS_OK = True
    FPDF_OK = True
except Exception:
    LIBS_OK = False
    FPDF_OK = False

# 템플릿 파일 정의 (경로 자동 인식)
TEMPLATE_FILENAMES = {
    "개인": "1.pdf",
    "3자담보": "2.pdf",
    "공동담보": "3.pdf",
    "자필_전자": "자필서명정보 템플릿.pdf",       # 기존
    "자필_서면": "자필서명정보_서면_템플릿.pdf", # 추가된 요구사항
    "영수증": "영수증_템플릿.xlsx"
}

# 폰트 경로
FONT_PATH = resource_path("Malgun.ttf")

# 템플릿 상태 확인
if 'template_status' not in st.session_state:
    st.session_state['template_status'] = {}
    for key, filename in TEMPLATE_FILENAMES.items():
        path = resource_path(filename)
        st.session_state['template_status'][key] = path if os.path.exists(path) else None

# 금융사 정보
CREDITORS = {
    "(주)티플레인대부 대표이사 윤웅원": {"addr": "서울특별시 마포구 삼개로16, 2신관1층103호(도화동,근신빌딩)", "corp_num": "110111-7350161"},
    "(주)유노스프레스티지대부 사내이사 한은수": {"addr": "서울특별시 강남구 압구정로28길24, 5층 501호(신사동,디앤씨빌딩)", "corp_num": "110111-4138560"},
    "(주)파트너스대부 사내이사 허성": {"addr": "부산광역시 부산진구 서면문화로 43, 2층(부전동)", "corp_num": "180111-1452175"},
    "(주)드림앤캐쉬대부 대표이사 김재섭": {"addr": "서울특별시 강남구 압구정로28길24, 6층 601호(신사동,디앤씨빌딩)", "corp_num": "110111-4176552"},
    "(주)마젤란트러스트대부 대표이사 김병수": {"addr": "서울특별시 서초구 강남대로34길 7, 7층(양재동,이안빌딩)", "corp_num": "110111-6649979"},
    "(주)하이클래스대부 사내이사 성윤호": {"addr": "서울특별시 강남구 도곡로 188, 3층 4호(도곡동,도곡스퀘어)", "corp_num": "110111-0933512"}
}

# =============================================================================
# 3. 유틸리티 함수
# =============================================================================
def format_date_korean(date_obj):
    if isinstance(date_obj, date): return f"{date_obj.year}년 {date_obj.month:02d}월 {date_obj.day:02d}일"
    return str(date_obj)

def format_number_with_comma(num_str):
    if num_str is None: return ""
    numbers = re.sub(r'[^\d]', '', str(num_str))
    if not numbers: return ""
    return "{:,}".format(int(numbers))

def remove_commas(v):
    if v is None: return ""
    return str(v).replace(',', '')

def floor_10(v): return math.floor(v / 10) * 10

def lookup_base_fee(amount):
    LOOKUP_KEYS = [0, 30_000_000, 45_000_000, 60_000_000, 106_500_000, 150_000_000, 225_000_000]
    LOOKUP_VALS = [150_000, 200_000, 250_000, 300_000, 350_000, 400_000, 450_000]
    for i in range(len(LOOKUP_KEYS) - 1, -1, -1):
        if amount > LOOKUP_KEYS[i]: return LOOKUP_VALS[i]
    return LOOKUP_VALS[0]

def get_rate():
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

# PDF 생성 관련 (ReportLab & FPDF)
if LIBS_OK:
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
        # 말소 문서 등 다른 문서 타입 처리
        if data.get("doc_type"):
            pass 
        
        # 1탭 계약서 오버레이
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
        if contract_type == "개인" and data.get("debtor_name"): c.drawString(450, height - 270, data["debtor_name"])
        elif contract_type == "3자담보" and data.get("owner_name"): c.drawString(490, height - 270, data["owner_name"])
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
# 4. Excel (영수증) 생성 로직 (경로 문제 해결 포함)
# =============================================================================
def create_receipt_excel(data, template_path=None):
    if not EXCEL_OK: return None
    
    # 템플릿 경로가 없거나 파일이 없으면 기본 생성
    if not template_path or not os.path.exists(template_path):
        wb = openpyxl.Workbook(); ws = wb.active
        # 간단 생성 로직 (생략 - 템플릿 사용 권장)
    else:
        wb = openpyxl.load_workbook(template_path); ws = wb.active
        client = data.get('client', {})
        
        # 1탭 날짜 입력 (AG2)
        ws['AG2'] = data.get('date_input', '')
        
        ws['B4'] = client.get('금융사', '')
        ws['V4'] = client.get('채무자', '')
        # 채권최고액 숫자만
        amt = re.sub(r'[^\d]', '', str(client.get('채권최고액', '0')))
        ws['AG5'] = int(amt) if amt else 0
        ws['Y7'] = client.get('물건지', '')
        
        cost_items = data.get('cost_items', {})
        ws['AH11'] = int(cost_items.get('등록면허세', 0))
        ws['AH12'] = int(cost_items.get('지방교육세', 0))
        ws['AH13'] = int(cost_items.get('증지대', 0))
        ws['AH14'] = int(cost_items.get('채권할인', 0))
        ws['AH15'] = int(cost_items.get('제증명', 0))
        ws['AH16'] = int(cost_items.get('원인증서', 0))
        ws['AH17'] = int(cost_items.get('주소변경', 0))
        ws['AH18'] = int(cost_items.get('선순위말소', 0))
        
        if int(cost_items.get('교통비', 0)) > 0:
            ws['AD19'] = '교통비'; ws['AH19'] = int(cost_items['교통비'])
        else: ws['AD19'] = None; ws['AH19'] = None
            
        if int(cost_items.get('확인서면', 0)) > 0:
            ws['AD20'] = '확인서면'; ws['AH20'] = int(cost_items['확인서면'])
        else: ws['AD20'] = None; ws['AH20'] = None

    output = BytesIO(); wb.save(output); output.seek(0)
    return output

# =============================================================================
# 5. 메인 UI (Streamlit)
# =============================================================================

# 세션 상태 초기화
if 't1_debtor_name' not in st.session_state: st.session_state['t1_debtor_name'] = ""
if 't1_owner_name' not in st.session_state: st.session_state['t1_owner_name'] = ""
if 't1_debtor_addr' not in st.session_state: st.session_state['t1_debtor_addr'] = ""
if 't1_owner_addr' not in st.session_state: st.session_state['t1_owner_addr'] = ""
if 'input_amount' not in st.session_state: st.session_state['input_amount'] = ""
if 'input_collateral_addr' not in st.session_state: st.session_state['input_collateral_addr'] = ""
if 'estate_text' not in st.session_state: st.session_state['estate_text'] = """[토지]\n서울특별시 강남구 대치동 123번지\n대 300㎡\n\n[건물]\n서울특별시 강남구 대치동 123번지\n철근콘크리트조 슬래브지붕 5층 주택\n1층 100㎡\n2층 100㎡"""
if 'contract_type' not in st.session_state: st.session_state['contract_type'] = "개인"
# Tab 3 수기비용 초기화
manual_keys = ['cost_manual_제증명', 'cost_manual_교통비', 'cost_manual_원인증서', 'cost_manual_주소변경', 'cost_manual_확인서면', 'cost_manual_선순위 말소']
for k in manual_keys:
    if k not in st.session_state: st.session_state[k] = "0"
if 'add_fee_val' not in st.session_state: st.session_state['add_fee_val'] = "0"
if 'etc_fee_val' not in st.session_state: st.session_state['etc_fee_val'] = "0"
if 'disc_fee_val' not in st.session_state: st.session_state['disc_fee_val'] = "0"

tab1, tab2, tab3, tab4 = st.tabs(["📄 근저당권설정 계약서", ✍️ 자필서명정보", "🧾 비용 계산 및 영수증", "🗑️ 말소 문서"])

# -----------------------------------------------------------------------------
# Tab 1: 근저당권설정 계약서 (UI 100% 유지)
# -----------------------------------------------------------------------------
with tab1:
    col_header = st.columns([5, 1])
    col_header[0].markdown("### 📝 근저당권설정 계약서 작성")
    if col_header[1].button("🔄 초기화", type="secondary", key="reset_tab1"):
        st.session_state['input_date'] = datetime.now().date()
        st.session_state['t1_debtor_name'] = ""
        st.session_state['t1_debtor_addr'] = ""
        st.session_state['t1_owner_name'] = ""
        st.session_state['t1_owner_addr'] = ""
        st.session_state['contract_type'] = "개인"
        st.session_state['guarantee'] = "한정근담보"
        st.session_state['input_amount'] = ""
        st.session_state['input_collateral_addr'] = ""
        st.rerun()
    st.markdown("---")
    
    with st.expander("📌 기본 정보", expanded=True):
        current_date = st.session_state.get('input_date', datetime.now().date())
        st.session_state['input_date'] = st.date_input("작성일자", value=current_date)

    with st.expander("👤 당사자 정보", expanded=True):
        creditor_list = list(CREDITORS.keys()) + ["🖊️ 직접입력"]
        selected_creditor = st.selectbox("채권자 선택", options=creditor_list, key='t1_creditor_select')
        st.session_state['input_creditor'] = selected_creditor
        
        if selected_creditor == "🖊️ 직접입력":
            st.session_state['input_creditor_name'] = st.text_input("채권자 성명/상호", value=st.session_state.get('input_creditor_name', ''))
            st.session_state['input_creditor_corp_num'] = st.text_input("법인번호", value=st.session_state.get('input_creditor_corp_num', ''))
            st.session_state['input_creditor_addr'] = st.text_area("채권자 주소", value=st.session_state.get('input_creditor_addr', ''), height=80)
        else:
            info = CREDITORS[selected_creditor]
            st.text_input("법인번호", value=info['corp_num'], disabled=True)
            st.text_area("채권자 주소", value=info['addr'], disabled=True)
            st.session_state['input_creditor_name'] = selected_creditor
            st.session_state['input_creditor_corp_num'] = info['corp_num']
            st.session_state['input_creditor_addr'] = info['addr']

        st.text_input("채무자 성명", key='t1_debtor_name')
        st.text_area("채무자 주소", key='t1_debtor_addr', height=80)
        st.text_input("설정자 성명", key='t1_owner_name')
        st.text_area("설정자 주소", key='t1_owner_addr', height=80)

    with st.expander("🤝 담보 및 계약 정보", expanded=True):
        st.session_state['contract_type'] = st.radio("계약서 유형", ["개인", "3자담보", "공동담보"], horizontal=True)
        st.session_state['guarantee'] = st.text_input("피담보채무", value="한정근담보")
        
        def format_amt():
            raw = st.session_state.get('amount_raw', '')
            st.session_state['input_amount'] = format_number_with_comma(raw)
        st.text_input("채권최고액", key='amount_raw', on_change=format_amt, placeholder="숫자만 입력")
        if st.session_state['input_amount']:
            st.info(f"💰 **{number_to_korean(st.session_state['input_amount'])}**")
        
        col_addr1, col_addr2 = st.columns([5, 1])
        with col_addr1:
            st.text_area("물건지 주소 (수기 입력)", key='input_collateral_addr', height=80)
        with col_addr2:
            st.write(""); st.write("")
            
            # -----------------------------------------------------------------
            # [수정됨] 콜백 함수로 구현하여 키 충돌 오류 해결
            # -----------------------------------------------------------------
            def copy_debtor_addr():
                st.session_state['input_collateral_addr'] = st.session_state.get('t1_debtor_addr', "")
                
            st.button("📋\n채무자\n주소복사", on_click=copy_debtor_addr)

    st.markdown("---")
    st.markdown("### 🏠 부동산의 표시")
    col_estate, col_pdf = st.columns([3, 1])
    with col_estate:
        st.text_area("부동산 표시 내용", key='estate_text', height=300)
    with col_pdf:
        st.markdown("#### 📑 파일 생성")
        tpl_path = st.session_state['template_status'].get(st.session_state['contract_type'])
        if st.button("🚀 계약서\nPDF 생성", disabled=not (LIBS_OK and tpl_path), use_container_width=True):
            data = {
                "date": format_date_korean(st.session_state['input_date']),
                "creditor_name": st.session_state['input_creditor_name'],
                "creditor_addr": st.session_state['input_creditor_addr'],
                "debtor_name": st.session_state['t1_debtor_name'],
                "debtor_addr": st.session_state['t1_debtor_addr'],
                "owner_name": st.session_state['t1_owner_name'],
                "owner_addr": st.session_state['t1_owner_addr'],
                "guarantee_type": st.session_state['guarantee'],
                "claim_amount": convert_multiple_amounts_to_korean(remove_commas(st.session_state['input_amount'])),
                "estate_list": st.session_state['estate_text'].strip().split("\n"),
                "contract_type": st.session_state['contract_type']
            }
            pdf = make_pdf(tpl_path, data)
            st.download_button("⬇️ 다운로드", pdf, f"근저당권설정_{data['debtor_name']}.pdf", "application/pdf", use_container_width=True)

# -----------------------------------------------------------------------------
# Tab 2: 자필서명정보 (수정됨: 2가지 템플릿 + 동기화 버튼)
# -----------------------------------------------------------------------------
with tab2:
    st.markdown("### ✍️ 자필서명정보 작성")
    
    # 상단 컨트롤: 접수 유형 & 동기화
    c1, c2 = st.columns([2, 1])
    with c1:
        submit_type = st.radio("접수 유형", ["전자접수", "서면접수"], horizontal=True, key="sig_type")
    with c2:
        if st.button("🔄 1탭 정보 가져오기", key="sync_tab2", use_container_width=True):
            st.session_state['sig_date'] = st.session_state['input_date']
            st.session_state['sig_debtor'] = st.session_state['t1_debtor_name']
            st.session_state['sig_owner'] = st.session_state['t1_owner_name']
            st.session_state['sig_estate'] = st.session_state['estate_text']
            st.rerun()

    st.markdown("---")
    
    # 입력 폼
    if 'sig_date' not in st.session_state: st.session_state['sig_date'] = datetime.now().date()
    st.date_input("작성일자", key="sig_date")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.text_input("설정자(채무자)", key="sig_debtor")
        st.text_input("주민등록번호", key="sig_debtor_rrn")
    with col_p2:
        st.text_input("설정자(소유자)", key="sig_owner")
        st.text_input("주민등록번호", key="sig_owner_rrn")
        
    st.text_area("부동산의 표시", key="sig_estate", height=150)
    
    # PDF 생성
    template_key = "자필_전자" if submit_type == "전자접수" else "자필_서면"
    sig_tpl_path = st.session_state['template_status'].get(template_key)
    
    if st.button("📄 자필서명 PDF 생성", disabled=not (LIBS_OK and sig_tpl_path), use_container_width=True):
        data = {
            "date": format_date_korean(st.session_state['sig_date']),
            "debtor_name": st.session_state.get('sig_debtor', ''),
            "debtor_rrn": st.session_state.get('sig_debtor_rrn', ''),
            "owner_name": st.session_state.get('sig_owner', ''),
            "owner_rrn": st.session_state.get('sig_owner_rrn', ''),
            "estate_text": st.session_state.get('sig_estate', '')
        }
        pdf = make_signature_pdf(sig_tpl_path, data)
        st.download_button("⬇️ 다운로드", pdf, f"자필서명_{submit_type}_{data['debtor_name']}.pdf", "application/pdf", use_container_width=True)


# -----------------------------------------------------------------------------
# Tab 3: 비용 계산 및 영수증 (수정됨: 동기화 버튼 + 디자인 유지)
# -----------------------------------------------------------------------------
with tab3:
    # 헤더 및 컨트롤
    col_h1, col_h2, col_h3 = st.columns([4, 1.5, 1])
    col_h1.markdown("### 🧾 등기비용 계산기")
    with col_h2:
        # [수정됨] 1탭 정보 가져오기 버튼 (명시적 동기화)
        if st.button("🔄 1탭 정보 가져오기", key="sync_tab3", use_container_width=True):
            st.session_state['calc_amount'] = st.session_state['input_amount']
            st.session_state['calc_debtor'] = st.session_state['t1_debtor_name']
            
            # 물건지: 1탭 수기입력 우선, 없으면 estate_text에서 추출
            addr = st.session_state['input_collateral_addr']
            if not addr: addr = extract_address_from_estate(st.session_state['estate_text'])
            st.session_state['calc_estate'] = addr
            
            # 금융사: 1탭 선택값
            cred = st.session_state.get('input_creditor', '')
            if cred in list(CREDITORS.keys()) + ["🖊️ 직접입력"]:
                st.session_state['calc_creditor_select'] = cred
            
            st.rerun()
            
    with col_h3:
        if st.button("🔄 초기화", type="secondary", key="reset_tab3", use_container_width=True):
            st.session_state['calc_amount'] = ""; st.session_state['calc_debtor'] = ""
            st.session_state['calc_estate'] = ""; st.session_state['calc_parcels'] = 1
            st.rerun()
            
    st.markdown("---")

    # 입력 섹션 (3단)
    # 초기값 설정 (동기화 안했을 때 대비)
    if 'calc_amount' not in st.session_state: st.session_state['calc_amount'] = ""
    if 'calc_debtor' not in st.session_state: st.session_state['calc_debtor'] = ""
    if 'calc_estate' not in st.session_state: st.session_state['calc_estate'] = ""
    if 'calc_parcels' not in st.session_state: st.session_state['calc_parcels'] = 1
    if 'calc_rate' not in st.session_state: st.session_state['calc_rate'] = "12.0"

    row1_c1, row1_c3, row1_c4 = st.columns([2, 1, 1.2])
    with row1_c1:
        def fmt_calc_amt(): st.session_state['calc_amount'] = format_number_with_comma(st.session_state['calc_amount'])
        st.text_input("채권최고액", key='calc_amount', on_change=fmt_calc_amt)
    with row1_c3:
        st.number_input("필지수", min_value=1, key='calc_parcels')
    with row1_c4:
        c_r, c_b = st.columns([2, 0.5])
        c_r.text_input("할인율(%)", key='calc_rate')
        if c_b.button("🔄", key="ref_rate"):
            st.session_state['calc_rate'] = f"{get_rate()*100:.4f}"; st.rerun()

    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        cred_opts = list(CREDITORS.keys()) + ["🖊️ 직접입력"]
        st.selectbox("금융사", options=cred_opts, key='calc_creditor_select')
    with row2_c2:
        st.text_input("채무자", key='calc_debtor')
    
    st.text_area("물건지", key='calc_estate', height=60)
    st.markdown("---")

    # 계산 로직
    # 금융사 수기 비용 자동 세팅
    sel_cred = st.session_state['calc_creditor_select']
    if sel_cred == "🖊️ 직접입력":
        # 직접입력이면 1탭의 직접입력값 사용 or 공란
        calc_cred_name = st.session_state.get('input_creditor_name', '직접입력')
        # 수기비용 초기화 (사용자가 입력하도록)
        # 단, 동기화 로직에 포함하지 않았으므로 여기서는 기존 값 유지 or 0
    else:
        calc_cred_name = sel_cred
        # 금융사별 비용 자동 적용 (유노스 등)
        if "유노스" in sel_cred:
            st.session_state['cost_manual_제증명'] = "20,000"
            st.session_state['cost_manual_교통비'] = "0"
            st.session_state['cost_manual_원인증서'] = "0"
        # 필요시 다른 금융사 로직 추가

    # 계산 실행
    amt_val = int(remove_commas(st.session_state['calc_amount']) or 0)
    base_fee = lookup_base_fee(amt_val)
    add_fee = int(remove_commas(st.session_state['add_fee_val']) or 0)
    etc_fee = int(remove_commas(st.session_state['etc_fee_val']) or 0)
    disc_fee = int(remove_commas(st.session_state['disc_fee_val']) or 0)
    
    # 보수액
    if 'show_fee' not in st.session_state: st.session_state['show_fee'] = True
    if st.session_state['show_fee']:
        supply = base_fee + add_fee + etc_fee - disc_fee
        vat = math.floor(max(0, supply) * 0.1)
        total_fee = supply + vat
    else:
        supply = 0; vat = 0; total_fee = 0

    # 공과금
    reg_tax = floor_10(amt_val * 0.002)
    edu_tax = floor_10(reg_tax * 0.2)
    parcels = st.session_state['calc_parcels']
    stamp = 15000 * parcels # 기본 증지대 등

    # 주소변경 포함 여부
    if 'use_addr' not in st.session_state: st.session_state['use_addr'] = False
    if 'addr_cnt' not in st.session_state: st.session_state['addr_cnt'] = 1
    
    if st.session_state['use_addr']:
        cnt = st.session_state['addr_cnt']
        reg_tax += 6000 * cnt
        edu_tax += 1200 * cnt
        stamp += 3000 * cnt
        # 수기비용 자동 추가
        unit_price = 20000 if "유노스" in calc_cred_name else 50000
        st.session_state['cost_manual_주소변경'] = format_number_with_comma(unit_price * cnt)
    else:
        st.session_state['cost_manual_주소변경'] = "0"

    # 채권
    try: rate = float(st.session_state['calc_rate']) / 100
    except: rate = 0
    bond = 0
    if amt_val >= 20000000: bond = math.ceil(amt_val * 0.01 / 10000) * 10000
    bond_disc = floor_10(bond * rate)

    # 수기비용 합산
    manual_total = 0
    for k in manual_keys:
        manual_total += int(remove_commas(st.session_state[k]) or 0)
    
    total_tax = reg_tax + edu_tax + stamp + bond_disc + manual_total
    grand_total = total_fee + total_tax

    # 결과 표시 UI (3단 - CSS 클래스 활용)
    def make_row(label, val, key, read_only=False):
        c1, c2 = st.columns([1, 1.8])
        with c1: st.markdown(f"<div class='row-label'>{label}</div>", unsafe_allow_html=True)
        with c2:
            if read_only: st.text_input(label, value=val, key=key, disabled=True, label_visibility="collapsed")
            else: 
                def fmt(): st.session_state[key] = format_number_with_comma(st.session_state[key])
                st.text_input(label, key=key, on_change=fmt, label_visibility="collapsed")

    col_inc, col_tax, col_pay = st.columns(3)

    # 1. 보수액
    with col_inc:
        st.markdown("<div class='section-header income-header'>💰 보수액 (Income)</div>", unsafe_allow_html=True)
        with st.container(border=True):
            make_row("기본료", format_number_with_comma(base_fee), "disp_base", True)
            make_row("추가보수", st.session_state['add_fee_val'], "add_fee_val")
            make_row("기타보수", st.session_state['etc_fee_val'], "etc_fee_val")
            make_row("할인금액", st.session_state['disc_fee_val'], "disc_fee_val")
            st.markdown("---")
            c_l, c_v = st.columns(2)
            c_l.markdown("**공급가액**"); c_v.markdown(f"<div style='text-align:right; color:#28a745;'>{format_number_with_comma(supply)} 원</div>", unsafe_allow_html=True)
            c_l.markdown("**부가세**"); c_v.markdown(f"<div style='text-align:right; color:#28a745;'>{format_number_with_comma(vat)} 원</div>", unsafe_allow_html=True)
            st.markdown(f"#### 보수 총액: <span style='color:#28a745'>{format_number_with_comma(total_fee)} 원</span>", unsafe_allow_html=True)

    # 2. 공과금
    with col_tax:
        st.markdown("<div class='section-header tax-header'>🏛️ 공과금 (Tax)</div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.caption("[자동 계산]")
            make_row("등록면허세", format_number_with_comma(reg_tax), "disp_reg", True)
            make_row("지방교육세", format_number_with_comma(edu_tax), "disp_edu", True)
            make_row("증지대", format_number_with_comma(stamp), "disp_stamp", True)
            make_row("채권할인", format_number_with_comma(bond_disc), "disp_bond", True)
            st.markdown("---"); st.caption("[수기 입력]")
            make_row("제증명", st.session_state['cost_manual_제증명'], "cost_manual_제증명")
            make_row("교통비", st.session_state['cost_manual_교통비'], "cost_manual_교통비")
            make_row("원인증서", st.session_state['cost_manual_원인증서'], "cost_manual_원인증서")
            make_row("주소변경", st.session_state['cost_manual_주소변경'], "cost_manual_주소변경", True) # 자동계산됨
            make_row("확인서면", st.session_state['cost_manual_확인서면'], "cost_manual_확인서면")
            make_row("선순위말소", st.session_state['cost_manual_선순위 말소'], "cost_manual_선순위 말소")
            st.markdown(f"#### 공과금 소계: <span style='color:#fd7e14'>{format_number_with_comma(total_tax)} 원</span>", unsafe_allow_html=True)

    # 3. 결제
    with col_pay:
        st.markdown("<div class='section-header total-header'>🧾 결제 및 청구</div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### 총 청구금액")
            st.markdown(f"<div class='total-box'><div class='total-amount'>{format_number_with_comma(grand_total)} 원</div></div>", unsafe_allow_html=True)
            st.markdown("---")
            st.checkbox("보수액 포함 표시", key='show_fee')
            st.markdown("#### ➕ 주소변경 추가")
            c1, c2 = st.columns(2)
            c1.checkbox("포함", key='use_addr')
            c2.number_input("인원", min_value=1, key='addr_cnt', label_visibility="collapsed")

    st.markdown("---")
    
    # 다운로드 버튼 영역
    d_c1, d_c2 = st.columns(2)
    
    # 데이터 패키징 (PDF/Excel용)
    final_data = {
        'date_input': format_date_korean(datetime.now().date()),
        'client': {
            '채권최고액': format_number_with_comma(amt_val),
            '필지수': str(parcels),
            '금융사': calc_cred_name,
            '채무자': st.session_state['calc_debtor'],
            '물건지': st.session_state['calc_estate']
        },
        'fee_items': { '기본료':base_fee, '추가보수':add_fee, '기타보수':etc_fee, '할인금액':disc_fee },
        'fee_totals': { '보수총액': total_fee },
        'cost_items': {
            '등록면허세': reg_tax, '지방교육세': edu_tax, '증지대': stamp, '채권할인': bond_disc,
            '제증명': int(remove_commas(st.session_state['cost_manual_제증명']) or 0),
            '교통비': int(remove_commas(st.session_state['cost_manual_교통비']) or 0),
            '원인증서': int(remove_commas(st.session_state['cost_manual_원인증서']) or 0),
            '주소변경': int(remove_commas(st.session_state['cost_manual_주소변경']) or 0),
            '확인서면': int(remove_commas(st.session_state['cost_manual_확인서면']) or 0),
            '선순위말소': int(remove_commas(st.session_state['cost_manual_선순위 말소']) or 0)
        },
        'cost_totals': { '공과금 총액': total_tax },
        'cost_section_title': '2. 공과금' if st.session_state['show_fee'] else '1. 공과금',
        'grand_total': grand_total
    }

    with d_c1:
        if st.button("📄 비용내역 PDF", disabled=not FPDF_OK, use_container_width=True):
            pdf_cv = PDFConverter(show_fee=st.session_state['show_fee'])
            pdf_buf = pdf_cv.output_pdf(final_data)
            st.download_button("⬇️ 다운로드", pdf_buf, f"비용내역_{final_data['client']['채무자']}.pdf", "application/pdf", use_container_width=True)

    with d_c2:
        receipt_tpl = st.session_state['template_status'].get('영수증')
        if st.button("🏦 영수증 Excel", disabled=not EXCEL_OK, use_container_width=True):
            xl_buf = create_receipt_excel(final_data, receipt_tpl)
            if xl_buf:
                st.download_button("⬇️ 다운로드", xl_buf, f"영수증_{final_data['client']['채무자']}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            else: st.error("엑셀 생성 실패 (라이브러리 확인)")

# -----------------------------------------------------------------------------
# Tab 4: 말소 문서 (수정됨: 공란/3자담보 로직 적용)
# -----------------------------------------------------------------------------
with tab4:
    st.markdown("### 🗑️ 말소 문서 작성")
    
    # 동기화 버튼 및 초기화
    h1, h2 = st.columns([5, 1.5])
    with h2:
        if st.button("🔄 1탭 정보 가져오기", key="sync_tab4", use_container_width=True):
            # 1. 등기의무자(금융사) -> 공란
            st.session_state['malso_obligor_corp'] = ""
            st.session_state['malso_obligor_rep'] = ""
            st.session_state['malso_obligor_id'] = ""
            st.session_state['malso_obligor_addr'] = ""
            
            # 2. 등기권리자 -> 로직 적용
            ctype = st.session_state.get('contract_type', '개인')
            if ctype == "3자담보":
                # 소유자만 입력
                st.session_state['malso_holder_debtor'] = ""
                st.session_state['malso_holder_debtor_addr'] = ""
                st.session_state['malso_holder_owner'] = st.session_state.get('t1_owner_name', '')
                st.session_state['malso_holder_owner_addr'] = st.session_state.get('t1_owner_addr', '')
            else:
                # 둘 다 입력 (개인/공동담보)
                st.session_state['malso_holder_debtor'] = st.session_state.get('t1_debtor_name', '')
                st.session_state['malso_holder_debtor_addr'] = st.session_state.get('t1_debtor_addr', '')
                st.session_state['malso_holder_owner'] = st.session_state.get('t1_owner_name', '')
                st.session_state['malso_holder_owner_addr'] = st.session_state.get('t1_owner_addr', '')
            
            # 3. 부동산 표시
            st.session_state['malso_estate_detail'] = st.session_state.get('estate_text', '')
            st.rerun()

    st.markdown("---")
    
    # 1. 말소 유형
    if 'malso_type' not in st.session_state: st.session_state['malso_type'] = "근저당권"
    m_cols = st.columns(3)
    for i, t in enumerate(["근저당권", "질권", "전세권"]):
        with m_cols[i]:
            if st.button(t, type="primary" if st.session_state['malso_type'] == t else "secondary", use_container_width=True):
                st.session_state['malso_type'] = t; st.rerun()
    
    # 2. 당사자 입력
    c_in1, c_in2 = st.columns(2)
    with c_in1:
        st.markdown("#### 1️⃣ 등기의무자 (금융사)")
        st.caption("※ 초기화(공란) 됩니다. 직접 입력하세요.")
        with st.container(border=True):
            st.text_input("법인명(성명)", key="malso_obligor_corp")
            st.text_input("대표자(지배인)", key="malso_obligor_rep")
            st.text_input("등록번호", key="malso_obligor_id")
            st.text_area("주소", key="malso_obligor_addr", height=80)
            
    with c_in2:
        st.markdown("#### 2️⃣ 등기권리자")
        with st.container(border=True):
            st.markdown("**[채무자]**")
            st.text_input("채무자 성명", key="malso_holder_debtor")
            st.text_area("채무자 주소", key="malso_holder_debtor_addr", height=60)
            st.markdown("---")
            st.markdown("**[소유자]**")
            st.text_input("소유자 성명", key="malso_holder_owner")
            st.text_area("소유자 주소", key="malso_holder_owner_addr", height=60)
            
    # 3. 등기정보
    st.markdown("---")
    col_inf1, col_inf2 = st.columns(2)
    with col_inf1:
        st.date_input("등기원인일", key="malso_cause_date", value=datetime.now().date())
        st.text_input("등기원인", value="해지", key="malso_cause")
    with col_inf2:
        st.text_input("등기목적", value=f"{st.session_state['malso_type']}말소", key="malso_purpose")
        
    st.text_area("부동산 표시", key="malso_estate_detail", height=150)
    st.text_area("말소할 등기", key="malso_cancel_text", placeholder="예) 2024년 10월 15일 접수 제12345호로 경료된 근저당권설정등기", height=80)
    
    # 4. 다운로드
    st.markdown("### 📥 문서 다운로드")
    MALSO_TEMPLATES = {
        "자필서명정보": "자필서명정보_말소_템플릿.pdf", # 파일명 확인 필요
        "위임장": "위임장_말소_템플릿.pdf",
        "해지증서": "해지증서_템플릿.pdf",
        "이관증명서": "이관증명서_템플릿.pdf"
    }
    # (여기서는 편의상 파일명이 없으면 자필서명정보_서면 등을 대체하거나 오류처리)
    
    dn_cols = st.columns(4)
    for i, (name, fname) in enumerate(MALSO_TEMPLATES.items()):
        with dn_cols[i]:
            path = resource_path(fname)
            # 파일이 없으면 버튼 비활성화
            is_ready = os.path.exists(path) and LIBS_OK
            if st.button(f"📄 {name}", key=f"btn_malso_{i}", disabled=not is_ready, use_container_width=True):
                # 말소용 PDF 데이터 생성 (간소화)
                m_data = {
                    "doc_type": name,
                    "date": format_date_korean(st.session_state['malso_cause_date']),
                    "obligor_corp": st.session_state.get('malso_obligor_corp', ''),
                    "debtor_name": st.session_state.get('malso_holder_debtor', ''),
                    # ... 나머지 필드도 make_pdf에서 활용 가능
                }
                pdf = make_pdf(path, m_data)
                st.download_button("저장", pdf, f"{name}_{m_data['obligor_corp']}.pdf", "application/pdf", key=f"dn_malso_{i}")

st.markdown("---")
st.markdown("""<div style='text-align: center; color: #6c757d; padding: 20px; background-color: white; border-radius: 10px; border: 2px solid #e1e8ed;'>
    <p style='margin: 0; font-size: 1rem; color: #00428B;'><strong>DG-Form 등기온 전자설정 자동화 시스템 | 법무법인 시화</strong></p>
    <p style='margin: 5px 0 0 0; font-size: 0.85rem; color: #6c757d;'>부동산 등기는 등기온</p></div>""", unsafe_allow_html=True)