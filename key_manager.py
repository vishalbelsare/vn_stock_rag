# key_manager.py

import os
import threading

class KeyManager:
    """
    Một lớp quản lý và xoay vòng các API key của Google Gemini.
    Lớp này được thiết kế để an toàn khi sử dụng trong môi trường đa luồng (thread-safe).
    """
    def __init__(self):
        self.keys = []
        self.current_index = 0
        # Sử dụng Lock để đảm bảo việc lấy key không bị xung đột giữa các thread
        self.lock = threading.Lock()
        self._load_keys()

    def _load_keys(self):
        """Tải tất cả các key có định dạng GOOGLE_API_KEY_n từ file .env."""
        i = 1
        while True:
            key = os.environ.get(f"GOOGLE_API_KEY_{i}")
            if key:
                self.keys.append(key)
                i += 1
            else:
                # Dừng lại khi không tìm thấy key tiếp theo
                break
        
        if not self.keys:
            raise ValueError("Không tìm thấy GOOGLE_API_KEY nào trong file .env! Vui lòng kiểm tra lại.")
            
        print(f"KeyManager đã tải thành công {len(self.keys)} Google API keys.")

    def get_next_key(self) -> str:
        """Lấy key tiếp theo trong danh sách một cách xoay vòng và an toàn."""
        with self.lock:
            if not self.keys:
                raise ValueError("Danh sách API key rỗng.")
            
            # Lấy key hiện tại
            key = self.keys[self.current_index]
            
            # Cập nhật index cho lần gọi tiếp theo
            self.current_index = (self.current_index + 1) % len(self.keys)
            
            print(f"KeyManager: Cấp phát key #{self.current_index + 1}")
            return key

key_manager = KeyManager()