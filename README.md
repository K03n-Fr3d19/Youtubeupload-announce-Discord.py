# YouTube Announcement Discord Bot

A Discord bot that announces new videos from a specified YouTube channel in a designated Discord channel. The bot supports setup via commands and checks for new videos periodically.

## Features

- **Automatic Announcements**: Automatically post announcements in a Discord channel when a new video is uploaded to a specified YouTube channel.
- **Setup Commands**: Configure the bot with `/setup` to set the YouTube and Discord channels for announcements.
- **Manual Video Check**: Use `/newestvideo` to manually fetch and display the latest video from the YouTube channel.
- **Configuration Management**: Admin commands to clear settings or update the channels through `/reset` and `/setup`.

## Setup Instructions

### Using Velvox Gamehosting

1. **Download the Bot Package**

   Download the `.tar` package of the bot from the [releases page](https://github.com/K03n-Fr3d19/Youtubeupload-announce-Discord.py/releases) or import it in to the server.

2. **Upload the Package to Velvox Gamehosting**

    - Buy your [bot (Discord bot.py)](https://billing.velvox.net/cart.php?a=confproduct&i=0) and use "Python Generic"
    - Then go to the [gamepanel](https://game.velvox.net) and go to "your server" > files and drop the .tar file in to the `/home/container/` directory, and extract it.
    - Create a database in the "Database" tab and write the login information down.

3. **Configure the Bot**

   - Open the `bot.py` and edit the the `def get_mysql_connection` and put the correct login data in to the file.
     ```python
     db_config = {
        'host': 'yourdatabasehost', # MySQL database host IP
        'user': 'yourdatabaseuser', # MySQL user
        'password': 'yourdatabasepassword', # MySQL password
        'database': 'yourdatabasename' # MySQL database name
     }
     ```
    - Then scroll down to the last line of code to the `bot.run()` statement. and add your bot token you can get this at the [Discord Developer Portal](https://discord.com/developers).
        ```python
        # Run the bot with your token
        bot.run()
        ```
    - Make sure that the MySQL database has the necessary tabels, by default the bot generates them automaticly but it could error.
        ```sql
        CREATE TABLE IF NOT EXISTS channel_settings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            discord_channel_id BIGINT NOT NULL,
            youtube_channel_id VARCHAR(100) NOT NULL,
            last_announced_video_id VARCHAR(100) DEFAULT NULL
        );
        ```

4. **Install Required Packages**

   - By default the panel should install the default and neccasary packages. If you get any errors contact thier [support](https://billing.velvox.net/submitticket.php).

5. **Run the Bot**

   - If you configured your bot the right way when you click "Start" in the gamepanel it should start and you can start using your bot!
   - Ensure it has the right permissions set in the [Discord Developer Portal](https://discord.com/developers).
   - Go ahead to the [commands section](#commands). And you can setup your bot inside your discord server.

## Local installation

### Prerequisites

- Ensure you have Python 3.8+ installed.
- Create a bot application on the [Discord Developer Portal](https://discord.com/developers/applications) and obtain your bot token.
- Set up a MySQL database and ensure you have the necessary credentials.

### Local installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/koenfred19-discord-bot.git
   cd koenfred19-discord-bot
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   Make sure to have `discord.py`, `aiohttp`, `pymysql`, and `pytz` listed in `requirements.txt`.

3. **Configure Database**

   - Update `db_config` in `bot.py` with your MySQL database credentials:

     ```python
     db_config = {
        'host': 'yourdatabasehost', # MySQL database host IP
        'user': 'yourdatabaseuser', # MySQL user
        'password': 'yourdatabasepassword', # MySQL password
        'database': 'yourdatabasename' # MySQL database name
     }
     ```

   - Ensure your database has the required tables. You can use the following SQL script:

     ```sql
     CREATE TABLE IF NOT EXISTS channel_settings (
         id INT AUTO_INCREMENT PRIMARY KEY,
         discord_channel_id BIGINT NOT NULL,
         youtube_channel_id VARCHAR(100) NOT NULL,
         last_announced_video_id VARCHAR(100) DEFAULT NULL
     );
     ```

4. **Set Up Bot Token**

   - Replace the placeholder token in `bot.run()` with your bot token:

     ```python
     bot.run('YOUR_BOT_TOKEN')
     ```

5. **Run the Bot**

   ```bash
   python bot.py
   ```

## Commands

All the commands work with [Discord Slashcommands](https://discord.com/blog/welcome-to-the-new-era-of-discord-apps?ref=badge)

1. **`/setup`**

   **Description:** Configure the YouTube channel and Discord channel for announcements. This currently only supports one channel, I think about adding this in the future.

   **Usage:**
   - `/setup <youtube_channel_id> <discord_channel_id>`

   **Permissions:** Requires administrator permissions.

2. **`/newestvideo`**

   **Description:** Fetch and display the latest video from the configured YouTube channel.

   **Usage:**
   - `/newestvideo`

3. **`/reset`**

   **Description:** Clear all channel settings from the database. (Use this when you accedently added 2 channels and the bot doesnt work anymore.)

   **Usage:**
   - `/reset`

   **Permissions:** Requires administrator permissions.

## License

This bot is licensed under the [GNU General Public License v3.0](https://github.com/Velvox-Cybersecurity/Velvox-Blacklist-Discordbot.py/blob/main/LICENSE). See the `LICENSE` file for more details.
