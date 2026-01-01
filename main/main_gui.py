import sys
import time
import csv
from datetime import datetime

from PySide6.QtCore import Qt, QObject, Signal, Slot, QThread
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QSpinBox, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QCheckBox
)

# Твои импорты
from qubits.qubit_func import *  # noqa


# --------- Worker для бенчмарка (чтобы UI не подвисал) ---------
class BenchmarkWorker(QObject):
    progress = Signal(int, int, float, bool)  # row_idx, qubits, seconds, check_ok
    log = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, simulator, shots: int, permissible: int, sizes: list[int], do_check: bool):
        super().__init__()
        self.simulator = simulator
        self.shots = shots
        self.permissible = permissible
        self.sizes = sizes
        self.do_check = do_check
        self._stop = False

    def stop(self):
        self._stop = True

    @Slot()
    def run(self):
        try:
            for idx, n in enumerate(self.sizes):
                if self._stop:
                    self.log.emit("Бенчмарк остановлен пользователем.")
                    break

                # 1) приватные
                private = generate_random_private_qbits(number_of_qbits_in_token=n)

                # 2) публичные + токен + spin/reverse (и при желании проверка)
                start = time.perf_counter()

                public = make_public_qbits_array(private_qbits_array=private)
                token = Token(1, public)

                make_spin_for_all_qbits_in_token(token, private)
                reverse_qbits_in_token(token, private)

                check_ok = True
                if self.do_check:
                    check_ok = bool(measure_token(self.simulator, token, self.shots, self.permissible))

                elapsed = time.perf_counter() - start
                qubits_count = len(token.array_of_public_qbits)

                self.progress.emit(idx, qubits_count, elapsed, check_ok)

            self.finished.emit()
        except Exception as e:
            self.error.emit(f"{type(e).__name__}: {e}")


# ---------------------------- GUI ----------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qubit Token")

        # Состояние приложения
        self.simulator = CPUQVM()
        self.privateQbitsArray = None
        self.publicQbitsArray = None
        self.token = None

        # Статистика (для CSV и таблицы)
        # элементы: dict(qubits=int, shots=int, permissible=int, seconds=float, check_ok=bool, ts=str)
        self.stats = []

        # Для бенчмарка (поток)
        self.bench_thread = None
        self.bench_worker = None

        # UI
        layout = QVBoxLayout(self)

        # ---- Параметры ----
        layout.addWidget(QLabel("Параметры:"))
        params = QHBoxLayout()

        self.qubits_spin = QSpinBox()
        self.qubits_spin.setRange(1, 256)
        self.qubits_spin.setValue(2)
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

        # ---- Лейбл времени/кубитов ----
        time_layout = QHBoxLayout()
        self.generation_time_label = QLabel("Токен: — кубитов | Время генерации: —")
        self.generation_time_label.setAlignment(Qt.AlignLeft)
        self.generation_time_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #1e88e5;
            }
        """)

        self.check_time_label = QLabel(
            "Время проверки токена: —"
        )
        self.check_time_label.setAlignment(Qt.AlignLeft)
        self.check_time_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2e7d32;
            }
        """)
        time_layout.addWidget(self.generation_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.check_time_label)
        layout.addLayout(time_layout)

        # ---- Кнопки (ручной режим) ----
        buttons = QHBoxLayout()
        self.btn_gen_private = QPushButton("Сгенерировать приватные кубиты")
        self.btn_gen_public = QPushButton("Сгенерировать публичный токен")
        self.btn_check = QPushButton("Проверить токен")
        self.btn_clear_log = QPushButton("Очистить лог")

        buttons.addWidget(self.btn_gen_private)
        buttons.addWidget(self.btn_gen_public)
        buttons.addWidget(self.btn_check)
        buttons.addWidget(self.btn_clear_log)
        layout.addLayout(buttons)

        # ---- Лог ----
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        # ---- Бенчмарк панель ----
        layout.addWidget(QLabel("Бенчмарк (автопрогон):"))
        bench_controls = QHBoxLayout()

        self.bench_start_spin = QSpinBox()
        self.bench_start_spin.setRange(1, 1024)
        self.bench_start_spin.setValue(2)
        bench_controls.addWidget(QLabel("Start N:"))
        bench_controls.addWidget(self.bench_start_spin)

        self.bench_steps_spin = QSpinBox()
        self.bench_steps_spin.setRange(1, 20)
        self.bench_steps_spin.setValue(5)
        bench_controls.addWidget(QLabel("Steps:"))
        bench_controls.addWidget(self.bench_steps_spin)

        self.bench_factor_spin = QSpinBox()
        self.bench_factor_spin.setRange(2, 10)
        self.bench_factor_spin.setValue(2)
        bench_controls.addWidget(QLabel("Factor:"))
        bench_controls.addWidget(self.bench_factor_spin)

        self.chk_bench_check = QCheckBox("Делать проверку (measure_token)")
        self.chk_bench_check.setChecked(True)
        bench_controls.addWidget(self.chk_bench_check)

        bench_controls.addStretch()

        self.btn_bench_run = QPushButton("Запустить бенчмарк")
        self.btn_bench_stop = QPushButton("Остановить")
        self.btn_bench_stop.setEnabled(False)

        self.btn_export_csv = QPushButton("Экспорт CSV")
        self.btn_clear_stats = QPushButton("Очистить таблицу")

        bench_controls.addWidget(self.btn_bench_run)
        bench_controls.addWidget(self.btn_bench_stop)
        bench_controls.addWidget(self.btn_export_csv)
        bench_controls.addWidget(self.btn_clear_stats)

        layout.addLayout(bench_controls)

        # ---- Таблица замеров ----
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Qubits", "Shots", "Permissible", "Seconds", "Check"
        ])
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # Сигналы (ручной режим)
        self.btn_gen_private.clicked.connect(self.generate_private)
        self.btn_gen_public.clicked.connect(self.generate_public_token)
        self.btn_check.clicked.connect(self.check_token)
        self.btn_clear_log.clicked.connect(self.clear_log)

        # Сигналы (бенчмарк)
        self.btn_bench_run.clicked.connect(self.run_benchmark)
        self.btn_bench_stop.clicked.connect(self.stop_benchmark)
        self.btn_export_csv.clicked.connect(self.export_csv)
        self.btn_clear_stats.clicked.connect(self.clear_stats)

        # Изначально нельзя генерировать public/check без private
        self.btn_gen_public.setEnabled(False)
        self.btn_check.setEnabled(False)

    # --------- helpers ---------
    def write(self, text: str):
        self.log.append(text)

    def clear_log(self):
        self.log.clear()

    def clear_stats(self):
        self.stats.clear()
        self.table.setRowCount(0)

    def _append_stat_row(self, ts: str, qubits: int, shots: int, permissible: int, seconds: float, check_ok: bool):
        self.stats.append({
            "ts": ts,
            "qubits": qubits,
            "shots": shots,
            "permissible": permissible,
            "seconds": seconds,
            "check_ok": check_ok,
        })

        was_sorting = self.table.isSortingEnabled()
        if was_sorting:
            self.table.setSortingEnabled(False)

        row = self.table.rowCount()
        self.table.insertRow(row)

        items = [
            QTableWidgetItem(ts),
            QTableWidgetItem(str(qubits)),
            QTableWidgetItem(str(shots)),
            QTableWidgetItem(str(permissible)),
            QTableWidgetItem(f"{seconds:.6f}"),
            QTableWidgetItem("OK" if check_ok else "FAIL"),
        ]

        # чтобы числовая сортировка работала
        items[1].setData(Qt.UserRole, qubits)
        items[2].setData(Qt.UserRole, shots)
        items[3].setData(Qt.UserRole, permissible)
        items[4].setData(Qt.UserRole, seconds)

        for c, it in enumerate(items):
            it.setFlags(it.flags() ^ Qt.ItemIsEditable)
            self.table.setItem(row, c, it)

        if was_sorting:
            self.table.setSortingEnabled(True)

    # --------- ручной режим ---------
    def generate_private(self):
        n = self.qubits_spin.value()
        shots = self.shots_spin.value()
        self.check_time_label.setText("Время проверки токена: —")
        self.generation_time_label.setText("Токен: — кубитов | Время генерации: —")

        self.write("=== Генерация приватных кубитов ===")
        self.privateQbitsArray = generate_random_private_qbits(number_of_qbits_in_token=n)

        self.write("Приватные кубиты:")
        for el in self.privateQbitsArray:
            self.write("*********************")
            self.write(f"  Кубит № {el.id}")
            self.write(f"  Тета: {el.theta}")
            self.write(f"  Фи: {el.phi}")
            self.write(f"  Id дочернего публичного кубита: {el.public_qbit.id}")

            # Если у тебя функция называется measureQbit — это перехватит NameError
            try:
                m = measure_qbit(self.simulator, el, number_of_measures_of_single_qbit=shots)
            except NameError:
                m = measureQbit(self.simulator, el, shots)

            self.write(str(m))
            self.write("*********************")

        self.write("")
        self.btn_gen_public.setEnabled(True)
        self.btn_check.setEnabled(False)
        self.publicQbitsArray = None
        self.token = None

    def generate_public_token(self):
        if not self.privateQbitsArray:
            self.write("Сначала сгенерируй приватные кубиты.")
            return

        shots = self.shots_spin.value()

        self.write("=== Генерация публичных кубитов + токена ===")

        start_time = time.perf_counter()

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

        self.token = Token(1, self.publicQbitsArray)

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

        elapsed = time.perf_counter() - start_time
        qubits_count = len(self.token.array_of_public_qbits)
        self.generation_time_label.setText(
            f"⏱ Токен: {qubits_count} кубитов | Время генерации: {elapsed:.6f} сек"
        )

        self.write("")
        self.btn_check.setEnabled(True)

        # Запишем в таблицу замеров (ручной режим — тоже статистика)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        permissible = self.permissible_spin.value()
        self._append_stat_row(ts, qubits_count, shots, permissible, elapsed, True)

    def check_token(self):
        if not self.token:
            self.write("Сначала создай публичный токен.")
            return

        shots = self.shots_spin.value()
        permissible = self.permissible_spin.value()

        self.write("=== Проверка токена ===")

        start = time.perf_counter()
        result = measure_token(self.simulator, self.token, shots, permissible)
        elapsed = time.perf_counter() - start

        self.write("Результат проверки: " + str(result))

        self.check_time_label.setText(
            f"🔍 Время проверки токена: {elapsed:.6f} сек"
        )

        # запишем проверку в таблицу
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        qubits = len(self.token.array_of_public_qbits)

        self._append_stat_row(
            ts=ts,
            qubits=qubits,
            shots=shots,
            permissible=permissible,
            seconds=elapsed,
            check_ok=bool(result),
        )

    # --------- бенчмарк ---------
    def _set_benchmark_ui_running(self, running: bool):
        self.btn_bench_run.setEnabled(not running)
        self.btn_bench_stop.setEnabled(running)

        # чтобы не мешать состояниям — можно блокировать и ручные кнопки
        self.btn_gen_private.setEnabled(not running)
        self.btn_gen_public.setEnabled(not running and bool(self.privateQbitsArray))
        self.btn_check.setEnabled(not running and bool(self.token))



    def run_benchmark(self):
        start_n = self.bench_start_spin.value()
        steps = self.bench_steps_spin.value()
        factor = self.bench_factor_spin.value()

        # генерим список N: start, start*factor, ...
        sizes = []
        cur = start_n
        for _ in range(steps):
            sizes.append(cur)
            cur *= factor

        shots = self.shots_spin.value()
        permissible = self.permissible_spin.value()
        do_check = self.chk_bench_check.isChecked()

        self.write(f"=== Бенчмарк старт: sizes={sizes}, shots={shots}, permissible={permissible}, check={do_check} ===")

        # под бенчмарк подготовим строки в таблице (по одной на size)
        # (добавлять будем по мере готовности)
        self._set_benchmark_ui_running(True)

        # поток
        self.bench_thread = QThread(self)
        self.bench_worker = BenchmarkWorker(
            simulator=self.simulator,
            shots=shots,
            permissible=permissible,
            sizes=sizes,
            do_check=do_check
        )
        self.bench_worker.moveToThread(self.bench_thread)

        # сигналы
        self.bench_thread.started.connect(self.bench_worker.run)
        self.bench_worker.log.connect(self.write)
        self.bench_worker.progress.connect(self._on_bench_progress)
        self.bench_worker.finished.connect(self._on_bench_finished)
        self.bench_worker.error.connect(self._on_bench_error)

        # корректная очистка
        self.bench_worker.finished.connect(self.bench_thread.quit)
        self.bench_worker.finished.connect(self.bench_worker.deleteLater)
        self.bench_thread.finished.connect(self.bench_thread.deleteLater)

        self.bench_thread.start()

    def stop_benchmark(self):
        if self.bench_worker:
            self.bench_worker.stop()

    @Slot(int, int, float, bool)
    def _on_bench_progress(self, idx: int, qubits: int, seconds: float, check_ok: bool):
        shots = self.shots_spin.value()
        permissible = self.permissible_spin.value()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self._append_stat_row(ts, qubits, shots, permissible, seconds, check_ok)

        # обновим “главный” лейбл, чтобы было видно последний прогон
        self.generation_time_label.setText(
            f"⏱ Токен: {qubits} кубитов | Время генерации: {seconds:.6f} сек"
        )

    @Slot()
    def _on_bench_finished(self):
        self.write("=== Бенчмарк завершён ===")
        self._set_benchmark_ui_running(False)
        self.bench_thread = None
        self.bench_worker = None

    @Slot(str)
    def _on_bench_error(self, msg: str):
        self.write(f"Ошибка бенчмарка: {msg}")
        QMessageBox.critical(self, "Ошибка бенчмарка", msg)
        self._set_benchmark_ui_running(False)
        self.bench_thread = None
        self.bench_worker = None

    # --------- экспорт CSV ---------
    def export_csv(self):
        if not self.stats:
            QMessageBox.information(self, "Экспорт CSV", "Нет данных для экспорта (таблица пуста).")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить CSV",
            "benchmark_results.csv",
            "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Timestamp", "Qubits", "Shots", "Permissible", "Seconds", "Check"])
                for row in self.stats:
                    writer.writerow([
                        row["ts"],
                        row["qubits"],
                        row["shots"],
                        row["permissible"],
                        f"{row['seconds']:.6f}",
                        "OK" if row["check_ok"] else "FAIL",
                    ])
            QMessageBox.information(self, "Экспорт CSV", "Файл успешно сохранён.")
        except Exception as e:
            QMessageBox.critical(self, "Экспорт CSV", f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1100, 800)
    w.show()
    sys.exit(app.exec())
