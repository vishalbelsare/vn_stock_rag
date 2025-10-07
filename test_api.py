# # test_gemini.py
# import os
# from dotenv import load_dotenv
# import google.generativeai as genai

# # Tải file .env để lấy API key và cấu hình SSL
# load_dotenv()

# # Cấu hình SSL (quan trọng trên Windows)
# ssl_cert_file = os.environ.get("SSL_CERT_FILE")
# if ssl_cert_file:
#     os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = ssl_cert_file

# try:
#     print("Đang cấu hình Google API...")
#     genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

#     model_name_to_test = "gemini-2.5-flash" 

#     print(f"Đang khởi tạo model: {model_name_to_test}...")
#     model = genai.GenerativeModel(model_name_to_test)

#     print("Đang gửi một yêu cầu đơn giản...")
#     response = model.generate_content("Chào bạn, bạn có khỏe không?")

#     print("\n--- KẾT QUẢ THÀNH CÔNG ---")
#     print(response.text)
#     print("--------------------------")
#     print("\n>>> Kết nối đến Google Gemini thành công với model này! Vấn đề có thể nằm ở việc gọi song song trong crewAI.")

# except Exception as e:
#     print("\n--- ĐÃ XẢY RA LỖI ---")
#     print(f"Lỗi: {e}")
#     print("----------------------")
#     print("\n>>> Nếu bạn vẫn thấy lỗi 503 ở đây, vấn đề nằm ở API key hoặc tài khoản Google của bạn, không phải do crewAI.")

#     "C:/Users/nguye/Documents/vn_stock_rag/bctcfpt.pdf"



import os
import PIL.Image
from io import BytesIO
import google.generativeai as genai

# Configure your API key
# Replace "YOUR_API_KEY" with your actual Gemini API key
# It's recommended to store your API key as an environment variable (GEMINI_API_KEY)
# For demonstration, it's directly set here.
genai.configure(api_key="AIzaSyDEov0T2N7_06qHJslvbnOCa2eQKv8VJgM") 

# Initialize the Gemini Flash model for image generation
model = genai.GenerativeModel('gemini-2.5-flash-image')

# Define your prompt for image generation
prompt = "A futuristic cityscape at sunset with flying cars and towering skyscrapers."

# Generate the image
try:
    response = model.generate_content(prompt)

    # Process the response to extract and save the image
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            # Assuming the image data is returned as inline_data
            image_data = part.inline_data.data
            image = PIL.Image.open(BytesIO(image_data))
            image.save("generated_image.png")
            print("Image generated and saved as generated_image.png")
        elif part.text is not None:
            # If the response contains text, print it
            print(f"Model response (text): {part.text}")

except Exception as e:
    print(f"An error occurred: {e}")
