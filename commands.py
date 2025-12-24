import asyncio
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import cv2
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus,
    GlobalSystemMediaTransportControlsSessionMediaProperties
)
from PIL import ImageFont, ImageDraw, Image
import numpy


def add_text_to_image(artist, trackname,  font_size, colour, background_color=(255, 255, 255), transparency=5, line_spacing = 0,font_path= 'font.ttf',):
    # Создаем временное изображение для определения размеров текста
    font = ImageFont.truetype(font_path, font_size)

    dummy_img = Image.new('RGBA', (1, 1))
    draw = ImageDraw.Draw(dummy_img)

    # Размеры первой строки (artist)
    bbox1 = draw.textbbox((0, 0), trackname, font=font)
    width1 = bbox1[2] - bbox1[0]
    height1 = bbox1[3] - bbox1[1]

    # Размеры второй строки (trackname)
    bbox2 = draw.textbbox((0, 0), artist, font=font)
    width2 = bbox2[2] - bbox2[0]
    height2 = bbox2[3] - bbox2[1]

    # Общая ширина и высота
    total_width = max(width1, width2)
    total_height = -bbox1[1]+height1 + line_spacing + height2+bbox2[1]



    # Создаём финальное изображение с фоном
    text_img = Image.new('RGBA', (total_width, total_height), background_color + (transparency,))
    draw = ImageDraw.Draw(text_img)
    # Рисуем первую строку (artist) — по левому краю, сверху
    draw.text((-bbox1[0]+(total_width-width1)//2, -bbox1[1]), trackname, font=font, fill=colour)

    # Рисуем вторую строку (trackname) — под первой
    draw.text((-bbox2[0]+(total_width-width2)//2, -bbox1[1] + height1 + line_spacing), artist, font=font, fill=colour)

    return numpy.array(text_img)  # Возвращаем как numpy array (RGBA)

class MediaData:
    def __init__(self, trackData: GlobalSystemMediaTransportControlsSessionMediaProperties, volume):
        self.artist = trackData.artist
        self.trackName = trackData.title
        self.volume = volume


class Commands:
    async def init(self):
        sessions = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        self.current_session = sessions.get_current_session()
        sessions.add_current_session_changed(self.getData)
        self.image = None
        await self.getData()
        self.indexIcon = cv2.imread("previous.png", cv2.IMREAD_UNCHANGED)
        self.ringIcon = cv2.imread("next.png", cv2.IMREAD_UNCHANGED)
        try:
            if self.current_session.get_playback_info().playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
                self.middleIcon = cv2.imread("play.png", cv2.IMREAD_UNCHANGED)
            elif self.current_session.get_playback_info().playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PAUSED:
                self.middleIcon = cv2.imread("pause.png", cv2.IMREAD_UNCHANGED)
        except AttributeError:
            self.middleIcon = cv2.imread("play.png", cv2.IMREAD_UNCHANGED)


    async def indexFinger(self):
        if self.current_session:
            # Проверяем, доступна ли команда
            controls = self.current_session.get_playback_info().controls
            if controls.is_next_enabled:
                result = await self.current_session.try_skip_previous_async()
                await self.getData()
        if self.current_session is None:
            await self.init()
            await self.indexFinger()
            return

    async def middleFinger(self):
        if self.current_session is None:
            await self.init()
            await self.middleFinger()
            return
        playback_info = self.current_session.get_playback_info()
        if playback_info.playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
            result = await self.current_session.try_pause_async()
            self.middleIcon = cv2.imread("pause.png", cv2.IMREAD_UNCHANGED)
        else:
            result = await self.current_session.try_play_async()
            self.middleIcon = cv2.imread("play.png", cv2.IMREAD_UNCHANGED)

    async def ringFinger(self):
        if self.current_session:
            # Проверяем, доступна ли команда
            controls = self.current_session.get_playback_info().controls
            if controls.is_next_enabled:
                result = await self.current_session.try_skip_next_async()
                await self.getData()
        if self.current_session is None:
            await self.init()
            await self.ringFinger()
            return

    async def setVolume(self, volume):
        pass

    async def getData(self):
        if self.current_session is None:
            self.image = add_text_to_image(artist="Нет артиста", trackname="Нет названия",font_size=36, colour=(255,255,255))
            return
        properties = await self.current_session.try_get_media_properties_async()
        device = AudioUtilities.GetSpeakers()

        # Получаем интерфейс управления громкостью напрямую
        volume_interface = device.EndpointVolume

        # Получаем текущую громкость (от 0.0 до 1.0)
        current_volume = volume_interface.GetMasterVolumeLevelScalar()
        mediaData = MediaData(properties, round(current_volume * 100))
        self.image = add_text_to_image(artist=mediaData.artist, trackname=mediaData.trackName,font_size=36, colour=(255,255,255))

