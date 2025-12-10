# scheduler.py
import schedule
import time
from datetime import datetime
import os
import markdown2
import pdfkit 
import database_manager
import shutil
from typing import Optional
import re
from main import generate_report_for_ticker
from email_manager import send_email_with_attachment

REPORTS_DIR = "reports"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
os.makedirs(REPORTS_DIR, exist_ok=True)

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
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

def generate_pdf_from_markdown(markdown_content: str, output_path: str, wkhtmltopdf_path: Optional[str] = None) -> bool:
    if wkhtmltopdf_path is None:
        wkhtmltopdf_path = WKHTMLTOPDF_PATH

    try:
        if not wkhtmltopdf_path:
            raise FileNotFoundError("Không tìm thấy wkhtmltopdf executable. Vui lòng cài đặt hoặc chỉnh đường dẫn.")

        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

        print(f"[INFO] Sử dụng wkhtmltopdf: {wkhtmltopdf_path}")
        print(f"[INFO] Chuẩn bị tạo PDF: {output_path}")

        html_content = markdown2.markdown(
            markdown_content,
            extras=["tables", "fenced-code-blocks", "cuddled-lists", "metadata"]
        )

        def replace_src(match):
            quote = match.group(1)       
            src = match.group(2)        

            if re.match(r'^(https?:|data:|file:)', src, flags=re.I):
                return f'src={quote}{src}{quote}'

            cleaned = src.lstrip("/\\")
            abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, cleaned))

            if not os.path.exists(abs_path):
                print(f"[WARN] Ảnh không tồn tại: {abs_path} (vẫn tiếp tục, wkhtmltopdf có thể thất bại nếu file thật sự không có)")

            # chuyển separator sang '/' để file URI chuẩn
            file_uri = f'file:///{abs_path.replace(os.sep, "/")}'
            return f'src={quote}{file_uri}{quote}'

        pdf_ready_html = re.sub(r'src=(["\'])([^"\']+)\1', replace_src, html_content)

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
            "enable-local-file-access": "",  
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


def job():
    unique_tickers = database_manager.get_unique_tickers()
    if not unique_tickers:
        print("Không có cổ phiếu nào được đăng ký. Bỏ qua phiên làm việc.")
        return

    print(f"Hôm nay sẽ phân tích {len(unique_tickers)} mã: {', '.join(unique_tickers)}")

    for ticker in unique_tickers:
        print(f"\n--- Đang xử lý mã: {ticker} ---")
        try:
            markdown_report, md_filename = generate_report_for_ticker(ticker)

            if not markdown_report:
                print(f"Không thể tạo báo cáo cho {ticker}. Bỏ qua.")
                continue
            
            print(f"Đã tạo thành công báo cáo Markdown cho {ticker} tại: {md_filename}")

            timestamp = datetime.now().strftime("%Y%m%d")
            pdf_filename = f"BanTin_{ticker}_{timestamp}.pdf"
            pdf_filepath = os.path.join(REPORTS_DIR, pdf_filename)

            # with open(md_filename, "r", encoding="utf-8") as f:
            #     report_read = f.read()
            
            if not generate_pdf_from_markdown(markdown_report, pdf_filepath):
                print(f"Không thể tạo file PDF cho {ticker}. Bỏ qua gửi mail.")
                continue

            recipients = database_manager.get_emails_for_ticker(ticker)
            if not recipients:
                print(f"Không có người dùng nào đăng ký nhận tin cho {ticker}.")
                continue
            
            email_subject = f"[Bản tin tài chính] Phân tích cổ phiếu {ticker} - Ngày {datetime.now().strftime('%d/%m/%Y')}"
            email_body = f"Chào bạn,\n\nTrợ lý Phân tích AI gửi bạn bản tin phân tích cho cổ phiếu {ticker} trong file đính kèm.\n\nChúc bạn một ngày đầu tư hiệu quả!\n\nTrân trọng,\nĐội ngũ AI."
            
            send_email_with_attachment(recipients, email_subject, email_body, pdf_filepath)

        except Exception as e:
            print(f"Đã xảy ra lỗi không mong muốn khi xử lý mã {ticker}: {e}")

    print(f"\n{'='*50}")
    print(f"Hoàn tất công việc định kỳ lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    print("Khởi chạy Scheduler - Hệ thống gửi bản tin tự động.")
    print("Công việc sẽ được thực thi vào 08:00 mỗi sáng.")
    
    schedule.every().day.at("07:00").do(job)

    # print("Thử nghiệm ngay bây giờ...")
    # job()

    while True:
        schedule.run_pending()
        time.sleep(1)