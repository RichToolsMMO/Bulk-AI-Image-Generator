import requests
from PyQt5.QtCore import QSettings
from datetime import datetime

# Cài đặt màu thông báo QTextBrowser
successFormat = '<span style="color:green;">{}</span>'      # Thành công
errorFormat = '<span style="color:red;">{}</span>'          # Lỗi
warningFormat = '<span style="color:orange;">{}</span>'     # Cảnh báo
infoFormat = '<span style="color:blue;">{}</span>'          # Thông tin


class ApiImagenService:
    def __init__(self, license_key, show_active_logs):
        self.license_key = license_key
        self.logging = show_active_logs
        self.base_url = ''
        self.timeout = 15
        self.settings = QSettings('RichTools', 'Gen Image Client')

    def get_imagen4_tokens_via_license(self, limit=5):
        """Gửi yêu cầu đến server để lấy danh sách token Imagen4 thông qua license key """
        endpoint = '/api/checker/get-imagen4-token.php'
        url = f'{self.base_url}{endpoint}'
        data = {'license_key': self.license_key, 'limit': limit}
        try:
            # Gửi request POST đến API
            self.logging.append(warningFormat.format(f'[Imagen4] Gửi request POST {url} với data: {data}'))
            response = requests.post(url, json=data, timeout=self.timeout)
            if response.status_code == 200:
                # Nếu phản hồi HTTP OK, parse JSON
                result = response.json()

                if result.get('success'):
                    # Nếu kết quả thành công, lấy danh sách token
                    tokens = result.get('data', {}).get('tokens', [])
                    self.logging.append(successFormat.format(f'[Imagen4] Nhận {len(tokens)} tokens từ server'))
                    return tokens
                else:
                    # Nếu response JSON không thành công, ghi lỗi từ thông báo trả về
                    self.logging.append(warningFormat.format(f"[Imagen4] Lỗi lấy token: {result.get('message')}"))
                    return []
            else:
                # Nếu mã trạng thái HTTP khác 200, ghi log lỗi chi tiết
                self.logging.append(warningFormat.format(f'[Imagen4] Lỗi HTTP khi lấy token: {response.status_code} - {response.text}'))
                return []
        except Exception as e:
            # Ghi log nếu có ngoại lệ xảy ra (lỗi mạng, timeout, JSON decode,...)
            self.logging.append(errorFormat.format(f'[Imagen4] Exception khi lấy token: {str(e)}'))
            return []
