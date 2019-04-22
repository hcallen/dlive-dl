# dlive.tv VOD Downloader
A script to download dlive.tv VODs. It's a very quick and dirty port of my [stream.me VOD Downloader](https://github.com/hcallen/stream-me-dl) script.

## Requirements

[Python 3.6+](http://python.org)  

## Usage

Show help
```console
$ python3 dlive-dl.py -h 
usage: dlive-dl.py [-h] [-l] [-q #] [-o path] url

positional arguments:
  url                   vod url

optional arguments:
  -h, --help            show this help message and exit
  -l, --list            list available encodings and exit
  -q #, --quality #     define which quality of video to download
  -o path, --outdir path
                        directory to save the video to

```

Download default video quality (quality '1')
```console
$ python3 dlive-dl.py https://dlive.tv/p/user+vod_id
```
List available video qualities
```console
$ python3 dlive-dl.py -l https://dlive.tv/p/user+vod_id

user - title
1 - 480p - 858x480
2 - 720p - 1280x720
3 - src - 1920x1080
4 - 360p - 640x360
```
Download second listed quality
```console
$ python3 dlive-dl.py -q 2 https://dlive.tv/p/user+vod_id
```