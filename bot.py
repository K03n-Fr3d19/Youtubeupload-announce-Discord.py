import discord
import aiohttp
import xml.etree.ElementTree as ET
from discord.ext import tasks, commands
from datetime import datetime
import pymysql
import pymysql.cursors
import pytz

# Set up bot intents
intents = discord.Intents.default()
intents.message_content = True  # Ensure the bot can read messages

# Initialize the bot with interactions only (no command prefix needed)
bot = commands.Bot(command_prefix='/', intents=intents)

# Database configuration
db_config = {
   'host': 'yourdatabasehost', # MySQL database host IP
   'user': 'yourdatabaseuser', # MySQL user
   'password': 'yourdatabasepassword', # MySQL password
   'database': 'yourdatabasename' # MySQL database name
}

# Connect to the database and create tables if they don't exist
def setup_database():
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS channel_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                discord_channel_id BIGINT NOT NULL,
                youtube_channel_id VARCHAR(100) NOT NULL,
                last_announced_video_id VARCHAR(100) DEFAULT NULL
            );
            """)
        connection.commit()
    finally:
        connection.close()

setup_database()

# Fetch settings from the database
def get_channel_settings():
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT discord_channel_id, youtube_channel_id, last_announced_video_id FROM channel_settings LIMIT 1;")
            result = cursor.fetchone()
    finally:
        connection.close()
    return result

# Static Configurations
announcement_channel_id = None
target_channel = None
last_check_date = datetime.utcnow().date()  # Track the last check date

@bot.event
async def on_ready():
    # Set custom status to "Watching Koenfred19"
    activity = discord.Activity(type=discord.ActivityType.watching, name="Koenfred19")
    await bot.change_presence(activity=activity)

    global announcement_channel_id, target_channel
    settings = get_channel_settings()
    if settings:
        announcement_channel_id, target_channel, last_announced_video_id = settings
        print(f'[INFO] Channel settings loaded: Announcement Channel ID = {announcement_channel_id}, Target Channel ID = {target_channel}')
        print(f'[INFO] Last announced video ID = {last_announced_video_id}')
    else:
        print('[ERROR] No channel settings found in the database.')
    
    print(f'[INFO] Logged in as {bot.user.name}')
    print('[INFO] Bot is ready and starting the check_for_new_video loop...')
    check_for_new_video.start()
    # Register slash commands
    await bot.tree.sync()
    print("[INFO] Commands synced.")  # Debug: Commands synced message

@tasks.loop(minutes=5)
async def check_for_new_video():
    global last_check_date

    print("[INFO] Checking for new video...")  # Debug: Start checking for new videos

    if not announcement_channel_id or not target_channel:
        print("[ERROR] No channel settings configured. Please set up the channel settings.")
        return

    channel = bot.get_channel(announcement_channel_id)
    if channel is None:
        print(f"[ERROR] Channel with ID {announcement_channel_id} not found or bot has no access.")
        return

    # Fetch latest video data
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={target_channel}"
    print(f"[INFO] Fetching RSS feed from URL: {feed_url}")  # Debug: Fetching RSS feed

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(feed_url) as response:
                if response.status == 200:
                    print("[INFO] RSS feed fetched successfully.")  # Debug: Feed fetched successfully

                    data = await response.text()

                    # Parse RSS feed
                    root = ET.fromstring(data)
                    entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')

                    if not entries:
                        print(" [ERROR] No video entries found in RSS feed.")
                        return

                    # Find the most recent video by comparing datetime
                    new_video_found = False
                    latest_video = None
                    latest_published_date = None

                    for entry in entries:
                        video_title = entry.find('{http://www.w3.org/2005/Atom}title').text
                        video_url = entry.find('{http://www.w3.org/2005/Atom}link').get('href')
                        channel_name = entry.find('{http://www.w3.org/2005/Atom}author').find('{http://www.w3.org/2005/Atom}name').text
                        video_id = video_url.split('v=')[-1]
                        published_date_str = entry.find('{http://www.w3.org/2005/Atom}published').text
                        published_date = datetime.strptime(published_date_str, '%Y-%m-%dT%H:%M:%S%z')

                        # Update the latest video if this one is newer
                        if latest_published_date is None or published_date > latest_published_date:
                            latest_published_date = published_date
                            latest_video = {
                                'title': video_title,
                                'url': video_url,
                                'channel_name': channel_name,
                                'video_id': video_id,
                                'published_date': published_date
                            }

                    if latest_video:
                        print(f"[INFO] Latest video found: {latest_video['title']} published on {latest_video['published_date']}")  # Debug: Print video details

                        # Fetch the last announced video ID from the database
                        connection = pymysql.connect(**db_config)
                        try:
                            with connection.cursor() as cursor:
                                cursor.execute("SELECT last_announced_video_id FROM channel_settings LIMIT 1;")
                                last_announced_video_id = cursor.fetchone()[0]
                        finally:
                            connection.close()

                        if latest_video['video_id'] != last_announced_video_id:
                            # Build and send embed
                            embed = discord.Embed(
                                title=latest_video['title'],
                                url=latest_video['url'],
                                description=f"**Channel:** {latest_video['channel_name']}",
                                color=discord.Colour.blurple()
                            )
                            embed.set_image(url=f"https://i4.ytimg.com/vi/{latest_video['video_id']}/maxresdefault.jpg")
                            embed.add_field(name='URL:', value=latest_video['url'], inline=False)

                            # Message with @everyone mention
                            message_content = f"@everyone **{latest_video['channel_name']}** has uploaded a new video or has just gone live!"

                            print(f"[INFO] Sending message for new video: {latest_video['title']}")  # Debug: Sending message

                            try:
                                await channel.send(content=message_content, embed=embed)

                                # Update last announced video ID in the database
                                connection = pymysql.connect(**db_config)
                                try:
                                    with connection.cursor() as cursor:
                                        cursor.execute("""
                                        UPDATE channel_settings
                                        SET last_announced_video_id = %s
                                        WHERE discord_channel_id = %s AND youtube_channel_id = %s;
                                        """, (latest_video['video_id'], announcement_channel_id, target_channel))
                                    connection.commit()
                                finally:
                                    connection.close()
                                    
                                new_video_found = True
                            except discord.Forbidden:
                                print("[ERROR] Bot does not have permission to send messages in this channel.")
                            except discord.HTTPException as e:
                                print(f"[ERROR] HTTP Exception: {e}")

                    if not new_video_found:
                        print("[INFO] No new video of the day found or already announced.")

                else:
                    print(f"[ERROR] Failed to fetch video data. Status code: {response.status}")
        except Exception as e:
            print(f"[ERROR] Error occurred while fetching RSS feed: {e}")

    # Update last check date
    last_check_date = datetime.utcnow().date()

@bot.tree.command(name="newestvideo", description="Get the latest video from the YouTube RSS feed")
async def nieuwstevideo(interaction: discord.Interaction):
    print("[INFO] Fetching latest video on slash command...")  # Debug: Slash command triggered

    if not target_channel:
        await interaction.response.send_message("No YouTube channel ID configured. Please set up the channel settings.")
        return

    # Fetch latest video data
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={target_channel}"
    print(f"[INFO] Fetching RSS feed from URL: {feed_url}")  # Debug: Fetching RSS feed

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(feed_url) as response:
                if response.status == 200:
                    print("[INFO] RSS feed fetched successfully.")  # Debug: Feed fetched successfully

                    data = await response.text()

                    # Parse RSS feed
                    root = ET.fromstring(data)
                    entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')

                    if not entries:
                        print("[ERROR] No video entries found in RSS feed.")
                        await interaction.response.send_message("No video entries found.")
                        return

                    # Find the most recent video by comparing datetime
                    latest_video = None
                    latest_published_date = None

                    for entry in entries:
                        video_title = entry.find('{http://www.w3.org/2005/Atom}title').text
                        video_url = entry.find('{http://www.w3.org/2005/Atom}link').get('href')
                        channel_name = entry.find('{http://www.w3.org/2005/Atom}author').find('{http://www.w3.org/2005/Atom}name').text
                        video_id = video_url.split('v=')[-1]
                        published_date_str = entry.find('{http://www.w3.org/2005/Atom}published').text
                        published_date = datetime.strptime(published_date_str, '%Y-%m-%dT%H:%M:%S%z')

                        # Update the latest video if this one is newer
                        if latest_published_date is None or published_date > latest_published_date:
                            latest_published_date = published_date
                            latest_video = {
                                'title': video_title,
                                'url': video_url,
                                'channel_name': channel_name,
                                'video_id': video_id,
                                'published_date': published_date
                            }

                    if latest_video:
                        print(f"[INFO] Latest video found: {latest_video['title']} published on {latest_video['published_date']}")  # Debug: Print video details

                        # Build and send embed
                        embed = discord.Embed(
                            title=latest_video['title'],
                            url=latest_video['url'],
                            description=f"**Channel:** {latest_video['channel_name']}",
                            color=discord.Colour.blurple()
                        )
                        embed.set_image(url=f"https://i4.ytimg.com/vi/{latest_video['video_id']}/maxresdefault.jpg")
                        embed.add_field(name='URL:', value=latest_video['url'], inline=False)

                        # Send message
                        await interaction.response.send_message(content=f"**{latest_video['channel_name']}** has uploaded a new video or has just gone live!", embed=embed)
                    else:
                        await interaction.response.send_message("No new video of the day found.")

                else:
                    print(f"[ERROR] Failed to fetch video data. Status code: {response.status}")
                    await interaction.response.send_message("Failed to fetch video data.")
        except Exception as e:
            print(f"[ERROR] Error occurred while fetching RSS feed: {e}")
            await interaction.response.send_message("An error occurred while fetching video data.")

    # Update last check date
    last_check_date = datetime.utcnow().date()

@bot.tree.command(name="setup", description="Set up the YouTube channel and Discord channel for announcements")
@commands.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction, youtube_channel_id: str, discord_channel_id: str):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
            INSERT INTO channel_settings (discord_channel_id, youtube_channel_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE discord_channel_id = VALUES(discord_channel_id), youtube_channel_id = VALUES(youtube_channel_id);
            """, (discord_channel_id, youtube_channel_id))
        connection.commit()
        global announcement_channel_id, target_channel
        announcement_channel_id = discord_channel_id
        target_channel = youtube_channel_id
        await interaction.response.send_message(f"Channel settings updated: Announcement Channel ID = {discord_channel_id}, Target Channel ID = {youtube_channel_id}")
    finally:
        connection.close()

@bot.tree.command(name="reset", description="Clear all channel settings from the database")
@commands.has_permissions(administrator=True)
async def clearsettings(interaction: discord.Interaction):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM channel_settings;")
        connection.commit()
        await interaction.response.send_message("All channel settings have been cleared from the database.")
    except Exception as e:
        print(f"[ERROR] Error occurred while clearing settings: {e}")
        await interaction.response.send_message("An error occurred while clearing settings.")
    finally:
        connection.close()

# Run the bot with your bot token
bot.run('YOUR_BOT_TOKEN')
