import fitz  # PyMuPDF
from PIL import Image, ImageTk
from tkinter import messagebox
import tkinter as tk
import os
import glob

# 해상도, 로딩이 너무 오래 걸리면 숫자 줄이기
DPI = 300

# 기존 파일 삭제
def clear_output_folders():
    for folder in ['./after_pdf', './crop_png']:
        if os.path.exists(folder):
            files = glob.glob(f'{folder}/*')
            for f in files:
                os.remove(f)
        else:
            os.makedirs(folder)

clear_output_folders()

# original 폴더 내 모든 PDF 파일 경로 가져오기
pdf_path = glob.glob('./before_pdf/*.pdf')

if len(pdf_path) == 1:
    pdf_path = pdf_path[0]
    pdf_filename = os.path.basename(pdf_path)
    pdf_document = fitz.open(pdf_path)
    
    print(f"편집할 파일 이름: {pdf_filename}")

    page = pdf_document[0]
    pix = page.get_pixmap()
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
    selected_regions = []
    rect_ids = [] 

    start_x, start_y = None, None
    end_x, end_y = None, None
    current_rect = None

    def on_button_press(event):
        global start_x, start_y, current_rect
        start_x, start_y = event.x, event.y
        current_rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="blue", width=2)
    
    def on_button_drag(event):
        global current_rect
        canvas.coords(current_rect, start_x, start_y, event.x, event.y)

    def on_button_release(event):
        global end_x, end_y, current_rect
        end_x, end_y = event.x, event.y
        save_selected_region()
        canvas.delete(current_rect)
        
    def save_selected_region():
        if start_x and start_y and end_x and end_y:
            region = (min(start_x, end_x), min(start_y, end_y), max(start_x, end_x), max(start_y, end_y))
            selected_regions.append(region)
            rect_id = canvas.create_rectangle(region[0], region[1], region[2], region[3], outline="red", width=2)
            rect_ids.append(rect_id)
            
    def undo_last_region():
        if selected_regions and rect_ids:
            selected_regions.pop()
            rect_id = rect_ids.pop()
            canvas.delete(rect_id)
            
    def save_all_pages_with_same_regions():
        if len(selected_regions) != 2:
            messagebox.showerror("오류", "두 개의 영역을 선택해야 합니다")
            return

        top_region = selected_regions[0]
        bottom_region = selected_regions[1]

        output_pdf = fitz.open()
        num_pages = len(pdf_document)

        try:
            for page_num in range(num_pages):
                page = pdf_document[page_num]

                # # 진행 퍼센트 계산.. 업뎃 예정
                # progress = (page_num + 1) / num_pages * 100
                # progress_label.config(text=f"진행률: {progress:.2f}%")
                # root.update_idletasks() 

                for idx, region in enumerate([top_region, bottom_region]):
                    x0, y0, x1, y1 = region
                    pix = page.get_pixmap(clip=fitz.Rect(x0, y0, x1, y1), dpi=DPI)
                    cropped_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    img_path = f'./crop_png/image_{page_num}.{idx}.png'
                    cropped_image.save(img_path)
                    
                    img_doc = fitz.open(img_path)
                    pdf_bytes = img_doc.convert_to_pdf()
                    img_pdf = fitz.open("pdf", pdf_bytes)
                    output_pdf.insert_pdf(img_pdf)
                    img_doc.close()

                    # 이미지 파일 삭제 (이미지 파일 필요없으면 주석 해제)
                    # os.remove(img_path)

            output_pdf_path = f'after_pdf/cropped_{pdf_filename}'
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            output_pdf.save(output_pdf_path)
            output_pdf.close()
            messagebox.showinfo("성공", f"모든 페이지가 동일한 상단과 하단 영역으로 잘린 PDF가 저장되었습니다: {output_pdf_path}")
            root.destroy()

        except Exception as e:
            messagebox.showerror("오류", f"저장에 실패했습니다: {e}")
            
    root = tk.Tk()
    root.title("PDF 모든 페이지 동일 상하 영역 선택 및 저장")
    canvas = tk.Canvas(root, width=image.width, height=image.height)
    canvas.pack()

    # 진행 퍼센트 레이블 추가...업뎃 예정
    # progress_label = tk.Label(root, text="진행률: 0%")
    # progress_label.pack()

    tk_image = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor="nw", image=tk_image)

    canvas.bind("<ButtonPress-1>", on_button_press)
    canvas.bind("<B1-Motion>", on_button_drag)  # 드래그 중
    canvas.bind("<ButtonRelease-1>", on_button_release)

    save_button = tk.Button(root, text="모든 페이지 동일 상하 영역으로 저장", command=save_all_pages_with_same_regions)
    save_button.pack()

    undo_button = tk.Button(root, text="뒤로가기", command=undo_last_region)
    undo_button.pack()

    root.mainloop()
    pdf_document.close()

elif len(pdf_path) == 0:
    messagebox.showerror("오류", "'original' 폴더에 PDF 파일이 존재하지 않습니다.")
else:
    messagebox.showerror("오류", "'original' 폴더에 PDF 파일이 2개 이상 있습니다. 하나만 넣어주십시오.")