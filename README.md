# Alfred

An opinionated fork of [Searcharr](https://github.com/toddrob99/searcharr) that
acts as a Telegram butler for Sonarr and Radarr.

Alfred lets authenticated Telegram users search for and add movies or TV shows,
automatically routes series and anime to their correct Sonarr folders, reports
new additions to an administrator chat, and can restart its own container.

## What changed in this fork

- `/reset` restarts only Alfred's Searcharr container and sends randomized,
  mildly humorous Alfred-style messages before and after the restart.
- Regular authenticated users and administrators can run `/reset`.
- Standard TV series are automatically stored in `/tv/Series`.
- The **Add as Anime** action automatically stores anime in `/tv/Anime` and
  submits it to Sonarr with the anime series type.
- `/notSparta/` is never presented as a series destination.
- Series and movies are added without selectable, username, or forced tags.
- Successful movie and series additions can be reported to a configured admin
  chat using the requester's Telegram display name.
- `/setadminchat` lets an authenticated administrator choose the reporting
  chat.

## Commands

| Command | Access | Purpose |
| --- | --- | --- |
| `/start <password>` | Everyone | Authenticate as a regular user or administrator. |
| `/help` | Authenticated users | Show the available Searcharr commands. |
| `/series <title>` | Authenticated users | Search Sonarr for a TV series. |
| `/movie <title>` | Authenticated users | Search Radarr for a movie. |
| `/reset` | Authenticated users | Restart only the Alfred/Searcharr container. |
| `/users` | Administrators | Manage authenticated users and admin access. |
| `/setadminchat` | Administrators | Send addition reports to the current chat. |
| `/setadminchat <chat_id>` | Administrators | Send addition reports to another chat ID. |

Command aliases for the standard Searcharr commands remain configurable in
`data/settings.py`.

## Requirements

- Docker with an `always` or `unless-stopped` restart policy for `/reset`
- A Telegram bot token from [BotFather](https://core.telegram.org/bots#6-botfather)
- Sonarr with both `/tv/Series` and `/tv/Anime` configured as root folders
- Radarr
- API keys for Sonarr and Radarr

The two Sonarr paths are deliberately fixed by this fork. Alfred refuses the
addition if its required destination is unavailable rather than silently using
the wrong folder.

## Configuration

Copy the sample settings file:

```sh
mkdir -p data logs
cp settings-sample.py data/settings.py
```

At minimum, configure these values in `data/settings.py`:

```python
searcharr_password = "regular-user-password"
searcharr_admin_password = "administrator-password"
tgram_token = "telegram-bot-token"

sonarr_url = "http://your-sonarr-host:8989"
sonarr_api_key = "sonarr-api-key"
sonarr_quality_profile_id = ["HD - 720p/1080p"]
sonarr_series_paths = ["/tv/Series", "/tv/Anime"]

radarr_url = "http://your-radarr-host:7878"
radarr_api_key = "radarr-api-key"
radarr_quality_profile_id = ["HD - 720p/1080p"]
```

Keep the following values disabled to preserve the no-tag workflow:

```python
sonarr_tag_with_username = False
sonarr_forced_tags = []
sonarr_allow_user_to_select_tags = False

radarr_tag_with_username = False
radarr_forced_tags = []
radarr_allow_user_to_select_tags = False
```

Never commit `data/settings.py`. The repository ignores `data/`, `logs/`,
databases, environment files, and settings files containing live credentials.

## Build and run with Docker

Build this repository locally. Do not deploy `toddrob/searcharr:latest`, because
that upstream image does not contain Alfred's custom commands.

```sh
docker build -t alfred-searcharr:latest .
```

Use the locally built image in your Compose service:

```yaml
services:
  searcharr:
    container_name: searcharr
    image: alfred-searcharr:latest
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - TZ=America/Costa_Rica
    restart: unless-stopped
    network_mode: host
```

Then create or update the container:

```sh
docker compose up -d
```

After future code changes, rebuild and recreate it with:

```sh
docker build -t alfred-searcharr:latest .
docker compose up -d --force-recreate
```

## Authentication

Authenticate privately so passwords are not exposed in a group chat:

```text
/start <searcharr_password>
```

Administrators authenticate with:

```text
/start <searcharr_admin_password>
```

Do not send the administrator password in a group chat.

## Adding media

Search for a regular series:

```text
/series Slow Horses
```

Selecting **Add Series** stores it in `/tv/Series`. When a search result is
recognized as anime, selecting **Add as Anime** stores it in `/tv/Anime`.
Neither workflow asks the user to select a path or tags. A quality-profile or
season-monitoring prompt may still appear when enabled in the settings.

Search for a movie:

```text
/movie The Dark Knight
```

Movies retain the configured Radarr path and quality-profile workflow, but no
tag prompt appears and the movie is submitted without tags.

## Admin addition reports

Add Alfred to the destination chat, authenticate your Telegram user as a
Searcharr administrator, and send this command inside that chat:

```text
/setadminchat
```

To configure a different chat by numeric ID:

```text
/setadminchat -1001234567890
```

Alfred verifies that it can message the destination before saving it. Reports
are stored in `data/admin_chat.json` and survive container restarts. A successful
addition produces a message similar to:

```text
Bruce Wayne added The Dark Knight movie.
```

If no admin chat is configured, additions continue normally and only the report
is skipped.

## Reset behavior

`/reset` writes the requesting chat ID into the persistent `data/` volume,
sends a random Alfred-style acknowledgement, and terminates only the Searcharr
process. Docker restarts that container because of its restart policy. Once the
new process initializes, it sends a random completion message to the requesting
chat.

It does **not** restart Sonarr, Radarr, Docker, or the host machine.

## Run from source

Install the dependencies and run the bot from the repository root:

```sh
python3 -m pip install -r requirements.txt
python3 searcharr.py
```

## Credits

Alfred is based on [Searcharr](https://github.com/toddrob99/searcharr), created
by Todd Roberts. The original project documentation and configuration reference
are available in the [Searcharr wiki](https://github.com/toddrob99/searcharr/wiki).
