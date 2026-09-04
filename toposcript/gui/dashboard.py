import os
import sys
import time
import queue
import threading

import matplotlib.pyplot as plt


PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROJECT_ROOT
    )

from PySide6.QtCore import (
    QObject,
    QThread,
    Signal,
    Slot,
    Qt,
)

from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from toposcript.instruments.keithley_2450 import Keithley2450
from toposcript.instruments.omh import OMM6810B
from toposcript.instruments.cage_rotator import K10CR2CageRotator
from toposcript.experiments.light_iv import run_light_iv


# ============================================================
# SETTINGS
# ============================================================

KEITHLEY_RESOURCE = (
    "TCPIP0::169.254.184.154::5025::SOCKET"
)

OMH_RESOURCE = "GPIB0::2::INSTR"

ROTATOR_SERIAL = "55538844"

KEITHLEY_POLL_S = 0.25
OMH_POLL_S = 1.0
ROTATOR_POLL_S = 0.25


# ============================================================
# LIGHT IV SETTINGS
# ============================================================

LIGHT_IV_SETTINGS = {

    "path": "data/light_iv",

    "scan_type": "LightIV",

    "sample_source": "SUNLAB",

    "sample_name": "C5776-X20Y10",

    "user": "Aya",

    "notes": "",

    "lens_position": "",

    "filter_name": "None",

    "wavelength_list_nm": [
        1502,
        1507
      
    ],

    "start": -0.1,

    "stop": 1.3,

    "step": 0.2,

    "current_limit": 0.02,

    "nplc": 0.1,

    "varied_step": True,

    "mid": 0.5,

    "step2": 0.2,
}


# ============================================================
# KEITHLEY WORKER
# ============================================================

class KeithleyWorker(QObject):

    measurement = Signal(
        float,
        float,
        float,
    )

    connected = Signal(str)
    error = Signal(str)
    finished = Signal()

    iv_started = Signal()
    iv_waiting = Signal(str)
    iv_plot_ready = Signal(object)

    iv_finished = Signal(
        bool,
        str,
    )

    def __init__(self):

        super().__init__()

        self.running = True
        self.smu = None

        self.iv_queue = queue.Queue()

        self.iv_continue_event = (
            threading.Event()
        )

        self.iv_running = False


    # ========================================================
    # REQUEST LIGHT IV
    # ========================================================

    def request_light_iv(self):

        if self.iv_running:
            return

        if not self.iv_queue.empty():
            return

        self.iv_queue.put(
            LIGHT_IV_SETTINGS.copy()
        )


    # ========================================================
    # CONTINUE LIGHT IV
    # ========================================================

    def continue_light_iv(self):

        self.iv_continue_event.set()


    # ========================================================
    # LIGHT IV MEASUREMENT CALLBACK
    # ========================================================

    def light_iv_measurement(
        self,
        voltage,
        current,
    ):

        voltage = float(
            voltage
        )

        current = float(
            current
        )

        power = (
            voltage
            * current
        )

        self.measurement.emit(
            voltage,
            current,
            power,
        )


    # ========================================================
    # LIGHT IV WAIT CALLBACK
    # ========================================================

    def light_iv_wait(
        self,
        message
    ):

        self.iv_continue_event.clear()

        self.iv_waiting.emit(
            message
        )

        while self.running:

            if self.iv_continue_event.wait(
                timeout=0.1
            ):

                return

        raise RuntimeError(
            "Light IV stopped because "
            "the dashboard is closing."
        )


    # ========================================================
    # EXECUTE LIGHT IV
    # ========================================================

    def execute_light_iv(
        self,
        settings
    ):

        self.iv_running = True

        self.iv_started.emit()

        print("")
        print("==============================")
        print("STARTING LIGHT IV")
        print("==============================")

        try:

            iv_data = run_light_iv(

                smu=self.smu,

                path=settings[
                    "path"
                ],

                scan_type=settings[
                    "scan_type"
                ],

                sample_source=settings[
                    "sample_source"
                ],

                sample_name=settings[
                    "sample_name"
                ],

                user=settings[
                    "user"
                ],

                notes=settings[
                    "notes"
                ],

                wavelength_list_nm=settings[
                    "wavelength_list_nm"
                ],

                lens_position=settings[
                    "lens_position"
                ],

                filter_name=settings[
                    "filter_name"
                ],

                start=settings[
                    "start"
                ],

                stop=settings[
                    "stop"
                ],

                step=settings[
                    "step"
                ],

                current_limit=settings[
                    "current_limit"
                ],

                nplc=settings[
                    "nplc"
                ],

                varied_step=settings[
                    "varied_step"
                ],

                mid=settings[
                    "mid"
                ],

                step2=settings[
                    "step2"
                ],

                measurement_callback=(
                    self.light_iv_measurement
                ),

                wait_callback=(
                    self.light_iv_wait
                ),

                show_plots=False,
            )

            self.iv_plot_ready.emit(
                iv_data
            )

            print("")
            print("==============================")
            print("LIGHT IV COMPLETE")
            print("==============================")

            self.iv_finished.emit(
                True,
                "Light IV complete."
            )

        except Exception as error:

            print(
                "Light IV error:",
                error
            )

            self.iv_finished.emit(
                False,
                str(error)
            )

        finally:

            # ------------------------------------------------
            # RETURN TO NORMAL LIVE MODE
            # ------------------------------------------------

            try:

                self.smu.configure_light_iv(
                    source_voltage=0.0,
                    current_limit=0.02,
                    nplc=1,
                )

                self.smu.set_voltage(
                    0.0
                )

                time.sleep(
                    0.2
                )

                self.smu.output_on()

                print(
                    "Keithley returned to "
                    "live monitoring at 0 V."
                )

            except Exception as error:

                print(
                    "Could not restore "
                    "Keithley monitoring:",
                    error
                )

            self.iv_running = False


    # ========================================================
    # MAIN WORKER LOOP
    # ========================================================

    @Slot()
    def run(self):

        try:

            print(
                "Connecting to Keithley..."
            )

            self.smu = Keithley2450(
                resource=KEITHLEY_RESOURCE
            ).connect()

            identity = (
                self.smu.identify()
            )

            print(
                "Keithley:"
            )

            print(
                identity
            )

            self.connected.emit(
                identity
            )

            # ------------------------------------------------
            # NORMAL LIVE MONITORING
            # ------------------------------------------------

            self.smu.configure_light_iv(
                source_voltage=0.0,
                current_limit=0.02,
                nplc=1,
            )

            self.smu.set_voltage(
                0.0
            )

            time.sleep(
                0.2
            )

            self.smu.output_on()

            print(
                "Keithley output ON at 0 V."
            )

            while self.running:

                # --------------------------------------------
                # CHECK FOR LIGHT IV REQUEST
                # --------------------------------------------

                try:

                    settings = (
                        self.iv_queue.get_nowait()
                    )

                    self.execute_light_iv(
                        settings
                    )

                    continue

                except queue.Empty:

                    pass

                # --------------------------------------------
                # NORMAL LIVE READ
                # --------------------------------------------

                try:

                    voltage, current = (
                        self.smu.read_voltage_current()
                    )

                    voltage = float(
                        voltage
                    )

                    current = float(
                        current
                    )

                    power = (
                        voltage
                        * current
                    )

                    self.measurement.emit(
                        voltage,
                        current,
                        power,
                    )

                except Exception as error:

                    print(
                        "Keithley read error:",
                        error
                    )

                    self.error.emit(
                        str(error)
                    )

                time.sleep(
                    KEITHLEY_POLL_S
                )

        except Exception as error:

            print(
                "Keithley connection error:",
                error
            )

            self.error.emit(
                str(error)
            )

        finally:

            if self.smu is not None:

                try:
                    self.smu.set_voltage(
                        0.0
                    )
                except Exception:
                    pass

                try:
                    self.smu.output_off()
                except Exception:
                    pass

                try:
                    if self.smu.inst is not None:
                        self.smu.inst.close()
                except Exception:
                    pass

                try:
                    if self.smu.rm is not None:
                        self.smu.rm.close()
                except Exception:
                    pass

            self.finished.emit()


    def stop(self):

        self.running = False

        self.iv_continue_event.set()


# ============================================================
# OMH WORKER
# ============================================================

class OMHWorker(QObject):

    measurement = Signal(
        float,
        float,
    )

    connected = Signal(str)
    error = Signal(str)
    finished = Signal()

    def __init__(self):

        super().__init__()

        self.running = True
        self.omm = None

    @Slot()
    def run(self):

        try:

            print(
                "Connecting to OMH..."
            )

            self.omm = OMM6810B(
                resource_name=OMH_RESOURCE,
                timeout_ms=10000,
            ).connect()

            instrument_id = (
                self.omm.identify_instrument()
            )

            head_id = (
                self.omm.identify_head()
            )

            print(
                "OMH:"
            )

            print(
                instrument_id
            )

            print(
                head_id
            )

            self.connected.emit(
                f"{instrument_id} | {head_id}"
            )

            while self.running:

                try:

                    measurement = (
                        self.omm.read_measurement()
                    )

                    power_w = measurement[
                        "power_w"
                    ]

                    wavelength_nm = measurement[
                        "wavelength_nm"
                    ]

                    self.measurement.emit(
                        float(
                            power_w
                        ),
                        float(
                            wavelength_nm
                        ),
                    )

                except Exception as error:

                    print(
                        "OMH read error:",
                        error
                    )

                    self.error.emit(
                        str(error)
                    )

                time.sleep(
                    OMH_POLL_S
                )

        except Exception as error:

            print(
                "OMH connection error:",
                error
            )

            self.error.emit(
                str(error)
            )

        finally:

            if self.omm is not None:

                try:
                    self.omm.close()
                except Exception:
                    pass

            self.finished.emit()


    def stop(self):

        self.running = False


# ============================================================
# ROTATOR WORKER
# ============================================================

class RotatorWorker(QObject):

    angle = Signal(float)
    connected = Signal(str)
    error = Signal(str)
    finished = Signal()

    def __init__(self):

        super().__init__()

        self.running = True
        self.rotator = None

        self.move_queue = (
            queue.Queue()
        )

    def request_move(
        self,
        target_angle
    ):

        self.move_queue.put(
            float(
                target_angle
            )
        )

    @Slot()
    def run(self):

        try:

            print(
                "Connecting to cage rotator..."
            )

            self.rotator = (
                K10CR2CageRotator(
                    serial_number=ROTATOR_SERIAL
                )
            )

            self.rotator.connect()

            print(
                "Cage rotator connected."
            )

            self.connected.emit(
                f"K10CR2 | "
                f"SN {ROTATOR_SERIAL}"
            )

            while self.running:

                try:

                    # ----------------------------------------
                    # MOVEMENT REQUEST
                    # ----------------------------------------

                    try:

                        target = (
                            self.move_queue.get_nowait()
                        )

                        print(
                            f"Moving rotator to "
                            f"{target:.2f}°"
                        )

                        self.rotator.move_to(
                            target
                        )

                    except queue.Empty:

                        pass

                    # ----------------------------------------
                    # READ ANGLE
                    # ----------------------------------------

                    current_angle = (
                        self.rotator.get_angle()
                    )

                    self.angle.emit(
                        float(
                            current_angle
                        )
                    )

                except Exception as error:

                    print(
                        "Rotator error:",
                        error
                    )

                    self.error.emit(
                        str(error)
                    )

                time.sleep(
                    ROTATOR_POLL_S
                )

        except Exception as error:

            print(
                "Rotator connection error:",
                error
            )

            self.error.emit(
                str(error)
            )

        finally:

            if self.rotator is not None:

                try:
                    self.rotator.close()
                except Exception:
                    pass

            self.finished.emit()


    def stop(self):

        self.running = False


# ============================================================
# DASHBOARD
# ============================================================

class Dashboard(QMainWindow):

    def __init__(self):

        super().__init__()

        self.current_angle = None

        self.setWindowTitle(
            "TOPO Live Monitor"
        )

        self.resize(
            900,
            720
        )

        self.build_ui()

        self.start_keithley()
        self.start_omh()
        self.start_rotator()


    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(self):

        # ====================================================
        # SCROLL AREA
        # ====================================================

        scroll_area = QScrollArea()

        scroll_area.setWidgetResizable(
            True
        )

        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: #f1f1f1;
            }
            """
        )

        self.setCentralWidget(
            scroll_area
        )

        central = QWidget()

        central.setStyleSheet(
            """
            QWidget {
                background-color: #f1f1f1;
                color: #111111;
                font-family: Segoe UI;
                font-size: 12px;
            }

            QPushButton {
                background-color: #e8e8e8;
                color: #111111;
                border: 1px solid #a9a9a9;
                border-radius: 2px;
                font-size: 12px;
                font-weight: normal;
                padding: 4px 8px;
            }

            QPushButton:hover {
                background-color: #f5f5f5;
                border: 1px solid #7f7f7f;
            }

            QPushButton:pressed {
                background-color: #d8d8d8;
            }

            QPushButton:disabled {
                color: #888888;
                background-color: #e5e5e5;
                border: 1px solid #c8c8c8;
            }

            QDoubleSpinBox {
                background-color: white;
                color: #111111;
                border: 1px solid #8f8f8f;
                border-radius: 1px;
                padding: 3px 6px;
                font-size: 12px;
                font-weight: normal;
            }
            """
        )

        scroll_area.setWidget(
            central
        )

        main_layout = QVBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            10,
            10,
            10,
            10
        )

        main_layout.setSpacing(
            8
        )


        # ====================================================
        # KEITHLEY CARD
        # ====================================================

        keithley_card = (
            self.make_card()
        )


        layout = QVBoxLayout(
            keithley_card
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8
        )

        layout.setSpacing(
            6
        )

        header = QHBoxLayout()

        self.keithley_title = self.make_title(
            "Keithley"
        )

        header.addWidget(
            self.keithley_title
        )

        header.addStretch()

        self.keithley_status = (
            self.make_status()
        )

        header.addWidget(
            self.keithley_status
        )

        layout.addLayout(
            header
        )

        row = QHBoxLayout()

        self.voltage = (
            self.make_display(
                "Voltage",
                "V"
            )
        )

        self.current = (
            self.make_display(
                "Current",
                "A"
            )
        )

        self.electrical_power = (
            self.make_display(
                "Electrical Power",
                "W"
            )
        )

        row.addWidget(
            self.voltage[
                "widget"
            ]
        )

        row.addStretch()

        row.addWidget(
            self.current[
                "widget"
            ]
        )

        row.addStretch()

        row.addWidget(
            self.electrical_power[
                "widget"
            ]
        )

        layout.addLayout(
            row
        )

        main_layout.addWidget(
            keithley_card
        )


        # ====================================================
        # LIGHT IV CARD
        # ====================================================

        light_iv_card = (
            self.make_card()
        )

        light_iv_layout = QVBoxLayout(
            light_iv_card
        )

        light_iv_layout.setContentsMargins(
            10,
            8,
            10,
            8
        )

        light_iv_layout.setSpacing(
            6
        )

        light_iv_layout.addWidget(
            self.make_title(
                "Light IV"
            )
        )

        iv_controls = QHBoxLayout()

        self.run_iv_button = QPushButton(
            "RUN LIGHT IV"
        )

        self.continue_iv_button = QPushButton(
            "CONTINUE"
        )

        self.run_iv_button.setMinimumHeight(
            32
        )

        self.continue_iv_button.setMinimumHeight(
            32
        )

        self.continue_iv_button.setEnabled(
            False
        )

        iv_controls.addWidget(
            self.run_iv_button
        )

        iv_controls.addWidget(
            self.continue_iv_button
        )

        light_iv_layout.addLayout(
            iv_controls
        )

        self.iv_status = QLabel(
            "Light IV idle"
        )

        self.iv_status.setStyleSheet(
            """
            color: #444444;
            font-size: 11px;
            """
        )

        light_iv_layout.addWidget(
            self.iv_status
        )

        self.run_iv_button.clicked.connect(
            self.start_light_iv
        )

        self.continue_iv_button.clicked.connect(
            self.continue_light_iv
        )

        main_layout.addWidget(
            light_iv_card
        )


        # ====================================================
        # OMH CARD
        # ====================================================

        omh_card = (
            self.make_card()
        )

        layout = QVBoxLayout(
            omh_card
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8
        )

        layout.setSpacing(
            6
        )

        header = QHBoxLayout()

        self.omh_title = self.make_title(
            "Optical Meter"
        )

        header.addWidget(
            self.omh_title
        )

        header.addStretch()

        self.omh_status = (
            self.make_status()
        )

        header.addWidget(
            self.omh_status
        )

        layout.addLayout(
            header
        )

        row = QHBoxLayout()

        self.wavelength = (
            self.make_display(
                "Wavelength",
                "nm"
            )
        )

        self.optical_power = (
            self.make_display(
                "Optical Power",
                "mW"
            )
        )

        row.addWidget(
            self.wavelength[
                "widget"
            ]
        )

        row.addStretch()

        row.addWidget(
            self.optical_power[
                "widget"
            ]
        )

        layout.addLayout(
            row
        )

        main_layout.addWidget(
            omh_card
        )


        # ====================================================
        # ROTATOR CARD
        # ====================================================

        rotator_card = (
            self.make_card()
        )

        layout = QVBoxLayout(
            rotator_card
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8
        )

        layout.setSpacing(
            6
        )

        header = QHBoxLayout()

        self.rotator_title = self.make_title(
            "Cage Rotator"
        )

        header.addWidget(
            self.rotator_title
        )

        header.addStretch()

        self.rotator_status = (
            self.make_status()
        )

        header.addWidget(
            self.rotator_status
        )

        layout.addLayout(
            header
        )

        self.angle = (
            self.make_display(
                "Rotation Angle",
                "°"
            )
        )

        layout.addWidget(
            self.angle[
                "widget"
            ]
        )


        # ====================================================
        # ROTATOR CONTROLS
        # ====================================================

        controls = QHBoxLayout()

        self.left_button = QPushButton(
            "◀"
        )

        self.right_button = QPushButton(
            "▶"
        )

        self.left_button.setMinimumHeight(
            32
        )

        self.right_button.setMinimumHeight(
            32
        )

        self.left_button.setMinimumWidth(
            75
        )

        self.right_button.setMinimumWidth(
            75
        )

        self.left_button.setEnabled(
            False
        )

        self.right_button.setEnabled(
            False
        )

        step_label = QLabel(
            "Step:"
        )

        step_label.setStyleSheet(
            """
            color: #333333;
            font-size: 11px;
            font-weight: normal;
            """
        )

        self.step_input = (
            QDoubleSpinBox()
        )

        self.step_input.setMinimum(
            0.01
        )

        self.step_input.setMaximum(
            360.0
        )

        self.step_input.setDecimals(
            2
        )

        self.step_input.setValue(
            1.0
        )

        self.step_input.setSingleStep(
            0.1
        )

        self.step_input.setSuffix(
            " °"
        )

        self.step_input.setMinimumWidth(
            105
        )

        self.step_input.setMinimumHeight(
            30
        )

        controls.addWidget(
            self.left_button
        )

        controls.addStretch()

        controls.addWidget(
            step_label
        )

        controls.addWidget(
            self.step_input
        )

        controls.addStretch()

        controls.addWidget(
            self.right_button
        )

        layout.addLayout(
            controls
        )

        self.left_button.clicked.connect(
            self.rotate_left
        )

        self.right_button.clicked.connect(
            self.rotate_right
        )

        main_layout.addWidget(
            rotator_card
        )

        main_layout.addStretch()


    # ========================================================
    # UI HELPERS
    # ========================================================

    def make_card(self):

        card = QFrame()

        card.setStyleSheet(
            """
            QFrame {
                background-color: #fafafa;
                border: 1px solid #b7b7b7;
                border-radius: 2px;
            }
            """
        )

        return card


    def make_title(
        self,
        text
    ):

        label = QLabel(
            text
        )

        label.setStyleSheet(
            """
            font-size: 13px;
            font-weight: 600;
            """
        )

        return label


    def make_status(self):

        label = QLabel(
            "● CONNECTING"
        )

        label.setStyleSheet(
            """
            background-color: #dcdcdc;
            color: #222222;
            border: 1px solid #a7a7a7;
            padding: 3px 7px;
            border-radius: 2px;
            font-size: 10px;
            font-weight: 600;
            """
        )

        return label


    def make_display(
        self,
        name,
        unit
    ):

        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )

        name_label = QLabel(
            name
        )

        name_label.setStyleSheet(
            """
            color: #444444;
            font-size: 11px;
            """
        )

        value_label = QLabel(
            "---"
        )

        value_label.setStyleSheet(
            """
            font-size: 22px;
            font-weight: 500;
            background-color: white;
            border: 1px solid #9a9a9a;
            padding: 4px 8px;
            """
        )

        unit_label = QLabel(
            unit
        )

        unit_label.setStyleSheet(
            """
            color: #555555;
            font-size: 10px;
            """
        )

        layout.addWidget(
            name_label
        )

        layout.addWidget(
            value_label
        )

        layout.addWidget(
            unit_label
        )

        return {
            "widget": widget,
            "value": value_label,
        }


    def set_connected(
        self,
        label,
        identity
    ):

        label.setText(
            "● CONNECTED"
        )

        label.setStyleSheet(
            """
            background-color: #dff0d8;
            color: #1f5f2c;
            border: 1px solid #7aaa83;
            padding: 3px 7px;
            border-radius: 2px;
            font-size: 10px;
            font-weight: 600;
            """
        )

        label.setToolTip(
            identity
        )


    def set_error(
        self,
        label,
        error
    ):

        label.setText(
            "● ERROR"
        )

        label.setStyleSheet(
            """
            background-color: #a35d10;
            color: white;
            padding: 8px 14px;
            border-radius: 7px;
            font-weight: bold;
            """
        )

        label.setToolTip(
            error
        )


    # ========================================================
    # START THREADS
    # ========================================================

    def start_keithley(self):

        self.keithley_thread = (
            QThread(self)
        )

        self.keithley_worker = (
            KeithleyWorker()
        )

        self.keithley_worker.moveToThread(
            self.keithley_thread
        )

        self.keithley_thread.started.connect(
            self.keithley_worker.run
        )

        self.keithley_worker.connected.connect(
            self.on_keithley_connected
        )

        self.keithley_worker.measurement.connect(
            self.update_keithley
        )

        self.keithley_worker.error.connect(
            self.on_keithley_error
        )

        self.keithley_worker.iv_started.connect(
            self.on_iv_started
        )

        self.keithley_worker.iv_waiting.connect(
            self.on_iv_waiting
        )

        self.keithley_worker.iv_plot_ready.connect(
            self.show_light_iv_plot
        )

        self.keithley_worker.iv_finished.connect(
            self.on_iv_finished
        )

        self.keithley_worker.finished.connect(
            self.keithley_thread.quit
        )

        self.keithley_thread.start()


    def start_omh(self):

        self.omh_thread = (
            QThread(self)
        )

        self.omh_worker = (
            OMHWorker()
        )

        self.omh_worker.moveToThread(
            self.omh_thread
        )

        self.omh_thread.started.connect(
            self.omh_worker.run
        )

        self.omh_worker.connected.connect(
            self.on_omh_connected
        )

        self.omh_worker.measurement.connect(
            self.update_omh
        )

        self.omh_worker.error.connect(
            self.on_omh_error
        )

        self.omh_worker.finished.connect(
            self.omh_thread.quit
        )

        self.omh_thread.start()


    def start_rotator(self):

        self.rotator_thread = (
            QThread(self)
        )

        self.rotator_worker = (
            RotatorWorker()
        )

        self.rotator_worker.moveToThread(
            self.rotator_thread
        )

        self.rotator_thread.started.connect(
            self.rotator_worker.run
        )

        self.rotator_worker.connected.connect(
            self.on_rotator_connected
        )

        self.rotator_worker.angle.connect(
            self.update_angle
        )

        self.rotator_worker.error.connect(
            self.on_rotator_error
        )

        self.rotator_worker.finished.connect(
            self.rotator_thread.quit
        )

        self.rotator_thread.start()


    # ========================================================
    # KEITHLEY
    # ========================================================

    @Slot(str)
    def on_keithley_connected(
        self,
        identity
    ):

        self.set_connected(
            self.keithley_status,
            identity
        )

        self.keithley_title.setText(
            identity
        )


    @Slot(
        float,
        float,
        float
    )
    def update_keithley(
        self,
        voltage,
        current,
        power
    ):

        self.voltage[
            "value"
        ].setText(
            f"{voltage:.5f}"
        )

        self.current[
            "value"
        ].setText(
            f"{current:.7f}"
        )

        self.electrical_power[
            "value"
        ].setText(
            f"{power:.7f}"
        )


    @Slot(str)
    def on_keithley_error(
        self,
        error
    ):

        self.set_error(
            self.keithley_status,
            error
        )


    # ========================================================
    # LIGHT IV
    # ========================================================

    def start_light_iv(self):

        self.run_iv_button.setEnabled(
            False
        )

        self.iv_status.setText(
            "Starting Light IV..."
        )

        self.keithley_worker.request_light_iv()


    def continue_light_iv(self):

        self.continue_iv_button.setEnabled(
            False
        )

        self.iv_status.setText(
            "Running IV sweep..."
        )

        self.keithley_worker.continue_light_iv()


    @Slot()
    def on_iv_started(self):

        self.iv_status.setText(
            "Light IV running..."
        )


    @Slot(str)
    def on_iv_waiting(
        self,
        message
    ):

        self.iv_status.setText(
            message
        )

        self.continue_iv_button.setEnabled(
            True
        )


    @Slot(
        bool,
        str
    )
    def on_iv_finished(
        self,
        success,
        message
    ):

        self.continue_iv_button.setEnabled(
            False
        )

        self.run_iv_button.setEnabled(
            True
        )

        if success:

            self.iv_status.setText(
                "Light IV complete."
            )
        else:

            self.iv_status.setText(
                f"Light IV error: {message}"
            )


    @Slot(object)
    def show_light_iv_plot(
        self,
        iv_data
    ):

        plt.figure()

        wavelengths = LIGHT_IV_SETTINGS[
            "wavelength_list_nm"
        ]

        run_number = 1

        while (
            f"volt_{run_number}" in iv_data
            and
            f"curr_{run_number}" in iv_data
        ):

            voltage = iv_data[
                f"volt_{run_number}"
            ]

            current = iv_data[
                f"curr_{run_number}"
            ]

            index = run_number - 1

            if index < len(wavelengths):
                label = (
                    f"{wavelengths[index]} nm"
                )
            else:
                label = (
                    f"Run {run_number}"
                )

            plt.plot(
                voltage,
                current,
                linewidth=1,
                marker="+",
                label=label,
            )

            run_number += 1

        plt.xlabel(
            "Voltage (V)"
        )

        plt.ylabel(
            "Current (A)"
        )

        plt.legend().set_draggable(
            True
        )

        plt.tight_layout()

        plt.show(
            block=False
        )


    # ========================================================
    # OMH
    # ========================================================

    @Slot(str)
    def on_omh_connected(
        self,
        identity
    ):

        self.set_connected(
            self.omh_status,
            identity
        )

        self.omh_title.setText(
            identity
        )


    @Slot(
        float,
        float
    )
    def update_omh(
        self,
        power_w,
        wavelength_nm
    ):

        self.wavelength[
            "value"
        ].setText(
            f"{wavelength_nm:.2f}"
        )

        self.optical_power[
            "value"
        ].setText(
            f"{power_w * 1000:.3f}"
        )


    @Slot(str)
    def on_omh_error(
        self,
        error
    ):

        self.set_error(
            self.omh_status,
            error
        )


    # ========================================================
    # ROTATOR
    # ========================================================

    @Slot(str)
    def on_rotator_connected(
        self,
        identity
    ):

        self.set_connected(
            self.rotator_status,
            identity
        )

        self.rotator_title.setText(
            identity
        )

        self.left_button.setEnabled(
            True
        )

        self.right_button.setEnabled(
            True
        )


    @Slot(float)
    def update_angle(
        self,
        angle
    ):

        self.current_angle = (
            angle
        )

        self.angle[
            "value"
        ].setText(
            f"{angle:.2f}"
        )


    @Slot(str)
    def on_rotator_error(
        self,
        error
    ):

        self.set_error(
            self.rotator_status,
            error
        )


    def rotate_left(self):

        if self.current_angle is None:
            return

        step = (
            self.step_input.value()
        )

        target = (
            self.current_angle
            - step
        )

        target = max(
            0.0,
            target
        )

        self.rotator_worker.request_move(
            target
        )


    def rotate_right(self):

        if self.current_angle is None:
            return

        step = (
            self.step_input.value()
        )

        target = (
            self.current_angle
            + step
        )

        target = min(
            360.0,
            target
        )

        self.rotator_worker.request_move(
            target
        )


    # ========================================================
    # CLOSE
    # ========================================================

    def closeEvent(
        self,
        event
    ):

        print(
            "Closing dashboard..."
        )

        self.keithley_worker.stop()
        self.omh_worker.stop()
        self.rotator_worker.stop()

        self.keithley_thread.wait(
            10000
        )

        self.omh_thread.wait(
            12000
        )

        self.rotator_thread.wait(
            7000
        )

        event.accept()


# ============================================================
# MAIN
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )

    dashboard = Dashboard()

    dashboard.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":

    main()