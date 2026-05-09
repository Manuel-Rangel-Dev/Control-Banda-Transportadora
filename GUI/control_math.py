import numpy as np
import control


def build_plant(modelo: str):
    if modelo == "Primer orden":
        return control.TransferFunction([17.4], [0.0583, 1])
    return control.TransferFunction([4.199], [6.033e-6, 0.01374, 0.2354])


def build_controller(tipo: str, kp: float, ki: float = 0.0, kd: float = 0.0):
    if tipo == "P":
        return control.TransferFunction([kp], [1])
    if tipo == "PI":
        return control.TransferFunction([kp, ki], [1, 0])
    if tipo == "PD":
        return control.TransferFunction([kd, kp], [1])
    return control.TransferFunction([kd, kp, ki], [1, 0])


def closed_loop_response(
    modelo: str,
    tipo: str,
    kp: float,
    ki: float,
    kd: float,
    setpoint: float,
    t_data,
):
    if len(t_data) == 0:
        return np.array([]), np.array([])

    t = np.asarray(t_data, dtype=float)
    t = t[t >= 0.0]
    if len(t) < 2:
        t = np.linspace(0.0, max(1.0, float(t[-1]) if len(t) else 1.0), 2)

    plant = build_plant(modelo)
    controller = build_controller(tipo, kp, ki, kd)
    system = control.feedback(controller * plant, 1)
    t_out, y_out = control.step_response(system, T=t)
    return np.asarray(t_out), np.asarray(y_out) * setpoint
