import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from control_math import closed_loop_response
from serial_banda import BandaSerial, list_ports


BG = "#0d0f14"
PANEL = "#12151c"
BORDER = "#1e2535"
TEXT = "#d8e4f8"
MUTED = "#8a99b8"
CYAN = "#00c8ff"
GREEN = "#00e676"
YELLOW = "#fcff34"
PURPLE = "#d070ff"
RED = "#ff6b6b"


def selected_gains(controller, kp, ki, kd):
    if controller == "P":
        return kp, 0.0, 0.0
    if controller == "PI":
        return kp, ki, 0.0
    if controller == "PD":
        return kp, 0.0, kd
    return kp, ki, kd


def read_float(variable, fallback):
    try:
        return float(variable.get())
    except (tk.TclError, ValueError):
        return fallback


def style_axis(ax, ylabel, color):
    ax.set_facecolor(PANEL)
    ax.grid(True, color="#2d3549", lw=0.45, ls="--", alpha=0.65)
    ax.tick_params(colors="#aab5c8", labelsize=8)
    ax.set_xlabel("Tiempo [s]", color="#aab5c8", fontsize=9, labelpad=8)
    ax.set_ylabel(ylabel, color=color, fontsize=9, labelpad=10)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)


class BandaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Control de Velocidad - Motor DC + Banda Transportadora")
        self.geometry("1320x820")
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.serial = BandaSerial()
        self.last_config = None
        self.applied_config = ("Primer orden", "PID", 60.0, 2.0, 0.4, 0.0)
        self.last_model_key = None
        self.cached_model = (np.array([]), np.array([]))
        self.running_plot = True

        self.setpoint_var = tk.DoubleVar(value=60.0)
        self.controller_var = tk.StringVar(value="PID")
        self.model_var = tk.StringVar(value="Primer orden")
        self.kp_var = tk.DoubleVar(value=2.0)
        self.ki_var = tk.DoubleVar(value=0.4)
        self.kd_var = tk.DoubleVar(value=0.0)
        self.port_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Desconectado")
        self.rpm_var = tk.StringVar(value="--")
        self.error_var = tk.StringVar(value="--")
        self.pwm_var = tk.StringVar(value="--")

        self.configure_style()
        self.build_layout()
        self.refresh_ports()
        self.after(50, self.update_live_plot)

    def configure_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=TEXT, fieldbackground=PANEL, bordercolor=BORDER)
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL, borderwidth=1, relief="solid")
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Metric.TLabel", background=PANEL, foreground=CYAN, font=("Consolas", 18, "bold"))
        style.configure("MetricName.TLabel", background=PANEL, foreground=MUTED, font=("Consolas", 8))
        style.configure("TButton", background="#182033", foreground=TEXT, bordercolor="#2a3a5a", padding=7)
        style.map("TButton", background=[("active", "#21304a")])
        style.configure("Accent.TButton", background="#063c4d", foreground=TEXT)
        style.configure("Stop.TButton", background="#4d1720", foreground=TEXT)
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background="#151b28", foreground=MUTED, padding=(16, 8))
        style.map("TNotebook.Tab", background=[("selected", PANEL)], foreground=[("selected", CYAN)])
        style.configure(
            "TCombobox",
            fieldbackground=PANEL,
            background=PANEL,
            foreground=TEXT,
            arrowcolor=CYAN,
            bordercolor="#2a3a5a",
            lightcolor="#2a3a5a",
            darkcolor="#2a3a5a",
            insertcolor=TEXT,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", PANEL), ("focus", PANEL), ("!disabled", PANEL)],
            foreground=[("readonly", TEXT), ("focus", TEXT), ("!disabled", TEXT)],
            background=[("readonly", PANEL), ("focus", PANEL), ("!disabled", PANEL)],
            selectbackground=[("readonly", "#1b2a42"), ("focus", "#1b2a42")],
            selectforeground=[("readonly", TEXT), ("focus", TEXT)],
        )
        style.configure(
            "TSpinbox",
            fieldbackground=PANEL,
            background=PANEL,
            foreground=TEXT,
            arrowcolor=CYAN,
            bordercolor="#2a3a5a",
            lightcolor="#2a3a5a",
            darkcolor="#2a3a5a",
            insertcolor=TEXT,
        )
        style.map(
            "TSpinbox",
            fieldbackground=[("focus", PANEL), ("!disabled", PANEL)],
            foreground=[("focus", TEXT), ("!disabled", TEXT)],
            background=[("focus", PANEL), ("!disabled", PANEL)],
            selectbackground=[("focus", "#1b2a42")],
            selectforeground=[("focus", TEXT)],
        )

    def build_layout(self):
        header = ttk.Frame(self, style="Panel.TFrame", padding=(18, 14))
        header.pack(fill="x", padx=14, pady=(14, 8))
        ttk.Label(header, text="CONTROL DE VELOCIDAD - MOTOR DC + BANDA TRANSPORTADORA", foreground=CYAN, background=PANEL, font=("Consolas", 15, "bold")).pack(anchor="w")
        ttk.Label(header, text="ENCODER HALL - CONTROL EN TIEMPO REAL - SETPOINT 35-80 RPM", foreground=MUTED, background=PANEL, font=("Consolas", 8)).pack(anchor="w", pady=(3, 0))

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.hardware_tab = ttk.Frame(self.tabs)
        self.model_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.hardware_tab, text="Conexion Arduino")
        self.tabs.add(self.model_tab, text="Modelado matematico")
        self.build_hardware_tab()
        self.build_model_tab()

    def build_hardware_tab(self):
        top = ttk.Frame(self.hardware_tab, style="Panel.TFrame", padding=12)
        top.pack(fill="x", pady=(0, 10))
        ttk.Label(top, text="Puerto serial", background=PANEL, foreground=MUTED, font=("Consolas", 8)).grid(row=0, column=0, sticky="w")
        self.port_combo = ttk.Combobox(top, textvariable=self.port_var, width=38, state="readonly")
        self.port_combo.grid(row=1, column=0, sticky="we", padx=(0, 8))
        ttk.Button(top, text="Actualizar", command=self.refresh_ports).grid(row=1, column=1, padx=4)
        ttk.Button(top, text="Conectar", style="Accent.TButton", command=self.connect_serial).grid(row=1, column=2, padx=4)
        ttk.Button(top, text="Desconectar", command=self.disconnect_serial).grid(row=1, column=3, padx=4)
        top.columnconfigure(0, weight=1)

        controls = ttk.Frame(top, style="Panel.TFrame")
        controls.grid(row=0, column=4, rowspan=2, sticky="e", padx=(18, 0))
        self.add_spin(controls, "Setpoint [RPM]", self.setpoint_var, 35.0, 80.0, 1.0, 0)
        self.add_combo(controls, "Controlador", self.controller_var, ["P", "PI", "PD", "PID"], 1)
        self.add_combo(controls, "Modelo", self.model_var, ["Primer orden", "Segundo orden"], 2)
        self.add_spin(controls, "Kp", self.kp_var, 0.0, 10000.0, 0.1, 3, width=8)
        self.add_spin(controls, "Ki", self.ki_var, 0.0, 10000.0, 0.1, 4, width=8)
        self.add_spin(controls, "Kd", self.kd_var, 0.0, 10000.0, 0.01, 5, width=8)
        ttk.Button(controls, text="Enviar parametros", command=self.send_config).grid(row=1, column=6, padx=(8, 4))
        ttk.Button(controls, text="START", style="Accent.TButton", command=self.start_motor).grid(row=1, column=7, padx=4)
        ttk.Button(controls, text="STOP", style="Stop.TButton", command=self.stop_motor).grid(row=1, column=8, padx=4)
        ttk.Button(controls, text="Limpiar", command=self.clear_data).grid(row=1, column=9, padx=4)

        metrics = ttk.Frame(self.hardware_tab)
        metrics.pack(fill="x", pady=(0, 10))
        self.metric_card(metrics, "ESTADO", self.status_var, 0)
        self.metric_card(metrics, "RPM REAL", self.rpm_var, 1)
        self.metric_card(metrics, "ERROR [RPM]", self.error_var, 2)
        self.metric_card(metrics, "PWM", self.pwm_var, 3)

        plot_frame = ttk.Frame(self.hardware_tab, style="Panel.TFrame", padding=8)
        plot_frame.pack(fill="both", expand=True)
        self.live_fig, (self.ax_rpm, self.ax_err) = plt.subplots(2, 1, figsize=(12, 6.6), gridspec_kw={"height_ratios": [2.0, 1.0]})
        self.live_fig.patch.set_facecolor(BG)
        style_axis(self.ax_rpm, "Velocidad [RPM]", CYAN)
        style_axis(self.ax_err, "Error [RPM]", RED)
        self.real_line, = self.ax_rpm.plot([], [], color=CYAN, lw=1.7, label="RPM real")
        self.setpoint_line, = self.ax_rpm.plot([], [], color="#8aa0c0", lw=1.1, ls="--", label="Setpoint")
        self.model_line, = self.ax_rpm.plot([], [], color="#d070ff", lw=1.4, alpha=0.9, label="Modelo matematico")
        self.error_line, = self.ax_err.plot([], [], color=RED, lw=1.4, label="Error")
        self.ax_err.axhline(0, color="#64748b", lw=1.0)
        self.ax_rpm.legend(facecolor=PANEL, edgecolor="#2a3a5a", labelcolor=TEXT, fontsize=8, loc="lower right")
        self.empty_text = self.ax_rpm.text(0.5, 0.5, "Conecta y presiona START para ver datos", transform=self.ax_rpm.transAxes, ha="center", va="center", color=MUTED, fontsize=10)
        self.live_fig.subplots_adjust(left=0.07, right=0.985, top=0.97, bottom=0.08, hspace=0.28)
        self.live_canvas = FigureCanvasTkAgg(self.live_fig, master=plot_frame)
        self.live_canvas.get_tk_widget().pack(fill="both", expand=True)

    def build_model_tab(self):
        panel = ttk.Frame(self.model_tab, style="Panel.TFrame", padding=12)
        panel.pack(fill="x", pady=(0, 10))
        self.add_spin(panel, "Setpoint [RPM]", self.setpoint_var, 35.0, 80.0, 1.0, 0)
        self.add_combo(panel, "Controlador", self.controller_var, ["P", "PI", "PD", "PID"], 1)
        self.add_combo(panel, "Modelo", self.model_var, ["Primer orden", "Segundo orden"], 2)
        self.add_spin(panel, "Kp", self.kp_var, 0.0, 10000.0, 0.1, 3, width=8)
        self.add_spin(panel, "Ki", self.ki_var, 0.0, 10000.0, 0.1, 4, width=8)
        self.add_spin(panel, "Kd", self.kd_var, 0.0, 10000.0, 0.01, 5, width=8)
        ttk.Button(panel, text="Actualizar modelo", style="Accent.TButton", command=self.update_model_tab).grid(row=1, column=6, padx=(10, 0))
        plot_frame = ttk.Frame(self.model_tab, style="Panel.TFrame", padding=8)
        plot_frame.pack(fill="both", expand=True)
        self.model_fig, self.ax_model = plt.subplots(figsize=(12, 5.2))
        self.model_fig.patch.set_facecolor(BG)
        style_axis(self.ax_model, "Velocidad [RPM]", CYAN)
        self.model_step_line, = self.ax_model.plot([], [], color=CYAN, lw=1.8, label="Respuesta del modelo")
        self.model_sp_line, = self.ax_model.plot([], [], color="#8aa0c0", lw=1.1, ls="--", label="Setpoint")
        self.ax_model.legend(facecolor=PANEL, edgecolor="#2a3a5a", labelcolor=TEXT, fontsize=8, loc="upper right")
        self.model_fig.subplots_adjust(left=0.07, right=0.985, top=0.96, bottom=0.12)
        self.model_canvas = FigureCanvasTkAgg(self.model_fig, master=plot_frame)
        self.model_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.update_model_tab()

    def add_spin(self, parent, label, variable, min_value, max_value, step, col, width=10):
        ttk.Label(parent, text=label, background=PANEL, foreground=MUTED, font=("Consolas", 8)).grid(row=0, column=col, sticky="w", padx=(0, 6))
        spin = ttk.Spinbox(parent, textvariable=variable, from_=min_value, to=max_value, increment=step, width=width)
        spin.grid(row=1, column=col, sticky="w", padx=(0, 8))
        return spin

    def add_combo(self, parent, label, variable, values, col):
        ttk.Label(parent, text=label, background=PANEL, foreground=MUTED, font=("Consolas", 8)).grid(row=0, column=col, sticky="w", padx=(0, 6))
        combo = ttk.Combobox(parent, textvariable=variable, values=values, width=14, state="readonly")
        combo.grid(row=1, column=col, sticky="w", padx=(0, 8))
        return combo

    def metric_card(self, parent, title, variable, col):
        card = ttk.Frame(parent, style="Panel.TFrame", padding=(12, 9))
        card.grid(row=0, column=col, sticky="we", padx=(0 if col == 0 else 8, 0))
        ttk.Label(card, text=title, style="MetricName.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=variable, style="Metric.TLabel").pack(anchor="w")
        parent.columnconfigure(col, weight=1)

    def refresh_ports(self):
        ports = list_ports()
        labels = [f"{p['device']} - {p['description']}" for p in ports]
        self.port_combo["values"] = labels
        self.port_map = {label: p["device"] for label, p in zip(labels, ports)}
        if labels and not self.port_var.get():
            self.port_var.set(labels[0])

    def current_config(self):
        controller = self.controller_var.get()
        setpoint = min(max(read_float(self.setpoint_var, 60.0), 35.0), 80.0)
        kp_raw = read_float(self.kp_var, 0.0)
        ki_raw = read_float(self.ki_var, 0.0)
        kd_raw = read_float(self.kd_var, 0.0)
        kp, ki, kd = selected_gains(controller, kp_raw, ki_raw, kd_raw)
        return (self.model_var.get(), controller, setpoint, float(kp), float(ki), float(kd))

    def on_config_changed(self, event=None):
        self.last_model_key = None
        if hasattr(self, "model_canvas"):
            self.update_model_tab()

    def send_config(self):
        if not self.serial.is_connected:
            return
        _, controller, setpoint, kp, ki, kd = self.current_config()
        config = (controller, setpoint, kp, ki, kd)
        if self.last_config != config:
            self.serial.configure(controller, setpoint, kp, ki, kd)
            self.last_config = config
            self.applied_config = self.current_config()
            self.last_model_key = None
            self.status_var.set("Parametros enviados")

    def connect_serial(self):
        label = self.port_var.get()
        if not label:
            messagebox.showwarning("Puerto serial", "Selecciona un puerto serial.")
            return
        try:
            self.serial.connect(self.port_map[label])
            self.status_var.set(f"Conectado {self.port_map[label]}")
        except Exception as exc:
            messagebox.showerror("Error serial", str(exc))

    def disconnect_serial(self):
        self.serial.disconnect()
        self.status_var.set("Desconectado")

    def start_motor(self):
        if not self.serial.is_connected:
            messagebox.showwarning("Arduino", "Conecta el Arduino antes de iniciar.")
            return
        self.serial.start()
        self.status_var.set("Ejecutando")
        self.last_model_key = None

    def stop_motor(self):
        self.serial.stop()
        if self.serial.is_connected:
            self.status_var.set("Detenido")

    def clear_data(self):
        self.serial.clear()
        self.last_model_key = None

    def update_live_plot(self):
        if not self.running_plot:
            return
        samples, _ = self.serial.snapshot()
        if samples:
            t = np.array([s["tiempo_s"] for s in samples], dtype=float)
            rpm = np.array([s["rpm_medida"] for s in samples], dtype=float)
            sp = np.array([s["setpoint_rpm"] for s in samples], dtype=float)
            err = np.array([s["error_rpm"] for s in samples], dtype=float)
            self.empty_text.set_visible(False)
            self.real_line.set_data(t, rpm)
            self.setpoint_line.set_data(t, sp)
            self.error_line.set_data(t, err)
            tm, ym = self.get_live_model(t)
            self.model_line.set_data(tm, ym)
            self.rpm_var.set(f"{rpm[-1]:.2f}")
            self.error_var.set(f"{err[-1]:.2f}")
            self.pwm_var.set(str(samples[-1]["pwm"]))
            xmin = max(0.0, float(t[-1]) - 30.0)
            xmax = max(float(t[-1]) + 0.5, 5.0)
            ymax = max(float(np.nanmax(rpm)), float(np.nanmax(sp)), 10.0)
            ymin = min(float(np.nanmin(rpm)), 0.0)
            self.ax_rpm.set_xlim(xmin, xmax)
            self.ax_rpm.set_ylim(ymin - 5.0, ymax * 1.18)
            emargin = max(float(np.nanmax(np.abs(err))) * 1.2, 5.0)
            self.ax_err.set_xlim(xmin, xmax)
            self.ax_err.set_ylim(-emargin, emargin)
        else:
            _, _, setpoint, _, _, _ = self.current_config()
            self.empty_text.set_visible(True)
            self.real_line.set_data([], [])
            self.setpoint_line.set_data([], [])
            self.model_line.set_data([], [])
            self.error_line.set_data([], [])
            self.ax_rpm.set_xlim(0, 10)
            self.ax_rpm.set_ylim(0, max(setpoint * 1.2, 50))
            self.ax_err.set_xlim(0, 10)
            self.ax_err.set_ylim(-10, 10)
            self.rpm_var.set("--")
            self.error_var.set("--")
            self.pwm_var.set("--")
        self.live_canvas.draw_idle()
        self.after(50, self.update_live_plot)

    def get_live_model(self, t_real):
        if len(t_real) < 2:
            return np.array([]), np.array([])
        model, controller, setpoint, kp, ki, kd = self.applied_config
        duration = max(float(t_real[-1] - t_real[0]), 0.5)
        key = (model, controller, setpoint, kp, ki, kd, round(duration, 1))
        if key != self.last_model_key:
            t_uniform = np.linspace(0.0, duration, min(max(len(t_real), 120), 1200))
            try:
                tm, ym = closed_loop_response(model, controller, kp, ki, kd, setpoint, t_uniform)
                self.cached_model = (tm + float(t_real[0]), ym)
            except Exception:
                self.cached_model = (np.array([]), np.array([]))
            self.last_model_key = key
        return self.cached_model

    def update_model_tab(self):
        model, controller, setpoint, kp, ki, kd = self.current_config()
        t = np.linspace(0.0, 5.0, 1000)
        try:
            tm, ym = closed_loop_response(model, controller, kp, ki, kd, setpoint, t)
            self.ax_model.set_title(f"{model} - Controlador {controller}", color=CYAN, fontsize=10)
        except Exception as exc:
            self.ax_model.set_title(f"Modelo no disponible: {exc}", color=RED, fontsize=10)
            tm, ym = np.array([]), np.array([])
        self.model_step_line.set_data(tm, ym)
        self.model_sp_line.set_data([0, 5], [setpoint, setpoint])
        self.ax_model.set_xlim(0, 5)
        ymax = max(float(np.nanmax(ym)) if len(ym) else setpoint, setpoint, 10.0)
        ymin = min(float(np.nanmin(ym)) if len(ym) else 0.0, 0.0)
        self.ax_model.set_ylim(ymin - 5.0, ymax * 1.18)
        self.model_canvas.draw_idle()

    def on_close(self):
        self.running_plot = False
        self.serial.disconnect()
        plt.close("all")
        self.destroy()


if __name__ == "__main__":
    app = BandaApp()
    app.mainloop()
