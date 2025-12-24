import cv2
import mediapipe as mp
from numpy.testing.print_coercion_tables import print_coercion_table

import commands
import asyncio
import numpy
from numpy import ndarray
from finger import Finger
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import commands
from PIL import ImageFont, ImageDraw, Image

image:ndarray = None
def putText(
    cv2_img, text_img,x, y,w,h):

    text_height, text_width = text_img.shape[:2]
    x = x - (text_width-w)//2
    y = y - (text_height - h)//2
    cv2.rectangle(cv2_img, (x, y), (x + text_width, y + text_height), (0, 0, 0), 2)
    if x > cv2_img.shape[1] or y > cv2_img.shape[0]:
        return
    if x < 0:
        text_width = text_width + x
        text_img = text_img[:,-text_width:]
        x = 0
    if y<0:
        text_height = text_height + y
        text_img = text_img[-text_height:,:]
        y = 0

    # Проверка размера текста перед вставкой
    if (y + text_height > cv2_img.shape[0]):
        text_img = text_img[:cv2_img.shape[0] - y, :]
        text_height = text_img.shape[0]
    if (x + text_width > cv2_img.shape[1]):
        text_img = text_img[:, :(cv2_img.shape[1] - x)]
        text_width = text_img.shape[1]

    # Обработка альфа-канала
    alpha = text_img[:, :, 3] / 255.0
    try:
        for c in range(3):
            cv2_img[y:y + text_height, x:x + text_width, c] = \
                cv2_img[y:y + text_height, x:x + text_width, c] * \
                (1 - alpha) + text_img[:, :, c] * alpha
    except:
        print(x, y)

def getSquare(index, pinky, wrist):
    index = (index[0]*image.shape[1], index[1]*image.shape[0])
    pinky = (pinky[0] * image.shape[1], pinky[1] * image.shape[0])
    wrist = (wrist[0] * image.shape[1], wrist[1] * image.shape[0])
    points = numpy.array([index, pinky, wrist], dtype=numpy.float32)
    return cv2.boundingRect(points)

def union(finger:Finger):
    global image
    if finger.visualBox is None:
        return
    x,y,w,h=finger.collisionBox
    foreground = finger.visualBox
    b, g, r, a = cv2.split(foreground)  # получаем матрицы каждого канала
    alpha = a / 255.0  # получаем матрицу альфа-каналов foreground
    # классическая формула альфа-смешивания:
    # result = alpha * foreground + (1 - alpha) * background
    image[y:y + h, x:x + w] = (  # берем пиксель по координатам (y между y+h) и (x между x+w) назначаем ему
            alpha[:, :, None] *  # берем значение альфа-канала с переднего плана пикселя который будет находиться над
            foreground[:, :, :3] +  # берем 3 канала пикселя с переднего плана который будет находиться над
            (1 - alpha[:, :, None]) *
            image[y:y + h, x:x + w]
    )

def isCollision(finger1: Finger,finger2:Finger) -> bool:
    '''
    Чтобы понять, пересекаются ли они, мы ищем общую часть — маленький прямоугольник, который принадлежит и A, и B одновременно.
    Этот общий прямоугольник должен начинаться:

    Слева не раньше, чем начнётся самый правый из двух боксов.
    То есть берём максимум из левых краёв: max(100, 250) = 250
    → inter_x_left = 250
    Справа не дальше, чем закончится самый левый из двух боксов.
    Берём минимум из правых краёв: min(300, 400) = 300
    → inter_x_right = 300
    '''
    x1, y1, w1, h1 = finger1.collisionBox
    x2, y2, w2, h2 = finger2.collisionBox
    inter_x_left = max(x1, x2)
    inter_y_top = max(y1, y2)
    inter_x_right = min(x1 + w1, x2 + w2)
    inter_y_bottom = min(y1 + h1, y2 + h2)
    return (inter_x_right > inter_x_left) and (inter_y_bottom > inter_y_top)

mediaCommands: commands.Commands = commands.Commands()

async def main():
    global image
    BaseOptions = mp.tasks.BaseOptions
    HandLandmarker = mp.tasks.vision.HandLandmarker
    HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
    HandLandmarkerResult = mp.tasks.vision.HandLandmarkerResult
    VisionRunningMode = mp.tasks.vision.RunningMode
    await mediaCommands.init()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Ошибка: не удалось открыть камеру")
        return
    latest_result: HandLandmarkerResult = None
    # Create a hand landmarker instance with the live stream mode:
    def print_result(result: HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
        nonlocal latest_result
        latest_result = result

    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
        running_mode=VisionRunningMode.LIVE_STREAM,
        result_callback=print_result,
        num_hands=4)
    with HandLandmarker.create_from_options(options) as landmarker:
        fingers = {"index": Finger(icon=(mediaCommands, "indexIcon"), command=mediaCommands.indexFinger),
                   "middle": Finger(icon = (mediaCommands, "middleIcon"), command = mediaCommands.middleFinger),
                   "ring": Finger(icon=(mediaCommands, "ringIcon"), command=mediaCommands.ringFinger),
                   "thumb": Finger(icon=None, command=None)
                   }
        while True:
            success, image = cap.read()
            image = cv2.flip(image, 1)
            Finger.image = image
            rgb_frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            landmarker.detect_async(mp_image, int(cv2.getTickCount() / cv2.getTickFrequency() * 1000))
            if latest_result is not None and latest_result.handedness:
                for handedness, hand_landmarks in zip(latest_result.handedness, latest_result.hand_landmarks):
                    if handedness[0].category_name == 'Left':
                        hand = hand_landmarks
                        fingers["index"].createBoxes(hand[8].x, hand[8].y, hand[7].x, hand[7].y)
                        fingers["middle"].createBoxes(hand[12].x, hand[12].y, hand[11].x, hand[11].y)
                        fingers["ring"].createBoxes(hand[16].x, hand[16].y, hand[15].x, hand[15].y)
                        fingers["thumb"].createBoxes(hand[4].x, hand[4].y, hand[3].x, hand[3].y)
                        checkFingers = ["index", "middle", "ring"]
                        pressedFinger = None
                        for finger in checkFingers:
                            union(fingers[finger])
                            if isCollision(fingers[finger], fingers["thumb"]):
                                pressedFinger = fingers[finger]
                        if pressedFinger is None:
                            for finger in checkFingers:
                                fingers[finger].isPressed = False
                        elif pressedFinger.isPressed == False:
                            pressedFinger.isPressed = True
                            await pressedFinger.command()
                        elif pressedFinger.isPressed == True:
                            print("Палец уже нажат")
                    if handedness[0].category_name == 'Right':
                        hand = hand_landmarks
                        square = getSquare(index=(hand[5].x,hand[5].y), pinky=(hand[17].x, hand[17].y), wrist=(hand[0].x, hand[0].y))
                        cv2.rectangle(image, (square[0], square[1]), (square[0] + square[2], square[1] + square[3]), (0, 0, 0), 2)
                        putText(image, mediaCommands.image, square[0],square[1],square[2],square[3])
            cv2.imshow('frame', image)
            cv2.waitKey(1)


# The landmarker is initialized. Use it here.
# ...


if '__main__' == __name__:
    asyncio.run(main())

