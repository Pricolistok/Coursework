import sys
import ctypes
import time
import os
from ctypes import wintypes
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import QTimer, Qt
from design.design import Ui_MainWindow
from view.map_manager import MapManager
from view.car_manager import CarManager
from view.scene_manager import SceneManager
from view.light_dialog import LightDialog
from settings.consts import *
import algorithms.draw_faces as draw_logic


class MainApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.map_manager = None
        self.car_manager = None
        self.scene_manager = None
        self.timer = None
        self.last_time = time.time()
        self.frame_count = 0

        self.initStart()

    def closeEvent(self, event):
        try:
            if os.path.exists(FILENAME_LIGHTS):
                with open(FILENAME_LIGHTS, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                if lines:
                    first_line = lines[0].strip()
                    with open(FILENAME_LIGHTS, 'w', encoding='utf-8') as f:
                        f.write(first_line)

        except Exception as e:
            print(f"Ошибка при очистке файла света: {e}")

        event.accept()

    def initStart(self):
        self.setupUi(self)
        self.setFixedSize(self.size())

        style = "background-color: #404040; color: white; font-weight: bold;"
        self.mapBtn.setStyleSheet(style)
        self.lightBtn.setStyleSheet(style)
        self.aboutProgramm.setStyleSheet(style)
        self.aboutCreator.setStyleSheet(style)

        self.setDarkTitleBar()
        self.init_managers()
        self.setup_connections()
        self.start_timer()

    def setDarkTitleBar(self):
        if sys.platform == "win32":
            try:
                value = wintypes.DWORD(1)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(int(self.winId()), 20, ctypes.byref(value),
                                                           ctypes.sizeof(value))
            except Exception:
                pass
        self.setDarkPalette()

    def setDarkPalette(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        self.setPalette(dark_palette)

    def init_managers(self):
        self.scene_manager = SceneManager(self.label_field)
        self.map_manager = MapManager(self.mapView, self.scene_manager)
        self.car_manager = CarManager(self.scene_manager)
        self.map_manager.on_path_calculated = self.on_path_calculated
        self.car_manager.on_movement_finished = self.on_movement_finished
        self.scene_manager.load_scene_data()
        self.car_manager.load_car_data()

    def setup_connections(self):
        self.mapBtn.clicked.connect(self.start_movement)
        self.lightBtn.clicked.connect(self.open_light_dialog)
        self.aboutProgramm.clicked.connect(self.show_about_program)
        self.aboutCreator.clicked.connect(self.show_about_creator)

    def open_light_dialog(self):
        dialog = LightDialog(self)
        if dialog.exec_():
            data = dialog.get_data()
            self.add_light_to_file(data)
            self.reload_lighting()

    def add_light_to_file(self, data):
        try:
            line = f"{data['dir'][0]} {data['dir'][1]} {data['dir'][2]} " \
                   f"{data['color'][0]} {data['color'][1]} {data['color'][2]} " \
                   f"{data['intensity']}"

            with open(FILENAME_LIGHTS, 'a', encoding='utf-8') as f:
                f.write('\n' + line)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить настройки света:\n{e}")

    def reload_lighting(self):
        draw_logic.reload_lights()

    def show_about_program(self):
        QMessageBox.information(self, ABOUT_PROGRAM_TITLE, ABOUT_PROGRAM_TEXT)

    def show_about_creator(self):
        QMessageBox.information(self, ABOUT_CREATOR_TITLE, ABOUT_CREATOR_TEXT)

    def start_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(FRAME_TIME_MS)

    def start_movement(self):
        if not self.map_manager.can_start_movement():
            self.show_start_error()
            return
        start_position = self.map_manager.get_start_position()
        path_points = self.map_manager.get_path_points()
        self.car_manager.start_movement(start_position, path_points)
        self.mapBtn.setEnabled(False)

    def show_start_error(self):
        start_idx = self.map_manager.start_idx
        end_idx = self.map_manager.end_idx
        if start_idx is None and end_idx is None:
            QMessageBox.warning(self, "Ошибка", "Не выбраны начальная и конечная точки!")
        elif start_idx is None:
            QMessageBox.warning(self, "Ошибка", "Не выбрана начальная точка!")
        elif end_idx is None:
            QMessageBox.warning(self, "Ошибка", "Не выбрана конечная точка!")
        else:
            QMessageBox.warning(self, "Ошибка", "Путь не может быть построен!")

    def update_scene(self):
        self.car_manager.update_movement()
        self.scene_manager.update_scene()
        self.update_fps()

    def update_fps(self):
        self.frame_count += 1
        current_time = time.time()
        elapsed_time = current_time - self.last_time
        if elapsed_time >= 1.0:
            real_fps = self.frame_count / elapsed_time
            self.label_fps.setText(f"ФПС: {real_fps:.1f}")
            self.frame_count = 0
            self.last_time = current_time

    # def update_scene(self):
    #     start_render_time = time.time()
    #     self.car_manager.update_movement()
    #     self.scene_manager.update_scene()
    #     end_render_time = time.time()
    #     render_time_ms = (end_render_time - start_render_time) * 1000
    #     self.update_fps(render_time_ms)
    #
    # def update_fps(self, render_time_ms):
    #     self.frame_count += 1
    #     current_time = time.time()
    #     elapsed_time = current_time - self.last_time
    #     if elapsed_time >= 1.0:
    #         real_fps = self.frame_count / elapsed_time
    #         self.label_fps.setText(f"ФПС: {real_fps:.1f}")
    #         current_scale = self.scene_manager.current_scale
    #         print(
    #             f"Масштаб: {current_scale:.1f} | Время генерации кадра: {render_time_ms:.2f} мс | FPS: {real_fps:.1f}")
    #         self.frame_count = 0
    #         self.last_time = current_time

    def on_path_calculated(self, success):
        pass

    def on_movement_finished(self):
        self.mapBtn.setEnabled(True)

    def keyPressEvent(self, event):
        self.scene_manager.key_press_event(event)

    def keyReleaseEvent(self, event):
        self.scene_manager.key_release_event(event)