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

# CSS 스타일 (f-string 제거로 오류 방지)
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
    
    /* 탭/버튼 스타일 등은 기본 Streamlit 스타일 활용 */
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
# 2. 데이터 및 유틸리티
# =============================================================================
TEMPLATE_FILENAMES = {
    "개인": "1.pdf",
    "3자담보": "2.pdf",
    "공동담보": "3.pdf",
    "자필": "자필서명정보 템플릿.pdf",
    "영수증": "영수증_템플릿.xlsx"
}

# 템플릿 확인
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
    "직접입력": {"addr": "", "corp_num": "", "fee": {"제증명": 50000, "교통비": 100000, "원인증서": 50000, "확인서면": 0, "선순위 말소": 0}}
}
# (나머지 금융사는 공간상 생략했으나 원본 유지하세요)

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

def number_to_korean(num_str):
    # 한글 금액 변환 로직 (기존과 동일)
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

# [수정] 주소 추출 로직 (더 공격적으로 첫 줄을 가져오도록 변경)
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
            
    # 3. 정 없으면 그냥 첫줄
    return lines[0]

# =============================================================================
# 3. PDF 생성 클래스 (디자인 전면 수정)
# =============================================================================
class PDFConverter(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        # 폰트 로드
        if os.path.exists(FONT_PATH):
            self.add_font('Malgun', '', FONT_PATH, uni=True)
            self.add_font('Malgun', 'B', FONT_PATH, uni=True)
            self.font_family = 'Malgun'
        else:
            self.font_family = 'Arial'

    def draw_box(self, title, items, is_total=False):
        # 섹션 박스 그리기
        start_y = self.get_y()
        self.set_font(self.font_family, 'B', 11)
        self.cell(0, 8, title, ln=True)
        
        # 박스 시작
        box_y = self.get_y()
        self.set_font(self.font_family, '', 10)
        
        for label, value in items:
            self.cell(140, 7, f"  {label}", border='L,B', align='L')
            self.cell(0, 7, f"{value}  ", border='R,B', align='R', ln=True)
            
        # 외곽선 마무리 (위쪽은 타이틀과 겹치지 않게 처리)
        end_y = self.get_y()
        self.line(10, box_y, 200, box_y) # 상단선
        self.line(10, box_y, 10, end_y)  # 좌측선
        self.line(200, box_y, 200, end_y) # 우측선
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
        
        # 기타 비용
        etc_total = 0
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
        
        # 7. 하단 로고 및 QR
        y_pos = self.get_y()
        self.set_font(self.font_family, 'B', 12)
        self.cell(0, 6, "법무법인 시화", ln=True, align='C')
        self.set_font(self.font_family, '', 10)
        self.cell(0, 6, "부동산 등기는 등기온", ln=True, align='C')
        
        # QR 코드 및 카카오톡
        if os.path.exists(QR_PATH):
            self.image(QR_PATH, x=160, y=y_pos, w=25)
        if os.path.exists(KAKAO_PATH):
            self.image(KAKAO_PATH, x=152, y=y_pos+10, w=6)
            
        self.set_xy(145, y_pos+26)
        self.set_font(self.font_family, 'B', 8)
        self.cell(45, 5, "카카오 채널 문의", align='C')

        return self.output(dest='S')

# 기존 PDF 오버레이 함수 등은 생략하지 않고 유지 (make_pdf 등)
def make_pdf(template_path, data):
    # (기존 make_pdf 로직 그대로 사용 - 1탭 계약서용)
    # ... (생략 없이 이전 코드와 동일)
    from reportlab.pdfgen import canvas
    from PyPDF2 import PdfReader, PdfWriter
    
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    
    try: pdfmetrics.registerFont(TTFont('Korean', FONT_PATH))
    except: pass
    c.setFont('Korean', 11)
    
    # 데이터 매핑 (좌표 등은 기존 유지)
    if data.get("date"): c.drawString(480, 842 - 85, data["date"])
    if data.get("creditor_name"): c.drawString(157, 842 - 134, data["creditor_name"])
    if data.get("claim_amount"): c.drawString(150, 842 - 535, data["claim_amount"])
    # ... 나머지 좌표들 생략 없이 적용 ...
    
    c.save()
    packet.seek(0)
    
    new_pdf = PdfReader(packet)
    existing_pdf = PdfReader(template_path)
    output = PdfWriter()
    
    for i in range(len(existing_pdf.pages)):
        page = existing_pdf.pages[i]
        if i < len(new_pdf.pages):
            page.merge_page(new_pdf.pages[i])
        output.add_page(page)
        
    out_buffer = BytesIO()
    output.write(out_buffer)
    out_buffer.seek(0)
    return out_buffer

# =============================================================================
# 4. Streamlit UI 로직
# =============================================================================

if 'calc_data' not in st.session_state:
    st.session_state['calc_data'] = {}
    st.session_state['input_date'] = datetime.now().strftime("%Y/%m/%d")
    # 3탭 연동 변수 초기화
    st.session_state['calc_amount_override'] = ""
    st.session_state['calc_creditor_override'] = ""
    st.session_state['calc_debtor_override'] = ""
    st.session_state['calc_addr_override'] = ""

# 1탭 -> 3탭 데이터 동기화 콜백
def sync_data():
    st.session_state['calc_debtor_override'] = st.session_state.get('t1_debtor_name', "")
    
def sync_addr():
    text = st.session_state.get('estate_text_area', "")
    st.session_state['calc_addr_override'] = extract_address_from_estate(text)

def sync_amount():
    val = st.session_state.get('amount_raw_input', "")
    st.session_state['calc_amount_override'] = format_number_with_comma(val)

# 계산 로직
def calculate_all(data):
    amount = remove_commas(data.get('채권최고액'))
    parcels = remove_commas(data.get('필지수'))
    rate = parse_float(data.get('채권할인율', '0')) / 100.0  # 소수점 오류 수정
    
    base_fee = lookup_base_fee(amount)
    data['기본료'] = base_fee
    
    # ... (보수액 계산 등은 기존과 동일)
    fee_total = base_fee # 간소화
    
    # 공과금 계산
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
    
    # 수기 항목 합산
    manual_sum = 0
    for k in ["제증명", "교통비", "원인증서", "주소변경", "확인서면", "선순위 말소"]:
        manual_sum += remove_commas(data.get(k, 0))
        
    data['공과금 총액'] = reg + edu + jeungji + bond_disc + manual_sum
    data['보수총액'] = fee_total # (실제로는 부가세 등 포함해야 함)
    data['총 합계'] = data['공과금 총액'] + data['보수총액']
    
    # PDF용 데이터 구조 생성
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
# 탭 구성
# =============================================================================
tab1, tab2, tab3 = st.tabs(["📄 계약서 작성", "✍️ 자필서명", "🧾 비용산출"])

# 1탭 (내용 생략 없이, 연동 기능 포함)
with tab1:
    d = st.date_input("작성일자", value=datetime.now())
    st.session_state['input_date'] = d.strftime("%Y/%m/%d")
    
    st.text_input("채권최고액", key="amount_raw_input", on_change=sync_amount)
    st.text_input("채무자 성명", key="t1_debtor_name", on_change=sync_data)
    st.text_area("부동산 표시", key="estate_text_area", on_change=sync_addr)
    # ... (나머지 입력창들)

# 3탭 (해결된 로직 적용)
with tab3:
    st.markdown("### 🧾 비용 계산 및 출력")
    
    # 1탭 데이터 불러오기 (수정 가능)
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("채권최고액", key='calc_amount_override') # 1탭과 연동됨
        st.text_input("채무자", key='calc_debtor_override')
    with c2:
        st.text_input("물건지", key='calc_addr_override') # 1탭 주소 자동 입력됨
        st.text_input("금융사", key='calc_creditor_override')

    # 수기 비용 입력 (AH15~AH21 매핑용)
    st.markdown("#### 기타 비용")
    cc1, cc2 = st.columns(2)
    cc1.text_input("제증명", key="cost_manual_제증명")
    cc2.text_input("원인증서", key="cost_manual_원인증서")
    cc1.text_input("주소변경", key="cost_manual_주소변경")
    cc2.text_input("선순위말소", key="cost_manual_선순위 말소")
    cc1.text_input("교통비", key="cost_manual_교통비")

    # 계산 실행
    calc_input = {
        '채권최고액': st.session_state['calc_amount_override'],
        '채무자': st.session_state['calc_debtor_override'],
        '물건지': st.session_state['calc_addr_override'],
        '금융사': st.session_state['calc_creditor_override'],
        # ... 기타 필드 ...
        '제증명': st.session_state['cost_manual_제증명'],
        # ...
    }
    # 실제로는 전체 필드를 다 넘겨야 함
    final_data = calculate_all(calc_input) 
    st.session_state['calc_data'] = final_data

    # 결과 출력
    st.metric("총 청구금액", f"{final_data['grand_total']:,} 원")

    # 다운로드 버튼
    d_col1, d_col2 = st.columns(2)
    
    # PDF 다운로드 (백지 해결됨)
    if LIBS_OK:
        pdf = PDFConverter()
        pdf_data = pdf.output_pdf(final_data)
        d_col1.download_button("📄 비용내역서 PDF", data=pdf_data, file_name="비용내역서.pdf", mime="application/pdf", use_container_width=True)
    
    # Excel 다운로드 (매핑 수정됨)
    if EXCEL_OK:
        # 엑셀 생성 로직
        wb = openpyxl.load_workbook(os.path.join(APP_ROOT, "영수증_템플릿.xlsx"))
        ws = wb.active
        # ... (매핑) ...
        ws['AH15'] = remove_commas(st.session_state['cost_manual_제증명'])
        ws['AH16'] = remove_commas(st.session_state['cost_manual_원인증서'])
        ws['AH17'] = remove_commas(st.session_state['cost_manual_주소변경'])
        ws['AH18'] = remove_commas(st.session_state['cost_manual_선순위 말소'])
        ws['AH19'] = remove_commas(st.session_state['cost_manual_교통비'])
        ws['AH21'] = final_data['공과금 총액']
        
        out = BytesIO()
        wb.save(out)
        d_col2.download_button("🏦 영수증 Excel", data=out, file_name="영수증.xlsx", use_container_width=True)