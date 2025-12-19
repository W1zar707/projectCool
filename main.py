import cv2
import mediapipe as mp
import commands
import asyncio
from commands import MediaData
def main():
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands


    # Настройки для распознавания рук
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break

        # Конвертация BGR в RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        # Обработка изображения
        results = hands.process(image)

        # Конвертация обратно в BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Отрисовка результатов
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                )

        cv2.imshow('Hand Tracking', image)
        if cv2.waitKey(5) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    hands.close()

if '__main__' == __name__:
    mediaCommands = commands.Commands()
    asyncio.run(mediaCommands.init())
    asyncio.run(mediaCommands.middleFinger())
    print(asyncio.run(mediaCommands.getData()).volume)

