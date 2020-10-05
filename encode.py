import sys
import os
import mutagen
import taggers
from subprocess import check_output, Popen, PIPE


FFMPEG_PATH = 'ffmpeg'


def ffmpeg(*args, print=False):
    command_line = [FFMPEG_PATH, '-loglevel', 'panic', '-y', *args]

    if not print:
        return check_output(command_line)

    process = Popen(command_line, stdout=PIPE, stderr=PIPE)
    for c in iter(lambda: process.stdout.read(1), b''):
        sys.stdout.buffer.write(c)


def encode_song(input_file, output_file, tagger_name, format, extra_args_before=None, extra_args_after=None):
    if extra_args_after is None:
        extra_args_after = []
    if extra_args_before is None:
        extra_args_before = []

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    if os.path.exists(output_file) and os.path.isfile(output_file):
        print('File', output_file, 'already exists, skipping')
        return output_file

    tagger = taggers.tagger_by_name(tagger_name)

    ffmpeg(*extra_args_before, '-i', input_file, *extra_args_after, output_file, print=True)

    if not tagger:
        return output_file

    file_tagger = tagger(mutagen.File(output_file))

    if 'title' in format and format['title']:
        file_tagger.title(format['title'])

    if 'subtitle' in format and format['subtitle']:
        file_tagger.subtitle(format['subtitle'])

    if 'comments' in format and format['comments']:
        file_tagger.comments(format['comments'])

    if 'artist' in format and format['artist']:
        file_tagger.artist(format['artist'])

    if 'album_artist' in format and format['album_artist']:
        file_tagger.album_artist(format['album_artist'])

    if 'album' in format and format['album']:
        file_tagger.album(format['album'])

    if 'year' in format and format['year']:
        file_tagger.year(format['year'])

    if 'number' in format and format['number']:
        file_tagger.track_number(format['number'])

    if 'genre' in format and format['genre']:
        file_tagger.genre(format['genre'])

    if 'disc_number' in format and format['disc_number']:
        file_tagger.disc_number(format['disc_number'])

    if 'composer' in format and format['composer']:
        file_tagger.composer(format['composer'])

    if 'producer' in format and format['producer']:
        file_tagger.producer(format['producer'])

    if 'album_art' in format and format['album_art']:
        file_tagger.album_art(format['album_art'])

    file_tagger.save()

    return output_file
