# daylist-album-art

This project aims to create album art for your Spotify Daylist playlist. The album art can be customized based on the songs in your playlist, creating a unique visual representation of your music collection.

Try out the site: [Daylist Album Art Generator](https://daylist-album-art-78ef6f049b28.herokuapp.com/))

## Features

- Generate album art based on the songs in your Spotify Daylist playlist.
- Export the generated album art in various formats (JPEG).

## Getting Started

To get started with this project, follow these steps:

1. Clone the repository: `git clone https://github.com/jwelch1123/daylist-album-art`
2. Follow [this guide from Spotify](https://developer.spotify.com/documentation/web-api/tutorials/getting-started) to register your own app and obtain credentials. Add 'http://127.0.0.1:8050/' as a redirect uri. Do the same for [OpenAI's API](https://platform.openai.com/docs/quickstart).
3. Install the required dependencies: `pip install -r requirements.txt`
4. Create a .env file and add your redirect uri, Spotify, and OpenAI credentials.
5. Run the application locally with Dash

## Usage

1. Open the application and authenticate with your Spotify account.
2. Get album art of your current Daylist. Download it if you want to keep it.

## Acknowledgements

This project was inspired by a running gag with my friend and the power of ChatGPT's image-generation features.

A third of the code used in this project was sourced from my [Playlistr](https://github.com/jwelch1123/playlistr) project. Check it out!

[Spotify's developer guide and API documentation](https://developer.spotify.com/documentation/web-api) was a great help in creating this project. 

[OpenAI's API reference and documentation](https://platform.openai.com/docs/guides/images)
