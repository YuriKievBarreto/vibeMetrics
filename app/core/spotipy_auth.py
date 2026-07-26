from spotipy.oauth2 import SpotifyOAuth
from app.core.config import settings

CLIENT_ID = settings.SPOTIPY_CLIENT_ID
CLIENT_SECRET = settings.SPOTIPY_CLIENT_SECRET
REDIRECT_URI = settings.SPOTIPY_REDIRECT_URI

todos_os_escopos = "user-read-private user-top-read user-read-recently-played user-read-playback-position   user-read-currently-playing"

sp_oauth_manager = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=todos_os_escopos,
    show_dialog=True 
)





    
    
        

