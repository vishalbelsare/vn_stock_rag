# Dockerfile

# --- Giai đoạn 1: Base Image ---
FROM python:3.11-slim

# --- Giai đoạn 2: Cấu hình Môi trường ---
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --- Giai đoạn 3: Cài đặt Dependencies ---
COPY requirements.txt .
RUN apt-get update && apt-get install -y git && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove git && \
    rm -rf /var/lib/apt/lists/*

# --- BẮT ĐẦU SỬA LỖI CÚ PHÁP ---
# Sử dụng /bin/sh -c để đảm bảo toàn bộ chuỗi được thực thi như một lệnh shell duy nhất.
# Điều này tránh lỗi cú pháp "can't find = in ...".
RUN /bin/sh -c 'CERTIFI_PATH=$(python -c "import certifi; print(certifi.where())") && \
    echo "SSL_CERT_FILE=${CERTIFI_PATH}" >> /etc/environment && \
    echo "REQUESTS_CA_BUNDLE=${CERTIFI_PATH}" >> /etc/environment'

# Thiết lập các biến môi trường này cho session hiện tại.
# Chúng ta sẽ chạy lệnh Python để lấy giá trị trực tiếp.
ENV SSL_CERT_FILE /usr/local/lib/python3.11/site-packages/certifi/cacert.pem
ENV REQUESTS_CA_BUNDLE /usr/local/lib/python3.11/site-packages/certifi/cacert.pem
# --- KẾT THÚC SỬA LỖI CÚ PHÁP ---
# Chú ý: Đường dẫn trên là đường dẫn mặc định cho Python 3.11-slim.
# Nếu bạn đổi base image, bạn có thể cần cập nhật lại đường dẫn này.
# Cách an toàn nhất là tìm đường dẫn bằng cách chạy container và `find / -name cacert.pem`

# --- Giai đoạn 4: Sao chép Mã nguồn Ứng dụng ---
COPY . .

# --- Giai đoạn 5: Cấu hình Cổng và Lệnh Khởi động ---
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]