"""Contains a number of common presence statuses, for consistency."""

# Standard imports
from typing import TYPE_CHECKING

# External imports
from discord import Activity, ActivityType

# Local imports
import utils.configuration as cfg

if TYPE_CHECKING:
    from cogs.cog_voice import MediaQueue, QueueItem

class BotPresence:
    """Class containing a number of common presence statuses, for consistency."""
    @staticmethod
    def idle() -> Activity:
        """Shown when the queue is empty, and nothing is playing."""
        return Activity(
            name=f'Nothing! Use `/play` to start',
            type=ActivityType.listening,
            state='Queue is empty.'
            )

    @staticmethod
    def playing(item: 'QueueItem', media_queue: 'MediaQueue') -> Activity:
        """Shown when a track is currently playing.

        @item: The item to show info for
        """
        return Activity(
            name=item.info.title,
            type=ActivityType.listening,
            state=f'{len(media_queue)} {'item' if len(media_queue) == 1 else 'items'} left in queue.'
            )
