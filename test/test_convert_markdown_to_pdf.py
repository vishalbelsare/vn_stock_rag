"""
test.py

Script độc lập để kiểm thử chức năng chuyển Markdown -> PDF (tương tự generate_pdf_from_markdown trong scheduler.py).

Cách dùng:
    python test.py
    python test.py path/to/input.md path/to/output.pdf

Yêu cầu:
    pip install markdown2 pdfkit
    cài wkhtmltopdf (https://wkhtmltopdf.org/) và đặt vào PATH hoặc chỉnh đường dẫn WKHTMLTOPDF_CANDIDATES bên dưới.

Mục tiêu của script:
- Đọc file Markdown (mặc định: sample.md sẽ được tạo nếu chưa có).
- Chuyển Markdown -> HTML bằng markdown2.
- Thay tất cả các thẻ img có src local (ví dụ: /charts/xxx.png hoặc charts/xxx.png) thành file:///absolute/path để wkhtmltopdf có thể đọc.
- Tạo PDF trong thư mục reports/.
"""
from __future__ import annotations
import os
import re
import sys
import base64
import shutil
from datetime import datetime
from typing import Optional

try:
    import markdown2
    import pdfkit
except Exception as e:
    print("Thiếu thư viện: hãy cài 'markdown2' và 'pdfkit' trước khi chạy:")
    print("    pip install markdown2 pdfkit")
    raise

# ----------------- Cấu hình -----------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Danh sách đường dẫn khả dĩ cho wkhtmltopdf (thử theo thứ tự)
WKHTMLTOPDF_CANDIDATES = [
    shutil.which("wkhtmltopdf") or "",
    r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
    r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
    "/usr/bin/wkhtmltopdf",
    "/usr/local/bin/wkhtmltopdf",
]

def find_wkhtmltopdf() -> Optional[str]:
    for c in WKHTMLTOPDF_CANDIDATES:
        if not c:
            continue
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    # fallback: shutil.which again
    exe = shutil.which("wkhtmltopdf")
    if exe and os.path.isfile(exe):
        return exe
    return None

WKHTMLTOPDF_PATH = find_wkhtmltopdf()

# ----------------- Hàm chính chuyển Markdown -> PDF -----------------
def generate_pdf_from_markdown(markdown_content: str, output_path: str, wkhtmltopdf_path: Optional[str] = None) -> bool:
    """
    Chuyển Markdown -> PDF. Trả về True nếu thành công.
    - Chuyển mọi src="..." (local) thành file:///absolute/path
    - Bỏ qua src bắt đầu bằng http:, https:, data:, file:
    """
    if wkhtmltopdf_path is None:
        wkhtmltopdf_path = WKHTMLTOPDF_PATH

    try:
        if not wkhtmltopdf_path:
            raise FileNotFoundError("Không tìm thấy wkhtmltopdf executable. Vui lòng cài đặt hoặc chỉnh đường dẫn.")

        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

        print(f"[INFO] Sử dụng wkhtmltopdf: {wkhtmltopdf_path}")
        print(f"[INFO] Chuẩn bị tạo PDF: {output_path}")

        # Markdown -> HTML
        html_content = markdown2.markdown(
            markdown_content,
            extras=["tables", "fenced-code-blocks", "cuddled-lists", "metadata"]
        )

        # Thay src="..." / src='...' cho ảnh local thành file:///absolute/path
        def replace_src(match):
            quote = match.group(1)       # " hoặc '
            src = match.group(2)         # nội dung bên trong

            # nếu là URL hoặc data URI hoặc đã là file: -> giữ nguyên
            if re.match(r'^(https?:|data:|file:)', src, flags=re.I):
                return f'src={quote}{src}{quote}'

            # bỏ leading slash nếu dùng /charts/...
            cleaned = src.lstrip("/\\")
            abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, cleaned))

            if not os.path.exists(abs_path):
                print(f"[WARN] Ảnh không tồn tại: {abs_path} (vẫn tiếp tục, wkhtmltopdf có thể thất bại nếu file thật sự không có)")

            # chuyển separator sang '/' để file URI chuẩn
            file_uri = f'file:///{abs_path.replace(os.sep, "/")}'
            return f'src={quote}{file_uri}{quote}'

        # regex cho src="..." hoặc src='...'
        pdf_ready_html = re.sub(r'src=(["\'])([^"\']+)\1', replace_src, html_content)

        # CSS cơ bản
        css_style = """
        <style>
            body { font-family: 'Times New Roman', serif; font-size: 11pt; line-height: 1.4; color: #333; padding: 18px; }
            h1, h2, h3, h4 { font-family: 'Arial', sans-serif; color: #000; font-weight: bold; }
            h1 { font-size: 22pt; text-align: center; margin-bottom: 10px;}
            h2 { font-size: 16pt; border-bottom: 1px solid #ccc; padding-bottom: 6px; margin-top: 18px;}
            p, li { text-align: justify; }
            table { border-collapse: collapse; width: 100%; margin-top: 10px; font-size: 10pt; }
            th, td { border: 1px solid #ccc; padding: 6px; text-align: left; }
            th { background-color: #f7f7f7; font-weight: bold; }
            img { max-width: 100%; height: auto; display: block; margin-left: auto; margin-right: auto; }
            pre { background: #f6f6f6; padding: 8px; overflow-x: auto; }
        </style>
        """

        html_full = f'<!DOCTYPE html><html><head><meta charset="utf-8">{css_style}</head><body>{pdf_ready_html}</body></html>'

        options = {
            "enable-local-file-access": "",  # cần để wkhtmltopdf đọc file:///...
            "encoding": "UTF-8",
            "quiet": ""
        }

        pdfkit.from_string(html_full, output_path, configuration=config, options=options)
        print(f"[OK] Tạo PDF thành công: {output_path}")
        return True

    except FileNotFoundError as e:
        print("[ERROR] wkhtmltopdf không tìm thấy hoặc không thể chạy.")
        print("Chi tiết:", e)
        print("Hướng dẫn: cài wkhtmltopdf từ https://wkhtmltopdf.org/ và thêm vào PATH, hoặc chỉnh WKHTMLTOPDF_CANDIDATES trong file này.")
        return False
    except Exception as e:
        print("[ERROR] Lỗi khi tạo PDF:", e)
        return False
    
def main():
    input_md = "C:/Users/nguye/Documents/vn_stock_rag/reports/PhanTich_FPT_20251103_203248.md"
    output_pdf = "test_output.pdf"

    print(f"[INFO] Input MD: {input_md}")
    print(f"[INFO] Output PDF: {output_pdf}")
    print(f"[INFO] PROJECT_ROOT: {PROJECT_ROOT}")

    with open(input_md, "r", encoding="utf-8") as f:
        md_content = f.read()

    ok = generate_pdf_from_markdown(md_content, output_pdf)
    if ok:
        print("[RESULT] THÀNH CÔNG ->", output_pdf)
    else:
        print("[RESULT] THẤT BẠI")
        if not WKHTMLTOPDF_PATH:
            print("Gợi ý: wkhtmltopdf không tìm thấy. Bạn có thể cài đặt và thêm vào PATH hoặc chỉnh WKHTMLTOPDF_CANDIDATES trong file này.")

if __name__ == "__main__":
    main()