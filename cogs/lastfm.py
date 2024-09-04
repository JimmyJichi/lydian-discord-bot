"""Cog for last.fm scrobbling and related commands."""

# Standard imports
import logging
import os
import time
import asyncio
from typing import Optional

# External imports
from discord.ext import commands
from discord import Message, Embed
import pylast

# Local imports
from cogs.common import embedq, is_command_enabled
import utils.configuration as cfg

log = logging.getLogger('lydian')

class LastFM(commands.Cog):
    """Last.fm scrobbling and related functions."""
    def __init__(self, bot: commands.bot.Bot):
        self.bot = bot
        self.network = pylast.LastFMNetwork(cfg.get('lastfm.api-key'), cfg.get('lastfm.api-secret'))
        if not os.path.exists('lastfm'):
            os.mkdir('lastfm')

    def now_playing(self, session_key, artist, title):
        """Update the now playing status on Last.fm."""
        self.network.session_key = session_key

        try:
            self.network.update_now_playing(artist, title)
        except Exception as e:
            log.error('Error updating now playing: %s', e)

    def scrobble(self, session_key, artist, title):
        """Scrobble the track to Last.fm."""
        self.network.session_key = session_key

        try:
            self.network.scrobble(artist, title, int(time.time()))
        except Exception as e:
            log.error('Error scrobbling: %s', e)

    @commands.hybrid_command(name='lastfm')
    @commands.check(is_command_enabled)
    async def lastfm(self, ctx: commands.Context):
        """Connect your Last.fm account to object.gg."""
        if cfg.get('lastfm.api-key') == 'API_KEY' or cfg.get('lastfm.api-secret') == 'API_SECRET':
            await ctx.send(embed=embedq('Last.fm API keys are not set.'))
            return
        
        if not os.path.exists('lastfm/{}.sessionkey'.format(ctx.author.id)):
            lastfm_msg: Optional[Message] = None
            skg = pylast.SessionKeyGenerator(self.network)
            auth_url = skg.get_web_auth_url()
            lastfm_msg = await ctx.send(embed=Embed(title='Please authenticate with Last.fm by clicking here.', url=auth_url), ephemeral=True)

            while True:
                try:
                    session_key = skg.get_web_auth_session_key(auth_url)
                    with open('lastfm/{}.sessionkey'.format(ctx.author.id), 'w') as f:
                        f.write(session_key)
                    await lastfm_msg.edit(embed=embedq('Your Last.fm account has been connected.'), delete_after=10)
                    break
                except pylast.WSError:
                    await asyncio.sleep(1)
        else:
            await ctx.send(embed=embedq('Your Last.fm account is already connected.'), ephemeral=True)