import nextcord
from nextcord import Interaction, message
from nextcord.ext import commands
from nextcord.utils import get
from os import getenv
import sys
import asyncio
import subprocess
import websockets
import traceback
import importlib
import json
global task
from cogs import server_status
import re

import sys
sys.path.append('../')
from util import n_fc, mc_status
import nira
import datetime

# rolepanel

#loggingの設定
import logging
dir = sys.path[0]
class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'{dir}/nira.log', level=logging.INFO)


class rolepanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(rolepanel(bot))
