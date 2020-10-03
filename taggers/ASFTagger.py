import mutagen.asf
import struct
from mutagen.asf import ASFUnicodeAttribute, ASFByteArrayAttribute

from utils import file_type

from .BaseTagger import BaseTagger


class ASFTagger(BaseTagger):
    format_types = [mutagen.asf.ASF]

    def __init__(self, file: mutagen.asf.ASF):
        super().__init__(file)

    def title(self, title: str):
        self.file['Title'] = ASFUnicodeAttribute(value=title)
        return self

    def subtitle(self, subtitle: str):
        self.file['WM/SubTitle'] = ASFUnicodeAttribute(value=subtitle)
        return self

    def comments(self, comments: str):
        self.file['Description'] = ASFUnicodeAttribute(value=comments)
        return self

    def artist(self, artist: str):
        self.file['Author'] = ASFUnicodeAttribute(value=artist)
        return self

    def album_artist(self, artist: str):
        self.file['WM/AlbumArtist'] = ASFUnicodeAttribute(value=artist)
        return self

    def album(self, album: str):
        self.file['WM/AlbumTitle'] = ASFUnicodeAttribute(value=album)
        return self

    def year(self, year: str):
        self.file['WM/Year'] = ASFUnicodeAttribute(value=year)
        return self

    def track_number(self, track_number: str):
        self.file['WM/TrackNumber'] = ASFUnicodeAttribute(value=track_number)
        return self

    def genre(self, genre: str):
        self.file['WM/Genre'] = ASFUnicodeAttribute(value=genre)
        return self

    def disc_number(self, disc: str):
        self.file['WM/PartOfSet'] = ASFUnicodeAttribute(value=disc)
        return self

    def composer(self, composer: str):
        self.file['WM/Composer'] = ASFUnicodeAttribute(value=composer)
        return self

    def producer(self, producer: str):
        self.file['WM/Producer'] = ASFUnicodeAttribute(value=producer)
        return self

    def album_art(self, art_location: str):
        with open(art_location, 'rb') as image:
            image_data = image.read()

        # https://github.com/beetbox/mediafile/blob/master/mediafile.py#L231
        value = struct.pack('<bi', 3, len(image_data))
        value += file_type(art_location).encode('utf-16-le') + b'\x00\x00'
        value += 'Cover'.encode('utf-16-le') + b'\x00\x00'
        value += image_data

        self.file['WM/Picture'] = ASFByteArrayAttribute(value=value)
        return self
