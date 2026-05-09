# Control de Velocidad - Motor DC + Banda Transportadora

Proyecto integrador para analizar, simular y controlar la velocidad de una banda transportadora accionada por un motor DC con encoder Hall. El sistema combina una interfaz grafica de escritorio en Python, un firmware para Arduino desarrollado con PlatformIO y herramientas de adquisicion de datos en tiempo real.

## Descripcion

La aplicacion permite trabajar en dos niveles:

- **Modelado matematico:** analisis de la respuesta temporal en lazo cerrado para la planta, controlador y ganancias seleccionadas.
- **Conexion Arduino:** comunicacion serial con la placa, visualizacion de la velocidad real en RPM, comparacion contra el modelo matematico, grafica del error, cambio de setpoint y ajuste de controlador/ganancias sin detener el programa ni recargar la interfaz.

La variable controlada es la velocidad de la banda en **RPM**, medida mediante encoder Hall. El actuador se controla con PWM a traves de un puente H L298N.

## Estructura Del Proyecto

```text
Proyecto_Integrador/
+-- Banda_GUI/
|   +-- platformio.ini
|   +-- src/
|       +-- main.cpp              # Firmware Arduino/PlatformIO
+-- GUI/
|   +-- GUI.py                    # Aplicacion principal Tkinter + Matplotlib
|   +-- serial_banda.py           # Comunicacion serial y registro CSV
|   +-- control_math.py           # Modelo matematico usado por la interfaz
|   +-- requirements.txt
+-- Docs/
+-- LICENSE
+-- README.md
```

La primera version de la interfaz hecha con Streamlit se conserva fuera del proyecto principal en:

```text
C:\Users\Manuel\Desktop\Universidad\Control Automático\VScode\GUI_Intento1
```

## Interfaz Grafica

La interfaz se ejecuta como aplicacion de escritorio con Tkinter y Matplotlib. Esta organizada en dos pestanas.

### Modelado Matematico

Incluye:

- Setpoint de referencia entre 35 RPM y 80 RPM.
- Seleccion de modelo de planta: primer orden o segundo orden.
- Controladores P, PI, PD y PID con ganancias configurables.
- Respuesta temporal en lazo cerrado escalada a RPM.

### Conexion Arduino

Incluye:

- Deteccion y seleccion del puerto serial.
- Botones para conectar, desconectar, iniciar, detener y limpiar datos.
- Setpoint en RPM configurable en tiempo real dentro del rango 35-80 RPM.
- Seleccion de controlador P, PI, PD o PID.
- Ajuste de ganancias `Kp`, `Ki` y `Kd` sin recompilar el firmware.
- Actualizacion fluida mediante temporizador de interfaz, sin recargar toda la aplicacion.
- Grafica superior con:
  - velocidad real medida,
  - setpoint,
  - respuesta del modelo matematico.
- Grafica inferior del error:
  - `error = setpoint - RPM medida`.
- Indicadores instantaneos de RPM real, setpoint, error y PWM aplicado.

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

### Parametros Del Encoder

```cpp
PPR motor = 34.02
Relacion de reduccion = 12.0
CPR = PPR motor * relacion de reduccion
Periodo de muestreo = 50 ms
```

## Protocolo Serial

La GUI envia comandos de texto terminados en salto de linea.

| Comando | Funcion |
|---|---|
| `START` | Inicia el control y la transmision de datos |
| `STOP` | Detiene el motor |
| `RESET` | Reinicia conteos e integrador |
| `SETPOINT:<rpm>` | Cambia el setpoint en RPM, limitado internamente a 35-80 RPM |
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

## Conversion RPM A PWM

El setpoint de usuario siempre se trabaja en **RPM**. La relacion actual se considera valida para setpoints entre **35 RPM y 80 RPM**. Para obtener un PWM base aproximado, el firmware usa la relacion experimental:

```text
PWM = -0.0022*RPM^3 + 0.4098*RPM^2 - 21.181*RPM + 440.87
```

Ese PWM base se usa como accion inicial o feed-forward. Luego el controlador P/PI/PD/PID suma una correccion segun el error medido por el encoder. El setpoint se limita a `35-80 RPM` y el resultado final se limita al rango valido de Arduino: `0` a `255`.

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

| Controlador | Funcion de transferencia | Parametros |
|---|---|---|
| P | `C(s) = Kp` | `Kp` |
| PI | `C(s) = Kp + Ki/s` | `Kp`, `Ki` |
| PD | `C(s) = Kp + Kd*s` | `Kp`, `Kd` |
| PID | `C(s) = Kp + Ki/s + Kd*s` | `Kp`, `Ki`, `Kd` |

## Instalacion

### Requisitos

- Python 3.9 o superior.
- VSCode.
- Extension PlatformIO.
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
| `tkinter` | Interfaz de escritorio, incluido con Python |
| `numpy` | Calculo numerico |
| `matplotlib` | Graficas |
| `control` | Funciones de transferencia y analisis de control |
| `pyserial` | Comunicacion con Arduino |

## Ejecucion

### Ejecutar La GUI

Desde la carpeta `GUI`:

```powershell
python GUI.py
```

La aplicacion se abrira como ventana de escritorio.

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

Tambien se puede hacer desde VSCode usando el boton **Upload** de PlatformIO.

## Flujo De Uso Recomendado

1. Conectar el Arduino por USB.
2. Cargar el firmware desde PlatformIO.
3. Ejecutar la GUI de escritorio.
4. Abrir la pestaña **Conexion Arduino**.
5. Seleccionar el puerto serial y presionar **Conectar**.
6. Elegir setpoint, controlador y ganancias.
7. Presionar **Enviar parametros** para mandar la configuracion al Arduino.
8. Presionar **START**.
8. Observar la velocidad real, la respuesta del modelo y el error.
9. Ajustar setpoint o ganancias en tiempo real y volver a presionar **Enviar parametros** para aplicarlos.
10. Presionar **STOP** antes de desconectar.

## Pendientes Y Mejoras Futuras

- Identificar experimentalmente el motor actual.
- Refinar la conversion RPM/PWM si se obtiene una curva experimental mas precisa.
- Ajustar ganancias iniciales recomendadas para cada controlador.
- Agregar limites de seguridad de RPM/PWM segun el comportamiento de la banda.
- Documentar capturas finales de la interfaz.
- Agregar ejemplos de ensayos CSV.

## Licencia

Este proyecto se distribuye bajo licencia MIT. Consulta el archivo `LICENSE` para mas detalles.
