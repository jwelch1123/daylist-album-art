import os
import base64
import hashlib
import secrets
from dotenv import load_dotenv, find_dotenv 
import requests
import urllib.parse
import re
from dash import Dash, html, dcc, callback, Input, Output, \
                    State, no_update
import dash_bootstrap_components as dbc
from openai import OpenAI


load_dotenv(find_dotenv())

# API Credentials and Redirect. 
spotify_client_id = os.getenv("spotify_client_id")
redirect_uri = os.getenv("redirect_uri")
# "OPENAI_API_KEY" is access directly by the OpenAI class

# Functions
def generate_code_verifier_and_challenge():
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8').replace('=', '')
    return code_verifier, code_challenge

def authorization_link(client_id, code_challenge, redirect_uri=redirect_uri):
    scope = 'playlist-read-private%20playlist-read-collaborative'

    auth_url = "https://accounts.spotify.com/authorize?"\
                + f"client_id={client_id}"\
                + "&response_type=code"\
                + f"&redirect_uri={redirect_uri}"\
                + f"&scope={scope}"\
                + f"&code_challenge_method=S256&code_challenge={code_challenge}"
    
    return auth_url

def obtain_pkce_token(client_id, authorization_code, code_verifier, redirect_uri=redirect_uri):

    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "client_id": client_id,
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }
    pkce_token_json = requests.post(token_url, headers=headers, data=data).json()
    return pkce_token_json

def get_user_info(token):
    response = requests.get("https://api.spotify.com/v1/me", headers={"Authorization": f"Bearer {token}"})
    return response.json()

def openai_gen_image(title, desc):
    client = OpenAI()


    prompt = f"Generate album cover for the playlist '{title}' with the following description: '{desc}'.\
                Avoid using text in the image. Use the genres and incorporate their themes into the image.\
                Attempt to make the image look like an album cover in the style of the main genres provided."

    print("Spending Money...")
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="hd"
        )
        return response.data[0].url
    except Exception as e:
        print("Error throw in gen image: ", response)
        return e


code_verifier, code_challenge = generate_code_verifier_and_challenge()
auth_link = authorization_link(spotify_client_id, code_challenge, redirect_uri)


# Dash App
app = Dash(__name__, external_stylesheets=[dbc.themes.MINTY])
server = app.server
app.title = "Daylist Album Art Generator"


app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="pkce_token"),
    html.H1("Daylist Album Art Generator", style={"textAlign": "center"}),
    html.Br(),
    html.P("Generate Album Art for your Daylist! Sign into Spotify to get started, make sure to save your daylist to your library.", style={"textAlign": "center"}),
    html.Br(),
    html.Div(children=[
        dbc.Button("Sign in with Spotify", id="sign_in", n_clicks=0, style={'display': 'inline-block', 'color':'DarkGreen'}, href=auth_link),
        dbc.Button("Download Image", id="download_btn", n_clicks=0, style={'display':'none',})],
        style={'margin': 'auto', 'padding': '10px', 'textAlign': 'center'}
        ),
    html.Br(), html.Br(),
    html.Div(id = "playlist_info", children = [], style={"textAlign": "center"}), # playlist info goes here
    html.Div(id = "image_div",children = [], style={"textAlign": "center", "min-height": "600px", 'display':'flex','align-items':'center'}), # image goes here
    html.Br(),
    dcc.Download(id = 'download_holder'),
    html.Br(), html.Br(),
    html.Div([
        "Made by ", 
        html.A("James Welch", href="https://github.com/jwelch1123",  target="_blank", style={'color': 'grey'}),
        " · ",
        "View ", 
        html.A("Daylist Album Art Generator on GitHub", href="https://github.com/jwelch1123/daylist-album-art",  target="_blank", style={'color': 'grey'})
        ], 
        style={'textAlign': 'center', 'color': 'grey', 'fontSize': '0.8em', 'marginTop': '20px'}
        )

    ],
    style={'margin': 'auto',
           'marginTop': '1%',
           'maxWidth': '95%', 
           'maxHeight': '95%',
           'padding': '20px',
           'border':'1px solid #ccc',
           'borderRadius': '10px'
           }
)


# Callbacks
@app.callback(
        Output('pkce_token', 'data'), 
        Input('url', 'search'))
def get_code_store_pkce(search):
    """
    Retrieves the PKCE token from the given search parameter.

    Args:
        search (str): The search parameter (url) containing the code.

    Returns:
        str: The PKCE token to the store component.

    Raises:
        Exception: If an error occurs while obtaining the PKCE token.
    """
    if search:
        params = urllib.parse.parse_qs(search[1:])
        auth_code = params.get('code', [''])[0]

        try:
            pkce_token_json = obtain_pkce_token(spotify_client_id, auth_code, code_verifier, redirect_uri)
            pkce_token = pkce_token_json['access_token']
        except:
            return no_update

        return pkce_token
    return no_update

@app.callback(
    Output('sign_in', 'style'),
    Output('sign_in', 'disabled'),
    Input('pkce_token', 'data'))
def block_button(data):
    """
    Show the hidden div when the PKCE token is available.

    Args:
        data (str): The PKCE token.

    Returns:
        dict: The style properties to be applied to the hidden div.
    """
    if data:
        return {'opacity':'0.5', 'pointerEvents':'none', 'margin-right':'25px'}, True
    return no_update, False

@app.callback(
    Output('playlist_info', 'children'),
    Output('image_div', 'children'),
    Input('pkce_token', 'data'))
def get_playlists(token):
    """
    Retrieves the user's playlists from Spotify, generates and shows album art for the 'daylist' playlist.

    Args:
        token (str): The access token for the Spotify API, saved to the store component.

    Returns:
        tuple: A tuple containing two elements:
            - info_div (html.Div): A Div element containing the playlist information.
            - pic_div (html.Img): An Img element containing the generated album art.

    Raises:
        ValueError: If there is an error while retrieving the playlist information.
    """
    if not token:
        return no_update, no_update
        
    user_id = get_user_info(token)['id']
    limit = 50 # 50 is the max limit
    
    endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists?limit={limit}"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(endpoint, headers=headers)
    if  (response.status_code != 200):
        raise ValueError(f"Error: Failed to get playlist information: {response.text}")

    daylist_playlist = None

    while not daylist_playlist:

        playlists = response.json()['items']
        next_page = response.json()['next']

        for playlist in playlists:
            if playlist['name'].startswith('daylist'):
                daylist_playlist = playlist
                break

        if (not daylist_playlist):
            if (not next_page):
                print("No daylist playlist found. Make sure you have added 'daylist' in your Spotify library.")
                return no_update, no_update
            response = requests.get(next_page, headers=headers)
        
    try:
        pl_name = daylist_playlist['name']
        pl_desc = daylist_playlist['description']
    except:
        print("Error: Failed to get playlist information.")
        return no_update, no_update

    daylist_title = re.sub(r'daylist • ', '', pl_name)
    daylist_desc = re.sub(r'<.*?>', '', pl_desc)
    
    img_url = openai_gen_image(daylist_title, daylist_desc)
    if isinstance(img_url, Exception):
        print("Error: Failed to generate image.")
        print(img_url)
        return no_update, no_update

    info_div = html.Div([
        html.H3(f"Daylist: {daylist_title.title()}"),
        html.P(f"{daylist_desc}")
    ])

    pic_div = html.Img(src=img_url, style={'width': '100%', 'height': 'auto', 'maxheight': '600px', 'margin':'10px'})

    return info_div, pic_div

@app.callback(
    Output('download_btn', 'style'),
    Input('image_div', 'children')
)
def add_download_button(image_div_children):
    if image_div_children:
        return  {'display': 'inline-block', 'color':'DarkGreen', 'margin': 'auto', 'marginRight':'10px'}
    return no_update

@app.callback(
    Output('download_holder', 'data'),
    Input('download_btn', 'n_clicks'),
    State('image_div', 'children'),
    State('playlist_info', 'children'))
def image_download(n_clicks, image_div_children, playlist_info_children):
    if image_div_children and (n_clicks > 0):

        playlist_title = playlist_info_children['props']['children'][0]['props']['children']
        img_url = image_div_children['props']['src']
        
        # Generating a filename
        filename = re.sub(r"[^a-zA-Z0-9-_ ]", "", playlist_title) + ".jpg"
        
        response = requests.get(img_url)

        if response.status_code == 200:
            
            # send bytes takes a function 
            def return_content(response):
                return response.content

            return dcc.send_bytes(return_content(response), filename=filename)
                
        else:
            return no_update

    return no_update



if __name__ == '__main__':
    app.run_server(debug=True)