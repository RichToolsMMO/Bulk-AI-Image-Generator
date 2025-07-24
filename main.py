# Welcome to Rich Gen Image Tool, a powerful and user-friendly software that lets you generate AI images for free – with no limits on how many images you can create.
# 
# Contact:
# • WhatsApp: https://wa.me/84777286725
# • Telegram: https://t.me/richsoftwaremmo

import sys, os
from pathlib import Path
import webbrowser, requests, machineid, re, subprocess, clipboard
from modules.image_generator import ImageGenerator
import account, packagetool

def start_generation_imagesai(self):
    """ Mô tả: Bắt đầu tiến hành tạo hình ảnh AI sử dụng ImageGen4 """
    try:
        prompts_text = self.list_prompts_content.toPlainText().strip()
        if not prompts_text:
            self.discardMessageDialog(self.file.item_text_language("mwarning", "message_mwarning3"))
            return
        prompts = [p.strip() for p in prompts_text.split('\n') if p.strip()]
        if not prompts:
            self.discardMessageDialog(self.file.item_text_language("mwarning", "message_mwarning4"))
            return
        if len(prompts) > 100:
            self.discardMessageDialog(self.file.item_text_language("mwarning", "message_mwarning5").format(str(len(prompts))))
            return
        # kiểm tra đường dẫn lưu kết quả
        output_dir = self.imageai_save_path.text()
        if not output_dir or not Path(output_dir).exists():
            self.discardMessageDialog(self.file.item_text_language("mwarning", "message_mwarning6"))
            return
        original_prompts = prompts.copy()
        tokens = self.tokenmanager.get_tokens()
        if not tokens:
            self.discardMessageDialog(self.file.item_text_language("mwarning", "message_mwarning8"))
            return
        if not self.image_generator:
            self.image_generator = ImageGenerator(tokens_list=tokens, show_logs=self.show_active_logs)

        # cấu hình kích thước
        aspect_text = self.imageai_size_list.currentText()
        aspect_ratio = self.imageai_size_mapping.get(aspect_text, 'IMAGE_ASPECT_RATIO_LANDSCAPE')
        # cấu hình phong cách
        style_text = self.imageai_styles_list.currentText()
        style_prefix = self.imageai_styles_mapping.get(style_text, '')

        # danh sách tất cả các prompts sau khi thêm phong cách
        api_prompts = prompts.copy()
        if style_prefix:
            api_prompts = [f'{style_prefix} {prompt}' for prompt in prompts]
            self.show_active_logs.append(infoFormat.format(f'Applied style \'{style_text}\' to {len(prompts)} prompts'))
        # thông số 'seed'
        self.fixed_seed = None
        self.show_active_logs.append(warningFormat.format('Sử dụng seed ngẫu nhiên cho mỗi ảnh'))

        # Cài đặt trạng thái tạo ảnh
        self.total_tasks = len(prompts)
        self.completed_tasks = 0
        self.is_generating = True
        self.datas_tasks = []
        self.generation_session_id += 1
        self.current_output_dir = output_dir
        self.show_active_logs.append(infoFormat.format(f'🔧 Starting generation session #{self.generation_session_id}'))

        # chuyển trạng thái hiện thị về giai đoạn bắt đầu
        self.reset_state_start_stage()
        # dọn dẹp các luồng
        self.cleanup_finished_threads()

        # bắt đầu quá trình tạo hình ảnh
        self.show_active_logs.append(successFormat.format(f'🚀 Starting new generation (active threads: {len(self.generation_threads)})'))
        thread_image_generator = ImageGenerator(tokens_list=self.tokenmanager.get_tokens(), show_logs=self.show_active_logs)
        # thêm các nhiệm vụ
        thread_image_generator.set_prompts_with_indices_and_seed_and_originals(api_prompts, original_prompts, aspect_ratio, self.fixed_seed)
        thread = ImageGenerationThread(thread_image_generator, output_dir, self.generation_session_id)
        self.current_generation_session = self.generation_session_id
        # tín hiệu tạo các hình ảnh AI
        thread.progress_updated.connect(self.update_progress)
        thread.status_updated.connect(self.update_status)
        thread.finished.connect(self.generation_finished)
        thread.start()
        self.generation_threads.append(thread)
    except Exception as e:
        self.errorsChangesDialog(str(e))