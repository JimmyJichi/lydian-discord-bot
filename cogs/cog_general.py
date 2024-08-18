"""Cog for general, miscellaneous commands."""

# Standard imports
import logging

# External imports
from discord.ext import commands

# Local imports
from cogs.common import command_aliases, embedq, is_command_enabled
from version import VERSION

log = logging.getLogger('lydian')

class General(commands.Cog):
    """General, miscellaneous functions."""
    def __init__(self, bot: commands.bot.Bot):
        self.bot = bot

    @commands.command(aliases=command_aliases('changelog'))
    @commands.check(is_command_enabled)
    async def changelog(self, ctx: commands.Context):
        """Returns a link to the changelog, and displays most recent version."""
        await ctx.send(embed=embedq('Read the latest changelog here: https://github.com/svioletg/lydian-discord-bot/blob/main/docs/changelog.md',
            f'This bot is currently running on v{VERSION}'))

    @commands.hybrid_command(name='ping')
    @commands.check(is_command_enabled)
    async def ping(self, ctx: commands.Context):
        """Check if the bot is online."""
        await ctx.send('Pong!')

    @commands.command(aliases=command_aliases('repository'))
    @commands.check(is_command_enabled)
    async def repository(self, ctx: commands.Context):
        """Returns the link to the Lydian GitHub repository."""
        await ctx.send(embed=embedq('Lydian GitHub repository: https://github.com/svioletg/lydian-discord-bot',
            'https://github.com/svioletg/lydian-discord-bot\nA GitHub account is required to submit issues.'))

    @commands.command(aliases=command_aliases('faq'))
    @commands.check(is_command_enabled)
    async def faq(self, ctx: commands.Context):
        """Returns a link to Lydian's FAQ page."""
        await ctx.send(embed=embedq('Lydian FAQ page: https://github.com/svioletg/lydian-discord-bot/blob/main/docs/faq.md'))

    @commands.command(aliases=command_aliases('issues'))
    @commands.check(is_command_enabled)
    async def issues(self, ctx: commands.Context):
        """Returns a link to Lydian's issues page on GitHub."""
        await ctx.send(embed=embedq('Lydian Issues page: https://github.com/svioletg/lydian-discord-bot/issues'))
