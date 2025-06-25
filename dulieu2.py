import threading
import time
from collections import defaultdict
from zlapi import ZaloAPI, ThreadType, Message
from zlapi.models import Mention  # Thêm dòng này để dùng Mention
from config import API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES


def banner():
    print("""
============================================================
      TOOL GỬI TOÀN BỘ FILE ngontreo.txt VÀO NHÓM ZALO
============================================================
""")


class Bot(ZaloAPI):
    def __init__(self, api_key, secret_key, imei=None, session_cookies=None):
        super().__init__(api_key, secret_key, imei, session_cookies)
        self.running = False

    def fetch_group_info(self):
        try:
            all_groups = self.fetchAllGroups()
            group_list = []
            for group_id, _ in all_groups.gridVerMap.items():
                group_info = super().fetchGroupInfo(group_id)
                group_name = group_info.gridInfoMap[group_id]["name"]
                group_list.append({'id': group_id, 'name': group_name})
            return group_list
        except Exception as e:
            print(f"Lỗi khi lấy danh sách nhóm: {e}")
            return []

    def display_group_menu_grouped(self, groups):
        if not groups:
            print("Không tìm thấy nhóm nào.")
            return None

        grouped = defaultdict(list)
        for group in groups:
            first_letter = group['name'][0].lower()
            grouped[first_letter].append(group)

        flat_list = []
        count = 1
        for letter in sorted(grouped.keys()):
            print(f"\n=== Nhóm bắt đầu bằng chữ '{letter.upper()}' ===")
            for group in grouped[letter]:
                print(f"{count}. {group['name']} (ID: {group['id']})")
                flat_list.append(group)
                count += 1
        return flat_list

    def select_group(self):
        groups = self.fetch_group_info()
        if not groups:
            return None

        flat_group_list = self.display_group_menu_grouped(groups)
        if not flat_group_list:
            return None

        while True:
            try:
                choice = int(input("\nNhập số thứ tự của nhóm: ").strip())
                if 1 <= choice <= len(flat_group_list):
                    return flat_group_list[choice - 1]['id']
                print(f"Vui lòng nhập từ 1 đến {len(flat_group_list)}.")
            except ValueError:
                print("Vui lòng nhập số hợp lệ.")

    def send_plain_message(self, thread_id, message_text):
        try:
            mention = Mention("-1", offset=0, length=len(message_text))  # Thêm mention @All
            self.send(
                Message(text=message_text, mention=mention),
                thread_id=thread_id,
                thread_type=ThreadType.GROUP
            )
            print("Đã gửi nội dung file vào nhóm.")
        except Exception as e:
            print(f"Lỗi khi gửi tin nhắn: {e}")

    def send_full_file_content(self, thread_id, delay):
        filename = "ngontreo.txt"
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    print("File ngontreo.txt rỗng hoặc không có nội dung hợp lệ.")
                    return

            self.running = True
            while self.running:
                self.send_plain_message(thread_id, content)
                time.sleep(delay)

        except FileNotFoundError:
            print("Không tìm thấy file: ngontreo.txt")
        except Exception as e:
            print(f"Lỗi khi gửi nội dung: {e}")

    def stop_sending(self):
        self.running = False
        print("Đã dừng gửi tin nhắn.")


def run_tool():
    banner()
    print("[1] Gửi toàn bộ nội dung từ ngontreo.txt vào nhóm Zalo")
    print("[0] Thoát")

    choice = input("Nhập lựa chọn: ").strip()
    if choice != '1':
        print("Đã thoát tool.")
        return

    client = Bot(API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES)
    thread_id = client.select_group()

    if not thread_id:
        print("Không có nhóm được chọn.")
        return

    try:
        delay = float(input("Nhập delay giữa mỗi lần gửi lại toàn bộ (giây): ").strip())
    except ValueError:
        print("Giá trị không hợp lệ, dùng mặc định 60s.")
        delay = 60

    send_thread = threading.Thread(
        target=client.send_full_file_content,
        args=(thread_id, delay)
    )
    send_thread.daemon = True
    send_thread.start()

    print(f"\nĐang gửi toàn bộ nội dung từ ngontreo.txt mỗi {delay}s... Nhấn Ctrl+C để dừng.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.stop_sending()
        print("Tool đã dừng bởi người dùng.")


if __name__ == "__main__":
    run_tool()
