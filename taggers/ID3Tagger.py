import mutagen.id3
import mutagen.wave
import mutagen.aiff
import mutagen.mp3
import mutagen.trueaudio
import mutagen.dsdiff
import mutagen.dsf

from mutagen.id3 import TALB, TPE2, TPE1, COMM, TCOM, TCON, TIT2, TIT3, TRCK, TDRC, TPOS, APIC, IPLS

from .BaseTagger import BaseTagger

from utils import file_type


class ID3Tagger(BaseTagger):
    format_types = [mutagen.id3.ID3FileType, mutagen.id3.ID3, mutagen.wave.WAVE, mutagen.aiff.AIFF, mutagen.mp3.MP3,
                    mutagen.trueaudio.TrueAudio, mutagen.dsdiff.DSDIFF, mutagen.dsf.DSF]

    def __init__(self, file: mutagen.id3.ID3FileType):
        super().__init__(file)

    def title(self, title: str):
        self.file['TIT2'] = TIT2(encoding=3, text=title)
        return self

    def subtitle(self, subtitle: str):
        self.file['TIT3'] = TIT3(encoding=3, text=subtitle)
        return self

    def comments(self, comments: str):
        self.file['COMM'] = COMM(encoding=3, text=comments)
        return self

    def artist(self, artist: str):
        self.file['TPE1'] = TPE1(encoding=3, text=artist)
        return self

    def album_artist(self, artist: str):
        self.file['TPE2'] = TPE2(encoding=3, text=artist)
        return self

    def album(self, album: str):
        self.file['TALB'] = TALB(encoding=3, text=album)
        return self

    def year(self, year: str):
        self.file['TDRC'] = TDRC(encoding=3, text=year)
        return self

    def track_number(self, track_number: str):
        self.file['TRCK'] = TRCK(encoding=3, text=track_number)
        return self

    def genre(self, genre: str):
        self.file['TCON'] = TCON(encoding=3, text=genre)
        return self

    def disc_number(self, disc: str):
        self.file['TPOS'] = TPOS(encoding=3, text=disc)
        return self

    def composer(self, composer: str):
        self.file['TCOM'] = TCOM(encoding=3, text=composer)
        return self

    def producer(self, producer: str):
        self.file['IPLS'] = IPLS(encoding=3, people=[['producer', producer]])
        return self

    def album_art(self, art_location: str):
        with open(art_location, 'rb') as image:
            image_data = image.read()

        self.file['APIC'] = APIC(
            encoding=0,
            mime=file_type(art_location),
            type=3,
            desc='Cover',
            data=image_data
        )

        return self
