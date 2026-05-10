#!/usr/bin/env python3
"""Smoke-test Twitter / X credentials from .env.

1. App-only TWITTER_BEARER_TOKEN (optional): lookup @X.
2. OAuth 2.0 user TWITTER_OAUTH2_ACCESS_TOKEN: get_me + optional --tweet (preferred).
3. OAuth 1.0a: consumer + access token + secret: get_me + optional --tweet.

Usage:
    python scripts/twitter_smoke_test.py
    python scripts/twitter_smoke_test.py --tweet
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env", override=True)


def _oauth1_values() -> tuple[str, str, str, str]:
    ck = os.environ.get("consumer_key", os.environ.get("TWITTER_API_KEY", "")).strip()
    cs = os.environ.get("consumer_secret", os.environ.get("TWITTER_API_SECRET", "")).strip()
    at = os.environ.get("access_token", os.environ.get("TWITTER_ACCESS_TOKEN", "")).strip()
    ats = os.environ.get("access_token_secret", os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")).strip()
    return ck, cs, at, ats


def main() -> int:
    import tweepy

    _load_env()
    parser = argparse.ArgumentParser(description="Twitter API smoke test")
    parser.add_argument(
        "--tweet",
        action="store_true",
        help="Post one test tweet (OAuth2 user or OAuth 1.0a)",
    )
    args = parser.parse_args()

    bearer = os.environ.get("TWITTER_BEARER_TOKEN", "").strip()
    if bearer:
        try:
            client = tweepy.Client(bearer_token=bearer)
            r = client.get_user(username="X")
            if r.data:
                print(f"[OK] App Bearer: GET /2/users/by/username/X -> id={r.data.id}")
            else:
                print("[?] App Bearer: empty data", getattr(r, "errors", None))
        except tweepy.TweepyException as e:
            print(f"[WARN] App Bearer check failed (optional): {e}")
    else:
        print("[SKIP] TWITTER_BEARER_TOKEN not set")

    oauth2 = os.environ.get("TWITTER_OAUTH2_ACCESS_TOKEN", "").strip()
    if oauth2:
        try:
            o2_client = tweepy.Client(bearer_token=oauth2)
            me = o2_client.get_me(user_auth=False)
            if me.data:
                print(f"[OK] OAuth2 user: @{me.data.username} (id={me.data.id})")
            else:
                print("[?] OAuth2 get_me: no data", getattr(me, "errors", None))
                return 1
            if args.tweet:
                text = "Consoles India notifier - API post test. (Safe to delete.)"
                resp = o2_client.create_tweet(text=text, user_auth=False)
                tid = resp.data["id"] if resp.data else None
                print(f"[OK] Posted tweet id={tid}")
        except tweepy.TweepyException as e:
            print(f"[FAIL] OAuth2 user: {e}")
            return 1
        return 0

    ck, cs, at, ats = _oauth1_values()
    if not all((ck, cs, at, ats)):
        print(
            "[SKIP] OAuth 1.0a incomplete - set access_token and access_token_secret "
            "(or use TWITTER_OAUTH2_ACCESS_TOKEN)."
        )
        if args.tweet:
            print("[FAIL] --tweet needs OAuth2 user token or full OAuth 1.0a quadruple")
            return 1
        return exit_code

    try:
        user_client = tweepy.Client(
            consumer_key=ck,
            consumer_secret=cs,
            access_token=at,
            access_token_secret=ats,
        )
        me = user_client.get_me()
        if me.data:
            print(f"[OK] OAuth 1.0a user: @{me.data.username} (id={me.data.id})")
        else:
            print("[?] get_me: no data", getattr(me, "errors", None))
    except tweepy.TweepyException as e:
        print(f"[FAIL] OAuth 1.0a (get_me): {e}")
        return 1

    if args.tweet:
        try:
            text = "Consoles India notifier - API post test. (Safe to delete.)"
            resp = user_client.create_tweet(text=text)
            tid = resp.data["id"] if resp.data else None
            print(f"[OK] Posted tweet id={tid}")
        except tweepy.TweepyException as e:
            print(f"[FAIL] create_tweet: {e}")
            return 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
