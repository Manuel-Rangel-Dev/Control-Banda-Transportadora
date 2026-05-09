# Control de Velocidad - Motor DC + Banda Transportadora

Proyecto integrador para analizar, simular y controlar la velocidad de una banda transportadora accionada por un motor DC con encoder Hall. El sistema combina una interfaz gráfica en Streamlit, un firmware para Arduino desarrollado con PlatformIO y herramientas de adquisición de datos en tiempo real.

## Descripción

La aplicación permite trabajar en dos niveles:

- **Modelado matemático:** Análisis del sistema en lazo cerrado, selección de planta, controladores P/PI/PD/PID, respuesta temporal, lugar de raíces, polos y ceros, diagramas de Bode y diagnóstico de estabilidad.
- **Conexión Arduino:** Comunicación serial con la placa, visualización de la velocidad real en RPM, comparación contra el modelo matemático, gráfica del error, cambio de setpoint y ajuste de controlador/ganancias sin detener el programa.

La variable controlada es la velocidad de la banda en **RPM**, medida mediante encoder Hall. El actuador se controla con PWM a través de un puente H L298N.

## Estructura Del Proyecto

```text
Proyecto_Integrador/
+-- Banda_GUI/
|   +-- platformio.ini
|   +-- src/
|       +-- main.cpp              # Firmware Arduino/PlatformIO
+-- GUI/
|   +-- GUI.py                    # Aplicación principal Streamlit
|   +-- hardware_tab.py           # Pestaña de conexión Arduino
|   +-- serial_banda.py           # Comunicación serial y registro CSV
|   +-- control_math.py           # Modelo matemático usado por la pestaña hardware
|   +-- requirements.txt
+-- Docs/
+-- LICENSE
+-- README.md

## Interfaz Gráfica

La interfaz se ejecuta con Streamlit y está organizada en dos pestañas.

### Modelado Matemático

Incluye:

- Setpoint de referencia en RPM.
- Selección de modelo de planta: primer orden o segundo orden.
- Controladores P, PI, PD y PID con ganancias configurables.
- Diagrama de bloques con retroalimentación unitaria.
- Respuesta temporal en lazo cerrado escalada a RPM.
- Especificaciones temporales: sobreimpulso, tiempo pico, tiempo de subida, tiempo de establecimiento y error estacionario.
- Lugar de raíces y regiones de estabilidad.
- Mapa de polos y ceros.
- Diagramas de Bode y margenes de estabilidad.
- Diagnóstico de estabilidad segun la ubicacion de los polos.

### Conexión Arduino

Incluye:

- Detección y selección del puerto serial.
- Botones para conectar, desconectar, iniciar, detener, limpiar datos y guardar CSV.
- Setpoint en RPM configurable en tiempo real.
- Selección de controlador P, PI, PD o PID.
- Ajuste de ganancias `Kp`, `Ki` y `Kd` sin recompilar el firmware.
- Gráfica superior con:
  - velocidad real medida,
  - setpoint,
  - respuesta del modelo matemático.
- Gráfica inferior del error:
  - `error = setpoint - RPM medida`.
- Indicadores instantáneos de RPM real, setpoint, error y PWM aplicado.

## Firmware PlatformIO

El firmware se encuentra en:

```text
Banda_GUI/src/main.cpp
```

La placa configurada actualmente es Arduino Uno:

```ini
[env:uno]
platform = atmelavr
board = uno
framework = arduino
monitor_speed = 115200
upload_speed = 115200
```

### Pines

| Elemento | Pin |
|---|---:|
| Encoder A | 2 |
| Encoder B | 3 |
| L298N IN1 | 8 |
| L298N IN2 | 9 |
| L298N ENA/PWM | 10 |

### Parámetros Del Encoder

```cpp
PPR motor = 34.02
Relación de reducción = 12.0
CPR = PPR motor * relación de reducción
Periodo de muestreo = 50 ms
```

## Protocolo Serial

La GUI envia comandos de texto terminados en salto de línea.

| Comando | Funcion |
|---|---|
| `START` | Inicia el control y la transmision de datos |
| `STOP` | Detiene el motor |
| `RESET` | Reinicia conteos e integrador |
| `SETPOINT:<rpm>` | Cambia el setpoint en RPM |
| `CTRL:P` | Selecciona controlador proporcional |
| `CTRL:PI` | Selecciona controlador proporcional-integral |
| `CTRL:PD` | Selecciona controlador proporcional-derivativo |
| `CTRL:PID` | Selecciona controlador PID |
| `GAINS:<kp>,<ki>,<kd>` | Actualiza las ganancias del controlador |

El firmware responde con datos CSV:

```text
tiempo_s,rpm_medida,setpoint_rpm,error_rpm,pwm,controlador
```

Ejemplo:

```text
1.250,86.42,90.00,3.58,218,PID
```

## Conversión Provisional RPM A PWM

El setpoint de usuario siempre se trabaja en **RPM**. Para obtener un PWM base aproximado, el firmware usa por ahora la relación experimental:

```text
RPM = 0.3997 * PWM + 3.004
```

Despejando:

```text
PWM = (RPM - 3.004) / 0.3997
```

Ese PWM base se usa como acción inicial o feed-forward. Luego el controlador P/PI/PD/PID suma una corrección según el error medido por el encoder.

## Modelos De Planta

### Primer Orden

```math
P(s) = \frac{17.4}{0.0583s + 1}
```

### Segundo Orden

```math
P(s) = \frac{4.199}{6.033 \times 10^{-6}s^2 + 0.01374s + 0.2354}
```

## Controladores

| Controlador | Función de transferencia | Parámetros |
|---|---|---|
| P | `C(s) = Kp` | `Kp` |
| PI | `C(s) = Kp + Ki/s` | `Kp`, `Ki` |
| PD | `C(s) = Kp + Kd*s` | `Kp`, `Kd` |
| PID | `C(s) = Kp + Ki/s + Kd*s` | `Kp`, `Ki`, `Kd` |

## Instalación

### Requisitos

- Python 3.9 o superior.
- VSCode.
- Extensión PlatformIO.
- Arduino Uno o placa compatible.
- Driver serial correspondiente a la placa, si aplica.

### Dependencias Python

Desde la carpeta `GUI`:

```powershell
cd "C:\Users\Manuel\Desktop\Universidad\Control Automático\VScode\Proyecto_Integrador\GUI"
pip install -r requirements.txt
```

Dependencias principales:

| Libreria | Uso |
|---|---|
| `streamlit` | Interfaz web |
| `numpy` | Cálculo numerico |
| `matplotlib` | Gráficas |
| `control` | Funciones de transferencia y análisis de control |
| `pyserial` | Comunicación con Arduino |

## Ejecución

### Ejecutar La GUI

Desde la carpeta `GUI`:

```powershell
streamlit run GUI.py
```

La aplicacion se abrira en:

```text
http://localhost:8501
```

### Compilar El Firmware

Desde la carpeta `Banda_GUI`:

```powershell
pio run
```

### Cargar El Firmware Al Arduino

Con la placa conectada por USB:

```powershell
pio run -t upload
```

También se puede hacer desde VSCode usando el boton **Upload** de PlatformIO.

## Flujo De Uso Recomendado

1. Conectar el Arduino por USB.
2. Cargar el firmware desde PlatformIO.
3. Ejecutar la GUI con Streamlit.
4. Abrir la pestaña **Conexion Arduino**.
5. Seleccionar el puerto serial y presionar **Conectar**.
6. Elegir setpoint, controlador y ganancias.
7. Presionar **START**.
8. Observar la velocidad real, la respuesta del modelo y el error.
9. Ajustar setpoint o ganancias en tiempo real.
10. Presionar **STOP** antes de desconectar.

## Datos Guardados

La pestaña de conexión puede guardar los ensayos en CSV con columnas:

```text
tiempo_s,rpm_medida,setpoint_rpm,error_rpm,pwm,controlador
```

Los archivos se guardan en la carpeta que se seleccione, reemplazando en:

```python
DATA_DIR = r"C:\Users\Manuel\Desktop\Universidad\Control Automático\VScode\Proyecto_Integrador\datos"
```

Que se encuentra en el archivo `serial_banda.py`.

## Pendientes Y Mejoras Futuras

- Ajustar ganancias iniciales recomendadas para cada controlador.
- Agregar límites de seguridad de RPM/PWM según el comportamiento de la banda.
- Documentar capturas finales de la interfaz.
- Agregar ejemplos de ensayos CSV.

## Licencia

Este proyecto se distribuye bajo licencia MIT. Consulta el archivo `LICENSE` para mas detalles.
