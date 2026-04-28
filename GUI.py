import streamlit as st
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import control

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Control Motor DC",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS profesional (industrial/utilitarian dark theme) ───────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Barlow:wght@400;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif;
    background-color: #0d0f14;
    color: #e0e6ef;
  }
  .stApp { background-color: #0d0f14; }

  /* Header principal */
  .main-header {
    background: linear-gradient(135deg, #12151c 0%, #1a1f2e 100%);
    border: 1px solid #2a3040;
    border-left: 4px solid #00c8ff;
    border-radius: 4px;
    padding: 18px 24px;
    margin-bottom: 20px;
  }
  .main-header h1 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.3rem;
    color: #00c8ff;
    margin: 0;
    letter-spacing: 0.08em;
  }
  .main-header p {
    font-size: 0.78rem;
    color: #6b7a99;
    margin: 4px 0 0 0;
    letter-spacing: 0.05em;
  }

  /* Sección label */
  .section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #00c8ff;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 6px;
  }

  /* Tarjetas */
  .card {
    background: #12151c;
    border: 1px solid #1e2535;
    border-radius: 4px;
    padding: 16px;
    margin-bottom: 16px;
  }

  /* Slider label */
  .setpoint-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #8a99b8;
    letter-spacing: 0.08em;
  }
  .setpoint-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.2rem;
    font-weight: 700;
    color: #00c8ff;
  }
  .setpoint-unit {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    color: #4a5a7a;
  }

  /* Sliders */
  .stSlider > div > div > div > div {
    background: #00c8ff !important;
  }

  /* Radio buttons */
  .stRadio > label { color: #8a99b8 !important; font-size: 0.8rem; }
  .stRadio > div > label { color: #c0cce0 !important; }

  /* Divider */
  hr { border-color: #1e2535 !important; }
</style>
""", unsafe_allow_html=True)


# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>⚙ CONTROL DE VELOCIDAD — MOTOR DC + BANDA TRANSPORTADORA</h1>
  <p>ENCODER HALL · RETROALIMENTACIÓN UNITARIA · ANÁLISIS EN LAZO CERRADO</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 1 — SETPOINT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">▸ 01 — SETPOINT</div>', unsafe_allow_html=True)

col_sp1, col_sp2 = st.columns([4, 1])
with col_sp1:
    setpoint = st.slider(
        "Setpoint (RPM)",
        min_value=60,
        max_value=120,
        value=90,
        step=1,
        label_visibility="collapsed",
    )
with col_sp2:
    st.markdown(
        f'<div style="text-align:right; padding-top:4px;">'
        f'<span class="setpoint-value">{setpoint}</span>'
        f'<span class="setpoint-unit"> RPM</span></div>',
        unsafe_allow_html=True
    )

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 2 — SELECCIÓN MODELO Y CONTROLADOR (necesario para el diagrama)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">▸ 02 — CONFIGURACIÓN DEL SISTEMA</div>', unsafe_allow_html=True)

col_m, col_c = st.columns(2)
with col_m:
    st.markdown('<div class="setpoint-label">MODELO DE PLANTA</div>', unsafe_allow_html=True)
    modelo = st.radio(
        "modelo",
        ["Primer orden", "Segundo orden"],
        horizontal=True,
        label_visibility="collapsed",
    )
with col_c:
    st.markdown('<div class="setpoint-label">CONTROLADOR</div>', unsafe_allow_html=True)
    controlador = st.radio(
        "controlador",
        ["P", "PI", "PD"],
        horizontal=True,
        label_visibility="collapsed",
    )

# Cajas de texto para ganancias del controlador
col_k1, col_k2, col_k3 = st.columns(3)
Kp = Ki = Kd = 0.0

with col_k1:
    Kp = st.number_input("Kp", min_value=0.0, max_value=10000.0,
                         value=5.0, step=0.1, format="%.4f")

if controlador == "PI":
    with col_k2:
        Ki = st.number_input("Ki", min_value=0.0, max_value=10000.0,
                             value=2.0, step=0.1, format="%.4f")
elif controlador == "PD":
    with col_k2:
        Kd = st.number_input("Kd", min_value=0.0, max_value=10000.0,
                             value=0.5, step=0.1, format="%.4f")

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 3 — DIAGRAMA DE BLOQUES (Matplotlib)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">▸ 03 — DIAGRAMA DE BLOQUES DEL SISTEMA</div>', unsafe_allow_html=True)

def texto_controlador(ctrl, kp, ki, kd):
    if ctrl == "P":
        return f"C(s) = {kp:.1f}"
    elif ctrl == "PI":
        return f"C(s) = {kp:.1f} + {ki:.1f}/s"
    else:
        return f"C(s) = {kp:.1f} + {kd:.1f}·s"

def texto_planta(mod):
    if mod == "Primer orden":
        return "G(s) = 17.4 / (0.0583s+1)"
    else:
        return "G(s) = 4.199 /\n(6.033e-6s²+0.01374s+0.2354)"

def draw_block_diagram(modelo, controlador, Kp, Ki, Kd):
    """
    Diagrama de bloques limpio con coordenadas fijas.
    Layout (coordenadas en unidades del axes):

      R(s) →→ [Σ] →→ [C(s)] →→ [G(s)] →→ Y(s)
                ↑                    |
                └────────────────────┘
                    H(s) = 1
    """
    # ── Figura ──────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(13, 3.2))
    fig.patch.set_facecolor("#0d0f14")
    ax.set_facecolor("#0d0f14")

    # Espacio de coordenadas: x ∈ [0,14], y ∈ [0,5]
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5)
    ax.axis("off")

    # ── Paleta ───────────────────────────────────────────────────────────────
    BG      = "#12151c"
    BORDER  = "#2a3a5a"
    ACC     = "#00c8ff"     # azul cian — controlador
    WHITE   = "#c8d8f0"
    DIM     = "#4a6080"
    LINE    = "#3a5070"
    GREEN   = "#00e676"
    RED     = "#ff4460"

    # ── Helpers ──────────────────────────────────────────────────────────────
    def hline(x0, x1, y, color=LINE, lw=1.6):
        ax.plot([x0, x1], [y, y], color=color, lw=lw, solid_capstyle="round")

    def vline(x, y0, y1, color=LINE, lw=1.6):
        ax.plot([x, x], [y0, y1], color=color, lw=lw, solid_capstyle="round")

    def arrow_right(x, y, color=LINE):
        ax.annotate("", xy=(x, y), xytext=(x - 0.01, y),
                    arrowprops=dict(arrowstyle="-|>", color=color,
                                   lw=1.6, mutation_scale=12))

    def label(x, y, txt, color=WHITE, fs=8, ha="center", va="center", mono=True):
        ff = "monospace" if mono else "sans-serif"
        ax.text(x, y, txt, ha=ha, va=va, fontsize=fs, color=color,
                fontfamily=ff, linespacing=1.4)

    def block(cx, cy, w, h, txt, sublabel=None, accent=False):
        """Rectángulo centrado en (cx,cy)."""
        ec = ACC if accent else BORDER
        rect = plt.Rectangle((cx - w/2, cy - h/2), w, h,
                              linewidth=1.8, edgecolor=ec,
                              facecolor=BG, zorder=3)
        ax.add_patch(rect)
        label(cx, cy + (0.18 if sublabel else 0), txt,
              color=ACC if accent else WHITE, fs=7.5)
        if sublabel:
            label(cx, cy - 0.38, sublabel, color=DIM, fs=6.2)

    def sumador(cx, cy, r=0.32):
        circle = plt.Circle((cx, cy), r, color=BG, ec=BORDER, lw=1.8, zorder=3)
        ax.add_patch(circle)
        label(cx, cy + 0.06, "+", color=GREEN, fs=11)
        label(cx - 0.04, cy - 0.21, "−", color=RED, fs=11)

    # ════════════════════════════════════════════════════════════════════
    # Coordenadas clave (Y central = 3.0)
    # ════════════════════════════════════════════════════════════════════
    Y   = 3.0       # altura de la línea principal
    Yf  = 1.4       # altura de la línea de retroalimentación

    X_R    = 0.5    # texto R(s)
    X_L0   = 1.1    # inicio flecha entrada
    X_SUM  = 2.0    # centro sumador
    X_L1   = 2.35   # fin flecha post-sumador
    X_C    = 4.0    # centro bloque C(s)
    X_L2   = 4.95   # fin flecha post-controlador
    X_G    = 6.8    # centro bloque G(s)
    X_L3   = 8.1    # nodo de salida (bifurcación)
    X_Y    = 8.9    # texto Y(s)
    X_FB   = X_L3   # línea vertical de retorno baja desde aquí

    # ── Entrada R(s) ────────────────────────────────────────────────────
    label(X_R, Y + 0.5, f"R(s)", color=ACC, fs=8.5)
    label(X_R, Y,       f"{setpoint} RPM", color=DIM, fs=7)
    hline(X_L0, X_SUM - 0.32, Y)
    arrow_right(X_SUM - 0.32, Y)

    # ── Sumador ──────────────────────────────────────────────────────────
    sumador(X_SUM, Y)

    # ── e(t) ─────────────────────────────────────────────────────────────
    hline(X_SUM + 0.32, X_C - 1.05, Y)
    label((X_SUM + 0.32 + X_C - 1.05) / 2, Y + 0.28, "e(t)", color=DIM, fs=7)
    arrow_right(X_C - 1.05, Y)

    # ── Bloque C(s) ──────────────────────────────────────────────────────
    block(X_C, Y, 2.0, 1.05,
          texto_controlador(controlador, Kp, Ki, Kd),
          sublabel="CONTROLADOR C(s)", accent=True)

    # ── u(t) ─────────────────────────────────────────────────────────────
    hline(X_C + 1.0, X_G - 1.15, Y)
    label((X_C + 1.0 + X_G - 1.15) / 2, Y + 0.28, "u(t)", color=DIM, fs=7)
    arrow_right(X_G - 1.15, Y)

    # ── Bloque G(s) ──────────────────────────────────────────────────────
    block(X_G, Y, 2.25, 1.05,
          texto_planta(modelo),
          sublabel="PLANTA G(s)", accent=False)

    # ── Línea de salida hasta nodo ───────────────────────────────────────
    hline(X_G + 1.125, X_L3, Y)

    # ── Y(s) ─────────────────────────────────────────────────────────────
    label(X_Y + 0.3, Y + 0.45, "Y(s)", color=ACC, fs=8.5)
    label(X_Y + 0.3, Y,        "ω [RPM]", color=DIM, fs=7)
    # flecha de salida
    hline(X_L3, X_Y + 0.05, Y)
    arrow_right(X_Y + 0.05, Y, color=ACC)

    # ── Retroalimentación: nodo → abajo → izquierda → sumador ────────────
    # Punto en (X_FB, Y) baja a (X_FB, Yf)
    vline(X_FB, Y, Yf)
    # Va hacia la izquierda hasta debajo del sumador
    hline(X_SUM, X_FB, Yf)
    # Sube al sumador
    vline(X_SUM, Yf, Y - 0.32)
    arrow_right(X_SUM, Y - 0.32, color=LINE)   # sólo para visibilidad
    # Etiqueta H(s)=1
    label((X_SUM + X_FB) / 2, Yf - 0.28, "H(s) = 1  [retroalimentación unitaria]",
          color=DIM, fs=7)

    plt.tight_layout(pad=0.2)
    return fig

fig_diag = draw_block_diagram(modelo, controlador, Kp, Ki, Kd)
st.pyplot(fig_diag, use_container_width=True)
plt.close(fig_diag)

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONTROL — construcción del sistema en lazo cerrado
# ══════════════════════════════════════════════════════════════════════════════
def build_plant(modelo):
    if modelo == "Primer orden":
        return control.TransferFunction([17.4], [0.0583, 1])
    else:
        return control.TransferFunction([4.199], [6.033e-6, 0.01374, 0.2354])

def build_controller(controlador, Kp, Ki, Kd):
    s = control.TransferFunction([1, 0], [1])
    if controlador == "P":
        return control.TransferFunction([Kp], [1])
    elif controlador == "PI":
        # Kp + Ki/s = (Kp*s + Ki) / s
        return control.TransferFunction([Kp, Ki], [1, 0])
    else:
        # Kp + Kd*s = (Kd*s + Kp) / 1
        return control.TransferFunction([Kd, Kp], [1])

def build_closed_loop(modelo, controlador, Kp, Ki, Kd):
    G = build_plant(modelo)
    C = build_controller(controlador, Kp, Ki, Kd)
    L = C * G                          # lazo abierto
    CL = control.feedback(L, 1)        # lazo cerrado
    return CL, L

def calc_step_specs(t, y, setpoint):
    """Calcula Mp, tr, tp, ts(2%), ess desde la respuesta al escalón normalizada."""
    # y está escalada al setpoint
    yss = y[-1]
    ymax = np.max(y)

    # Sobreimpulso
    Mp = max(0.0, (ymax - yss) / yss * 100) if yss > 0 else 0.0

    # Tiempo pico
    tp = t[np.argmax(y)]

    # Tiempo de subida (10% → 90% del valor final)
    try:
        i10 = np.where(y >= 0.1 * yss)[0][0]
        i90 = np.where(y >= 0.9 * yss)[0][0]
        tr = t[i90] - t[i10]
    except IndexError:
        tr = float("nan")

    # Tiempo de establecimiento (2%)
    banda = 0.02 * yss
    ts = float("nan")
    for i in range(len(y) - 1, -1, -1):
        if abs(y[i] - yss) > banda:
            ts = t[i] if i + 1 < len(t) else t[-1]
            break

    # Error en estado estacionario (referencia = setpoint)
    ess = abs(setpoint - yss)

    return Mp, tp, tr, ts, ess


# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 4 — RESPUESTA AL ESCALÓN + ESPECIFICACIONES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">▸ 04 — RESPUESTA TEMPORAL EN LAZO CERRADO</div>',
            unsafe_allow_html=True)

CL, L_open = build_closed_loop(modelo, controlador, Kp, Ki, Kd)

# ── Calcular tiempo de simulación adaptativo ─────────────────────────────────
def calc_T_end(sys_cl, fallback=0.2):
    """
    Estima el tiempo necesario para ver el transitorio completo.
    Estrategia: simula con T largo, detecta ts(2%), y añade margen visual.
    """
    try:
        t_long = np.linspace(0, 5.0, 10000)
        t_tmp, y_tmp = control.step_response(sys_cl, T=t_long)
        yss = y_tmp[-1]
        if yss == 0:
            return fallback
        banda = 0.02 * abs(yss)
        ts_idx = 0
        for i in range(len(y_tmp) - 1, -1, -1):
            if abs(y_tmp[i] - yss) > banda:
                ts_idx = i
                break
        ts_est = t_tmp[ts_idx]
        # Añadir 40% de margen visual, mínimo 2×tp
        tp_idx = np.argmax(y_tmp)
        tp_est = t_tmp[tp_idx]
        T_visual = max(ts_est * 1.4, tp_est * 2.5, 1e-4)
        # Acotar entre 1 ms y 2 s para que la gráfica sea útil
        return float(np.clip(T_visual, 1e-3, 2.0))
    except Exception:
        return fallback

T_end = calc_T_end(CL)
t_sim = np.linspace(0, T_end, 4000)
try:
    t_out, y_out = control.step_response(CL, T=t_sim)
    y_rpm = y_out * setpoint          # escalar al setpoint
    sim_ok = True
except Exception as e:
    sim_ok = False
    sim_error = str(e)

col_step, col_specs = st.columns([3, 2])

# ── Gráfica de respuesta al escalón ─────────────────────────────────────────
with col_step:
    if sim_ok:
        fig_step, ax_step = plt.subplots(figsize=(7, 3.6))
        fig_step.patch.set_facecolor("#0d0f14")
        ax_step.set_facecolor("#12151c")

        # Línea de setpoint
        ax_step.axhline(setpoint, color="#2a4060", lw=1.2, ls="--", label=f"Setpoint ({setpoint} RPM)")

        # Banda del 2%
        ax_step.axhspan(setpoint * 0.98, setpoint * 1.02,
                        alpha=0.08, color="#00c8ff", label="±2%")

        # Señal de respuesta
        ax_step.plot(t_out, y_rpm, color="#00c8ff", lw=2.0, label="y(t)")

        ax_step.set_xlabel("Tiempo [s]", color="#6a8ab8", fontsize=8, fontfamily="monospace")
        ax_step.set_ylabel("Velocidad [RPM]", color="#6a8ab8", fontsize=8, fontfamily="monospace")
        ax_step.set_xlim(0, T_end)
        ax_step.tick_params(colors="#4a6080", labelsize=7)
        for sp in ax_step.spines.values():
            sp.set_edgecolor("#1e2535")
        ax_step.legend(fontsize=7, facecolor="#12151c", edgecolor="#2a3a5a",
                       labelcolor="#8a9ab8")
        ax_step.grid(True, color="#1a2030", lw=0.6)
        fig_step.tight_layout(pad=0.6)
        st.pyplot(fig_step, use_container_width=True)
        plt.close(fig_step)
    else:
        st.error(f"Error en simulación: {sim_error}")

# ── Especificaciones temporales ──────────────────────────────────────────────
with col_specs:
    if sim_ok:
        Mp, tp, tr, ts, ess = calc_step_specs(t_out, y_rpm, setpoint)

        def fmt(val, unit="s", decimals=4):
            if np.isnan(val):
                return "—"
            return f"{val:.{decimals}f} {unit}"

        specs_html = f"""
        <div style="
            background:#12151c; border:1px solid #1e2535;
            border-left:3px solid #00c8ff;
            border-radius:4px; padding:18px 20px;
            font-family:'JetBrains Mono',monospace;
        ">
          <div style="color:#00c8ff; font-size:0.68rem; letter-spacing:0.12em;
                      margin-bottom:14px;">ESPECIFICACIONES TEMPORALES</div>

          <div style="display:flex; justify-content:space-between;
                      border-bottom:1px solid #1a2030; padding:7px 0;">
            <span style="color:#6a8ab8; font-size:0.75rem;">Sobreimpulso  Mp</span>
            <span style="color:#e0ecff; font-size:0.85rem; font-weight:700;">
              {Mp:.2f} %</span>
          </div>
          <div style="display:flex; justify-content:space-between;
                      border-bottom:1px solid #1a2030; padding:7px 0;">
            <span style="color:#6a8ab8; font-size:0.75rem;">Tiempo pico   tp</span>
            <span style="color:#e0ecff; font-size:0.85rem; font-weight:700;">
              {fmt(tp)}</span>
          </div>
          <div style="display:flex; justify-content:space-between;
                      border-bottom:1px solid #1a2030; padding:7px 0;">
            <span style="color:#6a8ab8; font-size:0.75rem;">Tiempo subida tr</span>
            <span style="color:#e0ecff; font-size:0.85rem; font-weight:700;">
              {fmt(tr)}</span>
          </div>
          <div style="display:flex; justify-content:space-between;
                      border-bottom:1px solid #1a2030; padding:7px 0;">
            <span style="color:#6a8ab8; font-size:0.75rem;">Estab. 2%     ts</span>
            <span style="color:#e0ecff; font-size:0.85rem; font-weight:700;">
              {fmt(ts)}</span>
          </div>
          <div style="display:flex; justify-content:space-between; padding:7px 0;">
            <span style="color:#6a8ab8; font-size:0.75rem;">Error est.    ess</span>
            <span style="color:{'#ff6b6b' if ess > 1 else '#00e676'};
                         font-size:0.85rem; font-weight:700;">
              {ess:.3f} RPM</span>
          </div>
        </div>
        """
        st.markdown(specs_html, unsafe_allow_html=True)

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 5 — MAPA DE POLOS Y CEROS (lazo cerrado)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">▸ 05 — MAPA DE POLOS Y CEROS (LAZO CERRADO)</div>',
            unsafe_allow_html=True)

def plot_poles_zeros(sys_cl):
    poles = control.poles(sys_cl)
    zeros = control.zeros(sys_cl)

    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor("#0d0f14")
    ax.set_facecolor("#12151c")

    # Ejes cartesianos
    ax.axhline(0, color="#2a3a5a", lw=1.0)
    ax.axvline(0, color="#2a3a5a", lw=1.0)
    ax.grid(True, color="#1a2030", lw=0.5, ls="--")

    # Polos (×)
    for p in poles:
        ax.plot(p.real, p.imag, "x", color="#ff4466",
                markersize=11, markeredgewidth=2.5, zorder=5)
        ax.annotate(f"{p.real:.2f}{'+' if p.imag >= 0 else ''}{p.imag:.2f}j",
                    xy=(p.real, p.imag),
                    xytext=(6, 8), textcoords="offset points",
                    fontsize=7, color="#ff8899",
                    fontfamily="monospace")

    # Ceros (o)
    for z in zeros:
        ax.plot(z.real, z.imag, "o", color="#00e676",
                markersize=9, markerfacecolor="none",
                markeredgewidth=2.0, zorder=5)
        ax.annotate(f"{z.real:.2f}{'+' if z.imag >= 0 else ''}{z.imag:.2f}j",
                    xy=(z.real, z.imag),
                    xytext=(6, 8), textcoords="offset points",
                    fontsize=7, color="#00e676",
                    fontfamily="monospace")

    # Leyenda manual
    from matplotlib.lines import Line2D
    legend_elem = [
        Line2D([0], [0], marker="x", color="#ff4466", lw=0,
               markersize=9, markeredgewidth=2.5, label="Polos"),
        Line2D([0], [0], marker="o", color="#00e676", lw=0,
               markersize=8, markerfacecolor="none",
               markeredgewidth=2.0, label="Ceros"),
    ]
    ax.legend(handles=legend_elem, fontsize=7,
              facecolor="#12151c", edgecolor="#2a3a5a", labelcolor="#8a9ab8")

    ax.set_xlabel("Re", color="#6a8ab8", fontsize=8, fontfamily="monospace")
    ax.set_ylabel("Im", color="#6a8ab8", fontsize=8, fontfamily="monospace")
    ax.tick_params(colors="#4a6080", labelsize=7)
    for sp in ax.spines.values():
        sp.set_edgecolor("#1e2535")

    fig.tight_layout(pad=0.6)
    return fig

fig_pz = plot_poles_zeros(CL)
st.pyplot(fig_pz, use_container_width=True)
plt.close(fig_pz)

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 6 — DIAGRAMA DE BODE + MÁRGENES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">▸ 06 — DIAGRAMA DE BODE (LAZO ABIERTO L(s) = C(s)·G(s))</div>',
            unsafe_allow_html=True)

def plot_bode(L):
    """Diagrama de Bode del lazo abierto: magnitud y fase."""
    omega = np.logspace(-1, 6, 2000)
    mag, phase, omega_out = control.bode(L, omega, plot=False)

    mag_db    = 20 * np.log10(np.abs(mag) + 1e-12)
    phase_deg = np.degrees(phase)

    fig, (ax_mag, ax_ph) = plt.subplots(2, 1, figsize=(7, 5), sharex=True)
    fig.patch.set_facecolor("#0d0f14")

    for ax in (ax_mag, ax_ph):
        ax.set_facecolor("#12151c")
        ax.grid(True, which="both", color="#1a2030", lw=0.5, ls="--")
        ax.tick_params(colors="#4a6080", labelsize=7)
        for sp in ax.spines.values():
            sp.set_edgecolor("#1e2535")

    # ── Magnitud ──────────────────────────────────────────────────────────
    ax_mag.semilogx(omega_out, mag_db, color="#00c8ff", lw=1.8)
    ax_mag.axhline(0, color="#2a4060", lw=1.0, ls="--")
    ax_mag.set_ylabel("Magnitud [dB]", color="#6a8ab8", fontsize=8,
                      fontfamily="monospace")
    ax_mag.set_title("Bode — L(s) = C(s)·G(s)", color="#8a9ab8",
                     fontsize=8, fontfamily="monospace", pad=6)

    # ── Fase ─────────────────────────────────────────────────────────────
    ax_ph.semilogx(omega_out, phase_deg, color="#ffa040", lw=1.8)
    ax_ph.axhline(-180, color="#2a4060", lw=1.0, ls="--")
    ax_ph.set_ylabel("Fase [°]", color="#6a8ab8", fontsize=8,
                     fontfamily="monospace")
    ax_ph.set_xlabel("Frecuencia [rad/s]", color="#6a8ab8", fontsize=8,
                     fontfamily="monospace")

    fig.tight_layout(pad=0.6)
    return fig


def calc_margins(L):
    """
    Devuelve (gm_db, pm_deg, wgm, wpm) usando control.margin.
    Maneja inf con seguridad.
    """
    try:
        gm, pm, wgm, wpm = control.margin(L)
    except Exception:
        return float("nan"), float("nan"), float("nan"), float("nan")

    # control.margin puede devolver inf cuando el margen no existe
    gm_db = 20 * np.log10(gm) if (np.isfinite(gm) and gm > 0) else float("inf")
    pm_deg = pm  if np.isfinite(pm)  else float("inf")
    wgm    = wgm if np.isfinite(wgm) else float("nan")
    wpm    = wpm if np.isfinite(wpm) else float("nan")
    return gm_db, pm_deg, wgm, wpm


col_bode, col_margins = st.columns([3, 2])

with col_bode:
    fig_bode = plot_bode(L_open)
    st.pyplot(fig_bode, use_container_width=True)
    plt.close(fig_bode)

with col_margins:
    gm_db, pm_deg, wgm, wpm = calc_margins(L_open)

    def fmt_margin(val, unit="", inf_str="∞"):
        if np.isnan(val):   return "—"
        if np.isinf(val):   return inf_str
        return f"{val:.3f} {unit}".strip()

    margins_html = f"""
    <div style="
        background:#12151c; border:1px solid #1e2535;
        border-left:3px solid #ffa040;
        border-radius:4px; padding:18px 20px;
        font-family:'JetBrains Mono',monospace;
        margin-top: 8px;
    ">
      <div style="color:#ffa040; font-size:0.68rem; letter-spacing:0.12em;
                  margin-bottom:14px;">MÁRGENES DE ESTABILIDAD</div>

      <div style="color:#4a6080; font-size:0.65rem; letter-spacing:0.1em;
                  margin:10px 0 4px;">MARGEN DE FASE</div>
      <div style="display:flex; justify-content:space-between;
                  border-bottom:1px solid #1a2030; padding:6px 0;">
        <span style="color:#6a8ab8; font-size:0.75rem;">PM</span>
        <span style="color:#e0ecff; font-size:0.9rem; font-weight:700;">
          {fmt_margin(pm_deg, '°')}</span>
      </div>
      <div style="display:flex; justify-content:space-between;
                  border-bottom:1px solid #1a2030; padding:6px 0;">
        <span style="color:#6a8ab8; font-size:0.75rem;">ω PM</span>
        <span style="color:#e0ecff; font-size:0.85rem; font-weight:700;">
          {fmt_margin(wpm, 'rad/s')}</span>
      </div>

      <div style="color:#4a6080; font-size:0.65rem; letter-spacing:0.1em;
                  margin:12px 0 4px;">MARGEN DE GANANCIA</div>
      <div style="display:flex; justify-content:space-between;
                  border-bottom:1px solid #1a2030; padding:6px 0;">
        <span style="color:#6a8ab8; font-size:0.75rem;">GM</span>
        <span style="color:#e0ecff; font-size:0.9rem; font-weight:700;">
          {fmt_margin(gm_db, 'dB')}</span>
      </div>
      <div style="display:flex; justify-content:space-between; padding:6px 0;">
        <span style="color:#6a8ab8; font-size:0.75rem;">ω GM</span>
        <span style="color:#e0ecff; font-size:0.85rem; font-weight:700;">
          {fmt_margin(wgm, 'rad/s')}</span>
      </div>
    </div>
    """
    st.markdown(margins_html, unsafe_allow_html=True)

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 7 — ESTABILIDAD
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">▸ 07 — DIAGNÓSTICO DE ESTABILIDAD</div>',
            unsafe_allow_html=True)

poles_cl = control.poles(CL)

TOL_ORIGIN = 1e-6   # umbral para considerar polo en el origen

def clasificar_estabilidad(poles):
    """
    Retorna: 'estable', 'critico', o 'inestable'
    - estable  : todos Re < 0
    - critico  : algún polo con Re ≈ 0 (en el origen o puramente imaginario),
                 sin polos con Re > 0
    - inestable: algún polo con Re > 0
    """
    if any(p.real > TOL_ORIGIN for p in poles):
        return "inestable"
    if any(abs(p.real) <= TOL_ORIGIN for p in poles):
        return "critico"
    return "estable"

resultado = clasificar_estabilidad(poles_cl)

if resultado == "estable":
    color_bg  = "#0a1a10"
    color_brd = "#00e676"
    color_txt = "#00e676"
    icono     = "&#10004;"
    estado    = "SISTEMA ESTABLE"
    detalle   = "Todos los polos del lazo cerrado tienen parte real negativa."
elif resultado == "critico":
    color_bg  = "#111000"
    color_brd = "#ffd740"
    color_txt = "#ffd740"
    icono     = "&#9888;"
    estado    = "ESTABILIDAD CRITICA"
    detalle   = "Existe al menos un polo en el origen o sobre el eje imaginario (Re ≈ 0)."
else:
    color_bg  = "#1a0a0a"
    color_brd = "#ff4466"
    color_txt = "#ff4466"
    icono     = "&#10008;"
    estado    = "SISTEMA INESTABLE"
    detalle   = "Existen polos con parte real > 0 en el lazo cerrado."

# ── Tabla de polos ────────────────────────────────────────────────────────────
filas_polos = ""
for p in poles_cl:
    re_str   = "{:.4f}".format(p.real)
    im_sign  = "+" if p.imag >= 0 else ""
    im_str   = "{:.4f}j".format(p.imag)
    polo_str = re_str + " " + im_sign + im_str

    if p.real > TOL_ORIGIN:
        signo  = "Re &gt; 0 &nbsp;&#10008;"
        c_fila = "#ff4466"
    elif abs(p.real) <= TOL_ORIGIN:
        signo  = "Re &asymp; 0 &nbsp;&#9888;"
        c_fila = "#ffd740"
    else:
        signo  = "Re &lt; 0 &nbsp;&#10004;"
        c_fila = "#00e676"

    filas_polos += (
        "<tr>"
        "<td style='padding:6px 14px; color:#8a9ab8; font-size:0.8rem;"
        " font-family:JetBrains Mono,monospace; border-bottom:1px solid #1a2030;'>"
        + polo_str +
        "</td>"
        "<td style='padding:6px 14px; color:" + c_fila + "; font-size:0.8rem;"
        " font-family:JetBrains Mono,monospace; text-align:right;"
        " border-bottom:1px solid #1a2030;'>" + signo + "</td>"
        "</tr>"
    )

n_poles  = len(poles_cl)
# altura: cabecera ~110px + fila header ~36px + cada fila ~38px + padding
iframe_h = 130 + 36 + n_poles * 42

stability_html = (
    "<html><body style='margin:0; padding:0; background:transparent;'>"
    "<div style='background:" + color_bg + "; border:2px solid " + color_brd + ";"
    " border-radius:6px; padding:20px 24px; font-family:JetBrains Mono,monospace;"
    " box-sizing:border-box;'>"

    "<div style='display:flex; align-items:center; gap:14px; margin-bottom:12px;'>"
    "<span style='font-size:2.2rem; color:" + color_txt + ";'>" + icono + "</span>"
    "<span style='font-size:1.25rem; font-weight:700; color:" + color_txt + ";"
    " letter-spacing:0.08em;'>" + estado + "</span>"
    "</div>"

    "<p style='color:#6a8ab8; font-size:0.75rem; margin:0 0 14px 0;'>" + detalle + "</p>"

    "<table style='border-collapse:collapse; width:100%;'>"
    "<tr style='border-bottom:2px solid #1e2535;'>"
    "<th style='padding:6px 14px; color:#4a6080; font-size:0.65rem;"
    " text-align:left; letter-spacing:0.1em; font-family:JetBrains Mono,monospace;'>"
    "POLO (lazo cerrado)</th>"
    "<th style='padding:6px 14px; color:#4a6080; font-size:0.65rem;"
    " text-align:right; letter-spacing:0.1em; font-family:JetBrains Mono,monospace;'>"
    "PARTE REAL</th>"
    "</tr>"
    + filas_polos +
    "</table>"
    "</div>"
    "</body></html>"
)

import streamlit.components.v1 as components
components.html(stability_html, height=iframe_h, scrolling=False)

st.markdown(
    '<p style="font-family:JetBrains Mono,monospace; font-size:0.62rem; '
    'color:#2a3a5a; text-align:center; margin-top:24px;">'
    'Control de Velocidad · Motor DC · Banda Transportadora · '
    'Encoder Hall · Retroalimentación Unitaria</p>',
    unsafe_allow_html=True
)