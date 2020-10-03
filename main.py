import argparse
import glob
import yaml
import sys
import random
import string
import mutagen
import os
import taggers
import json
import re
import concurrent.futures
import signal
import psutil
from time import time
from subprocess import check_output, CalledProcessError, Popen, PIPE

from models.Character import Character
from models.ExpansionPackInfo import ExpansionPackInfo
from models.Song import Song

remove_punctuation_map = dict((ord(char), '_') for char in '\/*?:"<>|')


def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        process.send_signal(sig)

    parent.send_signal(sig)


def ffmpeg(*args, print=False):
    command_line = ['ffmpeg', '-loglevel', 'panic', '-y', *args]

    if not print:
        return check_output(command_line)

    process = Popen(command_line, stdout=PIPE, stderr=PIPE)
    for c in iter(lambda: process.stdout.read(1), b''):
        sys.stdout.buffer.write(c)


def parse_format(format: dict, local_dict: dict):
    for key in local_dict.keys():
        exec(f'{key} = local_dict["{key}"]')

    return {
        key: re.sub(r'{(.+?)}', lambda m: str(eval(m.group(1))), value)
        if type(value) == str else value
        for key, value in format.items()
    }


def find(iterable, predicate):
    for item in iterable:
        if predicate(item):
            return item


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


if __name__ == '__main__':
    try:
        check_output(['ffmpeg', '-hide_banner', '-h'])
    except FileNotFoundError:
        print('Error: ffmpeg binary not found')
        sys.exit(1)

    with open('./config.yml', 'r', encoding='utf8') as f:
        config = yaml.load(f, yaml.Loader)

    parser = argparse.ArgumentParser(description='Convert Cytus 2 files to music album')
    parser.add_argument('-i', '--input-dir', dest='input_dir', type=str, default=config['input_dir'],
                        help=f'Input directory to use (default: {config["input_dir"]})')
    parser.add_argument('-o', '--output-dir', dest='output_dir', type=str, default=config['output_dir'],
                        help=f'Output directory to use (default: {config["output_dir"]})')
    parser.add_argument('-f', '--format', dest='format', type=str, default=config['format'],
                        help=f'File extension for files, such as mp3, flac, etc. (default: {config["format"]})')
    parser.add_argument('-c', '-c:a', '--codec', dest='codec', type=str, default=config['codec'],
                        help=f'Codec for files, such as alac, mp3, etc. Will be inferred if None (default: {config["codec"]}). '
                             'Note: for alac, use -f m4a -c alac')
    parser.add_argument('-b', '-b:a', '--bitrate', dest='bitrate', type=str, default=config['bitrate'],
                        help=f'Bitrate for ffmpeg, will use ffmpeg default if None (default: {config["bitrate"]})')

    args = parser.parse_args()

    print('Testing ffmpeg compatibility with file type', args.format)

    test_file = 'test' + ''.join(random.choices(string.digits + string.ascii_letters, k=16)) + '.' + args.format

    try:
        ffmpeg('-f', 'lavfi', '-i', 'anullsrc', '-t', '1', *([] if not args.codec else ['-c:a', args.codec]),
               *([] if not args.bitrate else ['-b:a', args.bitrate]), test_file)
    except CalledProcessError:
        print('Error: unsupported format', args.format, '(ffmpeg returned error)')
        sys.exit(1)

    print('Testing mutagen tagging compatibility with file type', args.format)
    mutagen_type = mutagen.File(test_file)
    tagger = taggers.tagger_for_type(type(mutagen_type))
    tagger_name = None

    if mutagen_type is None:
        print(f'Warning: mutagen does not support tagging with file type {args.format}. Music tags will not be added')
    elif not tagger:
        print(f'Warning: tagging support for file type {args.format} is not implemented. Music tags will not be added')
    else:
        tagger_name = tagger.__name__

    os.remove(test_file)

    special_files = []

    for special_file in config['special_files']:
        folder_name = special_file['folder_name'] if 'folder_name' in special_file else None
        special_files.append((special_file['input_filename'], folder_name))
        if 'intro' in special_file:
            special_files.append((special_file['intro'], folder_name))

    def special_file_filterer(special_file, file_base_name, base_dir_name):
        special_file_filename, special_file_dir_name = special_file
        invert = special_file_dir_name and special_file_dir_name[0] == '!'

        if file_base_name != special_file_filename:
            return False

        if special_file_dir_name and invert and base_dir_name == special_file_dir_name[1:]:
            return False

        if special_file_dir_name and not invert and base_dir_name != special_file_dir_name:
            return False

        return True


    music_wavs = {}
    music_thumbnails = {}
    song_pack_data = None
    expansion_pack_data = None
    character_album_art = {}

    print('Building file table')

    for file in glob.iglob(f'{config["character_art_folder"]}/*'):
        file_name = os.path.basename(file)
        if file_name.endswith('.png') or file_name.endswith('.jpg') or file_name.endswith('.jpeg'):
            character_album_art[os.path.splitext(file_name)[0]] = file

    for file in glob.iglob(f'{args.input_dir}/**/*', recursive=True):
        file_name = os.path.basename(file)
        dir_name = os.path.dirname(file)
        base_dir_name = os.path.basename(dir_name)
        file_base_name, file_extension = os.path.splitext(file_name)

        found = False

        if file_name == 'song_pack_data.bytes':
            found = True
            with open(file, 'r', encoding='utf8') as f:
                song_pack_data = json.load(f)
        elif file_name == 'expansion_pack_data.bytes':
            found = True
            with open(file, 'r', encoding='utf8') as f:
                expansion_pack_data = json.load(f)
        elif base_dir_name != 'previews' and re.match(r'[a-z]{2,8}00\d(?:_\d{3})?(?:_\d)?\.wav$', file_name,
                                                      re.IGNORECASE):
            found = True
            music_wavs[file_name] = file
        elif base_dir_name == 'unlocksongcovers' and re.match(r'[a-z]{2,8}00\d_\d{3}(?:_\d)?\.png$', file_name,
                                                              re.IGNORECASE):
            found = True
            music_thumbnails[file_name] = file
        elif file_extension == '.wav':
            special_file = find(special_files, lambda f: special_file_filterer(f, file_base_name, base_dir_name))

            if special_file:
                found = True
                special_file_name, special_dir_name = special_file
                key = special_file_name if not special_dir_name else f'{special_dir_name}/{special_file_name}'
                music_wavs[key] = file

        if found:
            print('Found', file_name)

    print('Parsing character and song data')

    characters = {}

    for index, character_data in enumerate(song_pack_data['offline_song_pack_list']):
        character = Character(character_data)
        character.number = index + 1

        for song_data in character_data['song_info_list']:
            song = Song(song_data, character.id)
            if config['rename_aesir'] and song.artist == 'Æsir':
                song.artist = config['rename_aesir_to']
            character.songs.append(song)

        characters[character.id] = character

    for expansion_pack in expansion_pack_data['ExpansionPackList']:
        pack_info = ExpansionPackInfo(expansion_pack)
        for song_data in expansion_pack['SongInfoList']:
            song = Song(song_data)
            if config['rename_aesir'] and song.artist == 'Æsir':
                song.artist = config['rename_aesir_to']
            song.expansion_pack_info = pack_info
            characters[song.character_id].songs.append(song)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        completed_futures = 0


        def submit_task(format, locals, input_file, album_art, extra_args_before=None, extra_args_after=None):
            if extra_args_after is None:
                extra_args_after = []

            extra_args_after = [
                *([] if not args.codec else ['-c:a', args.codec]),
                *([] if not args.bitrate else ['-b:a', args.bitrate]),
                *extra_args_after
            ]

            song_format = parse_format(format, locals)
            output_file = os.path.join(args.output_dir, song_format['output_dir'],
                                       song_format['filename'].translate(remove_punctuation_map) + '.' + args.format)

            futures.append(
                executor.submit(
                    encode_song,
                    input_file,
                    output_file,
                    tagger_name,
                    {"album_art": album_art, **song_format},
                    extra_args_before,
                    extra_args_after
                )
            )


        for character in characters.values():
            character.songs.sort(key=lambda song: song.number)

            format = config['music_format_character_theme']

            if format['enabled']:
                album_art = None
                if character.id in character_album_art:
                    album_art = character_album_art[character.id]

                submit_task(format, locals(), music_wavs[character.id + '.wav'], album_art,
                            extra_args_before=['-stream_loop', str(format['loops'])])

            for song in character.songs:
                format = config['music_format']

                album_art = None
                if config['album_art_style'] == 'character' and character.id in character_album_art:
                    album_art = character_album_art[character.id]
                elif config['album_art_style'] == 'track':
                    album_art = music_thumbnails[song.id + '.png']

                if format['enabled']:
                    if song.id + '.wav' in music_wavs:
                        submit_task(format, locals(), music_wavs[song.id + '.wav'], album_art)
                    else:
                        print('skipping', song.id, song.name, f'({song.id}.wav not found)')

                for difficulty in song.separate_difficulties:
                    format = config['music_format_separate_difficulty']

                    if format['enabled']:
                        if difficulty.music_id + '.wav' in music_wavs:
                            submit_task(format, locals(), music_wavs[difficulty.music_id + '.wav'], album_art)
                        else:
                            print('skipping', difficulty.music_id, song.name, f'({difficulty.music_id}.wav not found)')

        for format in config['special_files']:
            if not format['enabled']:
                continue

            prefix = f'{format["folder_name"]}/' if 'folder_name' in format else ''

            extra_args_before = []
            extra_args_after = []

            if 'intro' in format:
                extra_args_before.extend(['-i', music_wavs[prefix + format['intro']]])
                extra_args_after.extend(['-filter_complex', '[0:0][1:0]concat=n=2:v=0:a=1[out]', '-map', '[out]'])

            if 'loops' in format:
                extra_args_before.extend(['-stream_loop', str(format['loops'])])

            submit_task(format, locals(), music_wavs[prefix + format['input_filename']],
                        music_thumbnails[format['album_art_name']] if 'album_art_name' in format
                                                                      and format['album_art_name'] else None,
                        extra_args_before=extra_args_before, extra_args_after=extra_args_after)

        def stop():
            executor.shutdown(wait=False)
            if hasattr(signal, 'SIGKILL'):
                kill_child_processes(os.getpid(), signal.SIGKILL)
            else:
                kill_child_processes(os.getpid())
                Popen(['taskkill', '/F', '/PID', str(os.getpid())], shell=True)

        start = time()

        for future in concurrent.futures.as_completed(futures):
            try:
                exception = future.exception()
                if exception:
                    print(exception)
                    stop()
                    raise exception

                completed_futures += 1
                file_name = future.result()

                estimated_remaining = (time() - start) / completed_futures * (len(futures) - completed_futures)
                eta_min, eta_sec = divmod(estimated_remaining, 60)

                print('processed', file_name, f'({completed_futures}/{len(futures)}). ETA: {round(eta_min)} m {round(eta_sec)} s')
            except KeyboardInterrupt:
                stop()
