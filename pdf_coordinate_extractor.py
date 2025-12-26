"""
PDF 좌표 추출기 (PDF Coordinate Extractor)
- 점 클릭: 클릭한 위치의 (x, y) 좌표 표시
- 박스 드래그: 드래그 영역의 (x1, y1, x2, y2) 좌표 표시
- PDF 실제 좌표로 변환 (이미지 스케일 보정)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import pyperclip


class PDFCoordinateExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 좌표 추출기")
        self.root.geometry("1200x800")
        
        # 변수 초기화
        self.pdf_doc = None
        self.current_page = 0
        self.total_pages = 0
        self.scale = 2.0  # PDF 렌더링 스케일
        self.display_scale = 1.0  # 화면 표시 스케일
        self.tk_image = None
        self.pdf_image = None
        
        # 좌표 관련
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.mode = "point"  # "point" or "box"
        self.points = []  # 저장된 점들
        self.boxes = []   # 저장된 박스들
        
        self.setup_ui()
        self.bind_events()
    
    def setup_ui(self):
        # 상단 툴바
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="📂 PDF 열기", command=self.open_pdf).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 모드 선택
        ttk.Label(toolbar, text="모드:").pack(side=tk.LEFT, padx=2)
        self.mode_var = tk.StringVar(value="point")
        ttk.Radiobutton(toolbar, text="🔴 점", variable=self.mode_var, 
                        value="point", command=self.change_mode).pack(side=tk.LEFT)
        ttk.Radiobutton(toolbar, text="⬜ 박스", variable=self.mode_var, 
                        value="box", command=self.change_mode).pack(side=tk.LEFT)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 페이지 네비게이션
        ttk.Button(toolbar, text="◀ 이전", command=self.prev_page).pack(side=tk.LEFT, padx=2)
        self.page_label = ttk.Label(toolbar, text="페이지: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="다음 ▶", command=self.next_page).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 확대/축소
        ttk.Label(toolbar, text="표시:").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="➖", width=3, command=self.zoom_out).pack(side=tk.LEFT)
        self.zoom_label = ttk.Label(toolbar, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="➕", width=3, command=self.zoom_in).pack(side=tk.LEFT)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar, text="🗑️ 초기화", command=self.clear_all).pack(side=tk.LEFT, padx=2)
        
        # 메인 영역 (좌: 캔버스, 우: 좌표 목록)
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 캔버스 프레임 (스크롤 포함)
        canvas_frame = ttk.Frame(main_frame)
        main_frame.add(canvas_frame, weight=3)
        
        # 스크롤바
        self.h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 캔버스
        self.canvas = tk.Canvas(canvas_frame, bg="gray", 
                                xscrollcommand=self.h_scroll.set,
                                yscrollcommand=self.v_scroll.set)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.h_scroll.config(command=self.canvas.xview)
        self.v_scroll.config(command=self.canvas.yview)
        
        # 우측 패널 (좌표 정보)
        right_panel = ttk.Frame(main_frame)
        main_frame.add(right_panel, weight=1)
        
        # 현재 좌표 표시
        coord_frame = ttk.LabelFrame(right_panel, text="현재 좌표")
        coord_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.coord_display = tk.Text(coord_frame, height=4, width=30, font=("Consolas", 11))
        self.coord_display.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(coord_frame, text="📋 좌표 복사", command=self.copy_current_coord).pack(pady=2)
        
        # 저장된 좌표 목록
        list_frame = ttk.LabelFrame(right_panel, text="저장된 좌표 목록")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 트리뷰
        columns = ("type", "coords", "page")
        self.coord_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        self.coord_tree.heading("type", text="타입")
        self.coord_tree.heading("coords", text="좌표")
        self.coord_tree.heading("page", text="페이지")
        self.coord_tree.column("type", width=50)
        self.coord_tree.column("coords", width=150)
        self.coord_tree.column("page", width=50)
        
        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.coord_tree.yview)
        self.coord_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.coord_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 목록 버튼
        btn_frame = ttk.Frame(right_panel)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="📋 선택 복사", command=self.copy_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📋 전체 복사", command=self.copy_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ 선택 삭제", command=self.delete_selected).pack(side=tk.LEFT, padx=2)
        
        # 상태바
        self.status_var = tk.StringVar(value="PDF 파일을 열어주세요")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
    
    def bind_events(self):
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.root.bind("<Control-o>", lambda e: self.open_pdf())
        self.root.bind("<Left>", lambda e: self.prev_page())
        self.root.bind("<Right>", lambda e: self.next_page())
    
    def open_pdf(self):
        file_path = filedialog.askopenfilename(
            title="PDF 파일 선택",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.pdf_doc = fitz.open(file_path)
                self.total_pages = len(self.pdf_doc)
                self.current_page = 0
                self.clear_all()
                self.render_page()
                self.status_var.set(f"파일 로드: {file_path}")
            except Exception as e:
                messagebox.showerror("오류", f"PDF 로드 실패:\n{e}")
    
    def render_page(self):
        if not self.pdf_doc:
            return
        
        page = self.pdf_doc[self.current_page]
        
        # PDF를 이미지로 변환
        mat = fitz.Matrix(self.scale * self.display_scale, self.scale * self.display_scale)
        pix = page.get_pixmap(matrix=mat)
        
        # PIL Image로 변환
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.pdf_image = img
        self.tk_image = ImageTk.PhotoImage(img)
        
        # 캔버스 업데이트
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image, tags="pdf")
        self.canvas.config(scrollregion=(0, 0, pix.width, pix.height))
        
        # 페이지 라벨 업데이트
        self.page_label.config(text=f"페이지: {self.current_page + 1}/{self.total_pages}")
        self.zoom_label.config(text=f"{int(self.display_scale * 100)}%")
        
        # 저장된 마커 다시 그리기
        self.redraw_markers()
    
    def redraw_markers(self):
        """저장된 점과 박스 다시 그리기"""
        for item in self.points:
            if item["page"] == self.current_page:
                self.draw_point(item["canvas_x"], item["canvas_y"])
        
        for item in self.boxes:
            if item["page"] == self.current_page:
                self.draw_box(item["canvas_x1"], item["canvas_y1"], 
                             item["canvas_x2"], item["canvas_y2"])
    
    def canvas_to_pdf_coords(self, canvas_x, canvas_y):
        """캔버스 좌표를 PDF 좌표로 변환"""
        pdf_x = canvas_x / (self.scale * self.display_scale)
        pdf_y = canvas_y / (self.scale * self.display_scale)
        return round(pdf_x, 2), round(pdf_y, 2)
    
    def on_motion(self, event):
        if not self.pdf_doc:
            return
        
        # 캔버스 상의 실제 좌표
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # PDF 좌표로 변환
        pdf_x, pdf_y = self.canvas_to_pdf_coords(canvas_x, canvas_y)
        
        mode_text = "점" if self.mode == "point" else "박스"
        self.status_var.set(f"[{mode_text} 모드] PDF 좌표: ({pdf_x}, {pdf_y}) | 캔버스: ({int(canvas_x)}, {int(canvas_y)})")
    
    def on_click(self, event):
        if not self.pdf_doc:
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        self.start_x = canvas_x
        self.start_y = canvas_y
        
        if self.mode == "point":
            # 점 모드: 즉시 점 찍기
            pdf_x, pdf_y = self.canvas_to_pdf_coords(canvas_x, canvas_y)
            self.draw_point(canvas_x, canvas_y)
            
            # 좌표 표시
            coord_text = f"x: {pdf_x}\ny: {pdf_y}\n\n(x, y) = ({pdf_x}, {pdf_y})"
            self.coord_display.delete("1.0", tk.END)
            self.coord_display.insert("1.0", coord_text)
            
            # 저장
            self.points.append({
                "page": self.current_page,
                "pdf_x": pdf_x, "pdf_y": pdf_y,
                "canvas_x": canvas_x, "canvas_y": canvas_y
            })
            self.add_to_tree("점", f"({pdf_x}, {pdf_y})")
    
    def on_drag(self, event):
        if not self.pdf_doc or self.mode != "box":
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # 기존 임시 사각형 삭제
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        
        # 새 사각형 그리기
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, canvas_x, canvas_y,
            outline="blue", width=2, dash=(5, 5)
        )
        
        # 좌표 실시간 표시
        pdf_x1, pdf_y1 = self.canvas_to_pdf_coords(self.start_x, self.start_y)
        pdf_x2, pdf_y2 = self.canvas_to_pdf_coords(canvas_x, canvas_y)
        
        coord_text = f"x1: {pdf_x1}, y1: {pdf_y1}\nx2: {pdf_x2}, y2: {pdf_y2}\n\n({pdf_x1}, {pdf_y1}, {pdf_x2}, {pdf_y2})"
        self.coord_display.delete("1.0", tk.END)
        self.coord_display.insert("1.0", coord_text)
    
    def on_release(self, event):
        if not self.pdf_doc or self.mode != "box":
            return
        
        if self.current_rect:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # 너무 작은 박스는 무시
        if abs(canvas_x - self.start_x) < 5 or abs(canvas_y - self.start_y) < 5:
            return
        
        # 좌표 정렬 (x1 < x2, y1 < y2)
        x1, x2 = min(self.start_x, canvas_x), max(self.start_x, canvas_x)
        y1, y2 = min(self.start_y, canvas_y), max(self.start_y, canvas_y)
        
        pdf_x1, pdf_y1 = self.canvas_to_pdf_coords(x1, y1)
        pdf_x2, pdf_y2 = self.canvas_to_pdf_coords(x2, y2)
        
        # 박스 그리기
        self.draw_box(x1, y1, x2, y2)
        
        # 좌표 표시
        width = round(pdf_x2 - pdf_x1, 2)
        height = round(pdf_y2 - pdf_y1, 2)
        coord_text = f"x1: {pdf_x1}, y1: {pdf_y1}\nx2: {pdf_x2}, y2: {pdf_y2}\n크기: {width} x {height}\n\n({pdf_x1}, {pdf_y1}, {pdf_x2}, {pdf_y2})"
        self.coord_display.delete("1.0", tk.END)
        self.coord_display.insert("1.0", coord_text)
        
        # 저장
        self.boxes.append({
            "page": self.current_page,
            "pdf_x1": pdf_x1, "pdf_y1": pdf_y1,
            "pdf_x2": pdf_x2, "pdf_y2": pdf_y2,
            "canvas_x1": x1, "canvas_y1": y1,
            "canvas_x2": x2, "canvas_y2": y2
        })
        self.add_to_tree("박스", f"({pdf_x1}, {pdf_y1}, {pdf_x2}, {pdf_y2})")
    
    def draw_point(self, x, y, size=6):
        """점 그리기"""
        self.canvas.create_oval(
            x - size, y - size, x + size, y + size,
            fill="red", outline="darkred", width=2, tags="marker"
        )
        self.canvas.create_line(
            x - size - 2, y, x + size + 2, y,
            fill="darkred", width=1, tags="marker"
        )
        self.canvas.create_line(
            x, y - size - 2, x, y + size + 2,
            fill="darkred", width=1, tags="marker"
        )
    
    def draw_box(self, x1, y1, x2, y2):
        """박스 그리기"""
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="blue", width=2, tags="marker"
        )
        # 모서리 표시
        size = 4
        for x, y in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
            self.canvas.create_rectangle(
                x - size, y - size, x + size, y + size,
                fill="blue", outline="darkblue", tags="marker"
            )
    
    def add_to_tree(self, type_text, coords):
        """트리뷰에 좌표 추가"""
        self.coord_tree.insert("", tk.END, values=(type_text, coords, self.current_page + 1))
    
    def change_mode(self):
        self.mode = self.mode_var.get()
    
    def prev_page(self):
        if self.pdf_doc and self.current_page > 0:
            self.current_page -= 1
            self.render_page()
    
    def next_page(self):
        if self.pdf_doc and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.render_page()
    
    def zoom_in(self):
        if self.display_scale < 3.0:
            self.display_scale += 0.25
            self.render_page()
    
    def zoom_out(self):
        if self.display_scale > 0.25:
            self.display_scale -= 0.25
            self.render_page()
    
    def on_mousewheel(self, event):
        """Ctrl+휠로 확대/축소"""
        if event.state & 0x4:  # Ctrl 키
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def copy_current_coord(self):
        """현재 좌표 복사"""
        text = self.coord_display.get("1.0", tk.END).strip()
        if text:
            # 마지막 줄 (튜플 형태) 복사
            lines = text.split("\n")
            for line in reversed(lines):
                if line.startswith("("):
                    pyperclip.copy(line)
                    self.status_var.set(f"복사됨: {line}")
                    return
            pyperclip.copy(text)
            self.status_var.set("좌표 복사됨")
    
    def copy_selected(self):
        """선택된 좌표 복사"""
        selected = self.coord_tree.selection()
        if selected:
            coords = []
            for item in selected:
                values = self.coord_tree.item(item)["values"]
                coords.append(values[1])
            text = "\n".join(coords)
            pyperclip.copy(text)
            self.status_var.set(f"{len(coords)}개 좌표 복사됨")
    
    def copy_all(self):
        """전체 좌표 복사"""
        items = self.coord_tree.get_children()
        if items:
            lines = []
            for item in items:
                values = self.coord_tree.item(item)["values"]
                lines.append(f"[P{values[2]}] {values[0]}: {values[1]}")
            text = "\n".join(lines)
            pyperclip.copy(text)
            self.status_var.set(f"{len(items)}개 좌표 복사됨")
    
    def delete_selected(self):
        """선택된 항목 삭제"""
        selected = self.coord_tree.selection()
        for item in selected:
            self.coord_tree.delete(item)
        self.status_var.set(f"{len(selected)}개 삭제됨")
    
    def clear_all(self):
        """모든 마커 초기화"""
        self.canvas.delete("marker")
        self.points.clear()
        self.boxes.clear()
        for item in self.coord_tree.get_children():
            self.coord_tree.delete(item)
        self.coord_display.delete("1.0", tk.END)
        self.status_var.set("초기화 완료")


def main():
    root = tk.Tk()
    app = PDFCoordinateExtractor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
