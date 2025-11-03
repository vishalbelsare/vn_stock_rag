# email_manager.py
import smtplib
import os
from email.message import EmailMessage
from typing import List

def send_email_with_attachment(recipients: List[str], subject: str, body: str, attachment_path: str):
    """Gửi email với một file đính kèm cho một danh sách người nhận."""
    sender_email = os.environ.get("SENDER_EMAIL")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT")

    if not all([sender_email, smtp_password, smtp_host, smtp_port]):
        print("Lỗi: Vui lòng cấu hình đầy đủ các biến SMTP trong file .env")
        return False

    print(f"Đang chuẩn bị gửi email tới {len(recipients)} người nhận...")
    
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = ", ".join(recipients)
        msg.set_content(body)

        with open(attachment_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(attachment_path)
            msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)

        with smtplib.SMTP_SSL(smtp_host, int(smtp_port)) as smtp:
            smtp.login(sender_email, smtp_password)
            smtp.send_message(msg)
        
        print(f"Gửi email thành công cho báo cáo {file_name}!")
        return True
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi gửi email: {e}")
        return False