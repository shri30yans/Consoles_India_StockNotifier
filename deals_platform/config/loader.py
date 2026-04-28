"""Platform YAML loader.

Three files under config/platform/:
  - channels.yaml   : logical channels (tech/gaming/...) + notifier bindings
  - sources.yaml    : enabled retailer watches + aggregator sources
  - scoring.yaml    : threshold + signal weights
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from deals_platform.notify.router import ChannelBinding


class BindingYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notifier: Literal["telegram", "whatsapp", "discord", "twitter", "email"]
    target: str  # env var name (preferred) or literal value


class ChannelYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str
    name: str
    bindings: list[BindingYaml] = Field(default_factory=list)


class ChannelsYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channels: list[ChannelYaml]


class WatchYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")
    retailer: str
    url: str
    poll_seconds: int = Field(default=600, ge=30, le=86400)
    title_hint: str | None = None


class AggregatorYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["desidime", "reddit"]
    enabled: bool = False
    poll_seconds: int = Field(default=900, ge=60, le=86400)
    subreddits: list[str] = Field(default_factory=list)


class SourcesYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")
    watches: list[WatchYaml] = Field(default_factory=list)
    aggregators: list[AggregatorYaml] = Field(default_factory=list)
    amazon_signals: "AmazonSignalsYaml" = Field(default_factory=lambda: AmazonSignalsYaml())


class AmazonSignalsYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    poll_seconds: int = Field(default=900, ge=60, le=86400)
    max_links_per_seed: int = Field(default=20, ge=1, le=200)
    seed_urls: list[str] = Field(default_factory=list)


class ScoringYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")
    threshold: float = Field(default=0.55, ge=0.0, le=1.0)
    repost_cooldown_hours: int = Field(default=24, ge=1, le=720)
    weights: dict[str, float] = Field(default_factory=dict)


class PlatformConfig:
    def __init__(
        self,
        channels: ChannelsYaml,
        sources: SourcesYaml,
        scoring: ScoringYaml,
    ) -> None:
        self.channels = channels
        self.sources = sources
        self.scoring = scoring

    def channel_to_channel_keys(self) -> dict[str, tuple[str, ...]]:
        """For curator: category/value -> tuple of channel keys to target."""
        # v1: 1:1 mapping by key (category 'tech' routes to channel 'tech').
        return {c.key: (c.key,) for c in self.channels.channels}

    def channel_bindings(self) -> list[ChannelBinding]:
        out: list[ChannelBinding] = []
        for ch in self.channels.channels:
            for b in ch.bindings:
                out.append(
                    ChannelBinding(channel_key=ch.key, notifier_name=b.notifier, target=b.target)
                )
        return out


def _load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _platform_dir() -> Path:
    override = os.environ.get("DEALS_PLATFORM_CONFIG_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "config" / "platform"


def load_platform_config() -> PlatformConfig:
    base = _platform_dir()
    channels = ChannelsYaml.model_validate(_load_yaml(base / "channels.yaml"))
    sources = SourcesYaml.model_validate(_load_yaml(base / "sources.yaml"))
    scoring = ScoringYaml.model_validate(_load_yaml(base / "scoring.yaml"))
    return PlatformConfig(channels=channels, sources=sources, scoring=scoring)
