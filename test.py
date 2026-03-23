import sys
import ctypes
import subprocess
import screen_brightness_control as sbc
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSlider, QLabel, QGroupBox, QPushButton, 
                             QSystemTrayIcon, QMenu, QAction, QStyle, 
                             QGraphicsDropShadowEffect, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor, QMouseEvent

# --- 定义 Windows API 相关的结构体和常量 ---
class DISPLAY_DEVICE(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("DeviceName", ctypes.c_wchar * 32),
        ("DeviceString", ctypes.c_wchar * 128),
        ("StateFlags", ctypes.c_ulong),
        ("DeviceID", ctypes.c_wchar * 128),
        ("DeviceKey", ctypes.c_wchar * 128)
    ]
DISPLAY_DEVICE_ATTACHED_TO_DESKTOP = 0x00000001


class BrightnessApp(QWidget):
    def __init__(self):
        super().__init__()
        self.monitors = []
        self.brightness_labels = {}
        self.brightness_sliders = {} 
        self.eye_care_labels = {}
        self.eye_care_sliders = {}
        self.is_quitting = False     
        self.dragPos = QPoint() # 用于记录拖拽坐标
        
        self.init_ui()
        self.init_tray_icon()        
        self.refresh_monitors()      

    def init_ui(self):
        # 1. 设置无边框和背景透明
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(520) 

        # 2. 创建主容器（承载背景、圆角和阴影）
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("CentralWidget")
        
        # 👑 顶级现代暗黑 QSS (加入自定义标题栏样式)
        self.setStyleSheet("""
            /* 主容器圆角背景 */
            QWidget#CentralWidget {
                background-color: #121212; 
                border-radius: 12px;
                border: 1px solid #2C2C30;
            }
            QWidget { 
                color: #F4F4F5; 
                font-family: "Segoe UI Variable", "Segoe UI", "Microsoft YaHei", sans-serif; 
                font-size: 13px; 
            }
            
            /* 自定义标题栏按钮 */
            QPushButton.TitleBtn {
                background-color: transparent;
                border: none;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton.TitleBtn:hover { background-color: #27272A; }
            QPushButton#CloseBtn:hover { background-color: #E81123; color: white; } /* 微软经典悬浮红 */
            
            QGroupBox { 
                background-color: #1E1E20; 
                border: 1px solid #2C2C30; 
                border-radius: 10px; 
                margin-top: 20px; 
                padding-bottom: 15px; 
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                subcontrol-position: top left; 
                padding: 0 8px; 
                color: #60A5FA; 
                font-weight: bold; 
                left: 10px;
            }
            
            QSlider::groove:horizontal { border-radius: 4px; height: 8px; background: #27272A; }
            QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #60A5FA); border-radius: 4px; }
            QSlider::handle:horizontal { background: #FFFFFF; border: 2px solid #3B82F6; width: 16px; height: 16px; margin: -5px 0; border-radius: 9px; }
            QSlider::handle:horizontal:hover { background: #EFF6FF; border: 2px solid #2563EB;}
            
            QPushButton { background-color: #27272A; border: 1px solid #3F3F46; padding: 8px 12px; border-radius: 6px; }
            QPushButton:hover { background-color: #3F3F46; }
            QPushButton:pressed { background-color: #18181B; }
            
            QPushButton#primaryBtn { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6); color: white; border: none; }
            QPushButton#primaryBtn:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #2563EB); }
        """)

        # 3. 添加高级外阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 4)
        self.central_widget.setGraphicsEffect(shadow)

        # 整体布局 (外层布局用于留出阴影空间)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(15, 15, 15, 15) 
        outer_layout.addWidget(self.central_widget)

        # 内部主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 15, 20, 20)
        self.main_layout.setSpacing(12)

        # --- 顶部：自定义标题栏 ---
        title_bar_layout = QHBoxLayout()
        title_bar_layout.setContentsMargins(0, 0, 0, 10)
        
        # 软件名称
        title_label = QLabel("🖥️ 显示器控制中心 Pro")
        title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #F4F4F5;")
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # 最小化按钮
        min_btn = QPushButton("—")
        min_btn.setFixedSize(30, 30)
        min_btn.setProperty("class", "TitleBtn")
        min_btn.clicked.connect(self.hide) # 点击隐藏到托盘
        title_bar_layout.addWidget(min_btn)
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setObjectName("CloseBtn")
        close_btn.setProperty("class", "TitleBtn")
        close_btn.clicked.connect(self.close) # 触发 closeEvent 隐藏到托盘
        title_bar_layout.addWidget(close_btn)
        
        self.main_layout.addLayout(title_bar_layout)

        # 分割线
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #2C2C30;")
        self.main_layout.addWidget(line)

        # --- 功能区 ---
        self.refresh_btn = QPushButton("↻ 重新扫描所有设备")
        self.refresh_btn.setObjectName("primaryBtn")
        self.refresh_btn.clicked.connect(self.refresh_monitors)
        self.main_layout.addWidget(self.refresh_btn, alignment=Qt.AlignRight)

        self.brightness_layout = QVBoxLayout()
        self.main_layout.addLayout(self.brightness_layout)

        self.eye_care_group = QGroupBox(" 🌙 独立护眼模式 ")
        self.eye_care_layout = QVBoxLayout()
        self.eye_care_layout.setContentsMargins(15, 20, 15, 15)
        self.eye_care_group.setLayout(self.eye_care_layout)
        self.main_layout.addWidget(self.eye_care_group)

        self.create_system_controls()

    # --- 核心：接管鼠标事件实现无边框拖拽 ---
    def mousePressEvent(self, event: QMouseEvent):
        # 只有点击左键，且在窗口上方区域（标题栏附近）时才允许拖拽
        if event.button() == Qt.LeftButton and event.pos().y() < 60:
            self.dragPos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and not self.dragPos.isNull():
            self.move(event.globalPos() - self.dragPos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragPos = QPoint()
        
    # --- 原有的底层逻辑保持不变 ---
    def init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = self.style().standardIcon(QStyle.SP_DesktopIcon)
        self.tray_icon.setIcon(icon)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        self.tray_menu = QMenu()
        self.tray_menu.setStyleSheet("""
            QMenu { background-color: #1E1E20; color: #E4E4E7; border: 1px solid #3F3F46; border-radius: 5px; }
            QMenu::item { padding: 8px 25px 8px 20px; }
            QMenu::item:selected { background-color: #3B82F6; color: white; }
            QMenu::separator { height: 1px; background: #3F3F46; margin: 4px 10px; }
        """)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def update_tray_menu(self):
        self.tray_menu.clear() 
        action_show = QAction("⚙️ 打开主控制面板", self)
        action_show.triggered.connect(lambda: (self.showNormal(), self.activateWindow()))
        self.tray_menu.addAction(action_show)
        self.tray_menu.addSeparator()

        menu_brightness = self.tray_menu.addMenu("☀️ 亮度快速调节")
        if self.monitors:
            for monitor in self.monitors:
                sub_menu = menu_brightness.addMenu(f"显示器: {monitor}")
                for val in [0, 25, 50, 75, 100]:
                    act = QAction(f"{val}%", self)
                    act.triggered.connect(lambda checked, m=monitor, v=val: self.set_brightness_sync(m, v))
                    sub_menu.addAction(act)
        else:
            menu_brightness.setEnabled(False)

        menu_eye = self.tray_menu.addMenu("🌙 护眼模式快速切换")
        windows_displays = self.get_windows_displays()
        if windows_displays:
            for dev_name, friendly_name in windows_displays.items():
                sub_menu = menu_eye.addMenu(f"{friendly_name}")
                for val in [0, 25, 50, 75, 100]:
                    act = QAction(f"{val}% (关闭)" if val == 0 else f"{val}%", self)
                    act.triggered.connect(lambda checked, d=dev_name, v=val: self.set_eye_care_sync(d, v))
                    sub_menu.addAction(act)
        else:
            menu_eye.setEnabled(False)

        self.tray_menu.addSeparator()
        menu_proj = self.tray_menu.addMenu("🖥️ 投影模式")
        modes = [("仅电脑屏幕", '/internal'), ("复制", '/clone'), ("扩展", '/extend'), ("仅外接屏幕", '/external')]
        for name, cmd in modes:
            act = QAction(name, self)
            act.triggered.connect(lambda checked, c=cmd: subprocess.Popen(['displayswitch.exe', c]))
            menu_proj.addAction(act)

        self.tray_menu.addSeparator()
        action_quit = QAction("❌ 完全退出", self)
        action_quit.triggered.connect(self.quit_app)
        self.tray_menu.addAction(action_quit)

    def set_brightness_sync(self, monitor_name, value):
        self.update_brightness(monitor_name, value) 
        if monitor_name in self.brightness_sliders:
            self.brightness_sliders[monitor_name].blockSignals(True)
            self.brightness_sliders[monitor_name].setValue(value)
            self.brightness_sliders[monitor_name].blockSignals(False)

    def set_eye_care_sync(self, device_name, value):
        self.update_single_eye_care(device_name, value) 
        if device_name in self.eye_care_sliders:
            self.eye_care_sliders[device_name].blockSignals(True)
            self.eye_care_sliders[device_name].setValue(value)
            self.eye_care_sliders[device_name].blockSignals(False)

    def create_system_controls(self):
        sys_group = QGroupBox(" 🖥️ 投影切换 (Win+P) ")
        sys_layout = QVBoxLayout()
        sys_layout.setContentsMargins(15, 20, 15, 15)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_pc = QPushButton("仅电脑屏幕")
        btn_pc.clicked.connect(lambda: subprocess.Popen(['displayswitch.exe', '/internal']))
        
        btn_clone = QPushButton("复制")
        btn_clone.clicked.connect(lambda: subprocess.Popen(['displayswitch.exe', '/clone']))
        
        btn_extend = QPushButton("扩展")
        btn_extend.clicked.connect(lambda: subprocess.Popen(['displayswitch.exe', '/extend']))
        
        btn_second = QPushButton("仅外接屏幕")
        btn_second.clicked.connect(lambda: subprocess.Popen(['displayswitch.exe', '/external']))

        btn_layout.addWidget(btn_pc)
        btn_layout.addWidget(btn_clone)
        btn_layout.addWidget(btn_extend)
        btn_layout.addWidget(btn_second)
        
        sys_layout.addLayout(btn_layout)
        sys_group.setLayout(sys_layout)
        self.main_layout.addWidget(sys_group)

    def get_windows_displays(self):
        displays = {}
        user32 = ctypes.windll.user32
        dev_num = 0
        display_device = DISPLAY_DEVICE()
        display_device.cb = ctypes.sizeof(display_device)

        while user32.EnumDisplayDevicesW(None, dev_num, ctypes.byref(display_device), 0):
            if display_device.StateFlags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP:
                adapter_name = display_device.DeviceName
                monitor_device = DISPLAY_DEVICE()
                monitor_device.cb = ctypes.sizeof(monitor_device)
                if user32.EnumDisplayDevicesW(adapter_name, 0, ctypes.byref(monitor_device), 0):
                    friendly_name = monitor_device.DeviceString
                else:
                    friendly_name = f"显示器 {dev_num + 1}"
                displays[adapter_name] = friendly_name
            dev_num += 1
        return displays

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())
                item.layout().deleteLater()

    def refresh_monitors(self):
        self.refresh_btn.setText("扫描中...")
        QApplication.processEvents() 
        
        self.clear_layout(self.brightness_layout)
        self.clear_layout(self.eye_care_layout)
        self.brightness_labels.clear()
        self.brightness_sliders.clear()
        self.eye_care_labels.clear()
        self.eye_care_sliders.clear()

        try:
            self.monitors = sbc.list_monitors()
        except Exception:
            self.monitors = []

        if not self.monitors:
            error_label = QLabel('未检测到支持硬件亮度调节的显示器')
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: #9CA3AF;")
            self.brightness_layout.addWidget(error_label)
        else:
            for monitor_name in self.monitors:
                group = QGroupBox(f" ☀️ 硬件亮度: {monitor_name} ")
                vbox = QVBoxLayout()
                vbox.setContentsMargins(15, 20, 15, 15)

                label = QLabel('当前亮度: 读取中...')
                self.brightness_labels[monitor_name] = label
                vbox.addWidget(label)

                slider = QSlider(Qt.Horizontal)
                slider.setMinimum(0)
                slider.setMaximum(100)
                
                try:
                    current_brightness = sbc.get_brightness(display=monitor_name)[0]
                    slider.setValue(current_brightness)
                    label.setText(f'当前亮度: {current_brightness}%')
                except:
                    label.setText('亮度: 无法读取')
                    slider.setValue(50)

                slider.valueChanged.connect(lambda value, m=monitor_name: self.update_brightness(m, value))
                self.brightness_sliders[monitor_name] = slider 
                vbox.addWidget(slider)
                group.setLayout(vbox)
                self.brightness_layout.addWidget(group)

        windows_displays = self.get_windows_displays()
        
        if not windows_displays:
            e_label = QLabel('无法获取系统显示器列表')
            e_label.setAlignment(Qt.AlignCenter)
            e_label.setStyleSheet("color: #9CA3AF;")
            self.eye_care_layout.addWidget(e_label)
        else:
            for dev_name, friendly_name in windows_displays.items():
                box = QVBoxLayout()
                label = QLabel(f'色温 ({friendly_name}): 0% (关闭)')
                self.eye_care_labels[dev_name] = label
                box.addWidget(label)

                slider = QSlider(Qt.Horizontal)
                slider.setMinimum(0)
                slider.setMaximum(100)
                slider.setValue(0)
                slider.setStyleSheet("""
                    QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F59E0B, stop:1 #FCD34D); } 
                    QSlider::handle:horizontal { border: 2px solid #F59E0B; }
                    QSlider::handle:horizontal:hover { background: #FEF3C7; border: 2px solid #D97706;}
                """)
                
                slider.valueChanged.connect(lambda value, d=dev_name: self.update_single_eye_care(d, value))
                self.eye_care_sliders[dev_name] = slider 
                
                box.addWidget(slider)
                self.eye_care_layout.addLayout(box)

        self.refresh_btn.setText("↻ 重新扫描所有设备")
        self.update_tray_menu()

    def update_brightness(self, monitor_name, value):
        self.brightness_labels[monitor_name].setText(f'当前亮度: {value}%')
        try:
            sbc.set_brightness(value, display=monitor_name)
        except Exception:
            pass 

    def update_single_eye_care(self, device_name, value):
        self.eye_care_labels[device_name].setText(f'色温: {value}%')
        try:
            ramp = (ctypes.c_ushort * 768)()
            for i in range(256):
                ramp[i] = i * 256
                ramp[i + 256] = int(i * 256 * (1.0 - (0.15 * value / 100.0)))
                ramp[i + 512] = int(i * 256 * (1.0 - (0.50 * value / 100.0)))
                
            gdi32 = ctypes.windll.gdi32
            hdc = gdi32.CreateDCW(device_name, None, None, None)
            if hdc:
                gdi32.SetDeviceGammaRamp(hdc, ramp)
                gdi32.DeleteDC(hdc)
        except Exception as e:
            pass

    def closeEvent(self, event):
        if not self.is_quitting:
            event.ignore() 
            self.hide()    
            self.tray_icon.showMessage(
                "显示器控制中心",
                "已隐入托盘，右键可快速调节。",
                QSystemTrayIcon.Information,
                2000 
            )
        else:
            for dev_name in self.eye_care_sliders.keys():
                self.update_single_eye_care(dev_name, 0)
            event.accept()

    def quit_app(self):
        self.is_quitting = True
        self.close()           # 触发 closeEvent，执行护眼模式色彩恢复
        self.tray_icon.hide()  # 隐藏托盘图标，防止系统托盘留下残影
        QApplication.quit()    # 强制结束整个 Qt 应用程序的后台进程

if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    window = BrightnessApp()
    window.show()
    sys.exit(app.exec_())