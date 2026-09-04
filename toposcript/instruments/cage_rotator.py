import os
import time
import clr

from System import Decimal


class K10CR2CageRotator:

    def __init__(
        self,
        serial_number="55538844",
        kinesis_path=r"C:\Program Files\Thorlabs\Kinesis",
        poll_interval_ms=250,
        settings_timeout_ms=5000,
        move_timeout_ms=60000,
    ):

        self.serial_number = str(serial_number)
        self.kinesis_path = kinesis_path

        self.poll_interval_ms = poll_interval_ms
        self.settings_timeout_ms = settings_timeout_ms
        self.move_timeout_ms = move_timeout_ms

        self.device = None
        self._polling = False

        self._load_kinesis()


    # ========================================================
    # LOAD KINESIS
    # ========================================================

    def _load_kinesis(self):

        clr.AddReference(
            os.path.join(
                self.kinesis_path,
                "Thorlabs.MotionControl.DeviceManagerCLI.dll"
            )
        )

        clr.AddReference(
            os.path.join(
                self.kinesis_path,
                "Thorlabs.MotionControl.GenericMotorCLI.dll"
            )
        )

        clr.AddReference(
            os.path.join(
                self.kinesis_path,
                "Thorlabs.MotionControl.IntegratedStepperMotorsCLI.dll"
            )
        )

        global DeviceManagerCLI
        global CageRotator

        from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
        from Thorlabs.MotionControl.IntegratedStepperMotorsCLI import CageRotator


    # ========================================================
    # CONNECT
    # ========================================================

    def connect(self):

        DeviceManagerCLI.BuildDeviceList()

        devices = list(
            DeviceManagerCLI.GetDeviceList()
        )

        if self.serial_number not in devices:

            raise RuntimeError(
                f"Cage rotator {self.serial_number} was not detected."
            )

        self.device = CageRotator.CreateCageRotator(
            self.serial_number
        )

        if self.device is None:

            raise RuntimeError(
                "Could not create CageRotator object."
            )

        self.device.Connect(
            self.serial_number
        )

        if not self.device.IsSettingsInitialized():

            print(
                "Waiting for device settings..."
            )

            self.device.WaitForSettingsInitialized(
                self.settings_timeout_ms
            )

        print(
            "Loading motor configuration..."
        )

        self.device.LoadMotorConfiguration(
            self.serial_number
        )

        if not self.device.IsMotorSettingsValid:

            raise RuntimeError(
                "Motor settings are not valid."
            )

        self.device.StartPolling(
            self.poll_interval_ms
        )

        self._polling = True

        time.sleep(0.5)

        self.device.EnableDevice()

        time.sleep(0.5)

        info = self.device.GetDeviceInfo()

        print(
            f"Connected: {info.Name} | "
            f"{info.Description} | "
            f"SN {info.SerialNumber}"
        )

        print(
            f"Current angle: "
            f"{self.get_angle():.3f} deg"
        )

        return self


    # ========================================================
    # READ ANGLE
    # ========================================================

    def get_angle(self):

        self._require_connection()

        position = self.device.Position

        return float(
            str(position)
        )


    # ========================================================
    # MOVE
    # ========================================================

    def move_to(
        self,
        angle_deg
    ):

        self._require_connection()

        angle_deg = float(
            angle_deg
        )

        if not 0.0 <= angle_deg <= 360.0:

            raise ValueError(
                "Angle must be between 0 and 360 degrees."
            )

        current_angle = self.get_angle()

        print(
            f"Moving cage rotator: "
            f"{current_angle:.3f} -> "
            f"{angle_deg:.3f} deg"
        )

        # IMPORTANT:
        # DO NOT use Decimal(str(angle_deg))
        #
        # Your Python/.NET environment expects
        # a numeric value here.

        target = Decimal(
            angle_deg
        )

        self.device.MoveTo(
            target,
            self.move_timeout_ms
        )

        time.sleep(0.2)

        final_angle = self.get_angle()

        print(
            f"Reached: "
            f"{final_angle:.3f} deg"
        )

        return final_angle


    # ========================================================
    # HOME
    # ========================================================

    def home(self):

        self._require_connection()

        print(
            "Homing cage rotator..."
        )

        self.device.Home(
            self.move_timeout_ms
        )

        final_angle = self.get_angle()

        print(
            f"Homing complete: "
            f"{final_angle:.3f} deg"
        )

        return final_angle


    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        self._require_connection()

        self.device.StopImmediate()


    # ========================================================
    # CHECK CONNECTION
    # ========================================================

    def _require_connection(self):

        if self.device is None:

            raise RuntimeError(
                "Cage rotator is not connected."
            )


    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        if self.device is None:
            return

        if self._polling:

            try:
                self.device.StopPolling()
            except Exception:
                pass

            self._polling = False

        try:
            self.device.Disconnect()
        except Exception:
            pass

        self.device = None

        print(
            "Cage rotator disconnected."
        )