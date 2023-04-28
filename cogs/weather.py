import datetime
import nextcord
import locale

from nextcord.ext import commands

from util import nira, n_fc

data_call = ["今日", "明日", "明後日"]
day_of_week = ["月", "火", "水", "木", "金", "土", "日"]

class Weather(commands.Cog):
    def __init__(self, bot: nira.NIRA):
        self.bot = bot
        self.lang = "ja"
        self.endpoint_url = "https://wttr.in/{}?format=j1&lang=ja"
        locale.setlocale(locale.LC_TIME, 'ja_JP.UTF-8')

    def _getWeek(self, week: int) -> str:
        return day_of_week[week]

    async def _apiCall(self, location: str):
        async with self.bot.session.get(self.endpoint_url.format(location)) as resp:
            return await resp.json()

    async def _getWeather(self, location: str) -> nextcord.Embed:
        data = await self._apiCall(location)
        now = datetime.datetime.now()

        embed = nextcord.Embed(
            title=f"`{data['nearest_area'][0]['areaName'][0]['value']} ({data['nearest_area'][0]['country'][0]['value']})`の天気",
            description=f"今の天気: `{data['current_condition'][0]['lang_ja'][0]['value']}` ({data['current_condition'][0]['temp_C']}℃)",
            color=0x00ff00
        )

        for day in range(3):
            weather = data["weather"][day]
            target_date = now + datetime.timedelta(days=1*day)
            embed.add_field(
                name=f"{data_call[day]}(`{target_date.strftime('%m/%d')}-{self._getWeek(target_date.weekday())}`)の天気",
                value="\n".join(
                    [
                        (f"{int(j['time'])//100}時〜 `{j['lang_ja'][0]['value']}` ({j['tempC']}℃)") for j in weather["hourly"][( 0 if day != 0 else int(target_date.strftime("%H"))//3 ):]
                    ]
                )
            )

        return embed

    @nextcord.slash_command(name="weather", description="Get weather info from wttr.in", description_localizations={nextcord.Locale.ja: "Wttr.inより天気情報を取得します。"})
    async def weather(
            self,
            interaction: nextcord.Interaction,
            location: str = nextcord.SlashOption(
                description="location",
                description_localizations={nextcord.Locale.ja: "地名"},
                required=True
            )
        ):
        await interaction.response.defer(ephemeral=False)
        await interaction.send(embed=await self._getWeather(location))


def setup(bot: nira.NIRA):
    bot.add_cog(Weather(bot))
