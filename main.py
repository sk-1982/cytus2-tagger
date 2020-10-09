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
from time import time
from subprocess import check_output, CalledProcessError, Popen
from utils import kill_child_processes, find, special_file_filterer, parse_format
from encode import encode_song, ffmpeg
import encode

from models.Character import Character
from models.ExpansionPackInfo import ExpansionPackInfo
from models.Song import Song


remove_punctuation_map = dict((ord(char), '_') for char in r'\/*?:"<>|')

with open(find(sys.argv, lambda s: s.endswith('.yml')) or './config.yml', 'r', encoding='utf8') as f:
    config = yaml.load(f, yaml.Loader)

encode.FFMPEG_PATH = config['ffmpeg_path']


if __name__ == '__main__':
    try:
        check_output([config['ffmpeg_path'], '-hide_banner', '-h'])
    except FileNotFoundError:
        print('Error: ffmpeg binary not found. Please add it to the path or modify the file location in config.yml')
        sys.exit(1)

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
    parser.add_argument('config', nargs='?', default='config.yml', help='Config file to use (default: config.yml)')

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
