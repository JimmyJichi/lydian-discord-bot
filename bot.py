"""The main bot script. Running this will start Lydian."""

# pylint: disable=wrong-import-position

print('Starting up, this can take a few moments...')

# Standard imports
import asyncio
import glob
import logging
import os
import re
import sys
import traceback
from pathlib import Path
from platform import python_version

# External imports
import aioconsole
import colorama
import discord
import yt_dlp
from discord.ext import commands
from typing import Optional, Literal

# Local imports
from cogs.presence import BotPresence
import utils.configuration as cfg
from cogs import cog_general, cog_voice
from cogs.common import EmojiStr, SilentCancel, embedq
from utils import updating
from utils.miscutil import create_logger
from utils.palette import Palette
from version import VERSION

colorama.init(autoreset=True)
plt = Palette()

# Setup discord logging
discordpy_logfile_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=discordpy_logfile_handler, level=logging.INFO, root=False)

# Setup bot logging
log = create_logger('lydian', Path('lydian.log'))
log.info('Logging for bot.py is now active.')
log.info('Python version: %s', python_version())
log.info('Lydian version: %s', VERSION)

vc_ref: cog_voice.Voice

# Check for updates
if __name__ == '__main__':
    def check_for_updates():
        log.info('Running on version %s; checking for updates...', VERSION)

        if VERSION.startswith('dev.'):
            log.warning('You are running a development version.')

        latest_release = updating.Release.get_latest_release()
        if not latest_release:
            log.warning('Could not retrieve latest release.')
            return

        # Check for an outdated version
        if updating.is_outdated(latest_release.tag, VERSION):
            log.warning('### There is a new release available: %s', latest_release.tag)
            if latest_release.is_prerelease:
                log.warning('### This is a PRE-RELEASE, it may not be fully stable yet.')
            # Anything in the release notes preceded with "###" will be shown here,
            # usually for warnings of breaking changes or as a general summary
            if important_notes := '\n'.join(re.findall(r"###.*", latest_release.text.split('---')[0])):
                print(f'\n{important_notes}\n')
            log.warning('### Use "update.py" or "update.bat" to update.')
        else:
            log.info('You are up to date.')

        log.info('Changelog: https://github.com/svioletg/lydian-discord-bot/blob/main/docs/changelog.md')
    check_for_updates()

# Clear out downloaded files
log.info('Removing previously downloaded media files...')
for t in [f for f in glob.glob('*.*') if Path(f).suffix in cfg.CLEANUP_EXTENSIONS]:
    os.remove(t)

# Establish bot user
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.voice_states = True
intents.reactions = True
intents.guilds = True
intents.members = True

# Retrieve bot token
log.info('Using token from "%s"...', cfg.TOKEN_FILE_PATH)

if not cfg.PUBLIC:
    log.warning('Starting in dev mode.')

if Path(cfg.TOKEN_FILE_PATH).is_file():
    with open(cfg.TOKEN_FILE_PATH, 'r', encoding='utf-8') as f:
        token = f.read()
else:
    log.error('Filepath "%s" does not exist; exiting.', cfg.TOKEN_FILE_PATH)
    raise SystemExit(0)

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(cfg.COMMAND_PREFIX),
    description='',
    intents=intents,
)

@bot.event
async def on_command_error(ctx: commands.Context, error: BaseException):
    """Handles any exceptions raised by any commands or modules."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=embedq(EmojiStr.cancel + ' Not enough command arguments given.',
            'Use the `help` command to see the correct syntax.'))
        return
    if isinstance(error, commands.CommandInvokeError):
        if 'ffmpeg was not found' in repr(error):
            log.error('FFmpeg was not found. It must be present either in the bot\'s directory or your system\'s PATH in order to play audio.')
            await ctx.send(embed=embedq(EmojiStr.cancel + ' Can\'t play audio. Please check the bot\'s logs.'))
            return
    if isinstance(error, NotImplementedError):
        await ctx.send(embed=embedq(EmojiStr.cancel + f' The command `{ctx.command.name}` is not implemented yet,'+
            'but is planned to be in the future.'))
        return
    if isinstance(error, yt_dlp.utils.DownloadError):
        await ctx.send(embed=embedq(EmojiStr.cancel + ' Unable to retrieve video.',
            'It may be private, or otherwise unavailable.'))
        return
    if isinstance(error, SilentCancel | commands.CheckFailure | commands.CommandNotFound):
        return # Ignored, or are handled in other modules

    # If anything unexpected occurs, log it
    log.error(error)
    if cfg.LOG_TRACEBACKS:
        log.error('Full traceback to follow...\n\n%s', ''.join(traceback.format_exception(error)))
    await ctx.send(embed=embedq(EmojiStr.cancel + ' An unexpected error has occurred. Check your logs for more information.',
        str(error)))

@bot.event
async def on_error(event_name, *args, **kwargs): # pylint: disable=unused-argument
    """Handles any non-command errors."""
    error = sys.exc_info()[1]
    log.error(error)
    if cfg.LOG_TRACEBACKS:
        log.error('Full traceback to follow...\n\n%s', ''.join(traceback.format_exception(error)))

@bot.event
async def on_ready():
    "Runs when the bot is ready to start."
    log.info('Logged in as %s (ID: %s)', bot.user, bot.user.id)
    await bot.change_presence(activity=BotPresence.idle())
    log.info('=' * 20)
    log.info('Ready!')

@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

# Define threads, get ready to start

asyncio_tasks: dict[str, asyncio.Task] = {}

async def console_thread():
    """Handles console commands."""
    def exception_message(e: Exception):
        log.info('Error encountered in console thread.')
        log.error(e)
        if cfg.LOG_TRACEBACKS:
            log.error('Full traceback to follow...\n\n%s', ''.join(traceback.format_exception(e)))

    log.info('Console is active.')
    while True:
        user_input: str = await aioconsole.ainput('')
        user_input = user_input.lower().strip()
        if user_input == '':
            continue
        match user_input:
            case 'colors':
                plt.preview()
                print()
            case 'stop':
                try:
                    log.info('Stopping the bot...')
                    log.debug('Leaving voice if connected...')
                    if vc_ref.voice_client:
                        await vc_ref.voice_client.disconnect()
                    log.debug('Cancelling bot task...')
                    asyncio_tasks['bot'].cancel()
                    await asyncio_tasks['bot']
                    log.debug('Cancelling console task...')
                    asyncio_tasks['console'].cancel()
                    await asyncio_tasks['console']
                    log.info('All tasks stopped. Exiting...')
                except Exception as e:
                    exception_message(e)
            case _:
                log.info('Unrecognized command "%s"', user_input)

async def bot_thread():
    """Async thread for the Discord bot."""
    global vc_ref # Can't really do this without it being global; pylint: disable=global-statement

    log.info('Starting bot thread...')
    log.debug('Assigning bot logger to cogs...')
    cog_general.log = log
    cog_voice.log = log
    async with bot:
        log.debug('Adding cog: General')
        await bot.add_cog(cog_general.General(bot))
        log.debug('Adding cog: Voice')
        await bot.add_cog(vc_ref := cog_voice.Voice(bot))
        log.info('Logging in with token, please wait for a "Ready!" message before using any commands...')
        await bot.start(token)

async def main():
    """Creates main tasks and runs everything."""
    asyncio_tasks['bot'] = asyncio.create_task(bot_thread())
    asyncio_tasks['console'] = asyncio.create_task(console_thread())
    try:
        await asyncio.gather(asyncio_tasks['bot'], asyncio_tasks['console'])
    except asyncio.exceptions.CancelledError:
        pass

if __name__ == '__main__':
    asyncio.run(main())
