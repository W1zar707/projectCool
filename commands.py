import asyncio
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus,
    GlobalSystemMediaTransportControlsSessionMediaProperties
)
class MediaData:
    def __init__(self, trackData: GlobalSystemMediaTransportControlsSessionMediaProperties, volume ):
        self.artist = trackData.artist
        self.trackName = trackData.title
        self.volume = volume

class Commands:
    async def init(self):
        sessions = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        self.current_session = sessions.get_current_session()
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
        else:
            result = await self.current_session.try_play_async()
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
        mediaData = MediaData(properties, round(current_volume*100))
        return mediaData


