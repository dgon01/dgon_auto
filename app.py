import streamlit as st
import os
import re
import math
from io import BytesIO
from datetime import datetime
import pandas as pd

# =============================================================================
# 1. 라이브러리 설정 (Streamlit Cloud 호환)
# =============================================================================
try:
    import openpyxl
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from PyPDF2 import PdfReader, PdfWriter
    from fpdf import FPDF
except ImportError:
    st.error("필수 라이브러리가 설치되지 않았습니다. requirements.txt에 openpyxl, reportlab, pypdf, fpdf를 추가해주세요.")

# =============================================================================
# 2. 기본 설정 및 데이터
# =============================================================================
st.set_page_config(page_title="등기온 자동화(Web)", page_icon="⚖️", layout="wide")

# 폰트 등록 (Malgun.ttf가 같은 폴더에 있어야 함)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "Malgun.ttf")

if os.path.exists(FONT_PATH):
    try:
        pdfmetrics.registerFont(TTFont('Malgun', FONT_PATH))
        FONT_NAME = 'Malgun'
    except:
        FONT_NAME = 'Helvetica'
else:
    st.warning("⚠️ Malgun.ttf 폰트 파일이 없습니다. 한글이 깨질 수 있습니다.")
    FONT_NAME = 'Helvetica'

# 템플릿 파일 매핑
TEMPLATES = {
    "개인": "1.pdf",
    "3자담보": "2.pdf",
    "공동담보": "3.pdf",
    "자필": "자필서명정보 템플릿.pdf",
    "영수증": "영수증_템플릿.xlsx"
}

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
def format_number(val):
    if not val: return ""
    val = re.sub(r'[^\d]', '', str(val))
    if not val: return ""
    return "{:,}".format(int(val))

def unformat_number(val):
    if not val: return 0
    return int(re.sub(r'[^\d]', '', str(val)))

def number_to_korean(num_str):
    try:
        num = unformat_number(num_str)
        if num == 0: return "영원정"
        units = ['', '만', '억', '조']
        digits = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
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
    except: return ""

def lookup_base_fee(amount):
    LOOKUP_KEYS = [0, 30_000_000, 45_000_000, 60_000_000, 106_500_000, 150_000_000, 225_000_000]
    LOOKUP_VALS = [150_000, 200_000, 250_000, 300_000, 350_000, 400_000, 450_000]
    for i in range(len(LOOKUP_KEYS) - 1, -1, -1):
        if amount > LOOKUP_KEYS[i]: return LOOKUP_VALS[i]
    return LOOKUP_VALS[0]

# =============================================================================
# 4. PDF 생성 로직
# =============================================================================
def create_overlay_pdf(data):
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    c.setFont(FONT_NAME, 11)
    
    # 데이터 매핑 (좌표는 기존 로직 유지)
    if data.get("date"): c.drawString(480, height - 85, data["date"])
    if data.get("creditor_name"): c.drawString(157, height - 134, data["creditor_name"])
    if data.get("creditor_addr"): c.drawString(157, height - 150, data["creditor_addr"]) # 긴 주소 처리 생략(간소화)
    if data.get("debtor_name"): c.drawString(157, height - 172, data["debtor_name"])
    if data.get("debtor_addr"): c.drawString(157, height - 190, data["debtor_addr"])
    if data.get("owner_name"): c.drawString(157, height - 212, data["owner_name"])
    if data.get("owner_addr"): c.drawString(157, height - 230, data["owner_addr"])
    if data.get("guarantee_type"): c.drawString(65, height - 343, data["guarantee_type"])
    if data.get("claim_amount"): c.drawString(150, height - 535, data["claim_amount"]) # 한글금액
    
    # 2페이지 서명
    c.showPage() 
    c.setFont(FONT_NAME, 11)
    if data.get("date"): c.drawString(180, height - 270, data["date"])
    
    ctype = data.get("contract_type", "3자담보")
    if ctype == "개인":
        if data.get("debtor_name"): c.drawString(450, height - 270, data["debtor_name"])
    elif ctype == "3자담보":
        if data.get("owner_name"): c.drawString(490, height - 270, data["owner_name"])
    elif ctype == "공동담보":
        if data.get("debtor_name"): c.drawString(450, height - 270, data["debtor_name"])
        if data.get("owner_name"): c.drawString(490, height - 270, data["owner_name"])

    # 3페이지 부동산 표시
    c.showPage()
    c.setFont(FONT_NAME, 11)
    base_x = 35; base_y = height - 80; gap = 16
    if data.get("estate_list"):
        for i, line in enumerate(data["estate_list"]):
            c.drawString(base_x, base_y - (i * gap), line)
            
    c.save()
    packet.seek(0)
    return packet

def create_signature_overlay(data):
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    c.setFont(FONT_NAME, 10)
    
    estate_x = 150; estate_y = height - 170; line_h = 14
    if data.get("estate_text"):
        for i, line in enumerate(data["estate_text"].split("\n")[:17]):
            c.drawString(estate_x, estate_y - (i * line_h), line)
            
    if data.get("debtor_name"): c.drawString(250, 322, data["debtor_name"])
    if data.get("debtor_rrn"): c.drawString(250, 298, data["debtor_rrn"])
    if data.get("owner_name"): c.drawString(400, 322, data["owner_name"])
    if data.get("owner_rrn"): c.drawString(400, 298, data["owner_rrn"])
    if data.get("date"):
        c.setFont(FONT_NAME, 11)
        text = data["date"]
        tw = c.stringWidth(text, FONT_NAME, 11)
        c.drawString((width - tw) / 2, 150, text)
        
    c.save()
    packet.seek(0)
    return packet

def merge_pdf(template_path, overlay_packet):
    try:
        template_pdf = PdfReader(template_path)
        overlay_pdf = PdfReader(overlay_packet)
        writer = PdfWriter()

        for page_num in range(len(template_pdf.pages)):
            page = template_pdf.pages[page_num]
            if page_num < len(overlay_pdf.pages):
                page.merge_page(overlay_pdf.pages[page_num])
            writer.add_page(page)
            
        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception as e:
        st.error(f"PDF 병합 중 오류 발생: {e}")
        return None

# =============================================================================
# 5. UI 메인 (탭 구성)
# =============================================================================
st.title("⚖️ 법무법인 사화 - 등기온 자동화 시스템")

# 탭 생성
tab1, tab2, tab3 = st.tabs(["📄 근저당권설정", "✍️ 자필서명정보", "🧾 비용계산서"])

# 공통 데이터 세션 관리
if 'common_data' not in st.session_state:
    st.session_state.common_data = {
        'date': datetime.now().strftime("%Y년 %m월 %d일"),
        'debtor': '', 'owner': '', 'estate': ''
    }

# -----------------------------------------------------------------------------
# [탭 1] 근저당권 설정
# -----------------------------------------------------------------------------
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. 기본 정보")
        input_date = st.text_input("작성일자", value=st.session_state.common_data['date'], key="t1_date")
        
        creditor_key = st.selectbox("채권자 선택", list(CREDITORS.keys()))
        creditor_info = CREDITORS[creditor_key]
        st.info(f"법인번호: {creditor_info['corp_num']}\n주소: {creditor_info['addr']}")
        
        contract_type = st.radio("계약서 유형", ["개인", "3자담보", "공동담보"], horizontal=True)
        
        st.subheader("2. 당사자 정보")
        input_debtor = st.text_input("채무자 성명", key="t1_debtor")
        input_debtor_addr = st.text_input("채무자 주소")
        input_owner = st.text_input("설정자 성명", key="t1_owner")
        input_owner_addr = st.text_input("설정자 주소")
        
        guarantee_type = st.text_input("피담보채무", value="한정근담보")
        
        # 금액 입력 (콤마 자동화는 보여주기용 텍스트로 처리)
        raw_amount = st.text_input("채권최고액 (숫자만 입력)", value="0")
        formatted_amt = format_number(raw_amount)
        korean_amt = number_to_korean(raw_amount)
        st.caption(f"변환: {formatted_amt}원 / {korean_amt}")

    with col2:
        st.subheader("3. 부동산의 표시")
        default_estate = "[토지]\n서울특별시 강남구...\n[건물]\n..."
        input_estate = st.text_area("등기부 내용 붙여넣기", value=default_estate, height=300, key="t1_estate")
        
        # 세션 데이터 업데이트 (탭2와 공유)
        if st.button("💾 데이터 동기화 (탭2로 전달)"):
            st.session_state.common_data['date'] = input_date
            st.session_state.common_data['debtor'] = input_debtor
            st.session_state.common_data['owner'] = input_owner
            st.session_state.common_data['estate'] = input_estate
            st.success("데이터가 자필서명 탭으로 복사되었습니다.")

        st.divider()
        st.subheader("4. 실행")
        
        if st.button("🚀 근저당권 계약서 생성"):
            template_file = TEMPLATES.get(contract_type)
            if not os.path.exists(os.path.join(BASE_DIR, template_file)):
                st.error(f"템플릿 파일({template_file})이 없습니다.")
            else:
                data = {
                    "date": input_date,
                    "creditor_name": creditor_key,
                    "creditor_addr": creditor_info['addr'],
                    "debtor_name": input_debtor, "debtor_addr": input_debtor_addr,
                    "owner_name": input_owner, "owner_addr": input_owner_addr,
                    "guarantee_type": guarantee_type,
                    "claim_amount": korean_amt,
                    "estate_list": input_estate.split('\n'),
                    "contract_type": contract_type
                }
                
                overlay = create_overlay_pdf(data)
                final_pdf = merge_pdf(os.path.join(BASE_DIR, template_file), overlay)
                
                if final_pdf:
                    st.download_button(
                        label="📥 계약서 다운로드 (PDF)",
                        data=final_pdf,
                        file_name=f"근저당권설정계약서_{input_debtor}.pdf",
                        mime="application/pdf"
                    )

# -----------------------------------------------------------------------------
# [탭 2] 자필서명 정보 (★누락되었던 부분 추가됨★)
# -----------------------------------------------------------------------------
with tab2:
    st.header("✍️ 자필서명정보 입력")
    
    # 탭1에서 넘어온 데이터 활용
    c_date = st.session_state.common_data['date']
    c_debtor = st.session_state.common_data['debtor']
    c_owner = st.session_state.common_data['owner']
    c_estate = st.session_state.common_data['estate']
    
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        s_date = st.text_input("작성일자", value=c_date, key="s_date")
        s_debtor = st.text_input("설정자(단독/채무자)", value=c_debtor, key="s_debtor")
        s_debtor_rrn = st.text_input("주민등록번호(채무자)", placeholder="000000-0000000")
        
        st.markdown("---")
        s_owner = st.text_input("설정자(공동)", value=c_owner, key="s_owner")
        s_owner_rrn = st.text_input("주민등록번호(공동)", placeholder="000000-0000000")
        
    with col_s2:
        st.write("부동산 표시 (확인용)")
        s_estate = st.text_area("부동산 내용", value=c_estate, height=250, key="s_estate")
        
    st.divider()
    
    if st.button("🚀 자필서명정보 PDF 생성"):
        template_file = TEMPLATES["자필"]
        if not os.path.exists(os.path.join(BASE_DIR, template_file)):
            st.error("자필서명 템플릿 파일이 없습니다.")
        else:
            sig_data = {
                "date": s_date,
                "debtor_name": s_debtor, "debtor_rrn": s_debtor_rrn,
                "owner_name": s_owner, "owner_rrn": s_owner_rrn,
                "estate_text": s_estate
            }
            sig_overlay = create_signature_overlay(sig_data)
            final_sig_pdf = merge_pdf(os.path.join(BASE_DIR, template_file), sig_overlay)
            
            if final_sig_pdf:
                st.download_button(
                    label="📥 자필서명정보 다운로드 (PDF)",
                    data=final_sig_pdf,
                    file_name=f"자필서명정보_{s_debtor}.pdf",
                    mime="application/pdf"
                )

# -----------------------------------------------------------------------------
# [탭 3] 비용계산서 (웹 버전 간소화)
# -----------------------------------------------------------------------------
with tab3:
    st.header("🧾 비용계산 및 영수증")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("기본 입력")
        cost_amt_raw = st.text_input("채권최고액", value="0", key="c_amt")
        cost_amt = unformat_number(cost_amt_raw)
        st.caption(f"입력금액: {format_number(cost_amt)}원")
        
        parcels = st.number_input("필지수", min_value=1, value=1)
        rate = st.number_input("채권할인율(%)", value=9.135, step=0.01)
        
    with c2:
        st.subheader("보수료 (Income)")
        base_fee = lookup_base_fee(cost_amt)
        add_fee = st.number_input("추가보수", value=0, step=10000)
        etc_fee = st.number_input("기타보수", value=0, step=10000)
        disc_fee = st.number_input("할인금액", value=0, step=10000)
        
        supply = base_fee + add_fee + etc_fee - disc_fee
        vat = int(supply * 0.1)
        total_fee = supply + vat
        
        st.success(f"보수총액: {format_number(total_fee)} 원")
        
    with c3:
        st.subheader("공과금 (Tax)")
        reg_tax = math.floor(cost_amt * 0.002 / 10) * 10
        edu_tax = math.floor(reg_tax * 0.2 / 10) * 10
        stamps = 15000 * parcels
        
        bond = 0
        if cost_amt >= 20000000:
            bond = math.ceil(cost_amt * 0.01 / 10000) * 10000
        bond_disc = math.floor(bond * (rate/100) / 10) * 10
        
        manual_cost = st.number_input("기타 공과금(제증명 등)", value=150000, step=1000)
        
        total_tax = reg_tax + edu_tax + stamps + bond_disc + manual_cost
        st.warning(f"공과금총액: {format_number(total_tax)} 원")

    st.divider()
    grand_total = total_fee + total_tax
    st.metric(label="총 청구금액", value=f"{format_number(grand_total)} 원")
    
    # 영수증 엑셀 생성 (Streamlit Cloud에서는 Excel->PDF 변환 불가, 엑셀 다운로드만 제공)
    if st.button("📥 영수증(Excel) 다운로드"):
        receipt_tpl = TEMPLATES["영수증"]
        if os.path.exists(os.path.join(BASE_DIR, receipt_tpl)):
            wb = openpyxl.load_workbook(os.path.join(BASE_DIR, receipt_tpl))
            ws = wb.active
            
            # 엑셀 매핑 (좌표는 기존 코드 참조)
            ws['AG5'] = cost_amt # 채권최고액
            ws['AH21'] = total_tax # 공과금 소계
            ws['Y22'] = total_tax
            # 필요한 나머지 데이터 매핑 추가 가능
            
            out_buffer = BytesIO()
            wb.save(out_buffer)
            out_buffer.seek(0)
            
            st.download_button(
                label="엑셀 파일 받기",
                data=out_buffer,
                file_name=f"영수증_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("영수증 템플릿 파일이 없습니다.")