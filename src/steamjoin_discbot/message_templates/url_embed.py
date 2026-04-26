from discord import Embed, User, Member, File
from typing import List

class UrlEmbed(Embed):

    def __init__(self, old_link: str, new_link: str, game_name: str, game_logo_url: str, from_user: User | Member, mentions : List[User|Member] | None):
        super().__init__(title=game_name)
        #self.set_thumbnail(url=game_logo_url)

        for_str = ""
        if mentions is not None :
            for_str = " for " + ", ".join([x.mention for x in mentions])

        self.add_field(name="", value=f"Invite link from {from_user.mention}{for_str}\n", inline=False)
        self.add_field(name="Join Lobby:", value=f"[{old_link}]({new_link})")