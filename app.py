import streamlit as st
import math
import os
import io
import re
import requests
from datetime import datetime

# PDF 관련
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from PyPDF2 import PdfReader, PdfWriter

# 엑셀 관련
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

# =============================================================================
# 1. 설정 및 데이터
# =============================================================================
st.set_page_config(page_title="등기온 법무시스템", layout="wide", page_icon="⚖️")

st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight:bold; color:#d9534f; }
    .header-style { font-size:18px; font-weight:bold; color:#0056b3; margin-top:20px; margin-bottom:10px;}
    textarea { font-size: 14px !important; font-family: '맑은 고딕', sans-serif; }
    </style>
""", unsafe_allow_html=True)

CREDITORS = {
    "(주)티플레인대부 대표이사 윤웅원": "서울특별시 마포구 삼개로16, 2신관1층103호(도화동,근신빌딩)",
    "(주)유노스프레스티지대부 사내이사 한은수": "서울특별시 강남구 압구정로28길24, 5층 501호(신사동,디앤씨빌딩)",
    "(주)파트너스대부 사내이사 허성": "부산광역시 부산진구 서면문화로 43, 2층(부전동)",
    "(주)드림앤캐쉬대부 대표이사 김재섭": "서울특별시 강남구 압구정로28길24, 6층 601호(신사동,디앤씨빌딩)",
    "(주)마젤란트러스트대부 대표이사 김병수": "서울특별시 서초구 강남대로34길 7, 7층(양재동,이안빌딩)",
    "(주)하이클래스대부 사내이사 성윤호": "서울특별시 강남구 도곡로 188, 3층 4호(도곡동,도곡스퀘어)"
}

# 템플릿 파일 URL (깃허브 등을 쓸 때 사용)
TEMPLATE_URLS = {} 

# =============================================================================
# 2. 계산 로직
# =============================================================================
def floor_10(n): return math.floor(n / 10) * 10

def lookup_base_fee(amount):
    if amount <= 30000000: return 150000
    elif amount <= 45000000: return 200000
    elif amount <= 60000000: return 250000
    elif amount <= 106500000: return 300000
    elif amount <= 150000000: return 350000
    elif amount <= 225000000: return 400000
    return 450000

def calculate_all(amount, parcels, rate, is_addr, addr_count, show_fee, creditor_name):
    # 1. 공과금
    reg_tax = floor_10(amount * 0.002)
    edu_tax = floor_10(reg_tax * 0.2)
    
    # [수정됨] 기본 증지대 18,000원 (필지당)
    stamp = 18000 * parcels
    
    bond = 0
    if amount >= 20000000:
        bond = math.ceil(amount * 0.01 / 10000) * 10000
    bond_disc = floor_10(bond * rate / 100)

    # 2. 주소변경 비용
    addr_svc_fee = 0
    if is_addr:
        reg_tax += 6000 * addr_count
        edu_tax += 1200 * addr_count
        stamp += 3000 * addr_count # 주소변경 증지 추가
        if creditor_name and "유노스" in creditor_name:
            addr_svc_fee = 20000 * addr_count
        else:
            addr_svc_fee = 20000 * addr_count

    # 3. 보수료
    base_fee = lookup_base_fee(amount)
    cost_cert = 50000; cost_traffic = 100000; cost_cause = 50000
    if creditor_name and "유노스" in creditor_name:
        cost_cert = 20000; cost_traffic = 0; cost_cause = 0
    
    supply_val = base_fee + addr_svc_fee
    vat = math.floor(supply_val * 0.1)
    
    tax_total = reg_tax + edu_tax + stamp + bond_disc + cost_cert + cost_traffic + cost_cause
    fee_total = supply_val + vat
    
    # 보수액 미표시 옵션
    fee_display = fee_total if show_fee else 0
    grand_total = tax_total + fee_display

    return {
        "reg": reg_tax, "edu": edu_tax, "stamp": stamp, "bond": bond_disc,
        "cert": cost_cert, "traffic": cost_traffic, "cause": cost_cause,
        "supply": supply_val, "vat": vat, "fee_total": fee_total,
        "tax_total": tax_total, "grand_total": grand_total,
        "addr_fee": addr_svc_fee, "base_fee": base_fee,
        "show_fee": show_fee,
        "raw_fee_total": fee_total, "raw_supply": supply_val, "raw_vat": vat, "raw_grand_total": grand_total
    }

# =============================================================================
# 3. 문서 생성 (PDF / Excel)
# =============================================================================
def register_font():
    font_path = "Malgun.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Korean', font_path))
        pdfmetrics.registerFont(TTFont('Korean-Bold', font_path))
        return 'Korean'
    return 'Helvetica'

def draw_fit_text(c, text, x, y, max_width, font_name, max_size=11, min_size=6):
    if not text: return
    current_size = max_size
    text_width = pdfmetrics.stringWidth(text, font_name, current_size)
    while text_width > max_width and current_size > min_size:
        current_size -= 0.5
        text_width = pdfmetrics.stringWidth(text, font_name, current_size)
    c.setFont(font_name, current_size)
    c.drawString(x, y, text)

# [A] 계약서 PDF 생성 (3페이지 전체 유지)
def generate_contract_pdf(template_file, data):
    font_name = register_font()
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    c.setFont(font_name, 11)
    MAX_TEXT_WIDTH = 380

    # Page 1: 기본 정보
    if data["date"]: c.drawString(480, height - 85, data["date"])
    if data["creditor_name"]: c.drawString(157, height - 134, data["creditor_name"])
    if data["creditor_addr"]: draw_fit_text(c, data["creditor_addr"], 157, height - 150, MAX_TEXT_WIDTH, font_name)
    if data["debtor_name"]: c.drawString(157, height - 172, data["debtor_name"])
    if data["debtor_addr"]: draw_fit_text(c, data["debtor_addr"], 157, height - 190, MAX_TEXT_WIDTH, font_name)
    if data["owner_name"]: c.drawString(157, height - 212, data["owner_name"])
    if data["owner_addr"]: draw_fit_text(c, data["owner_addr"], 157, height - 230, MAX_TEXT_WIDTH, font_name)
    c.drawString(65, height - 343, "한정근담보")
    if data["claim_amount"]: c.drawString(150, height - 535, data["claim_amount"])
    
    c.showPage()
    c.setFont(font_name, 11)

    # Page 2: 서명
    if data["date"]: c.drawString(180, height - 270, data["date"])
    contract_type = data.get("contract_type", "개인")
    if contract_type == "개인":
        if data["debtor_name"]: c.drawString(450, height - 270, data["debtor_name"])
    elif contract_type == "3자담보":
        if data["owner_name"]: c.drawString(490, height - 270, data["owner_name"])
    elif contract_type == "공동담보":
        if data["debtor_name"]: c.drawString(450, height - 270, data["debtor_name"])
        if data["owner_name"]: c.drawString(490, height - 270, data["owner_name"])
    c.showPage()
    c.setFont(font_name, 11)

    # Page 3: 부동산 표시
    base_x = 35; base_y = height - 80; gap = 16
    lines = data["estate_text"].split('\n')
    for i, line in enumerate(lines):
        if line.strip(): c.drawString(base_x, base_y - (i * gap), line.strip())
    c.save(); packet.seek(0)
    
    overlay_pdf = PdfReader(packet)
    template_pdf = PdfReader(template_file)
    writer = PdfWriter()
    
    for i in range(len(template_pdf.pages)):
        page = template_pdf.pages[i]
        if i < len(overlay_pdf.pages):
            page.merge_page(overlay_pdf.pages[i])
        writer.add_page(page)
    
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output

# [B] 엑셀 템플릿 채우기
def fill_excel_template(template_file, res_data, basic_info):
    wb = load_workbook(template_file)
    ws = wb.active
    ws['B4'] = basic_info['creditor']; ws['V4'] = basic_info['debtor']
    ws['AG5'] = basic_info['amount']; ws['Y7'] = basic_info.get('estate_short', '')
    ws['AH14'] = res_data['bond']; ws['AH15'] = res_data['cert']
    ws['AH16'] = res_data['cause']; ws['AH17'] = res_data['addr_fee']
    ws['AH21'] = res_data['tax_total']
    # 엑셀 합계: 보수 포함된 최종 금액으로 설정
    ws['Y22'] = res_data['grand_total'] if res_data['show_fee'] else res_data['tax_total']
    
    output = io.BytesIO(); wb.save(output); output.seek(0)
    return output

# =============================================================================
# 4. 웹 UI 구성
# =============================================================================
st.title("🧾 등기온 근저당권설정 자동화")

st.markdown("<div class='header-style'>1. 기본 정보 입력</div>", unsafe_allow_html=True)

with st.container():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        date_val = st.date_input("작성일자", datetime.now())
        date_str = date_val.strftime("%Y년 %m월 %d일")
    with col2:
        contract_type = st.radio("계약 유형", ["개인", "3자담보", "공동담보"], horizontal=True)
    with col3: pass 

    st.markdown("---")
    
    c_cr1, c_cr2 = st.columns([1, 2])
    with c_cr1:
        creditor_select = st.selectbox("채권자(금융사)", ["직접입력"] + list(CREDITORS.keys()))
        if creditor_select in CREDITORS:
            creditor_final = creditor_select; creditor_addr_def = CREDITORS[creditor_select]
        else:
            creditor_final = st.text_input("채권자명 직접입력"); creditor_addr_def = ""
    with c_cr2:
        creditor_addr = st.text_input("채권자 주소", value=creditor_addr_def)

    c_db1, c_db2 = st.columns([1, 2])
    with c_db1: debtor_name = st.text_input("채무자 성명")
    with c_db2: debtor_addr = st.text_input("채무자 주소")

    c_ow1, c_ow2 = st.columns([1, 2])
    with c_ow1: owner_name = st.text_input("설정자 성명") 
    with c_ow2: owner_addr = st.text_input("설정자 주소")

    st.markdown("---")
    c_money1, c_money2, c_money3 = st.columns([2, 1, 1])
    
    with c_money1:
        # [채권최고액 콤마 자동 변환 로직]
        if "amount_str" not in st.session_state:
            st.session_state.amount_str = "0"
            
        def on_amount_change():
            # 입력된 값에서 숫자만 추출
            raw_val = re.sub(r'[^\d]', '', st.session_state.amount_input_key)
            if raw_val:
                # 콤마 포맷팅하여 저장
                st.session_state.amount_str = f"{int(raw_val):,}"
            else:
                st.session_state.amount_str = "0"

        # 텍스트 입력으로 받고, 엔터 치면 포맷팅된 값으로 바뀜
        st.text_input("채권최고액 (원)", key="amount_input_key", value=st.session_state.amount_str, on_change=on_amount_change)
        
        # 계산용 정수 변환
        amount_input = int(re.sub(r'[^\d]', '', st.session_state.amount_str or "0"))

    with c_money2: parcels_input = st.number_input("필지수", min_value=1, value=1)
    with c_money3: rate_input = st.number_input("할인율(%)", value=11.5, step=0.1, format="%.2f")

    st.markdown("##### 🏠 부동산의 표시 (3페이지 출력)")
    default_estate = """[토지]\n서울특별시 강남구 대치동 123-45\n대 300㎡\n\n[건물]\n서울특별시 강남구 대치동 123-45\n철근콘크리트구조 슬래브지붕 2층 단독주택\n1층 100㎡\n2층 100㎡"""
    estate_text = st.text_area("부동산 표시 입력", value=default_estate, height=380)

# 2. 비용 계산
st.markdown("<div class='header-style'>2. 비용 산출 및 견적</div>", unsafe_allow_html=True)
c_opt1, c_opt2 = st.columns([1, 4])
with c_opt1:
    is_addr_change = st.checkbox("주소변경 포함", value=False)
    show_fee_opt = st.checkbox("보수액 표시", value=True)
with c_opt2:
    addr_count = st.number_input("변경 인원", min_value=1, value=1) if is_addr_change else 1

res = calculate_all(amount_input, parcels_input, rate_input, is_addr_change, addr_count, show_fee_opt, creditor_final)

c_res1, c_res2, c_res3 = st.columns(3)
with c_res1:
    st.info("💰 보수액")
    st.metric("보수 총액", f"{res['raw_fee_total']:,} 원")
with c_res2:
    st.warning("🏛️ 공과금")
    st.metric("공과금 소계", f"{res['tax_total']:,} 원")
with c_res3:
    st.error("🧾 총 청구금액")
    st.markdown(f"<p class='big-font'>{res['raw_grand_total'] if show_fee_opt else res['tax_total']:,} 원</p>", unsafe_allow_html=True)

# 3. 문서 생성
st.markdown("---")
st.markdown("<div class='header-style'>3. 문서 생성 및 다운로드</div>", unsafe_allow_html=True)

col_doc1, col_doc2 = st.columns(2)

doc_info = {
    'date': date_str, 'creditor': creditor_final, 'debtor': debtor_name, 'amount': amount_input,
    'estate_short': estate_text.split('\n')[1] if len(estate_text.split('\n')) > 1 else "" 
}
pdf_data = {
    "date": date_str, "creditor_name": creditor_final, "creditor_addr": creditor_addr,
    "debtor_name": debtor_name, "debtor_addr": debtor_addr,
    "owner_name": owner_name, "owner_addr": owner_addr,
    "claim_amount": f"{amount_input:,} 원", "estate_text": estate_text, "contract_type": contract_type
}

with col_doc1:
    st.markdown("##### 📄 계약서 PDF")
    contract_file = st.file_uploader("계약서 템플릿(PDF) 업로드", type="pdf", key="contract")
    if contract_file and st.button("계약서 생성"):
        try:
            pdf_bytes = generate_contract_pdf(contract_file, pdf_data)
            st.download_button("📥 계약서 다운로드", pdf_bytes, f"계약서_{debtor_name}.pdf", "application/pdf")
        except Exception as e:
            st.error(f"오류: {e}")

with col_doc2:
    st.markdown("##### 📊 비용 엑셀")
    excel_file = st.file_uploader("영수증 템플릿(Excel) 업로드", type="xlsx", key="receipt")
    if excel_file and st.button("엑셀 영수증 생성"):
        try:
            excel_bytes = fill_excel_template(excel_file, res, doc_info)
            st.download_button("📥 엑셀 영수증 다운로드", excel_bytes, f"영수증_{debtor_name}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            st.error(f"오류: {e}")