from typing import Optional

from .ExpansionPackInfo import ExpansionPackInfo
from .SongChart import SongChart


class Song:
    def __init__(self, data, character_id: Optional[str] = None):
        self.expansion_pack_info: Optional[ExpansionPackInfo] = None

        if 'song_id' in data:
            self._parse_song_data(data)
        else:
            self._parse_expansion_data(data)

        if character_id:
            self.character_id = character_id

        self.number = int(self.id[self.id.index('_') + 1:])
        if self.character_id == 'paff001':
            self.number += 1  # paff's songs are 0-indexed instead of 1-indexed

        self.separate_difficulties = [self.charts[item] for item in self.charts.difficulties
                                      if self.charts[item].has_separate_file]

    def _parse_song_data(self, data):
        self.id: str = data['song_id']
        self.name: str = data['song_name']
        self.artist: str = data['artist']
        self.is_hidden: bool = data['is_hidden']
        self.is_download_only: bool = data['IsDownloadOnly']
        self.character_id: str = ''
        self.charts = SongChart(data['charts'])

    def _parse_expansion_data(self, data):
        self.id: str = data['SongId']
        self.name: str = data['SongName']
        self.artist: str = data['Artist']
        self.is_hidden: bool = data['IsHidden']
        self.is_download_only: bool = data['IsDownloadOnly']
        self.character_id: str = data['SongPackId']
        self.charts = SongChart(data['Charts'])

    def __str__(self):
        return f'Song(id={self.id}, name={self.name}, artist={self.artist})'

    __repr__ = __str__
