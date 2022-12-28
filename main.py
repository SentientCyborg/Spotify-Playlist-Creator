from bs4 import BeautifulSoup
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Billboard.com
URL = "https://www.billboard.com/charts/hot-100/"

# Spotify Keys
ID = "YOUR ID"
SECRET = "YOUR CLIENT SECRET"
REDIRECT = "http://example.com"


def get_song_data(date: str) -> BeautifulSoup:
    """Makes request for Billboard 100 info"""
    response = requests.get(f"{URL}/{date}/")
    data = response.text
    soup = BeautifulSoup(data, "html.parser")
    return soup


def parse_songs(soup: BeautifulSoup) -> list[str]:
    """Gets a list of songs from BeautifulSoup object"""
    titles = soup.find_all(name="h3", class_="u-letter-spacing-0021", id="title-of-a-story")
    titles = [title.text.strip() for title in titles][3::4]
    return titles


def parse_artists(soup: BeautifulSoup) -> list[str]:
    """Gets list of artists from BeautifulSoup object"""
    data = soup.find_all(name="li", class_="lrv-u-width-100p")
    artists = [n.find(name="span", class_="c-label").getText() for n in data]
    artists = [artist.strip() for artist in artists[::2]]
    return artists


def make_data(artists: list[str], titles: list[str]) -> list[dict]:
    """Combines artists with songs into a list of dictionaries."""
    song_list = []
    i = 0
    for x in range(len(titles)):
        song_list.append(dict(artist=artists[i], song=titles[i]))
        i += 1
    return song_list


def call_spotify(scope="") -> spotipy:
    """Create a Spotify API Client"""
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=ID,
            client_secret=SECRET,
            redirect_uri=REDIRECT,
            scope=scope
        )
    )
    return sp


def create_playlist(user_id: str, playlist_name: str) -> dict[str]:
    response = sp.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=False,
        collaborative=False,
        description='Hot 100 from billboard.com'
    )
    return response


def get_song_URIs(sp: spotipy, song_list:list[dict]) -> list[str]:
    song_URIs = []
    for x in song_list:
        result = sp.search(q=f"artist: {x['artist']} track: {x['song']} year: {year}", type="track", market="US")
        try:
            song_uri = result['tracks']['items'][0]['uri']
            song_URIs.append(song_uri)
        except IndexError:
            print("Song has been skipped. Song not found on Spotify.")
    return song_URIs


date = input("What date do you want music from? Use format YYYY-MM-DD: ")
year = date.split("-")[0]

soup = get_song_data(date)
titles = parse_songs(soup)
artists = parse_artists(soup)
song_list = make_data(artists, titles)

sp = call_spotify(scope="playlist-modify-private")

user = sp.current_user()
user_id = user["id"]
playlist_name = f"Hot 100 From Date: {date}"

playlist = create_playlist(user_id, playlist_name)
playlist_id = playlist["id"]

song_URIs = get_song_URIs(sp, song_list)
sp.playlist_add_items(playlist_id, song_URIs)