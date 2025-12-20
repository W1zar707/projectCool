import asyncio
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import cv2
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus,
    GlobalSystemMediaTransportControlsSessionMediaProperties
)


class MediaData:
    def __init__(self, trackData: GlobalSystemMediaTransportControlsSessionMediaProperties, volume):
        self.artist = trackData.artist
        self.trackName = trackData.title
        self.volume = volume


class Commands:
    async def init(self):
        sessions = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        self.current_session = sessions.get_current_session()
        self.indexIcon = cv2.imread("previous.png", cv2.IMREAD_UNCHANGED)
        self.ringIcon = cv2.imread("next.png", cv2.IMREAD_UNCHANGED)
        try:
            if self.current_session.get_playback_info().playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
                self.middleIcon = cv2.imread("play.png", cv2.IMREAD_UNCHANGED)
            elif self.current_session.get_playback_info().playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PAUSED:
                self.middleIcon = cv2.imread("pause.png", cv2.IMREAD_UNCHANGED)
        except AttributeError:
            self.middleIcon = cv2.imread("play.png", cv2.IMREAD_UNCHANGED)
        finally:
            self.middleIcon = cv2.resize(self.middleIcon, (80,80))


    async def indexFinger(self):
        if self.current_session:
            # Проверяем, доступна ли команда
            controls = self.current_session.get_playback_info().controls
            if controls.is_next_enabled:
                result = await self.current_session.try_skip_previous_async()

    async def middleFinger(self):
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

    async def setVolume(self, volume):
        pass

    async def getData(self) -> MediaData:
        properties = await self.current_session.try_get_media_properties_async()
        device = AudioUtilities.GetSpeakers()

        # Получаем интерфейс управления громкостью напрямую
        volume_interface = device.EndpointVolume

        # Получаем текущую громкость (от 0.0 до 1.0)
        current_volume = volume_interface.GetMasterVolumeLevelScalar()
        mediaData = MediaData(properties, round(current_volume * 100))
        return mediaData
