# Dockerfile

# --- Giai đoạn 1: Base Image ---
# Sử dụng một ảnh Python chính thức. Chọn một phiên bản cụ thể để đảm bảo tính nhất quán.
FROM python:3.11-slim

# --- Giai đoạn 2: Cấu hình Môi trường ---
# Thiết lập thư mục làm việc bên trong container
WORKDIR /app

# Thiết lập biến môi trường để Python không tạo file .pyc và chạy ở chế độ unbuffered
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --- Giai đoạn 3: Cài đặt Dependencies ---
# Sao chép file requirements.txt vào trước
COPY requirements.txt .

# Chạy pip install. Dùng --no-cache-dir để giữ image nhẹ.
# Cài đặt git để có thể clone các thư viện cần thiết nếu có
RUN apt-get update && apt-get install -y git && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove git && \
    rm -rf /var/lib/apt/lists/*

# --- Giai đoạn 4: Sao chép Mã nguồn Ứng dụng ---
# Sao chép toàn bộ mã nguồn của dự án vào thư mục làm việc /app
COPY . .

# --- Giai đoạn 5: Cấu hình Cổng và Lệnh Khởi động ---
# Cho Docker biết rằng ứng dụng sẽ lắng nghe trên cổng 8501 (cổng mặc định của Streamlit)
EXPOSE 8501

# Lệnh sẽ được thực thi khi container khởi động.
# --server.port 8501: Chỉ định cổng
# --server.address 0.0.0.0: Cho phép truy cập từ bên ngoài container (quan trọng!)
# --server.headless true: Tùy chọn để chạy ở chế độ headless, không tự mở trình duyệt.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]