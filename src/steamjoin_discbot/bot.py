from typing import List

import discord
import re
import requests
from requests.exceptions import ConnectionError

from message_templates.url_view import UrlView
from message_templates.url_embed import UrlEmbed
from helpers import MessageType
from datastore import Datastore

from discord import Role, User, Member, Intents, Activity, ActivityType, Status, Message
from discord.ext.commands import Bot, Context

class SteamSneggy():
    intents: Intents
    client: Bot
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

        self.client = Bot(intents=self.intents, command_prefix="$")
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

        @self.client.group(help="Commands to change SteamSneggy options.")
        async def sneggyset(ctx: Context):
            if ctx.invoked_subcommand is None or ctx.subcommand_passed == "help":
                helpmsg = "```\n" \
                    '$sneggyset :\n\n'\
                    'Change various settings of the bot.\n\n' \
                    'Commands:\n'\
                    '    big chungus\tThis is entirely just to troll Hollow.\n' \
                    '    message_type   Change the type of message the bot should send in response to steam links.\n' \
                    '                   (Current options: tiny, default)\n' \
                    '    permissions\tChange permissions. This lets you allow certain users/roles to change the bot settings.```'
                await ctx.send(helpmsg)

        @sneggyset.command(name="big", help="This is entirely just to troll Hollow.")
        async def hihollow(ctx: Context, word):
            if word == "chungus":
                await ctx.send("<@848401094329237524> give me $5")

        async def has_privleges(usr: User | Member, ctx: Context) -> bool:
            if ctx.guild is None or isinstance(usr, User):
                return False
            if usr.id == ctx.guild.owner_id:
                return True
            return await self.is_allowed(usr.id, [x.id for x in usr.roles], ctx.guild.id)
            
        @sneggyset.command(name="message_type", help="Command to change the message type to send (tiny,default)")
        async def set_message_type(ctx: Context, message_type: str):
            if not await has_privleges(ctx.author, ctx) :
                user = await self.client.fetch_user(ctx.author.id)
                await user.send(f"You don't have permissions to run this command: '$sneggyset message_type' {f'in server {ctx.guild.name}' if ctx.guild is not None else ""}.")
                return
            else:
                if ctx.guild is None:
                    return
                success = self.set_message_type(message_type, ctx.guild.id)
                if success:
                    await ctx.send(f"Message type has been set to {message_type}")
                else :
                    await ctx.send(f"Issue when trying to set message choice. Your options are: {", ".join([x.value for x in MessageType])}")
        
        @sneggyset.group(help = "Commands to change permissions options.")
        async def permissions(ctx: Context):
            if not await has_privleges(ctx.author, ctx) :
                user = await self.client.fetch_user(ctx.author.id)
                await user.send(f"You don't have permissions to run this command: '$sneggyset permissions' {f'in server {ctx.guild.name}' if ctx.guild is not None else ""}.")
                return
            if ctx.invoked_subcommand is None or ctx.subcommand_passed == "help":
                helpmsg = "```\n" \
                    '$sneggyset permissions :\n\n'\
                    'Set permissions for users and roles.\n\n' \
                    'Commands:\n'\
                    '    users\t\tCommands to control user permissions (add, remove, list)\n'\
                    '    roles\t\tCommands to control role permissions (add, remove, list)```'
                await ctx.send(helpmsg)
                return

        @permissions.group(help="Commands to change USER permissions.")
        async def users(ctx: Context):
            if ctx.invoked_subcommand is None or ctx.subcommand_passed == "help":
                helpmsg = "```\n" \
                    '$sneggyset permissions users:\n\n'\
                    'Set permissions for users in particular.\n\n' \
                    'Commands:\n'\
                    '    add\t\tAdd a user to the list of authorized users.\n'\
                    '    remove\t  Remove a list from the list of authorized users.\n'\
                    '    list\t\tList all users authorized to use this bot.```'
                await ctx.send(helpmsg)

        @users.command(name="add")
        async def add_user(ctx: Context, user: User):
            if ctx.guild is None:
                return
            success = self.add_user_message(user, ctx.guild.id)
            if success:
                await ctx.send(f"Added user {user.mention} to the elevated users list.", allowed_mentions=discord.AllowedMentions.none())
            else :
                await ctx.send("Issue when trying to add user. Please format your message as follows:\n```\n$sneggyset add_user @Systematical\n```")

        @users.command(name="remove")
        async def remove_user(ctx: Context, user: User):
            if ctx.guild is None:
                return
            success = self.remove_user_message(user, ctx.guild.id)
            if success :
                await ctx.send(f"Removed user {user.mention} from the elevated users list.", allowed_mentions=discord.AllowedMentions.none())
            else :
                await ctx.send("Issue when trying to remove user. Please format your message as follows:\n```\n$sneggyset remove_user @Systematical\n```")
        
        @users.command(name="list")
        async def list_users(ctx: Context):
            members = []
            if ctx.guild is None:
                return
            for u in self.datastore.get_allowed_users(ctx.guild.id):
                members.append(ctx.guild.get_member(u))
            await ctx.send(f"The following users can change this bot's settings (besides the server owner): {", ".join([m.mention for m in members])}", allowed_mentions=discord.AllowedMentions.none())

        @permissions.group(help="Commands to change ROLE permissions")
        async def roles(ctx: Context):
            if ctx.invoked_subcommand is None or ctx.subcommand_passed == "help":
                helpmsg = "```\n" \
                    '$sneggyset permissions roles:\n\n'\
                    'Set permissions for roles in particular.\n\n' \
                    'Commands:\n'\
                    '    add\t\tAdd a role to the list of authorized roles.\n'\
                    '    remove\t  Remove a list from the list of authorized roles.\n'\
                    '    list\t\tList all roles authorized to use this bot.```'
                await ctx.send(helpmsg)

        @roles.command("add")
        async def add_role(ctx: Context, role: Role):
            if ctx.guild is None:
                return
            success = self.add_role_message(role, ctx.guild.id)
            if success :
                await ctx.send(f"Added role {role.mention} to the elevated roles list.", allowed_mentions=discord.AllowedMentions.none())
            else :
                await ctx.send("Issue when trying to add role. Please format your message as follows:\n```\n$sneggyset add_role @BotManager\n```")
        
        @roles.command("remove")
        async def remove_role(ctx: Context, role: Role):
            if ctx.guild is None:
                return
            success = self.remove_role_message(role, ctx.guild.id)
            if success :
                await ctx.send(f"Removed role {role.mention} from the elevated roles list.", allowed_mentions=discord.AllowedMentions.none())
            else :
                await ctx.send("Issue when trying to remove role. Please format your message as follows:\n```\n$sneggyset remove_role @BotManager\n```")

        @roles.command("list")
        async def list_roles(ctx: Context):
            roles = []
            if ctx.guild is None:
                return
            for r in self.datastore.get_allowed_roles(ctx.guild.id):
                roles.append(ctx.guild.get_role(r))
            await ctx.send(f"The following roles can change this bot's settings: {", ".join([r.mention for r in roles])}", allowed_mentions=discord.AllowedMentions.none())

        @self.client.event
        async def on_message(message: Message):
            if message.author == self.client.user:
                return

            await self.client.process_commands(message)

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
                
    def start_bot(self):
        self.client.run(self.token)

    def create_new_link(self, match: re.Match):
        return f"{self.domain}/join/?id1={match['game_id']}&id2={match['unique_id']}&id3={match['user_id']}"
    
    def fetch_game_info(self, match: re.Match):
        game_id = match['game_id']
        contents = requests.get(f"https://store.steampowered.com/api/appdetails/?appids={game_id}").json()[game_id]['data']
        return contents['name'], contents['header_image']
    
    def set_message_type(self, type: str, server_id: int):
        if MessageType.has_value(type):
            self.datastore.set_message_type(server_id, MessageType(type))
            return True
        return False
    
    def add_user_message(self, user: User, server_id: int):
        self.datastore.add_allowed_user(server_id, user.id)
        return True
    
    def remove_user_message(self, user: User, server_id: int):
        self.datastore.remove_allowed_user(server_id, user.id)
        return True
    
    def add_role_message(self, role: Role, server_id: int):
        self.datastore.add_allowed_role(server_id, role.id)
        return True
    
    def remove_role_message(self, role: Role, server_id: int):
        self.datastore.remove_allowed_role(server_id, role.id)
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