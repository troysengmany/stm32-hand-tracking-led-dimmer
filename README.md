# STM32 Hand-Tracking LED Dimmer

A real-time computer-vision lighting controller that uses **MediaPipe hand tracking** to select one of three LEDs and continuously adjust its brightness. Python converts hand gestures into UART commands, and an **STM32 Nucleo-F303K8** applies the requested brightness using hardware PWM.

**Tech Stack:** STM32 HAL • C • Python • OpenCV • MediaPipe • UART • PWM • Timers

![Hand-tracking LED dimmer preview](media/preview.gif)

**[Watch the hardware demo clip](media/dimmer-demo.mp4)**

## What This Project Demonstrates

- Real-time hand tracking with OpenCV and MediaPipe
- Gesture-based LED selection using finger counting
- Pinch-distance measurement for continuous brightness control
- Python-to-STM32 UART communication
- Newline-delimited ASCII command parsing
- Three independent hardware PWM LED channels
- STM32 HAL UART and timer control
- Integration of computer vision, embedded firmware, and physical hardware

## Project Context and Contribution

This project was developed as my individual module within a larger embedded-systems team project.

My primary responsibility was the hand-tracking LED dimming system, including the Python gesture and UART logic and the STM32 UART/PWM control used to drive the three LEDs.

The module was later integrated into the broader gesture-controlled smart-home system, where the same computer-vision-to-STM32 control approach was expanded to additional hardware subsystems.

## Control Scheme

- **Left hand:** hold up 1, 2, or 3 fingers to select Light 1, Light 2, or Light 3.
- **Right hand:** change thumb-to-index pinch distance to control the selected LED's brightness.
- A closed pinch below the lower threshold produces a true `0` brightness command.
- A wide pinch above the upper threshold produces the maximum `999` brightness command.

The final Python controller maps approximately **55-150 pixels** of pinch distance to a **0-999** brightness range.

To reduce unnecessary UART traffic, the script only transmits a new command when the brightness changes enough to require an update.

## System Architecture

```text
Webcam
  |
  v
OpenCV + MediaPipe
  |  left hand -> LED selection
  |  right pinch -> 0..999 brightness
  v
Python UART @ 38,400 baud
  |
  v
STM32 Nucleo-F303K8
  |---- PB4 / TIM3_CH1 ---> Light 1
  |---- PB5 / TIM3_CH2 ---> Light 2
  `---- PB3 / TIM2_CH2 ---> Light 3
```

## UART Protocol

Commands are newline-terminated ASCII strings such as:

```text
L1:500
L2:999
L3:250
```

Each command follows this format:

```text
L\<light_number>:<brightness>
```

where:

- `light_number` is `1`, `2`, or `3`
- `brightness` ranges from `0` to `999`

The STM32 firmware receives UART characters using `HAL_UART_Receive()`, parses the command with `sscanf()`, clamps brightness to the valid `0-999` range, and updates the selected PWM timer channel using `__HAL_TIM_SET_COMPARE()`.

See [`docs/protocol.md`](docs/protocol.md) for the complete protocol mapping.

## Repository Layout

```text
.
├── README.md
├── requirements.txt
├── src/
│   └── python/
│       └── 3DimTest.py
├── firmware/
│   └── CPE185_DimmerLED/
│       ├── CPE185_DimmerLED.ioc
│       ├── Core/
│       ├── Drivers/
│       └── STM32F303K8TX_FLASH.ld
├── docs/
│   └── protocol.md
└── media/
    ├── preview.gif
    └── dimmer-demo.mp4
```

## Run the Python Controller

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/python/3DimTest.py
```

The script searches connected serial devices for an STM32/ST-Link-style port and opens it at **38,400 baud**. Camera permission is required.

## STM32 Setup

Open or import the project under `firmware/CPE185_DimmerLED` in STM32CubeIDE.

The included `.ioc` file records the STM32CubeMX configuration, and the repository contains the project `Core` files along with the STM32 HAL/CMSIS driver sources from the working project.

Build output directories and machine-specific configuration files are intentionally excluded from version control.

## Hardware Mapping

| Light | STM32 Pin | Timer Channel |
|---|---|---|
| Light 1 | PB4 | TIM3_CH1 |
| Light 2 | PB5 | TIM3_CH2 |
| Light 3 | PB3 | TIM2_CH2 |

Each LED is controlled independently through a hardware PWM timer channel.

## Verified Project Behavior

The working system demonstrated:

- Real-time webcam hand detection
- 1 / 2 / 3 finger LED selection
- Pinch-based continuous brightness adjustment
- Python-to-STM32 UART communication
- Independent PWM control of all three LEDs
- Physical hardware response to the gesture interface

The demo clip in `media/` shows the STM32 hardware responding to hand gestures in real time.

## Limitations

- Pinch-distance control uses fixed pixel thresholds, so behavior can vary with camera distance and hand position.
- MediaPipe landmark jitter can introduce small brightness fluctuations during hand movement.
- The system requires a computer running the Python/OpenCV application and a wired UART connection to the STM32.
- LED selection depends on predefined finger-count gestures rather than a configurable user interface.
- The system does not automatically calibrate the pinch-distance range for different users or camera setups.

## Future Improvements

- Add smoothing or filtering to the pinch-distance measurement for more stable brightness control.
- Add automatic calibration based on hand size and distance from the camera.
- Replace the wired UART connection with Bluetooth or another wireless interface.
- Add configurable gesture mappings and saved brightness presets.
- Expand the UART protocol to support additional lighting channels or embedded peripherals.
- Move more gesture-processing logic toward a standalone or edge-computing platform to reduce dependence on a laptop.

## Engineering Takeaways

This project introduced me to connecting real-time computer vision with embedded hardware through a simple serial communication protocol.

The main challenges were translating noisy hand-tracking data into stable hardware commands, keeping the Python and STM32 command formats synchronized, configuring multiple independent PWM timer channels, and tuning gesture thresholds so the physical LEDs responded predictably.

The project reinforced the importance of separating computer-vision processing from embedded control logic, defining a clear communication protocol between systems, and testing software, firmware, and hardware independently before integrating them into a complete real-time system.
