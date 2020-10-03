import mutagen.mp4
from mutagen.mp4 import MP4Cover

from utils import file_type

from .BaseTagger import BaseTagger

class MP4Tagger(BaseTagger):
    format_types = [mutagen.mp4.MP4]

    def __init__(self, file: mutagen.mp4.MP4):
        super().__init__(file)

    def title(self, title: str):
        self.file['\xa9nam'] = title
        return self

    def subtitle(self, subtitle: str):
        self.file['desc'] = subtitle
        return self

    def comments(self, comments: str):
        self.file['\xa9cmt'] = comments
        return self

    def artist(self, artist: str):
        self.file['\xa9ART'] = artist
        return self

    def album_artist(self, artist: str):
        self.file['aART'] = artist
        return self

    def album(self, album: str):
        self.file['\xa9alb'] = album
        return self

    def year(self, year: str):
        self.file['\xa9day'] = year
        return self

    def track_number(self, track_number: str):
        track_parts = track_number.split('/')
        self.file['trkn'] = [(int(track_parts[0]), int(track_parts[1]) if len(track_parts) > 1 else 0)]
        return self

    def genre(self, genre: str):
        self.file['\xa9gen'] = genre
        return self

    def disc_number(self, disc: str):
        disc_parts = disc.split('/')
        self.file['disk'] = [(int(disc_parts[0]), int(disc_parts[1]) if len(disc_parts) > 1 else 0)]
        return self

    def composer(self, composer: str):
        self.file['\xa9wrt'] = composer
        return self

    def producer(self, producer: str):
        print('Warning: MP4 does not support a producer tag')
        return self

    def album_art(self, art_location: str):
        with open(art_location, 'rb') as image:
            image_data = image.read()

        image_format = MP4Cover.FORMAT_PNG if file_type(art_location) == 'image/png' else MP4Cover.FORMAT_JPEG

        self.file['covr'] = [MP4Cover(image_data, imageformat=image_format)]

        return self

    def save(self):
        return self.file.save()
