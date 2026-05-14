import sys, os
import psutil
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer
import ctypes

def open_app(path):
    os.startfile(path)

def get_file_version(path):
    try:
        size = ctypes.windll.version.GetFileVersionInfoSizeW(path, None)
        if size == 0:
            return "N/A"
        res = ctypes.create_string_buffer(size)
        ctypes.windll.version.GetFileVersionInfoW(path, 0, size, res)

        r = ctypes.c_void_p()
        l = ctypes.c_uint()

        # Lấy danh sách ngôn ngữ/codepage
        if ctypes.windll.version.VerQueryValueW(res, '\\\\VarFileInfo\\\\Translation',
                                               ctypes.byref(r), ctypes.byref(l)) and l.value > 0:
            # Mỗi entry gồm 2 WORD: langID và codepage
            lang, codepage = ctypes.cast(r.value, ctypes.POINTER(ctypes.c_ushort * 2)).contents
            block = f'\\\\StringFileInfo\\\\{lang:04x}{codepage:04x}\\\\ProductVersion'
            if ctypes.windll.version.VerQueryValueW(res, block, ctypes.byref(r), ctypes.byref(l)) and l.value > 0:
                return ctypes.wstring_at(r.value, l.value)

            block = f'\\\\StringFileInfo\\\\{lang:04x}{codepage:04x}\\\\FileVersion'
            if ctypes.windll.version.VerQueryValueW(res, block, ctypes.byref(r), ctypes.byref(l)) and l.value > 0:
                return ctypes.wstring_at(r.value, l.value)

        # Nếu vẫn không có, fallback sang root
        if ctypes.windll.version.VerQueryValueW(res, '\\\\', ctypes.byref(r), ctypes.byref(l)) and l.value > 0:
            ver_struct = ctypes.cast(r.value, ctypes.POINTER(ctypes.c_uint * (l.value // 4))).contents
            ms = ver_struct[0]
            ls = ver_struct[1]
            return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"

        return "N/A"
    except Exception:
        return "N/A"


class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Launcher Applications")
        self.resize(500, 650)

        self.layout = QVBoxLayout()
        self.app_start_times = {}

        # Logo công ty
        logo = QLabel()
        pixmap = QPixmap("company_logo.png")
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(120, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo.setText("PHAT 11706")
            logo.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(logo, alignment=Qt.AlignCenter)

        # Nút chuyển theme
        self.theme_button = QPushButton("Dark Mode")
        self.theme_button.clicked.connect(self.toggle_theme)
        self.layout.addWidget(self.theme_button, alignment=Qt.AlignRight)

        # Tree hiển thị ứng dụng
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Application")
        self.tree.setIndentation(25)
        self.tree.setFont(QFont("Segoe UI", 12))
        self.apply_light_theme()

        # Node ứng dụng đang mở
        self.running_node = QTreeWidgetItem(self.tree, ["Open Application"])

        # Danh sách ứng dụng
        self.apps = {
            "KV STUDIO Ver.11G": "C:\\\\Program Files (x86)\\KEYENCE\\KVS11G\\KVS\\Kvs.exe",
            "VT STUDIO Ver.8G": "C:\\Program Files (x86)\\KEYENCE\\VTS8G\\VT5\\VTS.exe",
            "IP Setting Tool": "C:\\Program Files (x86)\\KEYENCE\\IP Setting Tool\\IPSettingTool.exe",
            "GX Works2":"C:\\Program Files (x86)\\MELSOFT\\GPPW2\\GD2.exe",
            "GT Designer3": "C:\\Program Files (x86)\\MELSOFT\\GTD3_2000\\GTD3_Startup.exe",
            "Launch Sysmac Studio": "C:\\Program Files\\OMRON\\Sysmac Studio\\SysmacStudio.exe",
            "CX-Designer": "C:\\Program Files (x86)\\Omron\\CX-Designer\\cxd.exe",
            "ACT Controller 2": "C:\\Program Files\\SMCApplication\\ACT Controller 2\\ACTController2.exe",
            "PC Interface Software for RC": "C:\\Program Files (x86)\\IAI Corporation\\RcPc\\RcPc.exe",
            "MPE720 Ver.7": "C:\\Program Files (x86)\\YASKAWA\\MPE720 Ver7\\Bin\\FWXIDE.exe",
            "SigmaWin+ Ver.7":"C:\\Program Files (x86)\\YASKAWA\\SigmaWinPlus7\\Bin\\SWPlus.exe",
            "Visual Studio Code": "C:\\Users\\CCSX\\AppData\\Local\\Programs\\Microsoft VS Code\\\\Code.exe",
            "MEXE02 English Edition": "C:\\Program Files (x86)\\ORIENTAL MOTOR\\MEXE02ENUS\\MEXE02.exe",
            "MEXE02 Ver.4": "C:\\Program Files (x86)\\ORIENTAL MOTOR\\MEXE02V4\\OM.MEXE02.exe",
            "RCX-Studio 2020": "C:\\Program Files (x86)\\Yamaha Motor\\RCX-Studio 2020\\RCX-Studio 2020.exe",
            "RCXiVY2+ Studio": "C:\\Program Files (x86)\\Yamaha Motor\\RCXiVY2+ Studio\\RCXiVY2+ Studio.exe"
        }

        # Nhóm ứng dụng
        self.add_group("Keyence", ["KV STUDIO Ver.11G", "VT STUDIO Ver.8G", "IP Setting Tool"])
        self.add_group("Mitsubishi", ["GX Works2", "GT Designer3"])
        self.add_group("Omron", ["Launch Sysmac Studio", "CX-Designer"])
        self.add_group("Robo", ["ACT Controller 2","PC Interface Software for RC"])
        self.add_group("Yaskawa", ["MPE720 Ver.7","SigmaWin+ Ver.7"])
        self.add_group("AI", ["Visual Studio Code"])
        self.add_group("Oriental", ["MEXE02 English Edition","MEXE02 Ver.4"])
        self.add_group("Yamaha", ["RCX-Studio 2020","RCXiVY2+ Studio"])

        self.tree.itemDoubleClicked.connect(self.launch_app)
        self.tree.itemExpanded.connect(self.collapse_other_nodes)

        # Timer cập nhật uptime
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_running_apps)
        self.timer.start(1000)

        self.layout.addWidget(self.tree)
        self.setLayout(self.layout)

    def add_group(self, group_name, app_list):
        group = QTreeWidgetItem(self.tree, [group_name])
        for app in app_list:
            version = get_file_version(self.apps[app])
            QTreeWidgetItem(group, [f"{app} v{version}"])

    # Theme
    def apply_light_theme(self):
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #f9fbfd;
                border: 1px solid #d0d7de;
                border-radius: 10px;
                padding: 8px;
                color: #000000;
            }
            QTreeWidget::item:hover {
                background-color: #e6f7ff;
                color: #0056b3;
            }
            QTreeWidget::item:selected {
                background-color: #cce5ff;
                color: #003366;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #0056b3;
                color: white;
                font-weight: bold;
                border: none;
                padding: 6px;
            }
        """)
        self.theme_button.setText("Dark Mode")

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #2c3e50;
                border: 1px solid #1a252f;
                border-radius: 10px;
                padding: 8px;
                color: #f5f5f5;
            }
            QTreeWidget::item:hover {
                background-color: #34495e;
                color: #1abc9c;
            }
            QTreeWidget::item:selected {
                background-color: #16a085;
                color: #ffffff;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #1abc9c;
                color: white;
                font-weight: bold;
                border: none;
                padding: 6px;
            }
        """)
        self.theme_button.setText("Light Mode")

    def toggle_theme(self):
        if "Dark" in self.theme_button.text():
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    # Hiển thị ứng dụng đang mở
    def update_running_apps(self):
        self.running_node.takeChildren()
        now = datetime.now()
        for p in psutil.process_iter(['name', 'create_time']):
            exe_name = p.info['name'].lower()
            for app_name, path in self.apps.items():
                if exe_name == os.path.basename(path).lower():
                    version = get_file_version(path)
                    uptime = now - datetime.fromtimestamp(p.info['create_time'])
                    uptime_str = str(uptime).split('.')[0]
                    QTreeWidgetItem(self.running_node, [f"{app_name} v{version} (Đang chạy: {uptime_str})"])

    # Mở ứng dụng
    def launch_app(self, item, column):
        text = item.text(column)
        app_name = text.split(" v")[0]
        if app_name in self.apps:
            open_app(self.apps[app_name])
            self.app_start_times[app_name] = datetime.now()
            self.update_running_apps()

    def collapse_other_nodes(self, item):
        for i in range(self.tree.topLevelItemCount()):
            node = self.tree.topLevelItem(i)
            if node is not item:
                node.setExpanded(False)

# MAIN
if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec_())
    input("\\nNhấn Enter để thoát...")
