import csv
import os
import threading
import time
from collections import deque
from datetime import datetime

import serial
import serial.tools.list_ports


BAUD_RATE = 115200
MAX_POINTS = 2500


def list_ports():
    ports = []
    for port in serial.tools.list_ports.comports():
        ports.append({
            "device": port.device,
            "description": port.description,
        })
    return ports


class BandaSerial:
    def __init__(self):
        self.serial = None
        self.thread = None
        self.running_reader = False
        self.lock = threading.Lock()
        self.samples = deque(maxlen=MAX_POINTS)
        self.all_samples = []
        self.messages = deque(maxlen=80)
        self.connected_port = None

    @property
    def is_connected(self):
        return self.serial is not None and self.serial.is_open

    def connect(self, port, baud_rate=BAUD_RATE):
        self.disconnect()
        self.serial = serial.Serial(port, baud_rate, timeout=0.05)
        self.connected_port = port
        self.running_reader = True
        self.thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.thread.start()
        self.messages.append(f"Conectado a {port} ({baud_rate} baud)")

    def disconnect(self):
        if self.is_connected:
            self.send("STOP")
        self.running_reader = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.7)
        if self.serial:
            try:
                self.serial.close()
            except serial.SerialException:
                pass
        self.serial = None
        self.thread = None
        self.connected_port = None

    def send(self, command):
        if not self.is_connected:
            return
        try:
            self.serial.write((command.strip() + "\n").encode("utf-8"))
        except serial.SerialException as exc:
            self.messages.append(f"Error serial: {exc}")

    def start(self):
        self.clear()
        self.send("START")

    def stop(self):
        self.send("STOP")

    def clear(self):
        with self.lock:
            self.samples.clear()
            self.all_samples.clear()

    def configure(self, controller, setpoint, kp, ki, kd):
        self.send(f"CTRL:{controller}")
        self.send(f"SETPOINT:{setpoint:.3f}")
        self.send(f"GAINS:{kp:.6f},{ki:.6f},{kd:.6f}")

    def snapshot(self):
        with self.lock:
            return list(self.samples), list(self.messages)

    def save_csv(self, folder):
        os.makedirs(folder, exist_ok=True)
        filename = os.path.join(folder, "ensayo_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv")
        with self.lock:
            rows = list(self.all_samples)

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["tiempo_s", "rpm_medida", "setpoint_rpm", "error_rpm", "pwm", "controlador"],
            )
            writer.writeheader()
            writer.writerows(rows)

        self.messages.append(f"CSV guardado: {filename}")
        return filename

    def _reader_loop(self):
        while self.running_reader and self.is_connected:
            try:
                line = self.serial.readline().decode("utf-8", errors="ignore").strip()
            except serial.SerialException as exc:
                self.messages.append(f"Lectura detenida: {exc}")
                break

            if not line:
                time.sleep(0.01)
                continue

            if line.startswith("#") or line.startswith("tiempo"):
                self.messages.append(line)
                continue

            parts = line.split(",")
            if len(parts) != 6:
                self.messages.append(f"LÃ­nea ignorada: {line}")
                continue

            try:
                sample = {
                    "tiempo_s": float(parts[0]),
                    "rpm_medida": float(parts[1]),
                    "setpoint_rpm": float(parts[2]),
                    "error_rpm": float(parts[3]),
                    "pwm": int(float(parts[4])),
                    "controlador": parts[5],
                }
            except ValueError:
                self.messages.append(f"LÃ­nea invÃ¡lida: {line}")
                continue

            with self.lock:
                self.samples.append(sample)
                self.all_samples.append(sample)

