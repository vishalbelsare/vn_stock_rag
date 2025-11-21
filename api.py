import sys
import io
import os
import traceback
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from werkzeug.utils import secure_filename
from main import run_analysis_workflow
import database_manager as db

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')
STATIC_ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')
UPLOADS_DIR = "uploads"
CHARTS_DIR = "charts"
REPORTS_DIR = "reports"

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

app = Flask(__name__, static_folder=STATIC_FRONTEND_DIR)
app.config['UPLOAD_FOLDER'] = UPLOADS_DIR
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

socket_sessions = {}

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    if os.path.exists(os.path.join(STATIC_FRONTEND_DIR, filename)):
        return send_from_directory(STATIC_FRONTEND_DIR, filename)
    if os.path.exists(os.path.join(STATIC_ASSETS_DIR, filename)):
        return send_from_directory(STATIC_ASSETS_DIR, filename)
    if filename.startswith(f"{CHARTS_DIR}/") and os.path.exists(os.path.join(PROJECT_ROOT, filename)):
        return send_from_directory(PROJECT_ROOT, filename)
    return "Not Found", 404

@app.route('/uploadfile/', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            return jsonify({"file_path": file_path, "file_name": filename})
        return jsonify({"error": "Invalid file object"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/subscribe', methods=['POST'])
def subscribe_newsletter():
    data = request.json
    email = data.get('email')
    ticker = data.get('ticker')
    if email and ticker:
        return jsonify({"status": "success", "message": f"Đã đăng ký nhận tin {ticker} cho {email}"})
    return jsonify({"error": "Thiếu thông tin"}), 400

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('start_chat')
def handle_start(data):
    client_session_id = data.get('sessionId') or str(uuid.uuid4())
    
    db.create_session(client_session_id)
    
    socket_sessions[request.sid] = client_session_id
    emit('session_initialized', {'sessionId': client_session_id})
    
    history = db.get_messages(client_session_id)
    emit('load_history', {'history': history})
    
    sessions_list = db.get_all_sessions_preview()
    emit('load_sidebar_sessions', {'sessions': sessions_list})

@socketio.on('switch_session')
def handle_switch_session(data):
    """Khi người dùng click vào sidebar"""
    new_session_id = data.get('sessionId')
    if new_session_id:
        socket_sessions[request.sid] = new_session_id
        
        history = db.get_messages(new_session_id)
        emit('session_initialized', {'sessionId': new_session_id}) 
        emit('load_history', {'history': history})

def analysis_thread_target(sid, user_query, session_id, file_info):
    try:
        def status_callback(msg):
            print(f"[Status Update] {msg}") 
            socketio.emit('thinking_step', {'step': msg}, to=sid)

        file_path = file_info.get('path') if file_info else None
        
        print(f"Starting workflow for SID: {sid}, File: {file_path}")

        final_report, report_filename = run_analysis_workflow(
            user_query, 
            session_id=session_id, 
            file_path=file_path,       
            status_callback=status_callback 
        )

        socketio.emit('analysis_complete', {'report': final_report}, to=sid)

    except Exception as e:
        traceback.print_exc()
        socketio.emit('analysis_error', {'error': str(e)}, to=sid)

@socketio.on('run_analysis')
def handle_run_analysis(data):
    sid = request.sid
    user_query = data.get('query')
    file_info = data.get('file_info')
    session_id = socket_sessions.get(sid)
    
    if not session_id:
        session_id = str(uuid.uuid4())
        socket_sessions[sid] = session_id

    socketio.start_background_task(
        target=analysis_thread_target, 
        sid=sid, 
        user_query=user_query, 
        session_id=session_id,
        file_info=file_info
    )

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000, debug=False, allow_unsafe_werkzeug=True)