import streamlit as st
import math
import os
import io
import re
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
    reg_tax = floor_10(amount * 0.002)
    edu_tax = floor_10(reg_tax * 0.2)
    stamp = 15000 * parcels
    bond = 0
    if amount >= 20000000:
        bond = math.ceil(amount * 0.01 / 10000) * 10000
    bond_disc = floor_10(bond * rate / 100)

    addr_svc_fee = 0
    if is_addr:
        reg_tax += 6000 * addr_count
        edu_tax += 1200 * addr_count
        stamp += 3000 * addr_count
        if creditor_name and "유노스" in creditor_name:
            addr_svc_fee = 20000 * addr_count
        else:
            addr_svc_fee = 20000 * addr_count

    base_fee = lookup_base_fee(amount)
    cost_cert = 50000; cost_traffic = 100000; cost_cause = 50000
    if creditor_name and "유노스" in creditor_name:
        cost_cert = 20000; cost_traffic = 0; cost_cause = 0
    
    supply_val = base_fee + addr_svc_fee
    vat = math.floor(supply_val * 0.1)
    
    tax_total = reg_tax + edu_tax + stamp + bond_disc + cost_cert + cost_traffic + cost_cause
    fee_total = supply_val + vat
    grand_total = tax_total + fee_total

    return {
        "reg": reg_tax, "edu": edu_tax, "stamp": stamp, "bond": bond_disc,
        "cert": cost_cert, "traffic": cost_traffic, "cause": cost_cause,
        "supply": supply_val if show_fee else 0, 
        "vat": vat if show_fee else 0, 
        "fee_total": fee_total if show_fee else 0,
        "tax_total": tax_total, "grand_total": grand_total if show_fee else tax_total,
        "addr_fee": addr_svc_fee, "base_fee": base_fee,
        # 엑셀 매핑용 원본 데이터
        "raw_fee_total": fee_total, "raw_supply": supply_val, "raw_vat": vat, "raw_grand_total": grand_total
    }

# =============================================================================
# 3. 문서 생성 (PDF / Excel)
# =============================================================================
def draw_fit_text(c, text, x, y, max_width, font_name, max_size=11, min_size=6):
    if not text: return
    current_size = max_size
    text_width = pdfmetrics.stringWidth(text, font_name, current_size)
    while text_width > max_width and current_size > min_size:
        current_size -= 0.5
        text_width = pdfmetrics.stringWidth(text, font_name, current_size)
    c.setFont(font_name, current_size)
    c.drawString(x, y, text)

# [계약서 PDF 생성]
def generate_contract_pdf(template_file, data):
    font_path = "Malgun.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Korean', font_path))
        font_name = 'Korean'
    else:
        font_name = 'Helvetica'
    
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    c.setFont(font_name, 11)
    MAX_TEXT_WIDTH = 380

    if data["date"]: c.drawString(480, height - 85, data["date"])
    if data["creditor_name"]: c.drawString(157, height - 134, data["creditor_name"])
    if data["creditor_addr"]: draw_fit_text(c, data["creditor_addr"], 157, height - 150, MAX_TEXT_WIDTH, font_name)
    if data["debtor_name"]: c.drawString(157, height - 172, data["debtor_name"])
    if data["debtor_addr"]: draw_fit_text(c, data["debtor_addr"], 157, height - 190, MAX_TEXT_WIDTH, font_name)
    if data["owner_name"]: c.drawString(157, height - 212, data["owner_name"])
    if data["owner_addr"]: draw_fit_text(c, data["owner_addr"], 157, height - 230, MAX_TEXT_WIDTH, font_name)
    
    c.drawString(65, height - 343, "한정근담보")
    if data["claim_amount"]: c.drawString(150, height - 535, data["claim_amount"])
    
    c.showPage() # 1페이지 끝
    c.setFont(font_name, 11)

    # 2페이지 서명
    if data["date"]: c.drawString(180, height - 270, data["date"])
    contract_type = data.get("contract_type", "개인")
    if contract_type == "개인":
        if data["debtor_name"]: c.drawString(450, height - 270, data["debtor_name"])
    elif contract_type == "3자담보":
        if data["owner_name"]: c.drawString(490, height - 270, data["owner_name"])
    elif contract_type == "공동담보":
        if data["debtor_name"]: c.drawString(450, height - 270, data["debtor_name"])
        if data["owner_name"]: c.drawString(490, height - 270, data["owner_name"])
    
    c.showPage() # 2페이지 끝
    c.setFont(font_name, 11)

    # 3페이지 부동산 표시
    base_x = 35; base_y = height - 80; gap = 16
    estate_list = data["estate_text"].split('\n')
    for i, line in enumerate(estate_list):
        if line.strip(): c.drawString(base_x, base_y - (i * gap), line.strip())
    
    c.save()
    packet.seek(0)
    
    overlay_pdf = PdfReader(packet)
    template_pdf = PdfReader(template_file)
    writer = PdfWriter()
    
    for i in range(len(template_pdf.pages)):
        page = template_pdf.pages[i]
        if i < len(overlay_pdf.pages):
            page.merge_page(overlay_pdf.pages[i])
        writer.add_page(page)
    
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer

# [엑셀 생성 - 템플릿 채우기]
def fill_excel_template(template_file, res_data, basic_info):
    # 업로드된 템플릿 로드
    wb = load_workbook(template_file)
    ws = wb.active
    
    # 데이터 매핑 (기존 Tkinter 코드의 셀 주소 기준)
    ws['B4'] = basic_info['creditor']
    ws['V4'] = basic_info['debtor']
    ws['AG5'] = basic_info['amount']
    ws['Y7'] = basic_info.get('estate_short', '') # 물건지 주소
    
    # 공과금 상세
    ws['AH14'] = res_data['bond']        # 채권할인
    ws['AH15'] = res_data['cert']        # 제증명
    ws['AH16'] = res_data['cause']       # 원인증서
    ws['AH17'] = res_data['addr_fee']    # 주소변경비용
    # ws['AH18'] = 0 # 선순위 말소 (입력값 없으면 0)
    
    # 합계
    ws['AH21'] = res_data['tax_total']   # 공과금 소계
    ws['Y22'] = res_data['tax_total']    # 합계 (공과금만? 보수포함? 템플릿 수식 확인 필요)
    
    # 만약 보수료가 템플릿에 들어가는 칸이 있다면 추가 매핑 필요
    # 현재는 Tkinter 코드에 있는 것만 넣었습니다.
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
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
    with col3:
        pass 

    st.markdown("---")
    
    c_cr1, c_cr2 = st.columns([1, 2])
    with c_cr1:
        creditor_select = st.selectbox("채권자(금융사)", ["직접입력"] + list(CREDITORS.keys()))
        if creditor_select in CREDITORS:
            creditor_final = creditor_select
            creditor_addr_def = CREDITORS[creditor_select]
        else:
            creditor_final = st.text_input("채권자명 직접입력")
            creditor_addr_def = ""
    with c_cr2:
        creditor_addr = st.text_input("채권자 주소", value=creditor_addr_def)

    c_db1, c_db2 = st.columns([1, 2])
    with c_db1:
        debtor_name = st.text_input("채무자 성명")
    with c_db2:
        debtor_addr = st.text_input("채무자 주소")

    c_ow1, c_ow2 = st.columns([1, 2])
    with c_ow1:
        owner_name = st.text_input("설정자(소유자) 성명") 
    with c_ow2:
        owner_addr = st.text_input("설정자 주소")

    st.markdown("---")
    
    c_money1, c_money2, c_money3 = st.columns([2, 1, 1])
    with c_money1:
        amount_input = st.number_input("채권최고액 (원)", min_value=0, value=0, step=1000, format="%d")
    with c_money2:
        parcels_input = st.number_input("필지수", min_value=1, value=1)
    with c_money3:
        rate_input = st.number_input("채권할인율 (%)", value=11.5, step=0.1, format="%.2f")

    st.markdown("##### 🏠 부동산의 표시 (등기부등본 내용 - 3페이지 출력)")
    default_estate = """[토지]
서울특별시 강남구 대치동 123-45
대 300㎡

[건물]
서울특별시 강남구 대치동 123-45
철근콘크리트구조 슬래브지붕 2층 단독주택
1층 100㎡
2층 100㎡"""
    estate_text = st.text_area("부동산 표시 입력", value=default_estate, height=380)

# --- 2. 비용 계산 ---
st.markdown("<div class='header-style'>2. 비용 산출 및 견적</div>", unsafe_allow_html=True)

c_opt1, c_opt2 = st.columns([1, 4])
with c_opt1:
    is_addr_change = st.checkbox("주소변경 등기 포함", value=False)
    show_fee_opt = st.checkbox("보수액 포함 표시", value=True)
with c_opt2:
    addr_count = st.number_input("변경 인원 (명)", min_value=1, value=1, width=150) if is_addr_change else 1

res = calculate_all(amount_input, parcels_input, rate_input, is_addr_change, addr_count, show_fee_opt, creditor_final)

c_res1, c_res2, c_res3 = st.columns(3)

with c_res1:
    st.info("💰 보수액 (Income)")
    st.write(f"• 기본료: {res['base_fee']:,}")
    st.write(f"• 주소변경: {res['addr_fee']:,}")
    st.write(f"**공급가액:** {res['raw_supply']:,}")
    st.write(f"**부가세:** {res['raw_vat']:,}")
    st.metric("보수 총액", f"{res['raw_fee_total']:,} 원")

with c_res2:
    st.warning("🏛️ 공과금 (Tax)")
    st.write(f"• 등록세/교육세: {res['reg']:,} / {res['edu']:,}")
    st.write(f"• 증지대: {res['stamp']:,}")
    st.write(f"• 채권할인: {res['bond']:,}")
    st.write(f"• 부대비용: {res['cert']+res['traffic']+res['cause']:,}")
    st.metric("공과금 소계", f"{res['tax_total']:,} 원")

with c_res3:
    st.error("🧾 총 청구금액")
    st.write(f"**채무자:** {debtor_name}")
    st.write(f"**금융사:** {creditor_final}")
    st.markdown(f"<p class='big-font'>{res['raw_grand_total'] if show_fee_opt else res['tax_total']:,} 원</p>", unsafe_allow_html=True)
    
    # ----------------------------------------------------
    # [버튼 영역] 엑셀 템플릿 채우기
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown("##### 📥 비용 견적서 (엑셀)")
    
    uploaded_excel = st.file_uploader("보유하신 엑셀 템플릿(영수증_템플릿.xlsx) 업로드", type="xlsx")
    
    if uploaded_excel:
        doc_info = {
            'date': date_str, 'creditor': creditor_final, 'debtor': debtor_name, 'amount': amount_input,
            'estate_short': estate_text.split('\n')[1] if len(estate_text.split('\n')) > 1 else "" 
        }
        
        try:
            excel_data = fill_excel_template(uploaded_excel, res, doc_info)
            st.download_button(
                label="✅ 작성된 엑셀파일 다운로드",
                data=excel_data,
                file_name=f"비용견적서_{debtor_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"엑셀 파일 처리 중 오류: {e}")

# --- 3. 계약서 생성 ---
st.markdown("---")
st.markdown("<div class='header-style'>3. 계약서 생성 (PDF)</div>", unsafe_allow_html=True)

col_pdf1, col_pdf2 = st.columns([1, 1])

with col_pdf1:
    template_file = st.file_uploader("📂 계약서 템플릿(PDF) 업로드", type="pdf")

with col_pdf2:
    st.write("") 
    st.write("")
    if template_file:
        pdf_data = {
            "date": date_str,
            "creditor_name": creditor_final,
            "creditor_addr": creditor_addr,
            "debtor_name": debtor_name,
            "debtor_addr": debtor_addr,
            "owner_name": owner_name,
            "owner_addr": owner_addr,
            "claim_amount": f"{amount_input:,} 원",
            "estate_text": estate_text,
            "contract_type": contract_type
        }
        
        if st.button("🚀 입력한 내용으로 PDF 생성"):
            if not os.path.exists("Malgun.ttf"):
                st.error("⚠️ 'Malgun.ttf' 폰트 파일이 없습니다.")
            else:
                try:
                    pdf_bytes = generate_contract_pdf(template_file, pdf_data)
                    st.success("생성 완료! 아래 버튼을 눌러 다운로드하세요.")
                    st.download_button(
                        label="📥 계약서 PDF 다운로드",
                        data=pdf_bytes,
                        file_name=f"근저당권설정계약서_{debtor_name}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"오류 발생: {e}")