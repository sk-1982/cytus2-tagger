# Cytus II Tagger
This repository contains various tools for pulling, extracting, and tagging music game files from Cytus II.

Prerequisites:
* [A copy of this repository](https://github.com/sk-1982/cytus2-tagger/archive/main.zip)
* [Latest version of Python](https://www.python.org/downloads/)
* Android device with Cytus II installed
    * DLC music will not be processed if they are not downloaded on the device (see [DLC music table](#dlc-music-table-345))
* [ADB installed on path and USB debugging enabled](https://www.xda-developers.com/install-adb-windows-macos-linux/)
* [FFmpeg installed on path](https://blog.gregzaal.com/how-to-install-ffmpeg-on-windows/)
* [uTinyRipper for extracting Unity assets](https://sourceforge.net/projects/utinyripper/files/)

## Usage
1. Follow the above prerequisites instructions
1. Open a command prompt in the repository folder
1. Run `pip3 install -r requirements.txt`

Pulling files from device:
1. Unlock your android device and plug it into your computer (accept any USB debugging prompts)
1. Run `python pull-files.py` to extract game files into the `data` directory

Extracting Unity assets:
1. Open the `assets` folder inside the `data` folder
1. Open uTinyRipper and drag over `bin` folder inside the `assets` folder onto the program
1. Export the files to the base repo directory. This will create a folder named `globalgamemanagers`
1. Click reset and open the `AssetBundles` folder inside the `assets` folder
1. Press `Ctrl+A` and drag all the files inside the folder onto uTinyRipper and export them to the base repo directory.
1. This will create a folder that ends with `.ab`. Open that folder, and move the `Assets` folder into the `globalgamemanagers` folder

Tagging and encoding files:
1. Open `config.yml` and change what you want (sensible defaults have been set for you)
1. Run `python main.py -f {format}` where `{format}` is the file extension you want (ex: `python main.py -f mp3`)
    * Note: for ALAC, run `python main.py -f m4a -c alac`
    * A different config file for track-based tagging has been provided with `config-track.yml`. Run `python main.py -f {format} config-track.yml` to use it.

## DLC music table (3.4.5)

The following songs need to be downloaded if you want them to be processed.  
Note: tapping "download all" on the download screen in-game will download all the character's songs you own.

| Character | Songs                                                                                                                                                                                                                                                                            |
|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| NEKO      | PrayStation (HiTECH NINJA Remix)<br /> 100sec Cat Dreams<br /> REmorse<br /> Stranger<br /> 小悪魔×3の大脱走！？<br /> Online<br /> Sunday Night Blues<br /> Blow My Mind (tpz Overheat Remix)<br /> Maboroshi<br /> TOKONOMA Spacewalk<br /> UnNOT!CED<br /> 下水鳴動して鼠一匹 |
| ROBO_Head | Sickest City<br /> Jazzy Glitch Machine<br /> dimensionalize nervous breakdown (rev.flat)<br /> cold<br /> NRG_Tech<br /> Break Through The Barrier<br /> Dead Master                                                                                                            |
| Paff      | So In Love                                                                                                                                                                                                                                                                       |
| Ivy       | Cristalisia<br /> Occidens<br /> Red Five<br /> Homebound Train & Moving Thoughts<br /> iL<br /> CODE NAME : SIGMA<br /> New Challenger Approaching<br /> What's Your PR.Ice?<br /> VIS::CRACKED<br /> Wicked Ceremony                                                           |

## Advanced Usage

#### `pull-files.py`

| Argument           | Description                                                                                 |
|--------------------|---------------------------------------------------------------------------------------------|
| `-h, --help`       | Show help message                                                                           |
| `-s, --serial`     | ADB device serial if more than once device is connected (use `adb devices` to show devices) |
| `-o, --output-dir` | Directory to output extracted files to (default: `data`)                                      |
| `--skip-cleanup`   | Don't remove obb and apk files after running                                                |
| `--pull-only`      | Pull apk, obb, and asset bundles from device only; skip extraction                          |
| `--extract-only`   | Extract data from apk, obb, and asset bundles only; skip pulling (requires `--input-dir`)   |
| `-i, --input-dir`  | Input directory with apk, obb, and asset bundles if using `--extract-only`                  |

Examples:
* `python pull-files.py -s ABCDEFG -o output`
    * Extract files from device with serial `ABCDEFG` into directory `output`
* `python pull-files.py --pull-only -o pulled`
    * Pull files from device into directory `pulled` (skip extraction)
* `python pull-files.py --extract-only -i pulled -o extracted`
    * Extract files from the directory `pulled` into directory `extracted`

#### `main.py`

| Argument              | Description                                                                                          |
|-----------------------|------------------------------------------------------------------------------------------------------|
| `-h, --help`          | Show help message                                                                                    |
| `-i, --input-dir`     | Input directory to use (default: `globalgamemanagers`)                                               |
| `-o, --output-dir`    | Output directory to use (default: `music`)                                                           |
| `-f, --format`        | File extension to use, such as `mp3`, `flac`, `m4a`, etc. (default: `mp3`)                           |
| `-c, -c:a, --codec`   | Codec for files, such as `alac`, `mp3`, `opus`, etc. Will be inferred from file extension if not set |
| `-b, -b:a, --bitrate` | Override bitrate for files, such as `320k`                                                           |
| `config`              | Config file to use (default: `config.yml`)                                                           |

Examples:
* `python main.py -o music-mp3 -f mp3 -b:a 320k`
    * Encode music into the `music-mp3` folder with `mp3` file extension and `320kbps` bitrate
* `python main.py -o music-flac -f flac config-track.yml`
    * Encode music into the `music-flac` folder with `flac` file extension, using the `config-track.yml` config file
* `python main.py -o music-alac -f m4a -c:a alac`
    * Encode music into the `music-alac` folder with `m4a` file extension with `alac` codec.
