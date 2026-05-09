#include <Arduino.h>

namespace {
const uint8_t kEncoderPinA = 2;
const uint8_t kEncoderPinB = 3;
const uint8_t kIN1 = 8;
const uint8_t kIN2 = 9;
const uint8_t kENA = 10;

const float kPprMotor = 34.02f;
const float kGearRatio = 12.0f;
const float kCountsPerRev = kPprMotor * kGearRatio;
const uint16_t kSampleMs = 50;
const uint16_t kCommandBufferSize = 72;
const float kPwmCubic = -0.0022f;
const float kPwmQuadratic = 0.4098f;
const float kPwmLinear = -21.181f;
const float kPwmOffset = 440.87f;
const float kMinSetpointRpm = 35.0f;
const float kMaxSetpointRpm = 80.0f;

enum class ControllerType : uint8_t {
  kP,
  kPI,
  kPD,
  kPID,
};

struct ControlConfig {
  ControllerType type = ControllerType::kPID;
  float setpoint_rpm = 60.0f;
  float kp = 2.0f;
  float ki = 0.4f;
  float kd = 0.0f;
};

volatile int32_t g_encoder_count = 0;

ControlConfig g_cfg;
int32_t g_prev_count = 0;
uint32_t g_prev_time = 0;
uint32_t g_start_time = 0;
bool g_running = false;
float g_integral = 0.0f;
float g_prev_error = 0.0f;
char g_cmd_buffer[kCommandBufferSize];
uint8_t g_cmd_len = 0;

void handleEncoderInterrupt() {
  if (digitalRead(kEncoderPinB) == HIGH) {
    ++g_encoder_count;
  } else {
    --g_encoder_count;
  }
}

void resetControlState() {
  noInterrupts();
  g_encoder_count = 0;
  interrupts();

  g_prev_count = 0;
  g_prev_time = millis();
  g_start_time = g_prev_time;
  g_integral = 0.0f;
  g_prev_error = 0.0f;
}

const char *controllerName(ControllerType type) {
  switch (type) {
    case ControllerType::kP:
      return "P";
    case ControllerType::kPI:
      return "PI";
    case ControllerType::kPD:
      return "PD";
    case ControllerType::kPID:
      return "PID";
  }
  return "PID";
}

ControllerType parseController(const char *value, ControllerType fallback) {
  if (strcmp(value, "P") == 0) return ControllerType::kP;
  if (strcmp(value, "PI") == 0) return ControllerType::kPI;
  if (strcmp(value, "PD") == 0) return ControllerType::kPD;
  if (strcmp(value, "PID") == 0) return ControllerType::kPID;
  return fallback;
}

void setMotorPwm(int pwm) {
  pwm = constrain(pwm, 0, 255);
  digitalWrite(kIN1, HIGH);
  digitalWrite(kIN2, LOW);
  analogWrite(kENA, pwm);
}

int computePwm(float rpm, float dt) {
  const float error = g_cfg.setpoint_rpm - rpm;
  const bool uses_i = (g_cfg.type == ControllerType::kPI || g_cfg.type == ControllerType::kPID);
  const bool uses_d = (g_cfg.type == ControllerType::kPD || g_cfg.type == ControllerType::kPID);

  if (uses_i) {
    g_integral += error * dt;
    g_integral = constrain(g_integral, -300.0f, 300.0f);
  } else {
    g_integral = 0.0f;
  }

  const float derivative = (dt > 0.0f) ? (error - g_prev_error) / dt : 0.0f;
  const float sp = g_cfg.setpoint_rpm;
  const float feed_forward = constrain(
      kPwmCubic * sp * sp * sp + kPwmQuadratic * sp * sp + kPwmLinear * sp + kPwmOffset,
      0.0f,
      255.0f);
  float correction = g_cfg.kp * error;

  if (uses_i) correction += g_cfg.ki * g_integral;
  if (uses_d) correction += g_cfg.kd * derivative;

  g_prev_error = error;
  return constrain(static_cast<int>(feed_forward + correction), 0, 255);
}

void printStatus(float t_s, float rpm, float error, int pwm) {
  Serial.print(t_s, 3);
  Serial.print(',');
  Serial.print(rpm, 2);
  Serial.print(',');
  Serial.print(g_cfg.setpoint_rpm, 2);
  Serial.print(',');
  Serial.print(error, 2);
  Serial.print(',');
  Serial.print(pwm);
  Serial.print(',');
  Serial.println(controllerName(g_cfg.type));
}

void printConfig() {
  Serial.print("#CFG,");
  Serial.print(controllerName(g_cfg.type));
  Serial.print(',');
  Serial.print(g_cfg.setpoint_rpm, 2);
  Serial.print(',');
  Serial.print(g_cfg.kp, 4);
  Serial.print(',');
  Serial.print(g_cfg.ki, 4);
  Serial.print(',');
  Serial.println(g_cfg.kd, 4);
}

void handleCommand(char *cmd) {
  if (strcmp(cmd, "START") == 0 || strcmp(cmd, "S") == 0) {
    resetControlState();
    g_running = true;
    Serial.println("tiempo_s,rpm_medida,setpoint_rpm,error_rpm,pwm,controlador");
    return;
  }

  if (strcmp(cmd, "STOP") == 0 || strcmp(cmd, "P") == 0) {
    setMotorPwm(0);
    g_running = false;
    Serial.println("#STOP");
    return;
  }

  if (strcmp(cmd, "RESET") == 0) {
    resetControlState();
    Serial.println("#RESET");
    return;
  }

  if (strncmp(cmd, "SETPOINT:", 9) == 0) {
    g_cfg.setpoint_rpm = constrain(atof(cmd + 9), kMinSetpointRpm, kMaxSetpointRpm);
    printConfig();
    return;
  }

  if (strncmp(cmd, "CTRL:", 5) == 0) {
    g_cfg.type = parseController(cmd + 5, g_cfg.type);
    printConfig();
    return;
  }

  if (strncmp(cmd, "GAINS:", 6) == 0) {
    char *kp = strtok(cmd + 6, ",");
    char *ki = strtok(nullptr, ",");
    char *kd = strtok(nullptr, ",");
    if (kp != nullptr) g_cfg.kp = atof(kp);
    if (ki != nullptr) g_cfg.ki = atof(ki);
    if (kd != nullptr) g_cfg.kd = atof(kd);
    printConfig();
    return;
  }

  Serial.print("#ERR,comando_desconocido,");
  Serial.println(cmd);
}

void readSerialCommands() {
  while (Serial.available() > 0) {
    char c = static_cast<char>(Serial.read());
    if (c == '\r') continue;

    if (c == '\n') {
      g_cmd_buffer[g_cmd_len] = '\0';
      if (g_cmd_len > 0) handleCommand(g_cmd_buffer);
      g_cmd_len = 0;
      continue;
    }

    if (g_cmd_len < kCommandBufferSize - 1) {
      g_cmd_buffer[g_cmd_len++] = c;
    } else {
      g_cmd_len = 0;
      Serial.println("#ERR,comando_muy_largo");
    }
  }
}
}  // namespace

void setup() {
  Serial.begin(115200);

  pinMode(kEncoderPinA, INPUT_PULLUP);
  pinMode(kEncoderPinB, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(kEncoderPinA), handleEncoderInterrupt, RISING);

  pinMode(kIN1, OUTPUT);
  pinMode(kIN2, OUTPUT);
  pinMode(kENA, OUTPUT);
  setMotorPwm(0);

  Serial.println("#LISTO");
  printConfig();
}

void loop() {
  readSerialCommands();
  if (!g_running) return;

  const uint32_t now = millis();
  if ((now - g_prev_time) < kSampleMs) return;

  noInterrupts();
  const int32_t count = g_encoder_count;
  interrupts();

  const float dt = (now - g_prev_time) / 1000.0f;
  const int32_t delta = count - g_prev_count;
  const float rpm = (delta / kCountsPerRev) / dt * 60.0f;
  const float t_s = (now - g_start_time) / 1000.0f;
  const float error = g_cfg.setpoint_rpm - rpm;
  const int pwm = computePwm(rpm, dt);

  setMotorPwm(pwm);
  printStatus(t_s, rpm, error, pwm);

  g_prev_count = count;
  g_prev_time = now;
}
