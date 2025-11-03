# test_mistral.py

import os
import requests
import json
from dotenv import load_dotenv

# --- Bước 1: Tải các biến môi trường từ file .env ---
print("Đang tải file .env...")
load_dotenv()

# Lấy API key từ biến môi trường
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
print(f"Đã đọc MISTRAL_API_KEY: '{MISTRAL_API_KEY[:5]}...'") # In 5 ký tự đầu để xác nhận

# --- Bước 2: Chuẩn bị yêu cầu API ---
# Đây là URL endpoint cho các mô hình chat của Mistral
url = "https://api.mistral.ai/v1/chat/completions"

# Dữ liệu gửi đi (payload) - một yêu cầu rất đơn giản
# Chúng ta sẽ dùng model 'mistral-tiny' vì nó rẻ và nhanh nhất, hoàn hảo để kiểm tra kết nối.
payload = {
    "model": "mistral-tiny",
    "messages": [
        {
            "role": "user",
            "content": "Chào bạn, hãy trả lời 'Kết nối thành công!' nếu bạn nhận được tin nhắn này."
        }
    ]
}

# Headers, bao gồm cả Authorization với API key
headers = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

print("\n--- Bắt đầu gửi yêu cầu đến Mistral AI ---")
print(f"Endpoint: {url}")
print(f"Model: {payload['model']}")

# --- Bước 3: Gửi yêu cầu và xử lý kết quả ---
try:
    # Gửi yêu cầu POST với timeout là 30 giây
    response = requests.post(url, json=payload, headers=headers, timeout=30)

    print(f"\nHTTP Status Code: {response.status_code}")

    # Kiểm tra xem yêu cầu có thành công không (status code 200-299)
    response.raise_for_status()

    # Phân tích và in ra kết quả
    response_data = response.json()
    
    print("\n--- KẾT NỐI THÀNH CÔNG! ---")
    print("Phản hồi thô từ API:")
    print(json.dumps(response_data, indent=2, ensure_ascii=False))
    
    # In ra nội dung tin nhắn trả lời
    content = response_data["choices"][0]["message"]["content"]
    print("\nNội dung trả lời từ Mistral:")
    print(f">>> {content}")

except requests.exceptions.HTTPError as http_err:
    print("\n--- LỖI HTTP ---")
    print(f"Đã xảy ra lỗi HTTP: {http_err}")
    # In ra nội dung lỗi từ server nếu có
    try:
        print("Chi tiết lỗi từ server:")
        print(response.json())
    except json.JSONDecodeError:
        print("Không thể phân tích phản hồi lỗi từ server.")
        print(response.text)
    print("\n**Gợi ý:** Lỗi 401 thường do API key sai. Lỗi 403/429 có thể do hết hạn mức. Lỗi 5xx là do server của Mistral.")

except requests.exceptions.RequestException as req_err:
    print("\n--- LỖI KẾT NỐI ---")
    print(f"Đã xảy ra lỗi kết nối mạng: {req_err}")
    print("\n**Gợi ý:** Vấn đề có thể do tường lửa, proxy, hoặc lỗi SSL. Hãy kiểm tra lại các biến môi trường SSL_CERT_FILE trong file .env nếu bạn đang dùng Windows.")

except Exception as e:
    print("\n--- LỖI KHÔNG XÁC ĐỊNH ---")
    print(f"Đã xảy ra một lỗi không mong muốn: {e}")