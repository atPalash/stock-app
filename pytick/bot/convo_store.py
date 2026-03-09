import json
import time
from datetime import datetime, timedelta
from typing import Optional


class ConvoStore:
    def __init__(self, redis):
        self.redis = redis

    def set_user(self, user_id: int,  **kwargs) -> None:
        self.redis.hset(f"user:{user_id}", mapping=kwargs)

    def get_user(self, user_id: int) -> dict:
        return self.redis.hgetall(f"user:{user_id}")

    def delete_user(self, user_id: int):
        self.redis.delete(f"llm_count:{user_id}")
        key = f"user:{user_id}"
        return self.redis.delete(key)  # Returns 1 (deleted) or 0 (not found)

    def incr_rate(self, user_id: int) -> int:
        """Increment per-second counter for user and return the count."""
        key = f"rate:{user_id}"
        count = self.redis.incr(key)
        # ensure key expires after 1 second
        self.redis.expire(key, 10)
        return int(count)

    def get_daily_llm(self, user_id: int) -> int:
        """Get daily LLM usage counter (UTC date) and return count."""
        key = f"llm_count:{user_id}"
        count = self.redis.get(key)
        if count is None:
            return 0
        return int(count)

    def incr_daily_llm(self, user_id: int) -> int:
        """Increment daily LLM usage counter (UTC date) and return count."""
        key = f"llm_count:{user_id}"
        count = self.redis.incr(key)
        # set expiry to midnight UTC if not set
        ttl = self.redis.ttl(key)
        if ttl is None or ttl < 0:
            tomorrow = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                        + timedelta(days=1))
            seconds = int((tomorrow - datetime.now()).total_seconds())
            self.redis.expire(key, seconds)
        return int(count)

    def subscribe_query(self, user_id: int, query: str, data: dict) -> None:
        """Subscribe user to a persistent query."""
        key = f"subs:{user_id}"
        self.redis.hset(key, query, json.dumps(data))

    def unsubscribe_query(self, user_id: int, query: str) -> bool:
        """Unsubscribe from specific query. Returns True if existed."""
        key = f"subs:{user_id}"
        return self.redis.hdel(key, query) > 0

    def get_user_subs(self, user_id: int) -> dict[str, str]:
        """Get {query: guild/dm} for user."""
        key = f"subs:{user_id}"
        return self.redis.hgetall(key)

    def get_all_user_sub_ids(self) -> list[int]:
        subs_keys = self.redis.keys("subs:*")
        ret = []
        for key in subs_keys:
            id = int(key.split(':')[1])
            ret.append(id)
        return ret

    def clear_user_subs(self, user_id: int) -> int:
        """Clear all user subscriptions. Returns count deleted."""
        key = f"subs:{user_id}"
        return self.redis.delete(key)
