import nextcord
import sys

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


class messages:
    def mreply(message, reply_message, **kwargs):
        if kwargs == None:
            kwargs["embed"] = None
            kwargs["ephemeral"] = None
        logging.info(kwargs)
        if type(message) == nextcord.Message:
            return message.reply(reply_message, embed=kwargs["embed"])
        elif type(message) == nextcord.Interaction:
            return message.respond.response.send_message(reply_message, embed=kwargs["embed"],  ephemeral=kwargs["ephemeral"])
        elif type(message) == nextcord.ext.commands.Context:
            return message.reply(reply_message, embed=kwargs["embed"])
        else:
            raise TypeError
            return
    
    def content_check(message):
        if type(message) == nextcord.Message:
            return message.content
        elif type(message) == nextcord.Interaction:
            return message.message.content
        else:
            raise TypeError
            return