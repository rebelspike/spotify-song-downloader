<div align="center">  

  ### Spotify Song Downloader

  Downloads Spotify playlists in high quality from YouTube Music

</div> 

## Features
- No subscription required
- No login required
- Lightweight
- Downloads in a higher bitrate (around 300 kbps)
- Contains metadata (title, artist, album, etc)

## Warning
This program uses YouTube Music for music downloads, there is a chance of songs being mismatched

> Users are responsible for complying with YouTube Music and Spotify's terms of service

## Usage
This program requires **ffmpeg** to work. Install [ffmpeg](https://ffmpeg.org/download.html) and add the folder where `ffmpeg.exe` is located to PATH/system environment variables.


### Installation
1. Clone the repository.

   ```sh
   git clone https://github.com/rebelspike/spotify-song-downloader.git
   cd spotify-song-downloader
   ```
   
2. Create and activate a virtual environment (Optional but recommended).

   ```sh
   python -m venv venv
   venv\Scripts\activate.bat  # Windows
   source venv/bin/activate   # Linux/macOS
   ```
   
3. Install required dependencies.

   ```sh
   python -m pip install -r requirements.txt
   ```
   
4. Run the program with your playlist URL.

   ```sh
   python -m spotify-dl playlist_url
   ```

**Available Options**

- To specify where to store downloaded files:
  ```sh
  python -m spotify-dl -o path playlist_url
  ```

- To change audio format (for example mp3):
  ```sh
  python -m spotify-dl -f mp3 playlist_url
  ```

- To save as `<title> - <artist>.<ext>` instead of the default `<artist> - <title>.<ext>`:
  ```sh
  python -m spotify-dl --title-first playlist_url
  ```

## License
This software is licensed under the [MIT License](https://github.com/rebelspike/spotify-song-downloader/blob/main/LICENSE) © [Kamran](https://github.com/rebelspike)
