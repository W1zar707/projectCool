import cv2
import mediapipe as mp
import commands
import asyncio
import numpy
from numpy import ndarray
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from commands import MediaData



def union(background, foreground,x,y, x2,y2):
    y = int(y*background.shape[0])
    x = int(x*background.shape[1])
    y2 = int(y2 * background.shape[0])
    x2 = int(x2 * background.shape[1])
    length = int(((x-x2)**2 + (y-y2)**2)**0.5)
    foreground = cv2.resize(foreground, (length, length))
    x -= length//2
    y -= length//2
    if (y >= background.shape[0] or x >= background.shape[1]
            or x+length<=0 or y+length<=0):
        print("защита")
        print(x+length//2)
        return

    if y < 0:
        foreground = foreground[-y:, :]
        y = 0
    if x < 0:
        foreground = foreground[:,-x:]
        print(foreground.shape, x)
        x = 0

    h, w = foreground.shape[:2]
    if y + h > background.shape[0]:
        h = background.shape[0] - y
        foreground = foreground[:h]
    if x + w > background.shape[1]:
        w = background.shape[1] - x
        foreground = foreground[:,:w]
    # print(x,y,w,h,foreground.shape[:2])
    #
    # print(foreground.shape)
    b, g, r, a = cv2.split(foreground) # получаем матрицы каждого канала
    alpha = a / 255.0  # получаем матрицу альфа-каналов foreground
    # классическая формула альфа-смешивания:
    # result = alpha * foreground + (1 - alpha) * background
    background[y:y + h, x:x + w] = ( # берем пиксель по координатам (y между y+h) и (x между x+w) назначаем ему
            alpha[:, :, None] * # берем значение альфа-канала с переднего плана пикселя который будет находиться над
            foreground[:, :, :3] + # берем 3 канала пикселя с переднего плана который будет находиться над
            (1 - alpha[:, :, None]) *
            background[y:y + h, x:x + w]
    )
    # берем диапазон фона на который попадает изображение переднего плана и используем к нему формулу

mediaCommands: commands.Commands = commands.Commands()

async def main():
    BaseOptions = mp.tasks.BaseOptions
    HandLandmarker = mp.tasks.vision.HandLandmarker
    HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
    HandLandmarkerResult = mp.tasks.vision.HandLandmarkerResult
    VisionRunningMode = mp.tasks.vision.RunningMode
    await mediaCommands.init()
    cap = cv2.VideoCapture(0)
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
            rgb_frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            landmarker.detect_async(mp_image, int(cv2.getTickCount() / cv2.getTickFrequency() * 1000))
            if latest_result is not None and latest_result.handedness:
                for i in range(len(latest_result.handedness[0])):
                    if latest_result.handedness[0][i].category_name == 'Left':
                        hand = latest_result.hand_landmarks[i]
                        union(image, mediaCommands.indexIcon, x=hand[8].x, y=hand[8].y, x2=hand[7].x, y2=hand[7].y)
                        union(image, mediaCommands.middleIcon, x=hand[12].x, y=hand[12].y, x2=hand[11].x, y2=hand[11].y)
                        union(image, mediaCommands.ringIcon, x=hand[16].x, y=hand[16].y, x2=hand[15].x, y2=hand[15].y)


            cv2.imshow('frame', image)
            cv2.waitKey(1)


# The landmarker is initialized. Use it here.
# ...


if '__main__' == __name__:
    asyncio.run(main())

