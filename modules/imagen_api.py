import json
import requests
import base64
import time
import random
from pathlib import Path
from PIL import Image
import string
import re

# Cài đặt màu thông báo QTextBrowser
successFormat = '<span style="color:green;">{}</span>'      # Thành công
errorFormat = '<span style="color:red;">{}</span>'          # Lỗi
warningFormat = '<span style="color:orange;">{}</span>'     # Cảnh báo
infoFormat = '<span style="color:blue;">{}</span>'          # Thông tin


class ImagenAPI:
    def __init__(self, token, proxy, show_logs):
        self.token = token                                                                              # Lưu access token
        self.proxy_raw = proxy                                                                          # Lưu chuỗi proxy chưa xử lý
        self.logging = show_logs
        self.api_url = 'https://aisandbox-pa.googleapis.com/v1:runImageFx'                              # URL API tạo ảnh
        self.session_id = f';{int(time.time() * 1000)}'                                                 # ID phiên bản dựa trên thời gian hiện tại (miliseconds)
        self.project_id = f'{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-' \
                          f'{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-' \
                          f'{random.randint(100000000000, 999999999999)}'                               # Tạo chuỗi project ID giả lập
        self.logging.append(warningFormat.format(f'[ImagenAPI] Khởi tạo với token: {self.token[:16]}..., proxy: {self.proxy_raw}'))
        # Kiểm tra proxy đầu vào
        if not proxy or proxy == 'Direct' or proxy.strip() == '':
            raise ValueError('Proxy là bắt buộc! Không thể tạo ảnh mà không có proxy.')
        self.proxies = self._parse_proxy(proxy)                                                         # Gọi hàm phân tích proxy

    def _parse_proxy(self, proxy_string):
        """ Mô tả: Hàm xử lý chuỗi proxy dạng host:port:user:pass thành dictionary """
        try:
            parts = proxy_string.split(':')                                                             # Tách chuỗi theo dấu :
            if len(parts) != 4:
                raise ValueError(f'Proxy không hợp lệ. Định dạng đúng: host:port:user:pass')
            host, port, user, password = parts                                                          # Gán các phần đã tách
            proxy_url = f'http://{user}:{password}@{host}:{port}'                                       # Tạo URL proxy đầy đủ
            return {'http': proxy_url, 'https': proxy_url}                                              # Trả về dict proxy cho requests
        except Exception as e:
            raise ValueError(f'Lỗi phân tích proxy: {e}')                                               # Ném lỗi nếu không phân tích được

    def generate_image(self, prompt, aspect_ratio='IMAGE_ASPECT_RATIO_LANDSCAPE', seed=None):
        """ Mô tả: Gửi yêu cầu đến API để tạo ảnh dựa trên prompt"""
        try:
            if not self.token:
                self.logging.append(warningFormat.format('Không có access token'))
                return

            if seed is None:
                seed = random.randint(1, 100000)                                                        # Nếu chưa có seed thì tạo ngẫu nhiên
            request_body = {
                'clientContext': {
                    'sessionId': self.session_id,
                    'tool': 'VIDEO_FX',
                    'projectId': self.project_id
                },
                'userInput': {
                    'candidatesCount': 1,
                    'seed': seed,
                    'prompts': [prompt]
                },
                'modelInput': {
                    'modelNameType': 'IMAGEN_3_5'
                },
                'aspectRatio': aspect_ratio
            }

            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'authorization': f'Bearer {self.token}',
                'content-type': 'text/plain;charset=UTF-8',
                'Referer': 'https://labs.google/',
            }

            self.logging.append(successFormat.format(f'Đang tạo ảnh với prompt: {prompt[:50]}...'))
            response = requests.post(
                self.api_url,
                data=json.dumps(request_body),
                headers=headers,
                proxies=self.proxies,
                timeout=90,
                verify=True
            )

            self.logging.append(infoFormat.format(f'Mã trạng thái HTTP: {response.status_code}'))
            if response.status_code != 200:
                self.logging.append(errorFormat.format(f'Nội dung lỗi: {response.text}'))

            if response.status_code == 200:
                return response.json()                                                          # Trả về dữ liệu JSON
            elif response.status_code == 401:
                self.logging.append(errorFormat.format('Token không hợp lệ hoặc đã hết hạn.'))
                return
            elif response.status_code == 400:
                self.logging.append(errorFormat.format(f'Lỗi từ API: {response.text}'))
                return {'error_code': 400, 'error_message': response.text}
            else:
                self.logging.append(errorFormat.format(f'Lỗi không xác định: {response.status_code} - {response.text}'))
                return
        except requests.exceptions.Timeout:
            self.logging.append(errorFormat.format('Yêu cầu quá thời gian cho phép (timeout)'))
            return
        except Exception as e:
            self.logging.append(errorFormat.format(f'Lỗi không xác định khi tạo ảnh: {e}'))
            return None

    def save_image(self, image_data, output_dir, prompt, index=0):
        """ Mô tả: Giải mã base64 ảnh và lưu vào ổ đĩa """
        try:
            encoded_image = image_data.get('encodedImage')  # Lấy dữ liệu base64
            if not encoded_image:
                self.logging.append(warningFormat.format('Không tìm thấy dữ liệu ảnh'))
                return

            image_bytes = base64.b64decode(encoded_image)  # Giải mã base64

            # Tạo tên file từ 5 từ đầu tiên của prompt
            words = prompt.split()[:5]
            first_five_words = '_'.join(words)
            safe_words = ''
            for char in first_five_words:
                if char.isalnum():
                    safe_words += char
                elif char in [' ', '-', '_']:
                    safe_words += '_'

            safe_words = re.sub('_+', '_', safe_words).strip('_')  # Loại bỏ dấu _
            random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))  # 4 ký tự ngẫu nhiên
            filename = f'{index:03d}_{safe_words}_{random_chars}.png'  # Tên file
            filepath = Path(output_dir) / filename  # Đường dẫn file đầy đủ

            filepath.parent.mkdir(parents=True, exist_ok=True)  # Tạo thư mục nếu chưa có
            with open(filepath, 'wb') as f:
                f.write(image_bytes)  # Ghi file ảnh

            # Kiểm tra tính hợp lệ của ảnh
            try:
                with Image.open(filepath) as img:
                    img.verify()
                self.logging.append(successFormat.format(f'Đã lưu ảnh tại: {filepath}'))
                return str(filepath)
            except Exception as e:
                self.logging.append(errorFormat.format(f'Ảnh không hợp lệ: {e}'))
                if filepath.exists():
                    filepath.unlink()  # Xóa file nếu không hợp lệ
                return
        except Exception as e:
            self.logging.append(errorFormat.format(f'Lỗi khi lưu ảnh: {e}'))
            return

    def process_response(self, response_data, output_dir, original_prompt, task_id=1):
        """ Mô tả: Duyệt qua kết quả trả về từ API và lưu tất cả ảnh"""
        saved_files = []                                                                                    # Danh sách các file đã lưu
        try:
            image_panels = response_data.get('imagePanels', [])                                             # Lấy danh sách panel ảnh
            for panel_idx, panel in enumerate(image_panels):
                generated_images = panel.get('generatedImages', [])                                         # Ảnh được tạo trong mỗi panel
                for img_idx, image_data in enumerate(generated_images):
                    file_path = self.save_image(image_data, output_dir, original_prompt, task_id)
                    if file_path:
                        saved_files.append(file_path)                                                       # Thêm đường dẫn ảnh đã lưu
            self.logging.append(successFormat.format(f'Đã lưu {len(saved_files)} ảnh cho prompt: {original_prompt[:50]}...'))
            return saved_files
        except Exception as e:
            self.logging.append(errorFormat.format(f'Lỗi khi xử lý response: {e}'))
            return saved_files
