import nextcord

class SemiEmbed:
    """
    沢山フィールドを付けられて、後でページ分けできるEmbed生成クラス
    """
    def __init__(self, title: str, description: str, color: int = 0x00FF00) -> None:
        self._embed_base = {
            "title": title,
            "description": description,
            "color": color,
        }
        self._embed_extra: dict[str, None | dict[str, str | None]] = {
            "author": None,
            "footer": None,
            "image": None,
            "thumbnail": None,
        }
        self.fields = []

    def add_field(self, name: str, value: str, inline: bool = True) -> None:
        if name is None or value is None:
            raise ValueError("name or value is None")
        self.fields.append(
            {
                "name": name,
                "value": value,
                "inline": inline,
            }
        )

    def set_author(self, name: str | None = None, url: str | None = None, icon_url: str | None = None) -> None:
        if name is None and url is None and icon_url is None:
            self._embed_extra["author"] = None
            return
        self._embed_extra["author"] = {
            "name": name,
            "url": url,
            "icon_url": icon_url,
        }

    def set_footer(self, text: str | None = None, icon_url: str | None = None) -> None:
        if text is None and icon_url is None:
            self._embed_extra["footer"] = None
            return
        self._embed_extra["footer"] = {
            "text": text,
            "icon_url": icon_url,
        }

    def set_image(self, url: str | None = None) -> None:
        if url is None:
            self._embed_extra["image"] = None
            return
        self._embed_extra["image"] = {
            "url": url,
        }

    def set_thumbnail(self, url: str | None = None) -> None:
        if url is None:
            self._embed_extra["thumbnail"] = None
            return
        self._embed_extra["thumbnail"] = {
            "url": url,
        }

    def _create_embed(self) -> nextcord.Embed:
        embed = nextcord.Embed(**self._embed_base)
        for key, value in self._embed_extra.items():
            if value is None:
                continue
            match key:
                case "author":
                    embed.set_author(**value)
                case "footer":
                    embed.set_footer(**value)
                case "image":
                    embed.set_image(**value)
                case "thumbnail":
                    embed.set_thumbnail(**value)
        return embed

    def get_embeds(self, limit: int = 7, page_show: bool = True) -> list[nextcord.Embed]:
        embeds = []
        if len(self.fields) == 0:
            return [nextcord.Embed(**self._embed_base)]
        for i in range(0, len(self.fields), limit):
            embed = self._create_embed()
            for field in self.fields[i : i + limit]:
                embed.add_field(**field)
            if page_show:
                embed.set_footer(
                    text=(("" if self._embed_extra['footer'] is None else f"{self._embed_extra['footer']['text']} | ") + f"{len(embeds) + 1}/{(len(self.fields) - 1) // limit + 1} Page(s)")
                )
            embeds.append(embed)
        return embeds
