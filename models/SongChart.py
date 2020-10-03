from typing import Optional


class SongChartDifficulty:
    def __init__(self, data, name):
        self.level = int(data['Level'])
        self.has_separate_file = data['MusicID'] != ''
        self.is_unlock_needed: bool = data['NeedUnlock']
        self.music_id = data['MusicID']
        self.name: str = name

    def __str__(self):
        if self.has_separate_file:
            return f'SongChartDifficulty(level={self.level}, music_id={self.music_id})'

        return f'SongChartDifficulty(level={self.level})'


class SongChart:
    def __init__(self, data):
        self.easy: SongChartDifficulty = None
        self.hard: SongChartDifficulty = None
        self.chaos: SongChartDifficulty = None
        self.glitch: Optional[SongChartDifficulty] = None

        self.difficulties = list(map(str.lower, data.keys()))
        self.difficulties.sort(key=['easy', 'hard', 'chaos', 'glitch'].index)
        for difficulty, data in data.items():
            setattr(self, difficulty.lower(), SongChartDifficulty(data, difficulty))

    def __getitem__(self, item) -> SongChartDifficulty:
        return self.__getattribute__(item)

    def __str__(self):
        return f'SongChart({", ".join([item + "=" + str(self[item]) for item in self.difficulties])})'

    __repr__ = __str__
