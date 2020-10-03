import mutagen.apev2
import mutagen.optimfrog
import mutagen.monkeysaudio
import mutagen.wavpack
import mutagen.musepack

from mutagen.apev2 import APETextValue, APEBinaryValue

from .BaseTagger import BaseTagger


# return to monke
class APEv2Tagger(BaseTagger):
    format_types = [mutagen.apev2.APEv2File, mutagen.optimfrog.OptimFROG, mutagen.monkeysaudio.MonkeysAudio,
                    mutagen.wavpack.WavPack, mutagen.musepack.Musepack]

    def __init__(self, file: mutagen.apev2.APEv2File):
        super().__init__(file)

    def title(self, title: str):
        self.file['Title'] = APETextValue(value=title, kind=0)
        return self

    def subtitle(self, subtitle: str):
        self.file['subtitle'] = APETextValue(value=subtitle, kind=0)
        return self

    def comments(self, comments: str):
        self.file['Comment'] = APETextValue(value=comments, kind=0)
        return self

    def artist(self, artist: str):
        self.file['Artist'] = APETextValue(value=artist, kind=0)
        return self

    def album_artist(self, artist: str):
        self.file['Album artist'] = self.file['ALBUMARTIST'] = APETextValue(value=artist, kind=0)
        return self

    def album(self, album: str):
        self.file['Album'] = APETextValue(value=album, kind=0)
        return self

    def year(self, year: str):
        self.file['Year'] = APETextValue(value=year, kind=0)
        return self

    def track_number(self, track_number: str):
        self.file['Track'] = APETextValue(value=track_number, kind=0)
        return self

    def genre(self, genre: str):
        self.file['Genre'] = APETextValue(value=genre, kind=0)
        return self

    def disc_number(self, disc: str):
        self.file['DISCNUMBER'] = APETextValue(value=disc, kind=0)
        return self

    def composer(self, composer: str):
        self.file['COMPOSER'] = APETextValue(value=composer, kind=0)
        return self

    def producer(self, producer: str):
        self.file['producer'] = APETextValue(value=producer, kind=0)
        return self

    def album_art(self, art_location: str):
        value = b'Cover\x00'

        with open(art_location, 'rb') as image:
            value += image.read()

        self.file['Cover Art (Front)'] = APEBinaryValue(value=value, kind=1)

        return self
