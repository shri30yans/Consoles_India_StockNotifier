"""Channel-agnostic post rendering helpers."""

from __future__ import annotations

from deals_platform.domain.events import PublishablePost


def render_plain(post: PublishablePost) -> str:
    lines = [post.title, "", post.body_markdown, "", post.affiliate_url]
    return "\n".join(lines)


def render_telegram_markdown(post: PublishablePost) -> str:
    title = _md_escape(post.title)
    return f"*{title}*\n\n{post.body_markdown}\n\n{post.affiliate_url}"


def render_tweet(post: PublishablePost, max_chars: int = 270) -> str:
    body = f"{post.title}\n{_strip_md(post.body_markdown)}\n{post.affiliate_url}"
    if len(body) <= max_chars:
        return body
    keep = max_chars - len(post.affiliate_url) - 4
    return f"{post.title[:keep]}…\n{post.affiliate_url}"


def _md_escape(text: str) -> str:
    return text.replace("_", r"\_").replace("*", r"\*").replace("[", r"\[").replace("`", r"\`")


def _strip_md(text: str) -> str:
    return text.replace("**", "").replace("*", "").replace("`", "")
