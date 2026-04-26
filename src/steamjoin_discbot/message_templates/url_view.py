from discord import ui

class UrlContainer(ui.Container):
    display: ui.TextDisplay
    content: str

    def __init__(self, old_link: str, new_link: str):
        super().__init__()
        self.content = "### Steam Invite\n"
        self.content += f"**Steam link:** \n{old_link}\n\n"
        self.content += f"**Hyperlink:** \n[{old_link}]({new_link})"
        
        self.display = ui.TextDisplay(content=self.content)
        self.add_item(self.display)

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

    def __init__(self, old_link: str, new_link: str, game_name: str, game_logo_url: str):
        self.old_link = old_link
        self.new_link = new_link

        super().__init__()

        self.header = GameInfoSection(game_name, game_logo_url)
        self.container = UrlContainer(old_link, new_link)
        self.actionrow = UrlActionRow(new_link)

        self.add_item(self.header)
        self.add_item(self.container)
        self.add_item(self.actionrow)