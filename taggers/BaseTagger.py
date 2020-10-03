import mutagen


class BaseTagger:
    def __init__(self, file: mutagen.FileType):
        self.file = file
        try:
            self.file.add_tags()
        except:
            pass

    def title(self, title: str): return self
    def subtitle(self, title: str): return self
    def comments(self, comments: str): return self
    def artist(self, artist: str): return self
    def album_artist(self, artist: str): return self
    def album(self, album: str): return self
    def year(self, year: str): return self
    def track_number(self, track_number: str): return self
    def genre(self, genre: str): return self
    def disc_number(self, disc: str): return self
    def composer(self, composer: str): return self
    def producer(self, producer: str): return self
    def album_art(self, art_location: str): return self
    def save(self): return self.file.save()
