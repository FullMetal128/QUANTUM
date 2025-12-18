import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QSpinBox
)

# Твои импорты
from qubits.qubit_func import *  # noqa


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qubit Token GUI (PySide6)")

        # Состояние приложения
        self.simulator = CPUQVM()
        self.privateQbitsArray = None
        self.publicQbitsArray = None
        self.token = None

        # UI
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Параметры:"))
        params = QHBoxLayout()

        self.qubits_spin = QSpinBox()
        self.qubits_spin.setRange(1, 100)
        self.qubits_spin.setValue(1)
        params.addWidget(QLabel("Qubits:"))
        params.addWidget(self.qubits_spin)

        self.shots_spin = QSpinBox()
        self.shots_spin.setRange(1, 1_000_000)
        self.shots_spin.setValue(10_000)
        params.addWidget(QLabel("Shots:"))
        params.addWidget(self.shots_spin)

        self.permissible_spin = QSpinBox()
        self.permissible_spin.setRange(0, 1_000_000)
        self.permissible_spin.setValue(50)
        params.addWidget(QLabel("Permissible ones:"))
        params.addWidget(self.permissible_spin)

        params.addStretch()
        layout.addLayout(params)

        buttons = QHBoxLayout()
        self.btn_gen_private = QPushButton("1) Сгенерировать приватные кубиты")
        self.btn_gen_public = QPushButton("2) Сгенерировать публичный токен")
        self.btn_clear_log = QPushButton("Очистить лог")
        self.btn_check = QPushButton("3) Проверить токен")

        buttons.addWidget(self.btn_gen_private)
        buttons.addWidget(self.btn_gen_public)
        buttons.addWidget(self.btn_clear_log)
        buttons.addWidget(self.btn_check)
        layout.addLayout(buttons)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        # Сигналы
        self.btn_gen_private.clicked.connect(self.generate_private)
        self.btn_gen_public.clicked.connect(self.generate_public_token)
        self.btn_clear_log.clicked.connect(self.clear_log)
        self.btn_check.clicked.connect(self.check_token)

        # Изначально нельзя генерировать public/check без private
        self.btn_gen_public.setEnabled(False)
        self.btn_check.setEnabled(False)

    def write(self, text: str):
        self.log.append(text)

    def clear_log(self):
        self.log.clear()

    def generate_private(self):
        n = self.qubits_spin.value()
        shots = self.shots_spin.value()

        self.write("=== Генерация приватных кубитов ===")
        self.privateQbitsArray = generate_random_private_qbits(number_of_qbits_in_token=n)

        self.write("Приватные кубиты:")
        for el in self.privateQbitsArray:
            self.write("*********************")
            self.write(f"Кубит № {el.id}")
            self.write(f"  Тета: {el.theta}")
            self.write(f"  Фи: {el.phi}")
            self.write(f"  Id дочернего публичного кубита: {el.public_qbit.id}")

            # ВАЖНО: если у тебя функция называется measureQbit, поменяй тут
            try:
                m = measure_qbit(self.simulator, el, number_of_measures_of_single_qbit=shots)
            except NameError:
                m = measureQbit(self.simulator, el, shots)

            self.write(str(m))
            self.write("*********************")

        self.write("")
        self.btn_gen_public.setEnabled(True)
        self.btn_check.setEnabled(False)  # токен ещё не создан
        self.publicQbitsArray = None
        self.token = None

    def generate_public_token(self):
        if not self.privateQbitsArray:
            self.write("Сначала сгенерируй приватные кубиты.")
            return

        shots = self.shots_spin.value()

        self.write("=== Генерация публичных кубитов + токена ===")
        self.publicQbitsArray = make_public_qbits_array(private_qbits_array=self.privateQbitsArray)

        self.write("Публичные кубиты:")
        for el in self.publicQbitsArray:
            self.write("___________")
            self.write(f"Кубит № {el.id}")
            try:
                m = measureQbit(self.simulator, el, shots)
            except NameError:
                m = measure_qbit(self.simulator, el, number_of_measures_of_single_qbit=shots)
            self.write(str(m))
            self.write("___________")

        # Токен на основе публичных
        self.token = Token(1, self.publicQbitsArray)

        # Spin
        make_spin_for_all_qbits_in_token(self.token, self.privateQbitsArray)
        self.write("")
        self.write("Публичные кубиты внутри токена после спина:")
        for el in self.token.array_of_public_qbits:
            self.write("___________")
            self.write(f"Кубит № {el.id}")
            try:
                m = measureQbit(self.simulator, el, shots)
            except NameError:
                m = measure_qbit(self.simulator, el, number_of_measures_of_single_qbit=shots)
            self.write(str(m))
            self.write("___________")

        # Reverse spin
        reverse_qbits_in_token(self.token, self.privateQbitsArray)
        self.write("")
        self.write("Публичные кубиты внутри токена после обратного спина:")
        for el in self.token.array_of_public_qbits:
            self.write("___________")
            self.write(f"Кубит № {el.id}")
            try:
                m = measureQbit(self.simulator, el, shots)
            except NameError:
                m = measure_qbit(self.simulator, el, number_of_measures_of_single_qbit=shots)
            self.write(str(m))
            self.write("___________")

        self.write("")
        self.btn_check.setEnabled(True)

    def check_token(self):
        if not self.token:
            self.write("Сначала создай публичный токен.")
            return

        shots = self.shots_spin.value()
        permissible = self.permissible_spin.value()

        self.write("=== Проверка токена ===")
        result = measure_token(self.simulator, self.token, shots, permissible)
        self.write("Результат проверки: " + str(result))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(950, 650)
    w.show()
    sys.exit(app.exec())
