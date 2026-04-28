# ⚙ Control de Velocidad — Motor DC + Banda Transportadora

Dashboard interactivo para el análisis y diseño de controladores de velocidad de un motor DC acoplado a una banda transportadora, construido con **Streamlit** y la librería **python-control**.

---

## 📋 Descripción

Este proyecto implementa una interfaz gráfica profesional tipo dashboard de ingeniería para analizar el comportamiento de un sistema de control de velocidad en lazo cerrado. La variable controlada es la velocidad en RPM, medida mediante encoder Hall con retroalimentación unitaria.

El usuario puede seleccionar el modelo de la planta, el tipo de controlador y sus ganancias, y observar en tiempo real cómo cambian la respuesta temporal, los polos y ceros, el diagrama de Bode y el diagnóstico de estabilidad del sistema.

---

## 🖥 Interfaz

La aplicación se organiza en una sola pantalla sin navegación entre páginas:

| Bloque | Contenido |
|--------|-----------|
| **01 Setpoint** | Slider de referencia de velocidad (60–120 RPM) |
| **02 Configuración** | Selección de modelo de planta y tipo de controlador con campos de ganancia |
| **03 Diagrama de bloques** | Diagrama visual C(s) → G(s) con retroalimentación unitaria |
| **04 Respuesta temporal** | Gráfica al escalón escalada en RPM + especificaciones (Mp, tr, tp, ts, ess) |
| **05 Polos y ceros** | Mapa en el plano complejo con valores numéricos |
| **06 Diagrama de Bode** | Magnitud y fase del lazo abierto L(s) = C(s)·G(s) + márgenes |
| **07 Estabilidad** | Diagnóstico por color: estable / crítico / inestable con tabla de polos |

---

## 🔧 Modelos de planta disponibles

**Primer orden (modelo aproximado):**

$$G(s) = \frac{17.4}{0.0583s + 1}$$

**Segundo orden:**

$$G(s) = \frac{4.199}{6.033 \times 10^{-6}s^2 + 0.01374s + 0.2354}$$

---

## 🎛 Controladores disponibles

| Controlador | Función de transferencia | Parámetros |
|-------------|--------------------------|------------|
| **P** | $C(s) = K_p$ | Kp |
| **PI** | $C(s) = K_p + \frac{K_i}{s}$ | Kp, Ki |
| **PD** | $C(s) = K_p + K_d s$ | Kp, Kd |

---

## 📊 Análisis incluidos

- **Respuesta al escalón** en lazo cerrado escalada al setpoint en RPM, con eje temporal adaptativo que ajusta automáticamente el rango para mostrar el transitorio con claridad.
- **Especificaciones temporales:** sobreimpulso Mp (%), tiempo pico tp, tiempo de subida tr, tiempo de establecimiento al 2% ts, y error en estado estacionario ess.
- **Mapa de polos y ceros** del sistema en lazo cerrado con valores complejos.
- **Diagrama de Bode** del lazo abierto con margen de fase (PM) y margen de ganancia (GM).
- **Diagnóstico de estabilidad** basado en la parte real de los polos:
  - 🟢 **Estable** — todos los polos con Re < 0
  - 🟡 **Estabilidad crítica** — algún polo con Re ≈ 0
  - 🔴 **Inestable** — algún polo con Re > 0

---

## 🚀 Instalación y ejecución

### Requisitos

- Python 3.9 o superior

### Instalar dependencias

```bash
pip install streamlit numpy matplotlib control
```

### Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en el navegador en `http://localhost:8501`.

---

## 📁 Estructura del proyecto

```
.
├── app.py          # Aplicación principal (única entrada)
└── README.md
```

---

## 📦 Dependencias

| Librería | Uso |
|----------|-----|
| `streamlit` | Interfaz web interactiva |
| `numpy` | Cálculo numérico y vectores de tiempo |
| `matplotlib` | Gráficas embebidas (Bode, escalón, polos/ceros, diagrama de bloques) |
| `control` | Funciones de transferencia, lazo cerrado, respuesta al escalón, márgenes |

---

## 📐 Detalles técnicos

- Todo el análisis se realiza sobre el **sistema en lazo cerrado** $T(s) = \frac{C(s)G(s)}{1 + C(s)G(s)}$.
- El diagrama de Bode se calcula sobre el **lazo abierto** $L(s) = C(s)G(s)$.
- Los márgenes de estabilidad se obtienen con `control.margin()`.
- El eje temporal de la respuesta se ajusta automáticamente estimando $t_s$ con una simulación previa en un rango largo (0–5 s) y añadiendo un 40% de margen visual.
- Las ganancias del controlador no tienen límite superior fijo; se ingresan como valores numéricos directamente.

---

## 🖼 Capturas

> Agrega aquí capturas de pantalla de la interfaz ejecutándose (`screenshot.png`).

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.
