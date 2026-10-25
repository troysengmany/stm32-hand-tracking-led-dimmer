# LED Dimmer UART Protocol

The Python host sends newline-terminated commands in this format:

```text
L<light>:<brightness>
```

Examples:

```text
L1:500
L2:999
L3:250
```

- `light` is 1, 2, or 3.
- `brightness` is clamped to 0-999.
- USART2 is configured for 38,400 baud.

The firmware receives UART data one character at a time, parses complete commands with `sscanf()`, and updates the corresponding PWM timer compare register with `__HAL_TIM_SET_COMPARE()`.

## PWM outputs

| Light | STM32 pin | Timer channel |
|---|---|---|
| 1 | PB4 | TIM3_CH1 |
| 2 | PB5 | TIM3_CH2 |
| 3 | PB3 | TIM2_CH2 |
