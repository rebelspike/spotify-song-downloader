__version__ = "1.3"
__author__ = "github.com/rebelspike"

import concurrent.futures

from typing import TypedDict
from time import sleep
from random import uniform
from sys import exit
from itertools import chain

from spotapi import Public
from innertube import InnerTube
from yt_dlp import YoutubeDL

DOWNLOAD_PATH = "./downloads/"
AUDIO_FORMAT = "m4a"
CONCURRENT_LIMIT = 3

client = None


class PlaylistInfo(TypedDict):
    title: str
    artist: str
    length: int


def get_playlist_info(playlist_id: str) -> list[PlaylistInfo]:
    """Extracts data from Spotify playlist and return them in the format
       `[{"title": title, "artist": artist, "length": length}]`."""

    result: list[PlaylistInfo] = []

    try:
        chunks = list(Public.playlist_info(playlist_id))
        items = list(chain.from_iterable([chunk["items"] for chunk in chunks]))
    except KeyError:
        return result

    for item in items:
        item = item["itemV2"]["data"]

        assert item["__typename"] in ("Track", "LocalTrack", "RestrictedContent", "NotFound", "Episode"), f"typename is {item['__typename']}"

        song: PlaylistInfo

        if item["__typename"] == "Track":
            song = {
                "title": item["name"],
                "artist": item["artists"]["items"][0]["profile"]["name"],
                "length": int(item["trackDuration"]["totalMilliseconds"])
            }
        elif item["__typename"] == "LocalTrack":
            song = {
                "title": item["name"],
                "artist": item["artistName"],
                "length": int(item["localTrackDuration"]["totalMilliseconds"])
            }
        else:
            continue

        if song in result:
            continue

        result.append(song)

    return result


def convert_to_milliseconds(text: str) -> int:
    """Converts `"%M:%S"` timestamp from YTMusic to milliseconds."""
    try:
        minutes, seconds = text.split(":")
    except ValueError:
        return 0

    return (int(minutes) * 60 + int(seconds)) * 1000


def get_song_url(song_info: PlaylistInfo) -> tuple[str, str]:
    """Simulates searching from the YTMusic web and returns url to the
    closest match."""

    global client
    if client is None:
        client = InnerTube("WEB_REMIX", "1.20250804.03.00")
    data = client.search(f"{song_info['title']} {song_info['artist']}")

    if "itemSectionRenderer" in data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]:
        del data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]

    try:
        first_song_id = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["overlay"]["musicItemThumbnailOverlayRenderer"]["content"]["musicPlayButtonRenderer"]["playNavigationEndpoint"]["watchEndpoint"]["videoId"]
        first_song_title = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["text"]
        first_song_length = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["musicShelfRenderer"]["contents"][0]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][-1]["text"]
        first_song_diff = abs(convert_to_milliseconds(first_song_length) - song_info["length"])
    except (KeyError, IndexError):
        first_song_length = 0

    try:
        top_result_id = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["title"]["runs"][0]["navigationEndpoint"]["watchEndpoint"]["videoId"]
        top_result_title = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["title"]["runs"][0]["text"]
        top_result_length = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["musicCardShelfRenderer"]["subtitle"]["runs"][-1]["text"]
        top_result_diff = abs(convert_to_milliseconds(top_result_length) - song_info["length"])
    except (KeyError, IndexError):
        top_result_length = 0

    url_part = "https://music.youtube.com/watch?v="

    if first_song_length and top_result_length:
        if top_result_diff < first_song_diff:
            return url_part + top_result_id, top_result_title
        else:
            return url_part + first_song_id, first_song_title
    elif top_result_length:
        return url_part + top_result_id, top_result_title
    elif first_song_length:
        return url_part + first_song_id, first_song_title
    else:
        return ("", "")


def get_song_urls(playlist_info: list[PlaylistInfo],
                  concurrent_limit: int) -> list[str]:
    """Repeatedly calls `get_song_url` on given playlist info.
    Returns list of results."""

    def process_song_entry(song_info: PlaylistInfo):
        """Helper function for concurrency in `get_song_urls`.
        Reports and prints status to user,
        returns matched url."""

        print(f"[MATCHING] {song_info['title']}")
        url, title = get_song_url(song_info)

        if url:
            print(f"[FOUND] {title} ({url})")
        else:
            print(f"[NO MATCH] {song_info['title']}")

        sleep(uniform(1, 2.5))

        return url

    urls: list[str] = []

    batches = [playlist_info[i: i+concurrent_limit]
               for i in range(0, len(playlist_info), concurrent_limit)]

    for batch in batches:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            urls.extend(executor.map(process_song_entry, batch))
        print()

    return urls


def download_from_urls(urls: list[str], output_dir: str,
                       audio_format: str, title_first: bool,
                       download_archive: str | None) -> None:
    """Downloads list of songs with yt-dlp"""

    if not output_dir.endswith("/"):
        output_dir += "/"

    if title_first:
        filename = f"{output_dir}%(title)s - %(creator)s.%(ext)s"
    else:
        filename = f"{output_dir}%(creator)s - %(title)s.%(ext)s"

    options = {'concurrent_fragment_downloads': 3,
               'extract_flat': 'discard_in_playlist',
               'final_ext': 'm4a',
               'format': 'bestaudio/best',
               'fragment_retries': 10,
               'ignoreerrors': 'only_download',
               'outtmpl': {'default': filename,
                           'pl_thumbnail': ''},
               'postprocessor_args': {'ffmpeg': ['-c:v',
                                                 'mjpeg',
                                                 '-vf',
                                                 "crop='if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'"]},
               'postprocessors': [{'format': 'jpg',
                                   'key': 'FFmpegThumbnailsConvertor',
                                   'when': 'before_dl'},
                                  {'key': 'FFmpegExtractAudio',
                                   'nopostoverwrites': False,
                                   'preferredcodec': audio_format,
                                   'preferredquality': '5'},
                                  {'add_chapters': True,
                                   'add_infojson': 'if_exists',
                                   'add_metadata': True,
                                   'key': 'FFmpegMetadata'},
                                  {'already_have_thumbnail': False,
                                   'key': 'EmbedThumbnail'},
                                  {'key': 'FFmpegConcat',
                                   'only_multi_video': True,
                                   'when': 'playlist'}],
               'retries': 10,
               'writethumbnail': True}

    if download_archive:
        options["download_archive"] = f"{output_dir}{download_archive}"

    with YoutubeDL(options) as ydl:
        ydl.download(urls)


def main(playlist_id: str,
         output_dir: str,
         audio_format: str,
         title_first: bool,
         concurrent_limit: int,
         download_archive: str | None) -> None:
    playlist_info = get_playlist_info(playlist_id)

    if not playlist_info:
        print("Invalid playlist URL. Aborting operation.")
        exit(1)

    download_urls = get_song_urls(playlist_info, concurrent_limit)
    download_from_urls(download_urls, output_dir, audio_format,
                       title_first, download_archive)


if __name__ == "__main__":
    url = "https://open.spotify.com/playlist/22hvxfJq0KwpgulLhDGslq"
    main(url, DOWNLOAD_PATH, AUDIO_FORMAT, False, CONCURRENT_LIMIT, ".archive")
