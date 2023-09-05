# Youtube Playlist Finder
This script searches for every song in a chaptered Youtube video on Youtube.
Chaptered videos are videos that have timestamped sections; typically guides
and other forms of content will use these for quick references, but what I've
found is that channels that make playlist mixes will use these for song credits.

for each chapter in such videos, this script will look up the chapter name along
with the video title and retrieve the most similar titled video. (This was done
in order to help ambiguous cases where album name was ommited and may produce
inaccurate results.) After finding the closest match, the script will output
the list of results with links.

# Installation
1. Clone repository
```shell
git clone git@github.com:ollycodes/Youtube_Playlist_Finder.git
cd Youtube_Playlist_Finder
```

2. install npm requirements
```shell
npm install
```

# Use
```shell
# run script with video id
# youtube.com/watch?v=[VIDEO_ID]
./playlist Video_id
```
