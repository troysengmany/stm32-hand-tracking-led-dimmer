import cv2
import mediapipe as mp
import serial
import time
import math
import serial.tools.list_ports

# ---------------- SERIAL ----------------
def find_stm_port():
    ports = list(serial.tools.list_ports.comports())

    for port in ports:
        device = port.device.lower()
        description = (port.description or "").lower()
        manufacturer = (port.manufacturer or "").lower()

        if "usbmodem" in device:
            return port.device
        if "stlink" in description or "stm" in description:
            return port.device
        if "stmicro" in manufacturer:
            return port.device

    raise RuntimeError("STM32 serial port not found. Check USB connection.")


PORT = find_stm_port()
print("Using port:", PORT)

ser = serial.Serial(PORT, 38400, timeout=0)
time.sleep(0.6)
# ---------------- MEDIAPIPE ----------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

selected_light = 1
last_sent = {1: -1, 2: -1, 3: -1}

def map_value(x, in_min, in_max, out_min, out_max):
    x = max(in_min, min(x, in_max))
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def fingers_up(hand_landmarks, hand_label):
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]

    count = 0

    # Thumb
    thumb_tip_x = hand_landmarks.landmark[4].x
    thumb_ip_x = hand_landmarks.landmark[3].x

    if hand_label == "Left":
        if thumb_tip_x > thumb_ip_x:
            count += 1
    else:
        if thumb_tip_x < thumb_ip_x:
            count += 1

    # Other fingers
    for tip, pip in zip(tips, pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            count += 1

    return count

try:
    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    ) as hands:

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            if results.multi_hand_landmarks and results.multi_handedness:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    label = handedness.classification[0].label  # Left or Right
                    h, w, _ = frame.shape

                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # LEFT HAND = SELECT LIGHT
                    if label == "Left":
                        finger_count = fingers_up(hand_landmarks, label)

                        if finger_count == 1:
                            selected_light = 1
                        elif finger_count == 2:
                            selected_light = 2
                        elif finger_count == 3:
                            selected_light = 3

                        cv2.putText(
                            frame,
                            f"Left Hand Fingers: {finger_count}",
                            (10, 80),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (255, 255, 0),
                            2
                        )

                    # RIGHT HAND = DIM SELECTED LIGHT
                    elif label == "Right":
                        thumb_tip = hand_landmarks.landmark[4]
                        index_tip = hand_landmarks.landmark[8]

                        x1, y1 = int(thumb_tip.x * w), int(thumb_tip.y * h)
                        x2, y2 = int(index_tip.x * w), int(index_tip.y * h)

                        distance = math.hypot(x2 - x1, y2 - y1)

                        # Hard cutoff so fully closed fingers = true OFF
                        if distance < 55:
                            brightness = 0
                        elif distance > 150:
                            brightness = 999
                        else:
                            brightness = map_value(distance, 55, 150, 0, 999)

                        cv2.circle(frame, (x1, y1), 8, (255, 0, 255), -1)
                        cv2.circle(frame, (x2, y2), 8, (255, 0, 255), -1)
                        cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

                        if abs(brightness - last_sent[selected_light]) > 10 or brightness == 0 or brightness == 999:
                            command = f"L{selected_light}:{brightness}\n"
                            ser.write(command.encode())
                            print("Sent:", command.strip())
                            last_sent[selected_light] = brightness

                        cv2.putText(
                            frame,
                            f"Brightness: {brightness}",
                            (10, 120),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 255, 0),
                            2
                        )

            cv2.putText(
                frame,
                f"Selected Light: {selected_light}",
                (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

            cv2.imshow("Smart Home Hand Tracking", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

finally:
    # Turn all lights fully off before closing
    ser.write(b"L1:0\n")
    ser.write(b"L2:0\n")
    ser.write(b"L3:0\n")
    time.sleep(0.1)

    cap.release()
    cv2.destroyAllWindows()
    ser.close()
