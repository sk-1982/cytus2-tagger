import mutagen.oggvorbis
import mutagen.oggtheora
import mutagen.oggopus
import mutagen.oggflac
import mutagen.oggspeex
import mutagen.ogg
from PIL import Image
import io
import base64
from mutagen.flac import Picture
from utils import file_type, mode_to_depth

from .BaseTagger import BaseTagger


class OggTagger(BaseTagger):
    format_types = [mutagen.oggvorbis.OggVorbis, mutagen.oggtheora.OggTheora, mutagen.oggspeex.OggSpeex,
                    mutagen.oggopus.OggOpus, mutagen.oggflac.OggFLAC, mutagen.ogg.OggFileType]

    def __init__(self, file: mutagen.ogg.OggFileType):
        super().__init__(file)

    def title(self, title: str):
        self.file['title'] = title
        return self

    def subtitle(self, subtitle: str):
        self.file['subtitle'] = subtitle
        return self

    def comments(self, comments: str):
        self.file['description'] = comments
        return self

    def artist(self, artist: str):
        self.file['artist'] = artist
        return self

    def album_artist(self, artist: str):
        self.file['albumartist'] = artist
        return self

    def album(self, album: str):
        self.file['album'] = album
        return self

    def year(self, year: str):
        self.file['year'] = year
        return self

    def track_number(self, track_number: str):
        self.file['tracknumber'] = track_number
        return self

    def genre(self, genre: str):
        self.file['genre'] = genre
        return self

    def disc_number(self, disc: str):
        self.file['discnumber'] = disc
        return self

    def composer(self, composer: str):
        self.file['composer'] = composer
        return self

    def producer(self, producer: str):
        self.file['producer'] = producer
        return self

    def create_album_art(self, art_location: str):
        with open(art_location, 'rb') as image:
            image_data = image.read()

        image = Image.open(io.BytesIO(image_data))

        picture = Picture()
        picture.data = image_data
        picture.type = 3  # COVER_FRONT
        picture.mime = file_type(art_location)
        picture.width, picture.height = image.size
        picture.depth = mode_to_depth(image.mode)
        picture.desc = "Front Cover"

        image.close()

        return picture

    def album_art(self, art_location: str):
        picture = self.create_album_art(art_location)

        picture_data = picture.write()
        encoded_data = base64.b64encode(picture_data)
        vcomment_value = encoded_data.decode('ascii')

        self.file['metadata_block_picture'] = [vcomment_value]

        return self
