import os, re, json
from langchain.llms import OpenAI
from langchain import PromptTemplate
from langchain.chains import LLMChain
from langchain.callbacks import get_openai_callback
import googleapiclient.discovery
import googleapiclient.errors
import google_auth_oauthlib.flow

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
# set YOUTUBE_API_KEY in your shell environment.
yt_api_key = os.getenv("YOUTUBE_API_KEY")
# set json in local directory. see: https://developers.google.com/youtube/v3/quickstart/python.
client_secrets_file = "client_secrets_file.json"

def create_yt_api():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    youtube = googleapiclient.discovery.build(
        serviceName="youtube", 
        version="v3", 
        developerKey=yt_api_key
    )
    return youtube

def yt_link_parser(link: str) -> str:
    """Parses yt playlist links to just the playlist ID."""
    playlist_pattern = r"^(?:https?://)?(?:www\.|music\.)?(?:youtube\.com/)?(?:playlist\?list=)?([\w-]+)$"

    match = re.match(playlist_pattern, link)
    if match:
        print(match)
        playlist_id = match.group(1)
        return playlist_id
    else:
        return "Invalid"

def get_playlist(playlistId: str) -> list:
    """Get video descriptions of each video in playlist via yt api."""

    youtube = create_yt_api()
    playlist_items = []
    next_page_token = None
    while True:
        playlist_request = youtube.playlistItems().list(
            part="snippet",
            playlistId=f"{playlistId}",
            pageToken=next_page_token
        )
        playlist_response = playlist_request.execute()
        playlist_items += playlist_response['items']
        next_page_token = playlist_response.get('nextPageToken')
        if not next_page_token:
            break
    return playlist_items

def get_videos(playlist: list) -> list:
    video_descriptions = []
    for video in playlist:
        title = video["snippet"]["title"]
        description = video["snippet"]["description"]
        video_descriptions.append(
            {
                "title":title,
                "description":description
             }
        )
    return video_descriptions

def gpt_parse_timestamp(title:str, description:str) -> str:
    """Asks GPT to parse video description for playlist."""

    llm = OpenAI(temperature=0, max_tokens=512)
    prompt = PromptTemplate(
        input_variables=["title", "description"],
        template=' \
        A playlist consists of a timestamp and some song information. \
        If there is a playlist in the description, \
        return a JSON containing only the song info like this: \
        {{"playlist":[{{"title": "song - song info"}},...]}} \
        If there is little song info, add the video title as the song info. \
        The title to this video is: {title} \
        Do not explain anything about the output. \
        The description starts here: {description}',
    )

    with get_openai_callback() as cb:
        chain = LLMChain(llm=llm, prompt=prompt)
        # video description will come back as
        parsed = chain.run(title=title, description=description)
        print(f"\nparsed: {parsed}\n")
        print(cb)
    return parsed

def parse_video_descriptions(video_list: list) -> list:
    """
    Parses video description for playlist if there is an initial timestamp of 00:00.
    Otherwise, removes the video from the list.
    """
    for video in video_list:
        title = video["title"]
        if "0:00" in video["description"]:
            print(f"\nWorking on video: {title}")
            description = video["description"]
            parsed_description = gpt_parse_timestamp(title, description)
            parsed_json = json.loads(parsed_description)
            video["playlist"] = parsed_json["playlist"]
        else:
            print(f"\nskipping: {title}. Reason: no timestamps.")
            video_list.remove(video)
    return video_list

def search_yt(video_list: list) -> list:
    """create a search for each video in the parsed description list."""
    youtube = create_yt_api()
    for video in video_list:
        for song in video["playlist"]:
            #search song
            search_request = youtube.search().list(
                part="snippet",
                maxResults=10,
                q=song["title"],
                type="video"
            )
            search_response = search_request.execute()

            # create a dictionary of the search results
            song["results"] = [
                {"title": v["snippet"]["title"], "id": v["id"]["videoId"]}
                for v in search_response["items"]
            ]
    return video_list

def gpt_pick_from_results(video_list: list) -> list:
    """Ask GPT to interpret search results."""

    llm = OpenAI(temperature=0, max_tokens=512)
    prompt = PromptTemplate(
        input_variables=["query", "results"],
        template='results are youtube video titles and ids. \
        find the best match for the given query: {query}, \
        reply only with the best pick like so: \
        {{"title": "song", "id": "id"}} \
        Do not explain anything about the output. \
        If there is no title that matches the query, \
        respond with an empty JSON. The description starts here: {results}',
    )
    with get_openai_callback() as cb:
        chain = LLMChain(llm=llm, prompt=prompt)
        for video in video_list:
            for song in video["playlist"]:
                query = song["title"]
                results = song["results"]
                print(f"\nworking on song: {query}...")
                pick = chain.run(query=query, results=results)
                try:
                    pick = json.loads(pick)
                except:
                    print("\ngpt could not decide.")
                    pick = song["results"][0]
                print(f"\npicked: {pick['title']} from results")
                song["gpt_pick"] = pick
        print(cb)
    return video_list 

def create_playlist_api():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_local_server()
    youtube = googleapiclient.discovery.build(
        serviceName="youtube", 
        version="v3", 
        credentials=credentials)
    return youtube

def create_playlist(video_list: list) -> None:
    youtube = create_playlist_api()

    for video in video_list:
        create_request = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": f"Playlist for video: {video['title']}",
                    "description": f"This is a playlist of the songs found {video['title']}. \
                    the songs were parsed from the video descriptions and searched. Each entry \
                    was picked by gpt based on the title of the song it parsed and the results \
                    it found. In some cases, gpt could not decide on a result so the first result was picked.",
                },
                "status": {"privacyStatus": "private"}
            }
        )
        create_response = create_request.execute()
        for song in video["playlist"]:
            populate_request = youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": create_response["id"],
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": song["gpt_pick"]["id"]
                        }
                    }
                }
            )
            populate_response = populate_request.execute()
    print("\n playlists created!")

def playlist_scraper(link: str) -> None:
    playlist_id = yt_link_parser(link)
    playlist = get_playlist(playlist_id)
    video_list = get_videos(playlist)
    video_list_parsed = parse_video_descriptions(video_list)
    video_list_searched = search_yt(video_list_parsed)
    gpt_playlist = gpt_pick_from_results(video_list_searched)
    create_playlist(gpt_playlist)

if __name__ == "__main__":
    link = input("paste link here: ")
    playlist_scraper(link)
