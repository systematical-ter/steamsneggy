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
    admin_id: int

    steam_invite_regex = r"steam:\/\/joinlobby\/(?P<game_id>[\d]+)\/(?P<unique_id>[\d]+)\/(?P<user_id>[\d]+)"

    working_activity: Activity
    not_working_activity: Activity

    def __init__(self, token, domain, backup_loc: str, admin_id: int):
        self.intents = Intents.default()
        self.intents.message_content = True

        self.client = Client(intents=self.intents)
        self.token = token
        self.domain = domain

        self.datastore = Datastore(backup_loc)

        self.is_healthy = True
        self.admin_id = admin_id

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

                message_type = MessageType.default
                if message.guild is not None:
                    message_type = self.datastore.get_message_type(message.guild.id)

                match message_type:
                    case MessageType.tiny:
                        await message.reply(embed=UrlEmbed(found.group(0), self.create_new_link(found), game_name, game_logo_url, message.author, mentions))
                    case MessageType.default:
                        await message.reply(view=UrlView(found.group(0), self.create_new_link(found), game_name, game_logo_url, message.author, mentions))
                

            if message.content.startswith('$sneggyset'):
                if message.guild is not None and isinstance(message.author, Member):
                    if message.guild.owner_id == message.author.id or await self.is_allowed(message.author.id, [x.id for x in message.author.roles], message.guild.id):
                        pieces = message.content.split(" ")
                        print(pieces)
                        match pieces[1]:
                            case "message_type":
                                success = self.set_message_type(message.content, message.guild.id)
                                if success:
                                    await message.channel.send(f"Message type has been set to {pieces[2]}")
                                else :
                                    await message.channel.send(f"Issue when trying to set message choice. Your options are: {", ".join([x.value for x in MessageType])}")
                            case "add_user":
                                success = self.add_user_message(message, message.guild.id)
                                if success :
                                    await message.channel.send(f"Added user {message.mentions[0].mention} to the elevated users list.", allowed_mentions=discord.AllowedMentions.none())
                                else :
                                    await message.channel.send("Issue when trying to add user. Please format your message as follows:\n```\n$sneggyset add_user @Systematical\n```")
                            case "remove_user":
                                success = self.remove_user_message(message, message.guild.id)
                                if success :
                                    await message.channel.send(f"Removed user {message.mentions[0].mention} from the elevated users list.", allowed_mentions=discord.AllowedMentions.none())
                                else :
                                    await message.channel.send("Issue when trying to remove user. Please format your message as follows:\n```\n$sneggyset remove_user @Systematical\n```")
                            case "list_user":
                                members = []
                                for u in self.datastore.get_allowed_users(message.guild.id):
                                    members.append(message.guild.get_member(u))
                                await message.channel.send(f"The following users can change this bot's settings (besides the server owner): {[m.mention for m in members]}", allowed_mentions=discord.AllowedMentions.none())
                            case "add_role":
                                success = self.add_role_message(message, message.guild.id)
                                if success :
                                    await message.channel.send(f"Added role {message.role_mentions[0].mention} to the elevated roles list.", allowed_mentions=discord.AllowedMentions.none())
                                else :
                                    await message.channel.send("Issue when trying to add role. Please format your message as follows:\n```\n$sneggyset add_role @BotManager\n```")
                            case "remove_role":
                                success = self.remove_role_message(message, message.guild.id)
                                if success :
                                    await message.channel.send(f"Removed role {message.role_mentions[0].mention} from the elevated roles list.", allowed_mentions=discord.AllowedMentions.none())
                                else :
                                    await message.channel.send("Issue when trying to remove role. Please format your message as follows:\n```\n$sneggyset remove_role @BotManager\n```")
                            case "list_role":
                                roles = []
                                for r in self.datastore.get_allowed_roles(message.guild.id):
                                    roles.append(message.guild.get_role(r))
                                await message.channel.send(f"The following roles can change this bot's settings: {[r.mention for r in roles]}", allowed_mentions=discord.AllowedMentions.none())
                            
                    else :
                        await message.reply("Sorry, you don't have permissions to set my options!")

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
    
    def set_message_type(self, message: str, server_id: int):
        reg = r"\$sneggyset message_type (?P<type>(%s))" % "|".join([x.value for x in MessageType])
        res = re.match(reg, message)
        print(res)
        print(reg)
        print(message)
        if not res:
            return False
        
        self.datastore.set_message_type(server_id, MessageType(res['type']))
        return True
    
    def add_user_message(self, message: discord.Message, server_id: int):
        print(message.content)
        reg = r"\$sneggyset add_user \<@(?P<user_id>[0-9]+)\>"
        res = re.match(reg, message.content)
        if not res:
            return False
        
        if len(message.mentions) == 0:
            return False
        
        self.datastore.add_allowed_user(server_id, int(res['user_id']))
        return True
    
    def remove_user_message(self, message: discord.Message, server_id: int):
        print(message.content)
        reg = r"\$sneggyset remove_user \<@(?P<user_id>[0-9]+)\>"
        res = re.match(reg, message.content)
        if not res:
            return False
        
        if len(message.mentions) == 0:
            return False
        
        self.datastore.remove_allowed_user(server_id, int(res['user_id']))
        return True
    
    def add_role_message(self, message: discord.Message, server_id: int):
        print(message.content)
        reg = r"\$sneggyset add_role \<@&(?P<role_id>[0-9]+)\>"
        res = re.match(reg, message.content)
        if not res:
            return False
        
        if len(message.role_mentions) == 0:
            return False
        
        self.datastore.add_allowed_role(server_id, int(res['role_id']))
        return True
    
    def remove_role_message(self, message: discord.Message, server_id: int):
        print(message.content)
        reg = r"\$sneggyset remove_role \<@&(?P<role_id>[0-9]+)\>"
        res = re.match(reg, message.content)
        if not res:
            return False
        
        if len(message.role_mentions) == 0:
            return False
        
        self.datastore.remove_allowed_role(server_id, int(res['role_id']))
        return True

    async def is_allowed(self, author_id: int, author_roles: List[int], server_id: int):
        if author_id == self.admin_id:
            return True
        
        if self.datastore.is_user_allowed(server_id, author_id):
            return True
        
        for role in author_roles:
            if self.datastore.is_role_allowed(server_id, role):
                return True
        
        return False
    
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