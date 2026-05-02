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

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Barlow:wght@400;600;700&display=swap');
  html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif;
    background-color: #0d0f14;
    color: #e0e6ef;
  }
  .stApp { background-color: #0d0f14; }
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
  .section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #00c8ff;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .ctrl-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #ffa040;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    margin-bottom: 4px;
  }
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
  .stRadio > label { color: #8a99b8 !important; font-size: 0.8rem; }
  .stRadio > div > label { color: #c0cce0 !important; }
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
    setpoint = st.slider("Setpoint (RPM)", min_value=60, max_value=120,
                         value=90, step=1, label_visibility="collapsed")
with col_sp2:
    st.markdown(
        f'<div style="text-align:right; padding-top:4px;">'
        f'<span class="setpoint-value">{setpoint}</span>'
        f'<span class="setpoint-unit"> RPM</span></div>',
        unsafe_allow_html=True)
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 2 — MODELO + GANANCIAS POR CONTROLADOR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">▸ 02 — CONFIGURACIÓN DEL SISTEMA</div>',
            unsafe_allow_html=True)

col_m, col_gap = st.columns([1, 3])
with col_m:
    st.markdown('<div class="setpoint-label">MODELO DE PLANTA</div>', unsafe_allow_html=True)
    modelo = st.radio("modelo", ["Primer orden", "Segundo orden"],
                      horizontal=True, label_visibility="collapsed")

st.markdown('<div class="setpoint-label" style="margin-top:12px;">GANANCIAS POR CONTROLADOR</div>',
            unsafe_allow_html=True)

# 4 controladores × sus parámetros
col_P, col_PI, col_PD, col_PID = st.columns(4)

with col_P:
    st.markdown('<div class="ctrl-label">P</div>', unsafe_allow_html=True)
    Kp_P = st.number_input("Kp_P", min_value=0.0, max_value=10000.0,
                            value=5.0, step=0.1, format="%.4f", label_visibility="collapsed")

with col_PI:
    st.markdown('<div class="ctrl-label">PI</div>', unsafe_allow_html=True)
    Kp_PI = st.number_input("Kp_PI", min_value=0.0, max_value=10000.0,
                             value=5.0, step=0.1, format="%.4f")
    Ki_PI = st.number_input("Ki_PI", min_value=0.0, max_value=10000.0,
                             value=2.0, step=0.1, format="%.4f")

with col_PD:
    st.markdown('<div class="ctrl-label">PD</div>', unsafe_allow_html=True)
    Kp_PD = st.number_input("Kp_PD", min_value=0.0, max_value=10000.0,
                             value=5.0, step=0.1, format="%.4f")
    Kd_PD = st.number_input("Kd_PD", min_value=0.0, max_value=10000.0,
                             value=0.5, step=0.1, format="%.4f")

with col_PID:
    st.markdown('<div class="ctrl-label">PID</div>', unsafe_allow_html=True)
    Kp_PID = st.number_input("Kp_PID", min_value=0.0, max_value=10000.0,
                              value=5.0, step=0.1, format="%.4f")
    Ki_PID = st.number_input("Ki_PID", min_value=0.0, max_value=10000.0,
                              value=2.0, step=0.1, format="%.4f")
    Kd_PID = st.number_input("Kd_PID", min_value=0.0, max_value=10000.0,
                              value=0.5, step=0.1, format="%.4f")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONTROL
# ══════════════════════════════════════════════════════════════════════════════
def build_plant(modelo):
    if modelo == "Primer orden":
        return control.TransferFunction([17.4], [0.0583, 1])
    return control.TransferFunction([4.199], [6.033e-6, 0.01374, 0.2354])

def build_controller(tipo, kp, ki=0, kd=0):
    if tipo == "P":
        return control.TransferFunction([kp], [1])
    elif tipo == "PI":
        return control.TransferFunction([kp, ki], [1, 0])
    elif tipo == "PD":
        return control.TransferFunction([kd, kp], [1])
    else:  # PID: Kp + Ki/s + Kd*s = (Kd*s^2 + Kp*s + Ki)/s
        return control.TransferFunction([kd, kp, ki], [1, 0])

def build_closed_loop(modelo, tipo, kp, ki=0, kd=0):
    G = build_plant(modelo)
    C = build_controller(tipo, kp, ki, kd)
    L = C * G
    CL = control.feedback(L, 1)
    return CL, L

def calc_step_specs(t, y, setpoint):
    yss  = y[-1]
    ymax = np.max(y)
    Mp   = max(0.0, (ymax - yss) / yss * 100) if yss > 0 else 0.0
    tp   = t[np.argmax(y)]
    try:
        i10 = np.where(y >= 0.1 * yss)[0][0]
        i90 = np.where(y >= 0.9 * yss)[0][0]
        tr  = t[i90] - t[i10]
    except IndexError:
        tr = float("nan")
    banda = 0.02 * yss
    ts = float("nan")
    for i in range(len(y) - 1, -1, -1):
        if abs(y[i] - yss) > banda:
            ts = t[i] if i + 1 < len(t) else t[-1]
            break
    ess     = abs(setpoint - yss)
    ess_pct = (ess / setpoint * 100) if setpoint != 0 else 0.0
    return Mp, tp, tr, ts, ess, ess_pct, yss

def calc_T_end(sys_cl, fallback=0.2):
    try:
        t_long = np.linspace(0, 5.0, 10000)
        t_tmp, y_tmp = control.step_response(sys_cl, T=t_long)
        yss = y_tmp[-1]
        if yss == 0:
            return fallback
        try:
            t10_idx = np.where(y_tmp >= 0.1 * yss)[0][0]
            t10 = t_tmp[t10_idx]
        except IndexError:
            t10 = 0.0
        try:
            t90_idx = np.where(y_tmp >= 0.9 * yss)[0][0]
            t90 = t_tmp[t90_idx]
        except IndexError:
            t90_idx = 0
            t90 = t_tmp[0]
        tau_visible = t90 - t10 if t90 > t10 else t90
        if tau_visible < 1e-3:
            banda5 = 0.05 * abs(yss)
            ts5_idx = 0
            for i in range(len(y_tmp) - 1, -1, -1):
                if abs(y_tmp[i] - yss) > banda5:
                    ts5_idx = i
                    break
            tau_lenta = t_tmp[ts5_idx] - t90 if ts5_idx > t90_idx else t90
            T_visual = max(t90 * 10, tau_lenta * 2.0, 0.01)
        else:
            banda = 0.02 * abs(yss)
            ts_idx = 0
            for i in range(len(y_tmp) - 1, -1, -1):
                if abs(y_tmp[i] - yss) > banda:
                    ts_idx = i
                    break
            ts_est = t_tmp[ts_idx]
            tp_idx = np.argmax(np.abs(y_tmp - yss))
            tp_est = t_tmp[tp_idx]
            T_visual = max(ts_est * 1.4, tp_est * 2.5, 1e-4)
        return float(np.clip(T_visual, 1e-3, 2.0))
    except Exception:
        return fallback

def calc_margins(L):
    try:
        gm, pm, wgm, wpm = control.margin(L)
    except Exception:
        return float("nan"), float("nan"), float("nan"), float("nan")
    gm_db = 20 * np.log10(gm) if (np.isfinite(gm) and gm > 0) else float("inf")
    pm_deg = pm  if np.isfinite(pm)  else float("inf")
    wgm    = wgm if np.isfinite(wgm) else float("nan")
    wpm    = wpm if np.isfinite(wpm) else float("nan")
    return gm_db, pm_deg, wgm, wpm

def fmt(val, unit="s", decimals=4):
    if np.isnan(val):
        return "—"
    return f"{val:.{decimals}f} {unit}"

def fmt_margin(val, unit="", inf_str="∞"):
    if np.isnan(val):  return "—"
    if np.isinf(val):  return inf_str
    return f"{val:.3f} {unit}".strip()

# ── Diccionario central de controladores ────────────────────────────────────
CONTROLLERS = {
    "P":   {"label": "Proporcional",             "kp": Kp_P,   "ki": 0,      "kd": 0,      "cs": f"C_P(s) = {Kp_P:.4f}"},
    "PI":  {"label": "Proporcional-Integral",    "kp": Kp_PI,  "ki": Ki_PI,  "kd": 0,      "cs": f"C_PI(s) = {Kp_PI:.4f} + {Ki_PI:.4f}/s"},
    "PD":  {"label": "Proporcional-Derivativo",  "kp": Kp_PD,  "ki": 0,      "kd": Kd_PD,  "cs": f"C_PD(s) = {Kp_PD:.4f} + {Kd_PD:.4f}·s"},
    "PID": {"label": "Proporcional-Integral-Derivativo", "kp": Kp_PID, "ki": Ki_PID, "kd": Kd_PID,
            "cs": f"C_PID(s) = {Kp_PID:.4f} + {Ki_PID:.4f}/s + {Kd_PID:.4f}·s"},
}

# Pre-construir todos los sistemas
systems = {}
for tipo, cfg in CONTROLLERS.items():
    try:
        CL, L = build_closed_loop(modelo, tipo, cfg["kp"], cfg["ki"], cfg["kd"])
        systems[tipo] = {"CL": CL, "L": L, "ok": True}
    except Exception as e:
        systems[tipo] = {"ok": False, "err": str(e)}

CTRL_COLORS = {"P": "#00c8ff", "PI": "#00e676", "PD": "#fcff34", "PID": "#d070ff"}
TOL_ORIGIN = 1e-6

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 3 — DIAGRAMA DE BLOQUES + EXPRESIONES C(s)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">▸ 03 — DIAGRAMA DE BLOQUES DEL SISTEMA</div>',
            unsafe_allow_html=True)

def texto_planta(mod):
    if mod == "Primer orden":
        return "G(s) = 17.4 / (0.0583s+1)"
    return "G(s) = 4.199 /\n(6.033e-6s²+0.01374s+0.2354)"

def draw_block_diagram(modelo):
    fig, ax = plt.subplots(figsize=(13, 3.2))
    fig.patch.set_facecolor("#0d0f14")
    ax.set_facecolor("#0d0f14")
    ax.set_xlim(0, 14); ax.set_ylim(0, 5); ax.axis("off")

    BG = "#12151c"; BORDER = "#2a3a5a"; ACC = "#00c8ff"
    WHITE = "#c8d8f0"; DIM = "#4a6080"; LINE = "#3a5070"
    GREEN = "#00e676"; RED = "#ff4460"

    def hline(x0, x1, y, color=LINE, lw=1.6):
        ax.plot([x0, x1], [y, y], color=color, lw=lw, solid_capstyle="round")
    def vline(x, y0, y1, color=LINE, lw=1.6):
        ax.plot([x, x], [y0, y1], color=color, lw=lw, solid_capstyle="round")
    def arrow_right(x, y, color=LINE):
        ax.annotate("", xy=(x, y), xytext=(x - 0.01, y),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6, mutation_scale=12))
    def label(x, y, txt, color=WHITE, fs=8, ha="center", va="center"):
        ax.text(x, y, txt, ha=ha, va=va, fontsize=fs, color=color,
                fontfamily="monospace", linespacing=1.4)
    def block(cx, cy, w, h, txt, sublabel=None, accent=False):
        ec = ACC if accent else BORDER
        ax.add_patch(plt.Rectangle((cx-w/2, cy-h/2), w, h,
                                   linewidth=1.8, edgecolor=ec, facecolor=BG, zorder=3))
        label(cx, cy + (0.18 if sublabel else 0), txt,
              color=ACC if accent else WHITE, fs=7.5)
        if sublabel:
            label(cx, cy - 0.38, sublabel, color=DIM, fs=6.2)
    def sumador(cx, cy, r=0.32):
        ax.add_patch(plt.Circle((cx, cy), r, color=BG, ec=BORDER, lw=1.8, zorder=3))
        label(cx, cy + 0.06, "+", color=GREEN, fs=11)
        label(cx - 0.04, cy - 0.21, "−", color=RED, fs=11)

    Y = 3.0; Yf = 1.4
    X_SUM = 2.0; X_C = 4.0; X_G = 6.8; X_L3 = 8.1; X_Y = 8.9

    label(0.5, Y + 0.5, "R(s)", color=ACC, fs=8.5)
    label(0.5, Y, f"{setpoint} RPM", color=WHITE, fs=7)
    hline(1.1, X_SUM - 0.32, Y); arrow_right(X_SUM - 0.32, Y)
    sumador(X_SUM, Y)
    hline(X_SUM + 0.32, X_C - 1.05, Y)
    label((X_SUM + 0.32 + X_C - 1.05) / 2, Y + 0.28, "e(t)", color=WHITE, fs=7)
    arrow_right(X_C - 1.05, Y)

    # Bloque C(s) — solo dice "C(s)"
    block(X_C, Y, 2.0, 1.05, "C(s)", sublabel="CONTROLADOR", accent=True)

    hline(X_C + 1.0, X_G - 1.15, Y)
    label((X_C + 1.0 + X_G - 1.15) / 2, Y + 0.28, "u(t)", color=WHITE, fs=7)
    arrow_right(X_G - 1.15, Y)
    block(X_G, Y, 2.25, 1.05, texto_planta(modelo), sublabel="PLANTA G(s)")
    hline(X_G + 1.125, X_L3, Y)
    label(X_Y + 0.3, Y + 0.45, "Y(s)", color=ACC, fs=8.5)
    label(X_Y + 0.3, Y, "ω [RPM]", color=WHITE, fs=7)
    hline(X_L3, X_Y + 0.05, Y); arrow_right(X_Y + 0.05, Y, color=ACC)
    vline(X_L3, Y, Yf); hline(X_SUM, X_L3, Yf)
    vline(X_SUM, Yf, Y - 0.32); arrow_right(X_SUM, Y - 0.32, color=LINE)
    label((X_SUM + X_L3) / 2, Yf - 0.28, "H(s) = 1  [retroalimentación unitaria]",
          color=WHITE, fs=7)
    plt.tight_layout(pad=0.2)
    return fig

fig_diag = draw_block_diagram(modelo)
st.pyplot(fig_diag, use_container_width=True)
plt.close(fig_diag)

# ── Expresiones C(s) debajo del diagrama ─────────────────────────────────────
st.markdown('<div class="setpoint-label" style="margin-top:6px; margin-bottom:8px;">FUNCIONES DE TRANSFERENCIA DE LOS CONTROLADORES</div>',
            unsafe_allow_html=True)
col_cs = st.columns(4)
for i, (tipo, cfg) in enumerate(CONTROLLERS.items()):
    color = CTRL_COLORS[tipo]
    with col_cs[i]:
        st.markdown(
            f"<div style='background:#12151c; border:1px solid #1e2535;"
            f" border-left:3px solid {color}; border-radius:4px;"
            f" padding:10px 14px; font-family:JetBrains Mono,monospace;'>"
            f"<div style='color:{color}; font-size:0.65rem; letter-spacing:0.1em;"
            f" margin-bottom:6px;'>{cfg['label'].upper()}</div>"
            f"<div style='color:#e0ecff; font-size:0.78rem;'>{cfg['cs']}</div>"
            f"</div>",
            unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 4 — RESPUESTA TEMPORAL (4 gráficas + especificaciones)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">▸ 04 — RESPUESTA TEMPORAL EN LAZO CERRADO</div>',
            unsafe_allow_html=True)

def plot_step(CL, tipo, setpoint):
    color = CTRL_COLORS[tipo]
    T_end = calc_T_end(CL)
    t_sim = np.linspace(0, T_end, 4000)
    t_out, y_out = control.step_response(CL, T=t_sim)
    y_rpm = y_out * setpoint

    fig, ax = plt.subplots(figsize=(5, 3.2))
    fig.patch.set_facecolor("#0d0f14")
    ax.set_facecolor("#12151c")
    ax.axhline(setpoint, color="#2a4060", lw=1.2, ls="--",
               label=f"Setpoint ({setpoint} RPM)")
    ax.axhspan(setpoint * 0.98, setpoint * 1.02,
               alpha=0.08, color=color, label="±2%")
    ax.plot(t_out, y_rpm, color=color, lw=2.0, label="y(t)")

    _ymin = float(np.nanmin(y_rpm))
    _ymax = float(np.nanmax(y_rpm))
    _ylo_base = min(0.0, _ymin, setpoint * 0.98)
    _yhi_base = max(_ymax, setpoint * 1.02)
    _padding = max(0.08 * (_yhi_base - _ylo_base), 0.05 * abs(setpoint), 1.0)
    _ylo = _ylo_base - _padding if _ylo_base < 0 else 0.0
    _yhi = _yhi_base + _padding
    ax.set_ylim(_ylo, _yhi)
    ax.set_xlim(0, T_end)
    ax.set_xlabel("Tiempo [s]", color="#B6B6B6", fontsize=7, fontfamily="monospace")
    ax.set_ylabel("Velocidad [RPM]", color=color, fontsize=7, fontfamily="monospace")
    ax.tick_params(colors="#B6B6B6", labelsize=6)
    for sp in ax.spines.values(): sp.set_edgecolor("#1e2535")
    ax.legend(fontsize=6, facecolor="#12151c", edgecolor="#2a3a5a", labelcolor="#8a9ab8")
    ax.grid(True, color="#2d3549", lw=0.5)
    fig.tight_layout(pad=0.5)
    return fig, t_out, y_rpm

def specs_card(t_out, y_rpm, setpoint, tipo):
    color = CTRL_COLORS[tipo]
    Mp, tp, tr, ts, ess, ess_pct, yss_rpm = calc_step_specs(t_out, y_rpm, setpoint)
    html = (
        f"<div style='background:#12151c; border:1px solid #1e2535;"
        f" border-left:3px solid {color}; border-radius:4px;"
        f" padding:12px 14px; font-family:JetBrains Mono,monospace;"
        f" margin-top:6px;'>"
        f"<div style='color:{color}; font-size:0.63rem; letter-spacing:0.12em;"
        f" margin-bottom:10px;'>ESPECIFICACIONES TEMPORALES</div>"
    )
    rows = [
        ("Mp",  f"{Mp:.2f} %"),
        ("tp",  fmt(tp)),
        ("tr",  fmt(tr)),
        ("ts",  fmt(ts)),
        ("y∞",  f"{yss_rpm:.3f} RPM"),
        ("ess", f"{ess:.3f} RPM | {ess_pct:.2f} %"),
    ]
    for i, (k, v) in enumerate(rows):
        border = "border-bottom:1px solid #1a2030;" if i < len(rows)-1 else ""
        ess_color = color
        if k == "ess":
            ess_color = "#ff6b6b" if ess_pct > 2 else "#00e676"
        val_color = ess_color if k == "ess" else "#e0ecff"
        html += (
            f"<div style='display:flex; justify-content:space-between;"
            f" {border} padding:5px 0;'>"
            f"<span style='color:#6a8ab8; font-size:0.72rem;'>{k}</span>"
            f"<span style='color:{val_color}; font-size:0.75rem;"
            f" font-weight:700;'>{v}</span></div>"
        )
    html += "</div>"
    return html

for fila, par in enumerate([["P", "PI"], ["PD", "PID"]]):
    cols_step = st.columns(2)
    for j, tipo in enumerate(par):
        with cols_step[j]:
            color = CTRL_COLORS[tipo]
            st.markdown(
                f"<div style='color:{color}; font-family:JetBrains Mono,monospace;"
                f" font-size:0.7rem; letter-spacing:0.1em;"
                f" margin-bottom:4px;'>CONTROLADOR {tipo}</div>",
                unsafe_allow_html=True)
            if systems[tipo]["ok"]:
                try:
                    fig_s, t_out, y_rpm = plot_step(systems[tipo]["CL"], tipo, setpoint)
                    st.pyplot(fig_s, use_container_width=True)
                    plt.close(fig_s)
                    st.markdown(specs_card(t_out, y_rpm, setpoint, tipo),
                                unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error(systems[tipo]["err"])
    if fila == 0:
        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 5 — LUGAR DE LAS RAICES Y REGIONES DE ESTABILIDAD
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">▸ 05 — LUGAR DE LAS RAICES Y REGIONES DE ESTABILIDAD</div>',
            unsafe_allow_html=True)

def _gain_limit(value):
    return float(max(10.0, abs(value) * 2.0, 1.0))

def _closed_loop_is_stable(tipo, kp, ki=0.0, kd=0.0):
    try:
        CL, _ = build_closed_loop(modelo, tipo, kp, ki, kd)
        poles = control.poles(CL)
        return bool(len(poles) > 0 and np.all(np.real(poles) < -TOL_ORIGIN))
    except Exception:
        return False

@st.cache_data(show_spinner=False)
def stability_grid_2d(modelo_cache, tipo, x_gain, y_gain, x_max, y_max, n, fixed_gain="", fixed_value=0.0):
    x_vals = np.linspace(0.0, float(x_max), int(n))
    y_vals = np.linspace(0.0, float(y_max), int(n))
    Z = np.zeros((len(y_vals), len(x_vals)))

    for iy, yv in enumerate(y_vals):
        for ix, xv in enumerate(x_vals):
            gains = {"Kp": 0.0, "Ki": 0.0, "Kd": 0.0}
            gains[x_gain] = float(xv)
            gains[y_gain] = float(yv)
            if fixed_gain:
                gains[fixed_gain] = float(fixed_value)

            try:
                CL, _ = build_closed_loop(modelo_cache, tipo, gains["Kp"], gains["Ki"], gains["Kd"])
                poles = control.poles(CL)
                Z[iy, ix] = 1.0 if len(poles) > 0 and np.all(np.real(poles) < -TOL_ORIGIN) else 0.0
            except Exception:
                Z[iy, ix] = 0.0

    return x_vals, y_vals, Z

@st.cache_data(show_spinner=False)
def stability_grid_3d_pid(modelo_cache, kp_max, ki_max, kd_max, n):
    kp_vals = np.linspace(0.0, float(kp_max), int(n))
    ki_vals = np.linspace(0.0, float(ki_max), int(n))
    kd_vals = np.linspace(0.0, float(kd_max), int(n))
    pts = []
    stable = []

    for kp in kp_vals:
        for ki in ki_vals:
            for kd in kd_vals:
                try:
                    CL, _ = build_closed_loop(modelo_cache, "PID", kp, ki, kd)
                    poles = control.poles(CL)
                    ok = len(poles) > 0 and np.all(np.real(poles) < -TOL_ORIGIN)
                except Exception:
                    ok = False
                pts.append((kp, ki, kd))
                stable.append(ok)

    return np.array(pts), np.array(stable, dtype=bool)

def plot_root_locus_p(kp_max, n):
    color = CTRL_COLORS["P"]
    G = build_plant(modelo)
    gains = np.linspace(0.0, float(kp_max), int(n))

    fig, ax = plt.subplots(figsize=(5, 3.4))
    fig.patch.set_facecolor("#0d0f14")
    ax.set_facecolor("#12151c")
    ax.axhline(0, color="#2a3a5a", lw=1.0)
    ax.axvline(0, color="#2a3a5a", lw=1.0)

    first = True
    for k in gains:
        try:
            CL = control.feedback(k * G, 1)
            poles = control.poles(CL)
            ax.scatter(np.real(poles), np.imag(poles), s=8, color=color,
                       alpha=0.55, label="Polos CL" if first else None)
            first = False
        except Exception:
            pass

    try:
        p0 = control.poles(G)
        ax.scatter(np.real(p0), np.imag(p0), marker="x", s=70,
                   color="#ff4466", linewidths=2.0, label="Polos OL")
    except Exception:
        pass

    ax.set_title("P — Lugar de las raices", color=color, fontsize=8,
                 fontfamily="monospace", pad=4)
    ax.set_xlabel("Re", color="#B6B6B6", fontsize=7, fontfamily="monospace")
    ax.set_ylabel("Im", color=color, fontsize=7, fontfamily="monospace")
    ax.tick_params(colors="#B6B6B6", labelsize=6)
    ax.grid(True, color="#2d3549", lw=0.5, ls="--")
    for sp in ax.spines.values(): sp.set_edgecolor("#1e2535")
    ax.legend(fontsize=6, facecolor="#12151c", edgecolor="#2a3a5a", labelcolor="#8a9ab8")
    fig.tight_layout(pad=0.5)
    return fig

def plot_stability_plane(tipo, x_gain, y_gain, x_max, y_max, n, fixed_gain="", fixed_value=0.0):
    from matplotlib.colors import ListedColormap

    color = CTRL_COLORS[tipo]
    x_vals, y_vals, Z = stability_grid_2d(modelo, tipo, x_gain, y_gain, x_max, y_max, n, fixed_gain, fixed_value)
    fig, ax = plt.subplots(figsize=(5, 3.4))
    fig.patch.set_facecolor("#0d0f14")
    ax.set_facecolor("#12151c")

    cmap = ListedColormap(["#3a1018", "#0d3a24"])
    ax.imshow(Z, origin="lower", aspect="auto",
              extent=[x_vals[0], x_vals[-1], y_vals[0], y_vals[-1]],
              cmap=cmap, vmin=0, vmax=1, alpha=0.88)

    if np.any((Z > 0.0) & (Z < 1.0)) or len(np.unique(Z)) > 1:
        ax.contour(x_vals, y_vals, Z, levels=[0.5], colors=[color], linewidths=1.5)

    ax.set_title(f"{tipo} — Estabilidad por ganancias", color=color, fontsize=8,
                 fontfamily="monospace", pad=4)
    ax.set_xlabel(x_gain, color="#B6B6B6", fontsize=7, fontfamily="monospace")
    ax.set_ylabel(y_gain, color=color, fontsize=7, fontfamily="monospace")
    ax.tick_params(colors="#B6B6B6", labelsize=6)
    ax.grid(True, color="#2d3549", lw=0.35, ls="--", alpha=0.5)
    for sp in ax.spines.values(): sp.set_edgecolor("#1e2535")

    stable_patch = mpatches.Patch(color="#0d3a24", label="Estable")
    unstable_patch = mpatches.Patch(color="#3a1018", label="Inestable")
    ax.legend(handles=[stable_patch, unstable_patch], fontsize=6,
              facecolor="#12151c", edgecolor="#2a3a5a", labelcolor="#8a9ab8")
    fig.tight_layout(pad=0.5)
    return fig

def plot_pid_3d(kp_max, ki_max, kd_max, n):
    color = CTRL_COLORS["PID"]
    pts, stable = stability_grid_3d_pid(modelo, kp_max, ki_max, kd_max, n)

    fig = plt.figure(figsize=(5, 3.8))
    fig.patch.set_facecolor("#0d0f14")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#12151c")

    unstable_pts = pts[~stable]
    stable_pts = pts[stable]
    if len(unstable_pts):
        ax.scatter(unstable_pts[:, 0], unstable_pts[:, 1], unstable_pts[:, 2],
                   c="#ff4466", s=10, alpha=0.18, label="Inestable")
    if len(stable_pts):
        ax.scatter(stable_pts[:, 0], stable_pts[:, 1], stable_pts[:, 2],
                   c=color, s=14, alpha=0.78, label="Estable")

    ax.set_title("PID — Región 3D de estabilidad", color=color, fontsize=8,
                 fontfamily="monospace", pad=8)
    ax.set_xlabel("Kp", color="#B6B6B6", fontsize=7, fontfamily="monospace")
    ax.set_ylabel("Ki", color="#B6B6B6", fontsize=7, fontfamily="monospace")
    ax.set_zlabel("Kd", color="#B6B6B6", fontsize=7, fontfamily="monospace")
    ax.tick_params(colors="#B6B6B6", labelsize=6)
    ax.xaxis.pane.set_facecolor("#12151c")
    ax.yaxis.pane.set_facecolor("#12151c")
    ax.zaxis.pane.set_facecolor("#12151c")
    ax.xaxis.pane.set_edgecolor("#1e2535")
    ax.yaxis.pane.set_edgecolor("#1e2535")
    ax.zaxis.pane.set_edgecolor("#1e2535")
    ax.grid(True, color="#2d3549")
    ax.legend(fontsize=6, facecolor="#12151c", edgecolor="#2a3a5a", labelcolor="#8a9ab8")
    fig.tight_layout(pad=0.5)
    return fig

st.markdown('<div class="setpoint-label">RANGOS PARA EL BARRIDO DE GANANCIAS</div>',
            unsafe_allow_html=True)
col_rl1, col_rl2, col_rl3, col_rl4 = st.columns(4)
with col_rl1:
    kp_scan_max = st.number_input("Kp máximo", min_value=0.1, max_value=10000.0,
                                  value=_gain_limit(max(Kp_P, Kp_PI, Kp_PD, Kp_PID)),
                                  step=1.0, format="%.3f")
with col_rl2:
    ki_scan_max = st.number_input("Ki máximo", min_value=0.1, max_value=10000.0,
                                  value=_gain_limit(max(Ki_PI, Ki_PID)),
                                  step=1.0, format="%.3f")
with col_rl3:
    kd_scan_max = st.number_input("Kd máximo", min_value=0.1, max_value=10000.0,
                                  value=_gain_limit(max(Kd_PD, Kd_PID)),
                                  step=0.1, format="%.3f")
with col_rl4:
    grid_n = st.slider("Resolución 2D", min_value=25, max_value=100,
                       value=55, step=5)

cols_rl_top = st.columns(2)
with cols_rl_top[0]:
    st.markdown(f"<div style='color:{CTRL_COLORS['P']}; font-family:JetBrains Mono,monospace;"
                f" font-size:0.7rem; letter-spacing:0.1em; margin-bottom:4px;'>CONTROLADOR P</div>",
                unsafe_allow_html=True)
    fig_rl_p = plot_root_locus_p(kp_scan_max, 180)
    st.pyplot(fig_rl_p, use_container_width=True)
    plt.close(fig_rl_p)

with cols_rl_top[1]:
    st.markdown(f"<div style='color:{CTRL_COLORS['PI']}; font-family:JetBrains Mono,monospace;"
                f" font-size:0.7rem; letter-spacing:0.1em; margin-bottom:4px;'>CONTROLADOR PI</div>",
                unsafe_allow_html=True)
    fig_rl_pi = plot_stability_plane("PI", "Kp", "Ki", kp_scan_max, ki_scan_max, grid_n)
    st.pyplot(fig_rl_pi, use_container_width=True)
    plt.close(fig_rl_pi)

st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

cols_rl_bottom = st.columns(2)
with cols_rl_bottom[0]:
    st.markdown(f"<div style='color:{CTRL_COLORS['PD']}; font-family:JetBrains Mono,monospace;"
                f" font-size:0.7rem; letter-spacing:0.1em; margin-bottom:4px;'>CONTROLADOR PD</div>",
                unsafe_allow_html=True)
    fig_rl_pd = plot_stability_plane("PD", "Kp", "Kd", kp_scan_max, kd_scan_max, grid_n)
    st.pyplot(fig_rl_pd, use_container_width=True)
    plt.close(fig_rl_pd)

with cols_rl_bottom[1]:
    st.markdown(f"<div style='color:{CTRL_COLORS['PID']}; font-family:JetBrains Mono,monospace;"
                f" font-size:0.7rem; letter-spacing:0.1em; margin-bottom:4px;'>CONTROLADOR PID</div>",
                unsafe_allow_html=True)
    pid_view = st.radio("Vista PID", ["3D", "Plano 2D con K fija"],
                        horizontal=True, label_visibility="collapsed")
    if pid_view == "3D":
        pid_grid_n = st.slider("Resolución 3D PID", min_value=6, max_value=20,
                               value=12, step=2)
        fig_rl_pid = plot_pid_3d(kp_scan_max, ki_scan_max, kd_scan_max, pid_grid_n)
    else:
        fixed_gain = st.selectbox("Ganancia fija", ["Kp", "Ki", "Kd"])
        fixed_max = {"Kp": kp_scan_max, "Ki": ki_scan_max, "Kd": kd_scan_max}[fixed_gain]
        fixed_default = {"Kp": Kp_PID, "Ki": Ki_PID, "Kd": Kd_PID}[fixed_gain]
        fixed_value = st.slider(f"Valor fijo de {fixed_gain}", 0.0, float(fixed_max),
                                float(min(fixed_default, fixed_max)))
        free_gains = [g for g in ["Kp", "Ki", "Kd"] if g != fixed_gain]
        max_by_gain = {"Kp": kp_scan_max, "Ki": ki_scan_max, "Kd": kd_scan_max}
        fig_rl_pid = plot_stability_plane("PID", free_gains[0], free_gains[1],
                                          max_by_gain[free_gains[0]],
                                          max_by_gain[free_gains[1]],
                                          grid_n, fixed_gain, fixed_value)
    st.pyplot(fig_rl_pid, use_container_width=True)
    plt.close(fig_rl_pid)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 6 — MAPA DE POLOS Y CEROS (4 mapas)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">▸ 06 — MAPA DE POLOS Y CEROS (LAZO CERRADO)</div>',
            unsafe_allow_html=True)

def plot_poles_zeros(sys_cl, tipo):
    from matplotlib.lines import Line2D
    color = CTRL_COLORS[tipo]
    poles = control.poles(sys_cl)
    zeros = control.zeros(sys_cl)

    fig, ax = plt.subplots(figsize=(5, 3.5))
    fig.patch.set_facecolor("#0d0f14")
    ax.set_facecolor("#12151c")
    ax.axhline(0, color="#2a3a5a", lw=1.0)
    ax.axvline(0, color="#2a3a5a", lw=1.0)
    ax.grid(True, color="#2d3549", lw=0.5, ls="--")

    for p in poles:
        ax.plot(p.real, p.imag, "x", color="#ff4466",
                markersize=10, markeredgewidth=2.2, zorder=5)
        ax.annotate(f"{p.real:.1f}{'+' if p.imag>=0 else ''}{p.imag:.1f}j",
                    xy=(p.real, p.imag), xytext=(5, 6),
                    textcoords="offset points", fontsize=6,
                    color="#ff8899", fontfamily="monospace")
    for z in zeros:
        ax.plot(z.real, z.imag, "o", color="#00e676",
                markersize=8, markerfacecolor="none",
                markeredgewidth=2.0, zorder=5)
        ax.annotate(f"{z.real:.1f}{'+' if z.imag>=0 else ''}{z.imag:.1f}j",
                    xy=(z.real, z.imag), xytext=(5, 6),
                    textcoords="offset points", fontsize=6,
                    color="#00e676", fontfamily="monospace")

    legend_elem = [
        Line2D([0],[0], marker="x", color="#ff4466", lw=0,
               markersize=8, markeredgewidth=2.2, label="Polos"),
        Line2D([0],[0], marker="o", color="#00e676", lw=0,
               markersize=7, markerfacecolor="none",
               markeredgewidth=2.0, label="Ceros"),
    ]
    ax.legend(handles=legend_elem, fontsize=6, facecolor="#12151c",
              edgecolor="#2a3a5a", labelcolor="#8a9ab8")
    ax.set_xlabel("Re", color="#4AA4D9", fontsize=7, fontfamily="monospace")
    ax.set_ylabel("Im", color="#4AA4D9", fontsize=7, fontfamily="monospace")
    ax.tick_params(colors="#B6B6B6", labelsize=6)
    for sp in ax.spines.values(): sp.set_edgecolor("#1e2535")
    fig.tight_layout(pad=0.5)
    return fig

for fila, par in enumerate([["P", "PI"], ["PD", "PID"]]):
    cols_pz = st.columns(2)
    for j, tipo in enumerate(par):
        with cols_pz[j]:
            color = CTRL_COLORS[tipo]
            st.markdown(
                f"<div style='color:{color}; font-family:JetBrains Mono,monospace;"
                f" font-size:0.7rem; letter-spacing:0.1em;"
                f" margin-bottom:4px;'>CONTROLADOR {tipo}</div>",
                unsafe_allow_html=True)
            if systems[tipo]["ok"]:
                try:
                    fig_pz = plot_poles_zeros(systems[tipo]["CL"], tipo)
                    st.pyplot(fig_pz, use_container_width=True)
                    plt.close(fig_pz)
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error(systems[tipo]["err"])
    if fila == 0:
        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 7 — BODE + MÁRGENES (4 diagramas)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">▸ 07 — DIAGRAMA DE BODE Y MÁRGENES (LAZO ABIERTO)</div>',
            unsafe_allow_html=True)

def plot_bode_single(L, tipo):
    color = CTRL_COLORS[tipo]
    omega = np.logspace(-1, 6, 2000)
    mag, phase, omega_out = control.bode(L, omega, plot=False)
    mag_db    = 20 * np.log10(np.abs(mag) + 1e-12)
    phase_deg = np.degrees(phase)

    fig, (ax_mag, ax_ph) = plt.subplots(2, 1, figsize=(5, 4.2), sharex=True)
    fig.patch.set_facecolor("#0d0f14")
    for ax in (ax_mag, ax_ph):
        ax.set_facecolor("#12151c")
        ax.grid(True, which="both", color="#2d3549", lw=0.5, ls="--")
        ax.tick_params(colors="#B6B6B6", labelsize=6)
        for sp in ax.spines.values(): sp.set_edgecolor("#1e2535")
    ax_mag.semilogx(omega_out, mag_db, color=color, lw=1.6)
    ax_mag.axhline(0, color="#2a4060", lw=1.0, ls="--")
    ax_mag.set_ylabel("Mag [dB]", color=color, fontsize=7, fontfamily="monospace")
    ax_mag.set_title(f"Bode — {tipo}", color=color, fontsize=7,
                     fontfamily="monospace", pad=4)
    ax_ph.semilogx(omega_out, phase_deg, color="#ffa040", lw=1.6)
    ax_ph.axhline(-180, color="#2a4060", lw=1.0, ls="--")
    ax_ph.set_ylabel("Fase [°]", color="#ffa040", fontsize=7, fontfamily="monospace")
    ax_ph.set_xlabel("ω [rad/s]", color="#B6B6B6", fontsize=7, fontfamily="monospace")
    fig.tight_layout(pad=0.5)
    return fig

def margins_card(L, tipo):
    color = CTRL_COLORS[tipo]
    gm_db, pm_deg, wgm, wpm = calc_margins(L)
    html = (
        f"<div style='background:#12151c; border:1px solid #1e2535;"
        f" border-left:3px solid {color}; border-radius:4px;"
        f" padding:12px 14px; font-family:JetBrains Mono,monospace;"
        f" margin-top:6px;'>"
        f"<div style='color:{color}; font-size:0.63rem; letter-spacing:0.12em;"
        f" margin-bottom:10px;'>MÁRGENES DE ESTABILIDAD</div>"
    )
    rows = [
        ("PM",   fmt_margin(pm_deg, "°")),
        ("ω PM", fmt_margin(wpm,    "rad/s")),
        ("GM",   fmt_margin(gm_db,  "dB")),
        ("ω GM", fmt_margin(wgm,    "rad/s")),
    ]
    for i, (k, v) in enumerate(rows):
        border = "border-bottom:1px solid #1a2030;" if i < len(rows)-1 else ""
        html += (
            f"<div style='display:flex; justify-content:space-between;"
            f" {border} padding:5px 0;'>"
            f"<span style='color:#6a8ab8; font-size:0.72rem;'>{k}</span>"
            f"<span style='color:#e0ecff; font-size:0.75rem;"
            f" font-weight:700;'>{v}</span></div>"
        )
    html += "</div>"
    return html

for fila, par in enumerate([["P", "PI"], ["PD", "PID"]]):
    cols_bode = st.columns(2)
    for j, tipo in enumerate(par):
        with cols_bode[j]:
            color = CTRL_COLORS[tipo]
            st.markdown(
                f"<div style='color:{color}; font-family:JetBrains Mono,monospace;"
                f" font-size:0.7rem; letter-spacing:0.1em;"
                f" margin-bottom:4px;'>CONTROLADOR {tipo}</div>",
                unsafe_allow_html=True)
            if systems[tipo]["ok"]:
                try:
                    fig_b = plot_bode_single(systems[tipo]["L"], tipo)
                    st.pyplot(fig_b, use_container_width=True)
                    plt.close(fig_b)
                    st.markdown(margins_card(systems[tipo]["L"], tipo),
                                unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error(systems[tipo]["err"])
    if fila == 0:
        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 8 — ESTABILIDAD (4 diagnósticos)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">▸ 08 — DIAGNÓSTICO DE ESTABILIDAD</div>',
            unsafe_allow_html=True)

def clasificar_estabilidad(poles):
    if any(p.real > TOL_ORIGIN for p in poles):
        return "inestable"
    if any(abs(p.real) <= TOL_ORIGIN for p in poles):
        return "critico"
    return "estable"

def stability_card(CL, tipo, n_poles_max):
    poles_cl = control.poles(CL)
    resultado = clasificar_estabilidad(poles_cl)
    if resultado == "estable":
        cb="#0a1a10"; cbrd="#00e676"; ct="#00e676"
        icono="&#10004;"; estado="ESTABLE"
        detalle="Todos Re &lt; 0"
    elif resultado == "critico":
        cb="#111000"; cbrd="#ffd740"; ct="#ffd740"
        icono="&#9888;"; estado="CRÍTICO"
        detalle="Re &asymp; 0 detectado"
    else:
        cb="#1a0a0a"; cbrd="#ff4466"; ct="#ff4466"
        icono="&#10008;"; estado="INESTABLE"
        detalle="Re &gt; 0 detectado"

    filas = ""
    for p in poles_cl:
        re_s = "{:.3f}".format(p.real)
        im_s = ("+" if p.imag >= 0 else "") + "{:.3f}j".format(p.imag)
        polo_str = re_s + im_s
        if p.real > TOL_ORIGIN:
            sig="Re&gt;0 &#10008;"; cf="#ff4466"
        elif abs(p.real) <= TOL_ORIGIN:
            sig="Re≈0 &#9888;"; cf="#ffd740"
        else:
            sig="Re&lt;0 &#10004;"; cf="#00e676"
        filas += (
            "<tr>"
            "<td style='padding:3px 8px; color:#8a9ab8; font-size:0.68rem;"
            " font-family:JetBrains Mono,monospace; border-bottom:1px solid #1a2030;'>"
            + polo_str + "</td>"
            "<td style='padding:3px 8px; color:" + cf + "; font-size:0.68rem;"
            " font-family:JetBrains Mono,monospace; text-align:right;"
            " border-bottom:1px solid #1a2030;'>" + sig + "</td></tr>"
        )

    n = len(poles_cl)
    h = 140 + 28 + n * 32
    html = (
        "<html><body style='margin:0;padding:0;background:transparent;'>"
        "<div style='background:" + cb + ";border:2px solid " + cbrd + ";"
        "border-radius:6px;padding:14px 16px;font-family:JetBrains Mono,monospace;"
        "box-sizing:border-box;'>"
        "<div style='display:flex;align-items:center;gap:10px;margin-bottom:8px;'>"
        "<span style='font-size:1.6rem;color:" + ct + ";'>" + icono + "</span>"
        "<span style='font-size:0.95rem;font-weight:700;color:" + ct + ";"
        "letter-spacing:0.06em;'>" + estado + "</span></div>"
        "<p style='color:#6a8ab8;font-size:0.68rem;margin:0 0 10px 0;'>" + detalle + "</p>"
        "<table style='border-collapse:collapse;width:100%;'>"
        "<tr style='border-bottom:2px solid #1e2535;'>"
        "<th style='padding:3px 8px;color:#4a6080;font-size:0.6rem;"
        "text-align:left;font-family:JetBrains Mono,monospace;'>POLO</th>"
        "<th style='padding:3px 8px;color:#4a6080;font-size:0.6rem;"
        "text-align:right;font-family:JetBrains Mono,monospace;'>Re</th>"
        "</tr>" + filas +
        "</table></div></body></html>"
    )
    return html, h

import streamlit.components.v1 as components

# Calcular altura máxima para alinear los iframes
max_poles = max(
    len(control.poles(systems[t]["CL"])) for t in ["P","PI","PD","PID"]
    if systems[t]["ok"]
)

for fila, par in enumerate([["P", "PI"], ["PD", "PID"]]):
    cols_stab = st.columns(2)
    for j, tipo in enumerate(par):
        with cols_stab[j]:
            color = CTRL_COLORS[tipo]
            st.markdown(
                f"<div style='color:{color}; font-family:JetBrains Mono,monospace;"
                f" font-size:0.7rem; letter-spacing:0.1em;"
                f" margin-bottom:4px;'>CONTROLADOR {tipo}</div>",
                unsafe_allow_html=True)
            if systems[tipo]["ok"]:
                html_s, h_s = stability_card(systems[tipo]["CL"], tipo, max_poles)
                components.html(html_s, height=h_s, scrolling=False)
            else:
                st.error(systems[tipo]["err"])
    if fila == 0:
        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

st.markdown(
    '<p style="font-family:JetBrains Mono,monospace; font-size:0.62rem; '
    'color:#2a3a5a; text-align:center; margin-top:24px;">'
    'Control de Velocidad · Motor DC · Banda Transportadora · '
    'Encoder Hall · Retroalimentación Unitaria</p>',
    unsafe_allow_html=True)
