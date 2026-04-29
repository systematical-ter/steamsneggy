from typing import List

import discord
import re
import requests
from requests.exceptions import ConnectionError

from message_templates.url_section import UrlSectionLayout

from discord import User, Member, Intents, Activity, ActivityType, Status, Message
from discord.ext.commands import Bot

class SteamSneggy():
    intents: Intents
    client: Bot
    token: str
    domain: str

    is_healthy: bool

    steam_invite_regex = r"steam:\/\/joinlobby\/(?P<game_id>[\d]+)\/(?P<unique_id>[\d]+)\/(?P<user_id>[\d]+)"

    working_activity: Activity
    not_working_activity: Activity

    def __init__(self, token, domain, backup_loc: str, admin_id: int):
        self.intents = Intents.default()
        self.intents.message_content = True

        self.client = Bot(intents=self.intents, command_prefix="$")
        self.token = token
        self.domain = domain

        self.is_healthy = True

        self.working_activity = Activity(type=ActivityType.listening, name="Listening for steam lobby links!")
        self.not_working_activity = Activity(type=ActivityType.competing, name="Cannot connect to web server...")

    def setup_commands(self):
        @self.client.event
        async def on_ready():
            await self.client.change_presence(activity= self.working_activity, status=Status.online)
            print(f'We have logged in as {self.client.user}')

        @self.client.event
        async def on_message(message: Message):
            if message.author == self.client.user:
                return
            if message.guild is None:
                return

            found = re.search(self.steam_invite_regex, message.content)
            if found:
                if not await self.health_check():
                    return False
                
                game_name, game_logo_url = self.fetch_game_info(found)
                mentions = await self.get_mentions(message)

                await message.reply(view=UrlSectionLayout(found.group(0), self.create_new_link(found), message.author, mentions, game_name, game_logo_url))
                
    def start_bot(self):
        self.client.run(self.token)

    def create_new_link(self, match: re.Match):
        return f"{self.domain}/join/?id1={match['game_id']}&id2={match['unique_id']}&id3={match['user_id']}"
    
    def fetch_game_info(self, match: re.Match):
        game_id = match['game_id']
        contents = requests.get(f"https://store.steampowered.com/api/appdetails/?appids={game_id}").json()[game_id]['data']
        return contents['name'], contents['header_image']
    
    async def get_mentions(self, message: Message) -> List[User|Member] | None:
        mentions = []
        if message.reference and message.reference.message_id:
            msg = await message.channel.fetch_message(message.reference.message_id)
            mentions.append(msg.author)
        if message.mentions is not None:
            for ment in message.mentions:
                if ment not in mentions:
                    mentions.append(ment)
        
        if len(mentions) == 0 :
            mentions = None
        
        return mentions
    
    async def health_check(self):
        try :
            health_check = requests.get(f"{self.domain}/health")
            if health_check.status_code != 200:
                if self.is_healthy:
                    await self.client.change_presence(activity = self.not_working_activity, status=discord.Status.do_not_disturb)
                    self.is_healthy = False
                return False
            else :
                if not self.is_healthy:
                    await self.client.change_presence(activity= self.working_activity, status=discord.Status.online)
                    self.is_healthy = True
                return True
        except ConnectionError:
            if self.is_healthy:
                await self.client.change_presence(activity = self.not_working_activity, status=discord.Status.do_not_disturb)
                self.is_healthy = False
            return False