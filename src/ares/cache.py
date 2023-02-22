"""Tools for caching attribute values.

"""
from functools import wraps


def property_cache_once_per_frame(f):
    """Cache an attribute that won't change this frame.

    This decorator caches the return value for one game loop,
    then clears it if it is accessed in a different game loop.
    Only works on properties of the bot object, because it requires
    access to self.state.game_loop.
    """

    @wraps(f)
    def inner(self):
        """Inner level cache

        Parameters
        ----------
        self :
            Must have an `ai` attribute that is, or inherits, BotAI

        Returns
        -------

        """
        property_cache = "_cache_" + f.__name__
        state_cache = "_frame_" + f.__name__
        cache_updated = getattr(self.ai, state_cache, -1) == self.ai.state.game_loop
        if not cache_updated:
            setattr(self.ai, property_cache, f(self))
            setattr(self.ai, state_cache, self.ai.state.game_loop)

        cache = getattr(self.ai, property_cache)
        should_copy = callable(getattr(cache, "copy", None))
        if should_copy:
            return cache.copy()
        return cache

    return property(inner)
