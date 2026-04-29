from typing import List
from discord import ui, User, Member, Color

class UrlSection(ui.Section):

    def __init__(self, old_link: str, new_link: str, from_user: User|Member, to_user: List[User|Member] | None, game_title: str, game_image: str):
        title = f"## {game_title} Lobby Link"
        msg = f"From {from_user.mention}"
        if to_user is not None and len(to_user) > 0:
            msg += f" for {", ".join([x.mention for x in to_user])}"
        link = f"[{old_link}]({new_link})"
        super().__init__(title, msg, link, accessory = ui.Thumbnail(game_image))

class UrlSectionLayout(ui.LayoutView):

    def __init__(self, old_link: str, new_link: str, from_user: User | Member, to_user: List[User|Member] | None, game_title, game_image):
        super().__init__()
        section = ui.Container(UrlSection(old_link, new_link, from_user, to_user, game_title, game_image), accent_color=Color.blurple())

        self.add_item(section)
