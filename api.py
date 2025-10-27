# api.py

import sys
import io
import os
import traceback
from datetime import datetime
import threading 
import re

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from werkzeug.utils import secure_filename

from main import get_user_intent_with_mistral, FinancialCrew

app = Flask(__name__, static_folder='frontend')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOADS_DIR

def clean_ansi_codes(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

class WebSocketLogHandler(io.StringIO):
    def __init__(self, sid):
        super().__init__()
        self.sid = sid
    def write(self, s: str):
        if not self.closed:
            cleaned_log = clean_ansi_codes(s)
            if cleaned_log.strip():
                socketio.emit('log_update', {'log': cleaned_log}, to=self.sid)
            super().write(s)
    def close(self):
        super().close()


@app.route('/')
def index(): return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join('frontend', path)):
        return send_from_directory('frontend', path)
    elif os.path.exists(os.path.join('assets', path)):
        return send_from_directory('assets', path)
    return "Not Found", 404

@app.route('/uploadfile/', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files: return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '': return jsonify({"error": "No selected file"}), 400
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            print(f"File '{filename}' uploaded to project path: {file_path}")
            return jsonify({"file_path": file_path, "file_name": filename})
        return jsonify({"error": "Invalid file object"}), 400
    except Exception as e:
        print(f"File upload error: {e}")
        return jsonify({"error": f"Server error during file upload: {e}"}), 500


def analysis_thread_target(sid, user_query):
    """
    Hàm này là "trái tim" của quy trình, sẽ được chạy trong một thread riêng.
    Nó bao bọc toàn bộ logic blocking.
    """
    log_handler = WebSocketLogHandler(sid)
    original_stdout = sys.stdout
    try:
        sys.stdout = log_handler

        print("Bắt đầu phân tích yêu cầu người dùng...")
        intent = get_user_intent_with_mistral(user_query)
        
        ticker = intent.get('ticker')
        file_path = intent.get('file_path')

        if not ticker or not file_path:
            raise ValueError("Không thể xác định yêu cầu. Vui lòng cung cấp đủ thông tin.")
        
        print(f"\nBắt đầu quy trình tạo Bản tin Toàn diện cho {ticker}...\n")
        crew_runner = FinancialCrew(symbol=ticker, file_path=file_path)
        
        result = crew_runner.run_newsletter_creation()
        
        final_report = result.raw if result and hasattr(result, 'raw') else "Không có báo cáo được tạo ra."

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"reports/BanTin_{ticker}_{timestamp}.md"
        os.makedirs('reports', exist_ok=True)
        with open(report_filename, "w", encoding='utf-8') as f: f.write(final_report)
        print(f"\nBáo cáo đã được lưu tại: {report_filename}")
        
        socketio.emit('analysis_complete', {'report': final_report}, to=sid)

    except Exception as e:
        print(f"Lỗi trong quá trình xử lý: {e}")
        traceback.print_exc()
        socketio.emit('analysis_error', {'error': f"Đã xảy ra lỗi nghiêm trọng: {e}"}, to=sid)
    finally:
        sys.stdout = original_stdout
        if log_handler and not log_handler.closed:
            log_handler.close()


@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('run_analysis')
def handle_run_analysis(data):
    """
    Sự kiện chính, chỉ có nhiệm vụ khởi động một thread mới.
    """
    user_query = data.get('query')
    sid = request.sid
    print(f"Received query from {sid}. Starting new analysis thread.")
    
    socketio.start_background_task(target=analysis_thread_target, sid=sid, user_query=user_query)


if __name__ == '__main__':
    print("Starting Flask-SocketIO server in threading mode...")
    socketio.run(app, host='0.0.0.0', port=8000, debug=False, use_reloader=False)