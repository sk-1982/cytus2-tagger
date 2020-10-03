import mutagen.flac

from .OggTagger import OggTagger


class FLACTagger(OggTagger):
    format_types = [mutagen.flac.FLAC]

    def __init__(self, file: mutagen.flac.FLAC):
        self.file = file
        super().__init__(file)

    def album_art(self, art_location: str):
        picture = self.create_album_art(art_location)

        self.file.add_picture(picture)

        return self
