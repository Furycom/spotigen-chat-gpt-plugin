<h3 align="center">
	<img src="https://raw.githubusercontent.com/Railly/spotigen-chat-gpt-plugin/main/static/logo.png" style="border-radius: 8px;" width="100" alt="Logo"/><br/>
	<img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/misc/transparent.png" height="30" width="0px"/>
	Spotigen, a <a href="https://openai.com/blog/chatgpt-plugins">Chat GPT Plugin</a>
</h3>

<p align="center">
A <a href="https://chat.openai.com/">Chat GPT</a> Plugin that generates Spotify playlists 🎵 based on your prompts ✨.
  <br>
</p>

## Installation

1. Go to [ChatGPT](https://chat.openai.com/)
2. Go to: `Plugin Store` > `Install an unverified plugin`
3. Enter the following domain: [spotigen.vercel.app](https://spotigen.vercel.app)
4. OpenAI will warn you that the plugin is unverified. Click `Continue`.
5. Click `Login with Spotigen`.
6. Now you're ready to use the plugin!

## Setup development environment

### Setup a Spotify app

To integrate ChatGPT with Spotify API via OAuth, you have to set up a Spotify app in the `Spotify Developer Dashboard` and obtain your `client_id` and `client_secret`:

1. Go to [Spotify developer's dashboard](https://developer.spotify.com/dashboard) and click "Create app".
2. Enter an App name and App description.

3. For the Redirect URI, put `https://chat.openai.com/aip/plugin-id-temporary-value/oauth/callback` as a temporary value, then you will need to replace it later once you obtain your plugin ID.

4. Accept the terms and conditions and click "Create".

### 🔑 OAuth setup

The **same** URL must appear both in Railway → Variables → `REDIRECT_URI`
and in the Spotify Dashboard → Redirect URIs.

### Required environment variables

Set the following variables in Railway and your `.env` file:

```
CLIENT_ID=...
CLIENT_SECRET=...
REDIRECT_URI=https://<your-domain>/auth/callback
UPSTASH_REDIS_REST_URL=...
UPSTASH_REDIS_REST_TOKEN=...
LASTFM_API_KEY=...
LASTFM_USERNAME=...
```

### Setup the plugin

To install the required packages for this plugin, run the following command:

```bash
pip install -r requirements.txt
```

To run the plugin, enter the following command:

```bash
uvicorn main:app --reload
```

> **Note**
> If you update `.well-known/ai-plugin.json` or `static/spec.json`, you need to
> redeploy the Railway app so the public manifest reflects your changes.

### Setup ngrok

To test your plugin locally, you will need to use [ngrok](https://ngrok.com/) to provide HTTPS access to your local server.

1. Download ngrok from [here](https://ngrok.com/download) and unzip it.
2. Run the following command to expose your local server to the internet:

```bash
./ngrok http 8000
```
3. It's important to note that you will need to have a ngrok paid plan to **bypass the ngrok-skip-browser-warning**.

### Setup the plugin in ChatGPT

Once the local server is running:

1. If you are a ChatGPT Plus user, you will be able to access the Plugins option. Otherwise, you will need to sign up for the [waitlist](https://openai.com/waitlist/plugins).
2. Go to: Plugin Store > Develop your own plugin
3. Enter your ngrok domain: <ngrok_id>.ngrok.app
4. Enter `client_id` and `client_secret` from your Spotify app.
5. ChatGPT will provide you a verification token. Update it in your `ai-plugin.json` as follows:

```json
{
    "verification_tokens": {
      "openai": "<open_ai_verification_token>"
    }
}
```
6. Click `Install for me`.
7. Click `Log in with Spotigen (DEV)`.
8. You will see a page with `INVALID_CLIENT: Invalid redirect URI` error. Copy the `plugin_id` from the URL and update the `redirect_uri` in your Spotify app settings.
9. Reload the error page and you will be redirected to the ChatGPT app.

> **Note**
> Personally, I don't have a paid `ngrok` account, so I use my `spotigen.vercel.app` URL directly within ChatGPT for my whole development process. 

## Usage

Once the plugin is installed, you'd like to try the following prompts:

**Purpose**: Tell how you are feeling and get a playlist that matches your mood.

> **Prompt 1**: "I'm feeling a bit tired today and in a mood for some nostalgia. Could you create a playlist featuring the best English pop songs from the 2010s?"

> **Prompt 2**: "I'm feeling happy today and would like a playlist that reflects my mood. Could you generate one with all English songs?"


**Purpose**: Create playlists based on different scenarios and inspirations.

> **Prompt 1**: "I have a photo of a family vacation at a pool with a blue background that I'd like to post on Instagram. Could you create a playlist that would complement this image? I'm looking for a playlist suitable for a family vacation photo taken at a pool with a blue background."

> **Prompt 2**: "I'm planning a trip to a place with abundant greenery and would like to feel as if I'm on a summer trip in 2017. Could you create a playlist to match this mood? I want the playlist to evoke the feeling of a summer trip in a lush green location reminiscent of the summer of 2017."


**Purpose**: Create a playlist based on your favorite playlist/artist.

> **Prompt 1**: "I have a favorite playlist named 'Chill Vibes' that I absolutely love and listen to all the time. Could you create a new playlist inspired by my 'Chill Vibes' playlist? I want to discover similar songs and artists that I might enjoy."

> **Prompt 2**: "There's this one artist named 'John Smith' who is my absolute favorite, and I can't get enough of their music. Could you curate a playlist based on 'John Smith's' style and genre? I'm looking to explore more songs that resonate with their sound."


## API

### `GET /top_tracks`

Returns the top 5 tracks for the authenticated user.
The backend stores the Spotify access token, so no `Authorization` header is required.

```bash
curl https://spotigen.vercel.app/top_tracks
```

## Testing

Install the required packages before running the test suite:

```bash
pip install -r requirements.txt
pytest
```

## Opération gratuite 24/7

Tokens Spotify sont conservés dans Upstash Redis et un workflow keep-alive ping la route `/` toutes les 15 minutes pour éviter la mise en veille Railway. Importez `log-alerts.json` dans Railway ▸ Settings ▸ Alerts pour être notifié des erreurs 401/403.
