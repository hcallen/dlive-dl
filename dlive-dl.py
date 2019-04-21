import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.request


def main():
    # define args
    # TODO: add out dir
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='vod archive url')
    parser.add_argument('-l', '--list', help='list available encodings and exit', action='store_true')
    parser.add_argument('-q', '--quality', help='define which quality of video to download', type=int, metavar='#',
                        default=1)
    args = parser.parse_args()

    vod_id = args.url.split('/')[-1]
    pb_info = get_playback_info(args.url)

    # define video info
    root_query = f'$ROOT_QUERY.pastBroadcast({{"permlink":"{vod_id}"}})'
    info = pb_info['defaultClient'][root_query]
    title = info['title']
    user = info['creator']['id'].split('user:')[1]
    playback_url = info['playbackUrl']

    vid_info = parse_vod_m3u8(playback_url)
    videos = []
    for vid in vid_info:
        v = Video(user, title, vid['resolution'], vid['quality'], vid['url'])
        videos.append(v)

    if args.list:
        print_qualities(videos)
        sys.exit(0)

    if args.quality > len(videos) or args.quality < 0:
        raise Exception('Selected quality doesn\'t exist')

    # download video
    try:
        video = videos[args.quality - 1]
    except IndexError:
        video = videos[0]
    video.download()
    sys.exit(0)


def get_playback_info(url):
    response = urllib.request.urlopen(url)
    html = response.read().decode('utf-8')
    text = html.replace('\n', '').replace('\t', '')
    match = re.search('<script>window.__APOLLO_STATE__=(.*);\(function', text)
    if not match:
        raise Exception('Failed to find playback info')
    return json.loads(match.group(1))


def print_qualities(videos):
    print(f'\n{videos[0].user} - {videos[0].title}')
    for i, video in enumerate(videos):
        print(f'{i + 1} - {video.quality} - {video.resolution}')


def parse_vod_m3u8(url):
    vid_info = []
    m3u8_text = urllib.request.urlopen(url).read().decode('utf-8')
    m3u8_lines = m3u8_text.splitlines()
    for i, line in enumerate(m3u8_lines):
        if line.startswith('#EXT-X-STREAM-INF:'):
            re_str = '#EXT-X-STREAM-INF:PROGRAM-ID=(?P<program_id>.*),BANDWIDTH=(?P<bandwidth>.*),' \
                     'CODECS="(?P<codecs>.*)",RESOLUTION=(?P<resolution>.*),VIDEO="(?P<quality>.*)"'
            match = re.search(re_str, line)
            v = {'resolution': match.group('resolution'),
                 'quality': match.group('quality'),
                 'url': m3u8_lines[i + 1]}
            vid_info.append(v)
    return vid_info


class Video(object):
    def __init__(self, user, title, resolution, quality, playback_url):
        self.user = user
        self.title = title
        self.resolution = resolution
        self.quality = quality
        self.m3u8_url = playback_url
        self.filename = f'{self.user}-{self.title}-{resolution}-{quality}.mp4'
        self._ts_urls = None
        self._duration = None
        self._m3u8 = None
        self._size = None

    def download(self, out_dir=None):
        if not out_dir:
            out_dir = os.getcwd()
        temp_dir = tempfile.TemporaryDirectory()
        ts_files = self._download_ts_files(temp_dir)
        self._merge_ts_files(ts_files, out_dir)
        temp_dir.cleanup()
        print('\nDone!')

    def _download_ts_files(self, temp_dir):
        out_files = []
        i = 0
        while i < len(self.ts_urls):
            percent = ((i + 1) / len(self.ts_urls)) * 100
            print(f'Downloading {self.filename} - part {i + 1} of {len(self.ts_urls)} - {percent:0.2f}%', end='\r')
            out_file = os.path.join(temp_dir.name, str(i) + '.ts')
            block_size = 1024
            try:
                response = urllib.request.urlopen(self.ts_urls[i])
                with open(out_file, 'wb') as f:
                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        f.write(buffer)
                out_files.append(out_file)
                i += 1
            except ConnectionResetError:
                print(f'Failed to download {self.title} - part {i + 1} of '
                      f'{len(self.ts_urls)} - {percent:0.2f}%', end='\r')
                print('\nRetrying download')

        print('')
        return out_files

    def _merge_ts_files(self, ts_list, out_dir):
        with open(os.path.join(out_dir, self.filename), 'wb') as merged:
            for i, ts_file in enumerate(ts_list):
                percent = ((i + 1) / len(ts_list) * 100)
                with open(ts_file, 'rb') as merged_file:
                    shutil.copyfileobj(merged_file, merged)
                print(f'Merging files - {percent:0.2f}%', end='\r')

    @property
    def ts_urls(self):
        if self._ts_urls:
            return self._ts_urls
        self._ts_urls = []
        for line in self.m3u8.splitlines():
            if line.endswith('.ts'):
                self._ts_urls.append(line)
        return self._ts_urls

    @property
    def m3u8(self):
        if self._m3u8:
            return self._m3u8
        self._m3u8 = urllib.request.urlopen(self.m3u8_url).read().decode('utf-8')
        return self._m3u8

    @property
    def duration(self):
        if self._duration:
            return self._duration
        self._duration = 0
        for line in self.m3u8.splitlines():
            match = re.search('^#EXTINF:(\d*.\d*),', line)
            if match:
                self._duration += float(match.group(1))
        return self._duration

    # @property
    # def size(self):
    #     if self._size:
    #         return self._size
    #     # convert to MBs
    #     self._size = (self.video_kbps + self.audio_kbps) * (self.duration / 60) * 0.0075
    #     return self._size


if __name__ == '__main__':
    main()
