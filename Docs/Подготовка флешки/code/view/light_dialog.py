from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, QDialogButtonBox, QLabel, QGroupBox
from PyQt5.QtCore import Qt


class LightDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить источник света")
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        info_group = QGroupBox("Параметры")
        info_layout = QVBoxLayout()
        info_label = QLabel(
            "Добавление дополнительного бесконечно удаленного источника света.\n\n"
            "• Вектор (X, Y, Z) задает направление, ОТКУДА падает свет."
        )
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        form_layout = QFormLayout()

        self.spin_dir_x = self.create_double_spin(-100, 100, 15.0, 0.5)
        self.spin_dir_y = self.create_double_spin(-100, 100, 25.0, 0.5)
        self.spin_dir_z = self.create_double_spin(-100, 100, 10.0, 0.5)

        form_layout.addRow(QLabel("<b>Направление:</b>"))
        form_layout.addRow("X:", self.spin_dir_x)
        form_layout.addRow("Y:", self.spin_dir_y)
        form_layout.addRow("Z:", self.spin_dir_z)

        hint_dir = QLabel("<i>(Y > 0 — свет сверху)</i>")
        hint_dir.setStyleSheet("color: gray; font-size: 10pt;")
        form_layout.addRow(hint_dir)

        self.spin_intensity = self.create_double_spin(0.0, 1.0, 0.5, 0.1)
        form_layout.addRow(QLabel("<b>Интенсивность:</b>"), self.spin_intensity)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def create_double_spin(self, min_val, max_val, def_val, step):
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(def_val)
        spin.setSingleStep(step)
        return spin

    def get_data(self):
        return {
            'dir': [self.spin_dir_x.value(), self.spin_dir_y.value(), self.spin_dir_z.value()],
            'color': [255, 255, 255],
            'intensity': self.spin_intensity.value()
        }