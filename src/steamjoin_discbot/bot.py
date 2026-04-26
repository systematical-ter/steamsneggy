import discord
import re
import requests

from message_templates.url_view import UrlView

class SteamSneggy():
    intents: discord.Intents
    client: discord.Client
    token: str
    domain: str

    steam_invite_regex = r"steam:\/\/joinlobby\/(?P<game_id>[\d]+)\/(?P<unique_id>[\d]+)\/(?P<user_id>[\d]+)"

    def __init__(self, token, domain):
        self.intents = discord.Intents.default()
        self.intents.message_content = True

        self.client = discord.Client(intents=self.intents)
        self.token = token
        self.domain = domain

    def setup_commands(self):
        @self.client.event
        async def on_ready():
            print(f'We have logged in as {self.client.user}')

        @self.client.event
        async def on_message(message: discord.Message):
            if message.author == self.client.user:
                return

            found = re.search(self.steam_invite_regex, message.content)
            if found:
                game_name, game_logo_url = self.fetch_game_info(found)
                await message.reply(view=UrlView(found.group(0), self.create_new_link(found), game_name, game_logo_url))
            if message.content.startswith('$hello'):
                await message.channel.send('Hello!')

    def start_bot(self):
        self.client.run(self.token)

    def create_new_link(self, match: re.Match):
        return f"{self.domain}/join/?id1={match['game_id']}&id2={match['unique_id']}&id3={match['user_id']}"
    
    def fetch_game_info(self, match: re.Match):
        game_id = match['game_id']
        contents = requests.get(f"https://store.steampowered.com/api/appdetails/?appids={game_id}").json()[game_id]['data']
        return contents['name'], contents['header_image']
        