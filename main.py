import cv2
import mediapipe as mp
import commands
import asyncio
import numpy
from numpy import ndarray
from finger import Finger
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from commands import MediaData

image:ndarray = None



def vector(x,y,x2,y2)->int:
    return int(((x-x2)**2 + (y-y2)**2)**0.5)

def union(foreground, finger):
    global image
    x,y,w,h=finger.box
    foreground = cv2.resize(foreground, (w,h))
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

def isCollision(finger1,finger2) -> bool:
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
    x1, y1, w1, h1 = finger1.box
    x2, y2, w2, h2 = finger2.box
    inter_x_left = max(x1, x2)
    inter_y_top = max(y1, y2)
    inter_x_right = min(x1 + w1, x2 + w2)
    inter_y_bottom = min(y1 + h1, y2 + h2)
    return (inter_x_right > inter_x_left) and (inter_y_bottom > inter_y_top)

def createBox(x,y,x2,y2):
    global image
    y = int(y * image.shape[0])
    x = int(x * image.shape[1])
    y2 = int(y2 * image.shape[0])
    x2 = int(x2 * image.shape[1])
    radius = vector(x,y,x2,y2)
    height = radius * 2
    width = radius * 2
    print(radius)
    x -= radius
    y -= radius
    if x>image.shape[1] or y>image.shape[0]:
        return
    if x<0:
        width = width+x
        x = 0
    if y<0:
        height = height+y
        y = 0
    if x+width>image.shape[1]:
        width = image.shape[1]-x
    if x+height>image.shape[0]:
        height = image.shape[0]-y
    return (x,y,width,height)

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
        num_hands=2)
    with HandLandmarker.create_from_options(options) as landmarker:
        while True:
            success, image = cap.read()
            image = cv2.flip(image, 1)
            Finger.image = image
            rgb_frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            landmarker.detect_async(mp_image, int(cv2.getTickCount() / cv2.getTickFrequency() * 1000))
            if latest_result is not None and latest_result.handedness:
                for i in range(len(latest_result.handedness[0])):
                    if latest_result.handedness[0][i].category_name == 'Left':
                        hand = latest_result.hand_landmarks[i]
                        fingersBoxes = {"index": Finger((hand[8].x, hand[8].y, hand[7].x, hand[7].y)),
                                   "middle": Finger((hand[12].x, hand[12].y, hand[11].x, hand[11].y)),
                                   "ring": Finger((hand[16].x, hand[16].y, hand[15].x, hand[15].y)),
                                   "thumb": Finger((hand[4].x, hand[4].y, hand[3].x, hand[3].y))
                                   }
                        union(mediaCommands.indexIcon, fingersBoxes["index"])
                        union(mediaCommands.middleIcon, fingersBoxes["middle"])
                        union(mediaCommands.ringIcon, fingersBoxes["ring"])
                        if isCollision(fingersBoxes["index"],fingersBoxes["thumb"]):
                            if fingersBoxes["index"].isPressed == False:
                                fingersBoxes["index"].isPressed = True
                                await mediaCommands.indexFinger()
                            elif fingersBoxes["index"].isPressed == True:
                                pass
                        elif isCollision(fingersBoxes["middle"],fingersBoxes["thumb"]):
                            if fingersBoxes["middle"].isPressed == False:
                                fingersBoxes["middle"].isPressed = True
                                await mediaCommands.middleFinger()
                                print("Пауза")
                            elif fingersBoxes["middle"].isPressed == True:
                                pass
                        elif isCollision(fingersBoxes["ring"],fingersBoxes["thumb"]):
                            if fingersBoxes["ring"].isPressed == False:
                                fingersBoxes["ring"].isPressed = True
                                await mediaCommands.ringFinger()
                            elif fingersBoxes["ring"].isPressed == True:
                                pass
                        else:
                            print("Условия нет")
                            fingersBoxes["index"].isPressed = False
                            fingersBoxes["middle"].isPressed = False
                            fingersBoxes["ring"].isPressed = False

            cv2.imshow('frame', image)
            cv2.waitKey(1)


# The landmarker is initialized. Use it here.
# ...


if '__main__' == __name__:
    asyncio.run(main())

