from typing import List

from discord import ui, Member, User

class UrlContainer(ui.Container):
    display: ui.TextDisplay
    content: str

    def __init__(self, old_link: str, new_link: str, from_user: User|Member, to_user: List[User|Member]|None, game_name: str, game_logo_url: str):
        super().__init__()
        to_mentions = ""
        if to_user is not None:
            to_mentions = " for " + ", ".join([x.mention for x in to_user])
        self.content = f"### Steam Invite from {from_user.mention}{to_mentions}\n"
        # self.content += f"**Steam link:** \n{old_link}\n\n"
        self.content += f"**Hyperlink:** \n[{old_link}]({new_link})"
        
        self.header = GameInfoSection(game_name, game_logo_url)
        
        self.display = ui.TextDisplay(content=self.content)
        self.add_item(self.display)
        self.add_item(self.header)

class UrlActionRow(ui.ActionRow):
    linkbutton: ui.Button

    def __init__(self, new_link: str):
        super().__init__()

        self.linkbutton = ui.Button(label="Click here to join the lobby!", url=new_link)
        self.add_item(self.linkbutton)

class GameInfoSection(ui.MediaGallery):
    def __init__(self, game_name: str, game_logo_url: str):
        super().__init__()
        self.add_item(media = game_logo_url, description= game_name)

class UrlView(ui.LayoutView):
    old_link: str
    new_link: str

    container: UrlContainer
    actionrow: UrlActionRow

    def __init__(self, old_link: str, new_link: str, game_name: str, game_logo_url: str, from_user: User | Member, mentions : List[User|Member] | None):
        self.old_link = old_link
        self.new_link = new_link

        super().__init__()

        self.container = UrlContainer(old_link, new_link, from_user, mentions, game_name, game_logo_url)
        self.actionrow = UrlActionRow(new_link)

        self.add_item(self.container)
        self.add_item(self.actionrow)