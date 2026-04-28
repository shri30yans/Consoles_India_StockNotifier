"""Resolve Telegram chat ids for the configured bot.

Usage:
    1. Add the bot to your group/channel and promote it to admin.
    2. Send any message in the group (or post in the channel).
    3. Run:  python scripts/telegram_resolve_chat_id.py
       It will print every (chat_id, title, type) the bot has seen.

Then copy the chat id (it will be a negative number for groups/channels)
into the relevant TELEGRAM_CHAT_* variable in .env.
"""

from __future__ import annotations

import os
import sys

import requests
from dotenv import load_dotenv


def main() -> int:
    load_dotenv()
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    if not token:
        print("ERROR: TELEGRAM_TOKEN not set in .env", file=sys.stderr)
        return 1

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    resp = requests.get(url, timeout=20)
    if resp.status_code != 200:
        print(f"ERROR: Telegram returned HTTP {resp.status_code}: {resp.text}")
        return 2

    data = resp.json()
    if not data.get("ok"):
        print(f"ERROR: Telegram says: {data}")
        return 3

    updates = data.get("result", [])
    if not updates:
        print(
            "No updates yet. Make sure you have:\n"
            "  1. Added @<your_bot> to the group/channel\n"
            "  2. Promoted it to admin\n"
            "  3. Sent at least one message in the group after that\n"
            "Then re-run this script."
        )
        return 0

    seen: dict[int, dict] = {}
    for upd in updates:
        for key in ("message", "channel_post", "edited_message", "edited_channel_post"):
            msg = upd.get(key)
            if not msg:
                continue
            chat = msg.get("chat", {})
            cid = chat.get("id")
            if cid is None or cid in seen:
                continue
            seen[cid] = {
                "id": cid,
                "type": chat.get("type"),
                "title": chat.get("title") or chat.get("username") or chat.get("first_name", ""),
            }

    if not seen:
        print("Bot received updates but none from a chat. Send a message in the group.")
        return 0

    print("Found chats:")
    print("-" * 60)
    for c in seen.values():
        print(f"  chat_id = {c['id']:>20}    type = {c['type']:<10}  title = {c['title']}")
    print("-" * 60)
    print("\nPaste the chat_id you want into the relevant TELEGRAM_CHAT_* in .env")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
