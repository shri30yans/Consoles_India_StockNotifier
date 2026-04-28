from deals_platform.sources.aggregators.desidime import DesiDimeSource
from deals_platform.sources.aggregators.reddit_source import RedditSource
from deals_platform.sources.retailers.amazon_signals import AmazonSignalsSource
from deals_platform.sources.retailers.retailer_source import RetailerWatchSource
from deals_platform.sources.spec import WatchSpec

__all__ = [
    "AmazonSignalsSource",
    "DesiDimeSource",
    "RedditSource",
    "RetailerWatchSource",
    "WatchSpec",
]
