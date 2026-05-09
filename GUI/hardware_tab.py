import os

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from control_math import closed_loop_response
from serial_banda import BandaSerial, list_ports


DATA_DIR = r"C:\Users\Manuel\Desktop\Universidad\Control Automático\VScode\datos"
CTRL_COLORS = {"P": "#00c8ff", "PI": "#00e676", "PD": "#fcff34", "PID": "#d070ff"}


@st.cache_resource
def get_serial_manager():
    return BandaSerial()


def _selected_gains(controller, kp, ki, kd):
    if controller == "P":
        return kp, 0.0, 0.0
    if controller == "PI":
        return kp, ki, 0.0
    if controller == "PD":
        return kp, 0.0, kd
    return kp, ki, kd


def _plot_response(samples, modelo, controller, kp, ki, kd, setpoint):
    fig, ax = plt.subplots(figsize=(11, 4.4))
    fig.patch.set_facecolor("#0d0f14")
    ax.set_facecolor("#12151c")

    if samples:
        t = np.array([s["tiempo_s"] for s in samples])
        rpm = np.array([s["rpm_medida"] for s in samples])
        sp = np.array([s["setpoint_rpm"] for s in samples])
        ax.plot(t, rpm, color="#00c8ff", lw=1.6, label="RPM real")
        ax.plot(t, sp, color="#64748b", lw=1.0, ls="--", label="Setpoint")
        try:
            t_model, y_model = closed_loop_response(modelo, controller, kp, ki, kd, setpoint, t)
            ax.plot(t_model, y_model, color=CTRL_COLORS[controller], lw=1.4, alpha=0.85, label="Modelo matemático")
        except Exception as exc:
            ax.text(0.02, 0.92, f"Modelo no disponible: {exc}", transform=ax.transAxes, color="#ff6680", fontsize=8)
        xmax = max(float(t[-1]), 1.0)
        ymax = max(float(np.nanmax(rpm)), float(setpoint), 10.0)
        ymin = min(float(np.nanmin(rpm)), 0.0)
        ax.set_xlim(max(0.0, xmax - 30.0), xmax + 0.5)
        ax.set_ylim(ymin - 5.0, ymax * 1.18)
    else:
        ax.set_xlim(0, 10)
        ax.set_ylim(0, max(setpoint * 1.2, 20))
        ax.text(
            0.5,
            0.5,
            "Conecta y presiona START para ver datos",
            transform=ax.transAxes,
            ha="center",
            va="center",
            color="#8a99b8",
            fontsize=10,
        )

    ax.set_xlabel("Tiempo [s]", color="#B6B6B6", fontsize=8, fontfamily="monospace", labelpad=8)
    ax.set_ylabel("Velocidad [RPM]", color="#00c8ff", fontsize=8, fontfamily="monospace", labelpad=10)
    ax.grid(True, color="#2d3549", lw=0.45, ls="--", alpha=0.65)
    ax.tick_params(colors="#B6B6B6", labelsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#1e2535")
    ax.legend(facecolor="#12151c", edgecolor="#2a3a5a", labelcolor="#d8e4f8", fontsize=8)
    fig.subplots_adjust(left=0.08, right=0.985, top=0.96, bottom=0.16)
    return fig


def _plot_error(samples):
    fig, ax = plt.subplots(figsize=(11, 2.7))
    fig.patch.set_facecolor("#0d0f14")
    ax.set_facecolor("#12151c")

    if samples:
        t = np.array([s["tiempo_s"] for s in samples])
        error = np.array([s["error_rpm"] for s in samples])
        ax.axhline(0, color="#64748b", lw=1.0)
        ax.plot(t, error, color="#ff6b6b", lw=1.3, label="Error")
        xmax = max(float(t[-1]), 1.0)
        margin = max(float(np.nanmax(np.abs(error))) * 1.2, 5.0)
        ax.set_xlim(max(0.0, xmax - 30.0), xmax + 0.5)
        ax.set_ylim(-margin, margin)
    else:
        ax.set_xlim(0, 10)
        ax.set_ylim(-10, 10)
        ax.text(
            0.5,
            0.5,
            "Error = setpoint - RPM medida",
            transform=ax.transAxes,
            ha="center",
            va="center",
            color="#8a99b8",
            fontsize=10,
        )

    ax.set_xlabel("Tiempo [s]", color="#B6B6B6", fontsize=8, fontfamily="monospace", labelpad=8)
    ax.set_ylabel("Error [RPM]", color="#ff6b6b", fontsize=8, fontfamily="monospace", labelpad=10)
    ax.grid(True, color="#2d3549", lw=0.45, ls="--", alpha=0.65)
    ax.tick_params(colors="#B6B6B6", labelsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#1e2535")
    fig.subplots_adjust(left=0.08, right=0.985, top=0.94, bottom=0.24)
    return fig


def render_hardware_tab():
    manager = get_serial_manager()

    st.markdown('<div class="section-label">CONEXIÓN Y CONTROL EN TIEMPO REAL</div>', unsafe_allow_html=True)
    ports = list_ports()
    port_labels = [f"{p['device']} - {p['description']}" for p in ports]
    port_by_label = {label: p["device"] for label, p in zip(port_labels, ports)}

    col_conn, col_run, col_save = st.columns([2.4, 1.4, 1.2])
    with col_conn:
        selected_port = st.selectbox("Puerto serial", port_labels, index=0 if port_labels else None, placeholder="No hay puertos detectados")
    with col_run:
        st.write("")
        if not manager.is_connected:
            if st.button("Conectar", use_container_width=True, disabled=not selected_port):
                manager.connect(port_by_label[selected_port])
                st.rerun()
        else:
            if st.button("Desconectar", use_container_width=True):
                manager.disconnect()
                st.rerun()
    with col_save:
        st.write("")
        if st.button("Guardar CSV", use_container_width=True, disabled=not manager.is_connected):
            path = manager.save_csv(DATA_DIR)
            st.success(f"Guardado en {path}")

    st.markdown("---")

    col_a, col_b, col_c, col_d, col_e = st.columns([1.2, 1.2, 1, 1, 1])
    with col_a:
        modelo = st.radio("Modelo", ["Primer orden", "Segundo orden"], horizontal=False)
    with col_b:
        controller = st.radio("Controlador", ["P", "PI", "PD", "PID"], horizontal=True)
    with col_c:
        setpoint = st.number_input("Setpoint [RPM]", min_value=0.0, max_value=300.0, value=90.0, step=1.0)
    with col_d:
        kp = st.number_input("Kp", min_value=0.0, max_value=10000.0, value=2.0, step=0.1, format="%.4f")
        ki = st.number_input("Ki", min_value=0.0, max_value=10000.0, value=0.4, step=0.1, format="%.4f")
    with col_e:
        kd = st.number_input("Kd", min_value=0.0, max_value=10000.0, value=0.0, step=0.01, format="%.4f")
        live = st.checkbox("Actualizar", value=manager.is_connected)

    kp_eff, ki_eff, kd_eff = _selected_gains(controller, kp, ki, kd)

    col_start, col_stop, col_clear, col_send = st.columns(4)
    with col_start:
        if st.button("START", use_container_width=True, disabled=not manager.is_connected):
            manager.configure(controller, setpoint, kp_eff, ki_eff, kd_eff)
            manager.start()
            st.rerun()
    with col_stop:
        if st.button("STOP", use_container_width=True, disabled=not manager.is_connected):
            manager.stop()
    with col_clear:
        if st.button("Limpiar", use_container_width=True):
            manager.clear()
            st.rerun()
    with col_send:
        if st.button("Enviar parámetros", use_container_width=True, disabled=not manager.is_connected):
            manager.configure(controller, setpoint, kp_eff, ki_eff, kd_eff)

    config = (controller, float(setpoint), float(kp_eff), float(ki_eff), float(kd_eff))
    if manager.is_connected and st.session_state.get("last_hw_config") != config:
        manager.configure(controller, setpoint, kp_eff, ki_eff, kd_eff)
        st.session_state["last_hw_config"] = config

    samples, messages = manager.snapshot()
    latest = samples[-1] if samples else None
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("RPM real", f"{latest['rpm_medida']:.2f}" if latest else "--")
    m2.metric("Setpoint", f"{latest['setpoint_rpm']:.2f}" if latest else f"{setpoint:.2f}")
    m3.metric("Error", f"{latest['error_rpm']:.2f}" if latest else "--")
    m4.metric("PWM", str(latest["pwm"]) if latest else "--")

    fig = _plot_response(samples, modelo, controller, kp_eff, ki_eff, kd_eff, setpoint)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    fig_error = _plot_error(samples)
    st.pyplot(fig_error, use_container_width=True)
    plt.close(fig_error)

    with st.expander("Mensajes seriales"):
        st.code("\n".join(messages[-30:]) if messages else "Sin mensajes todavía")

    if live and manager.is_connected:
        st.empty()
        import time

        time.sleep(0.35)
        st.rerun()
