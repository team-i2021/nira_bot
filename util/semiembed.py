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
        self._embed_extra: dict[str, None | nextcord.embeds.EmbedProxy] = {
            "author": None,
            "footer": None,
            "image": None,
            "thumbnail": None,
        }
        self.fields = []

    def add_field(self, name: str, value: str, inline: bool = True) -> None:
        self.fields.append(
            {
                "name": name,
                "value": value,
                "inline": inline,
            }
        )

    def set_author(self, name: str | None = None, url: str | None = None, icon_url: str | None = None) -> None:
        self._embed_extra["author"] = nextcord.embeds.EmbedProxy({
            "name": name,
            "url": url,
            "icon_url": icon_url,
        })

    def set_footer(self, text: str | None = None, icon_url: str | None = None) -> None:
        self._embed_extra["footer"] = nextcord.embeds.EmbedProxy({
            "text": text,
            "icon_url": icon_url,
        })

    def set_image(self, url: str | None = None) -> None:
        self._embed_extra["image"] = nextcord.embeds.EmbedProxy({
            "url": url,
        })

    def set_thumbnail(self, url: str | None = None) -> None:
        self._embed_extra["thumbnail"] = nextcord.embeds.EmbedProxy({
            "url": url,
        })

    def _create_embed(self) -> nextcord.Embed:
        embed = nextcord.Embed(**self._embed_base)
        for key, value in self._embed_extra.items():
            if value is not None:
                embed.__setattr__(key, value)
        return embed

    def get_embeds(self, limit: int = 7, page_show: bool = True) -> list[nextcord.Embed]:
        embeds = []
        for i in range(0, len(self.fields), limit):
            embed = self._create_embed()
            for field in self.fields[i : i + limit]:
                embed.add_field(**field)
            if page_show:
                embed.set_footer(text=f"{'' if (footer := getattr(embed, 'footer', None)) is None else footer.text + ' | '}{len(embeds) + 1}/{len(self.fields) // limit + 1} Page(s)")
            embeds.append(embed)
        return embeds
