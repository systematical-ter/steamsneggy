from discord import Embed, User, Member, File
from typing import List

class UrlEmbed(Embed):

    def __init__(self, old_link: str, new_link: str, game_name: str, game_logo_url: str, from_user: User | Member, mentions : List[User|Member] | None):
        super().__init__(title=game_name, url=new_link)
        self.set_thumbnail(url=game_logo_url)

        self.set_author(name=from_user.display_name)