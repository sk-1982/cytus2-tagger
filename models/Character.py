from typing import List

from .Song import Song


class Character:
    def __init__(self, data):
        self.id: str = data['song_pack_id']
        self.name: str = data['song_pack_name']
        self.color: str = data['theme_color']
        self.is_dlc: bool = data['is_iap_pack']
        self.price = float(data['price'].strip('$') or 0)
        self.has_im: bool = data['hasIM']
        self.songs: List[Song] = []
        self.number = 0

    def __str__(self):
        return f'Character(id={self.id}, name={self.name}, songs={self.songs})'

    __repr__ = __str__
