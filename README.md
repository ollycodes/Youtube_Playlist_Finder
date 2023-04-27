# GPT Playlist Maker
gpt_playlist is a simple script meant to automate the creation of youtube playlists based on video descriptions.

# How it works
1. gpt_playlist takes a video or playlist link and retrieves the video description(s).
2. if there is a timestamp in the description, gpt parses the description for a playlist.
3. gpt_playlist creates a search query for each song in the playlist.
4. gpt is then tasked with finding the best result, if it is unable to decide, the first result is picked.
5. finally, the playlist is created with the user's permission.

# Installation
1. Clone repository
```shell
git clone git@github.com:ollycodes/gpt_playlist_maker.git
cd gpt_playlist_maker
```
2. create Python virtual environment & activate.
```shell
python3 -m venv .venv
source .venv/bin/activate
```
3. pip install requirements
```shell
pip install -r requirements.txt
```
4. Set your API keys for Youtube & OpenAI.
```shell
export OPENAI_API_KEY=#your-openai-key
export YOUTUBE_API_KEY=#your-youtube-api-key
```
5. To create youtube playlists, download the client_secrets_file to the local directory.
    - https://developers.google.com/youtube/v3/quickstart/python 
    - https://console.developers.google.com/apis/credentials 

# Use
- Run script with video link
```shell
./gpt_playlist https://www.youtube.com/watch?v=#Video_id
```
- Run script with a playlist link
```shell
./gpt_playlist -p https://youtube.com/playlist?list=#Playlist_id
```

# Limitations
- Youtube Data API has a quota of 10,000 units per day. This limits the script to ~60 searches/day. Because of this I would only recommend using the video link for now.
    - searches cost 100 units
    - adding videos to playlists cost 50 units
    - retrieving videos cost 1 unit
    - for more info visit: https://developers.google.com/youtube/v3/determine_quota_cost
- Because not all videos have descriptive track lists for GPT to understand, some playlists will be far off the mark.

# Future Features
- User fallback for when gpt gets stuck creating a track list or picking results.
- final confirmation to create playlist
- Save results and have retry functionalities.
- calculate song durations based off track list.
- provide song duration to gpt when picking results.
- find track lists that extend into the comments seciton or are only found in the comments section.
