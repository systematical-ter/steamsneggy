from typing import List

import discord
import re
import requests
from requests.exceptions import ConnectionError

from message_templates.url_view import UrlView
from message_templates.url_embed import UrlEmbed
from helpers import MessageType
from datastore import Datastore

from discord import User, Member, Intents, Client, Activity, ActivityType, Status, Message

class SteamSneggy():
    intents: Intents
    client: Client
    token: str
    domain: str

    datastore: Datastore

    is_healthy: bool

    steam_invite_regex = r"steam:\/\/joinlobby\/(?P<game_id>[\d]+)\/(?P<unique_id>[\d]+)\/(?P<user_id>[\d]+)"

    working_activity: Activity
    not_working_activity: Activity

    def __init__(self, token, domain, backup_loc: str):
        self.intents = Intents.default()
        self.intents.message_content = True

        self.client = Client(intents=self.intents)
        self.token = token
        self.domain = domain

        self.datastore = Datastore(backup_loc)

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

            found = re.search(self.steam_invite_regex, message.content)
            if found:
                if not await self.health_check():
                    return False
                
                game_name, game_logo_url = self.fetch_game_info(found)
                mentions = await self.get_mentions(message)

                message_type = MessageType.Default
                if message.guild is not None:
                    message_type = self.datastore.get_message_type(message.guild.id)

                match message_type:
                    case MessageType.Tiny:
                        await message.reply(embed=UrlEmbed(found.group(0), self.create_new_link(found), game_name, game_logo_url, message.author, mentions))
                    case MessageType.Default:
                        await message.reply(view=UrlView(found.group(0), self.create_new_link(found), game_name, game_logo_url, message.author, mentions))
                

            if message.content.startswith('$sneggyset'):
                if message.guild is not None :
                    pieces = message.content.split(" ")
                    if pieces[1] == "message_type":
                        self.datastore.set_message_type(message.guild.id, MessageType(pieces[2]))
                        await message.channel.send(f"Message type has been set to {pieces[2]}")
                        
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
        except ConnectionError as err:
            if self.is_healthy:
                await self.client.change_presence(activity = self.not_working_activity, status=discord.Status.do_not_disturb)
                self.is_healthy = False
            return False