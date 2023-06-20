const { Client, MusicClient } = require("youtubei");
const youtube = new Client();
let query = process.argv[2];
let action = process.argv[3];

// gets playlist video titles, ids, & video durations
// retrieves each video's chapter titles & durations
const getPlaylistInfo = async (query) => {
    const playlist = await youtube.getPlaylist(query);
    let data = {results: []};
    for (let i = 0; i < playlist.videos.items.length; i++) {
        data.results.push({
            title: playlist.videos.items[i].title,
            id: playlist.videos.items[i].id, 
            duration: playlist.videos.items[i].duration
        });
    }
    for (let i = 0; i < data.results.length; i++) {
        var video = await youtube.getVideo(data.results[i].id);
        video.chapters.forEach(function(dictionary) {
            if (dictionary === 0) {
                // do nothing
            } else {
                delete dictionary["thumbnails"];
            }
        });
        data.results[i].chapters = video.chapters
    }

    var jsonstring = JSON.stringify(data);
    console.log(jsonstring);
};

// gets video info
const getVideoInfo = async (query) => {
    const video = await youtube.getVideo(query);
    if (video.chapters === 0) {
        // do nothing
    } else {
        video.chapters.forEach(function(chapter) {
            delete chapter.thumbnails;
        });
    }
    let videoData = {
        title: video.title,
        id: video.id, 
        duration: video.duration,
        chapters: video.chapters
    };

    var jsonString = JSON.stringify(videoData);
    console.log(jsonString);
};

// search video
const videoSearch = async (query) => {
    const search = await youtube.search(query, {type: "video"});
    let data = {results: []};
    for (let i = 0; i < search.items.length; i++) {
        if (search.items[i].duration !== null){
            data.results.push({
                title: search.items[i].title,
                id: search.items[i].id,
                duration: search.items[i].duration
            });
        };
    }
    var jsonstring = JSON.stringify(data);
    console.log(jsonstring);
};

if (action === 'playlist') {
    getPlaylistInfo(query);
} else if (action === 'video') {
    getVideoInfo(query);
} else if (action === 'search') {
    videoSearch(query)
} else {
    console.log("invalid prompt")
}
