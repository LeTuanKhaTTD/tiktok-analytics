"""Modules package with lazy exports to avoid eager heavy imports at startup."""

from importlib import import_module

__all__ = [
    "YouTubeScraper",
    "TikTokScraper",
    "SentimentAnalyzer",
    "MetricsAnalyzer",
    "TikTokAPICollector",
    "GeminiSentimentAnalyzer",
    "get_gemini_analyzer",
]

_SYMBOL_MAP = {
    "YouTubeScraper": ("youtube_scraper", "YouTubeScraper"),
    "TikTokScraper": ("tiktok_scraper", "TikTokScraper"),
    "SentimentAnalyzer": ("sentiment_analyzer", "SentimentAnalyzer"),
    "MetricsAnalyzer": ("metrics_analyzer", "MetricsAnalyzer"),
    "TikTokAPICollector": ("tiktok_api_scraper", "TikTokAPICollector"),
    "GeminiSentimentAnalyzer": ("gemini_sentiment", "GeminiSentimentAnalyzer"),
    "get_gemini_analyzer": ("gemini_sentiment", "get_gemini_analyzer"),
}


def __getattr__(name):
    """Load module members on demand instead of importing everything eagerly."""
    if name not in _SYMBOL_MAP:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, symbol_name = _SYMBOL_MAP[name]
    module = import_module(f".{module_name}", __name__)
    value = getattr(module, symbol_name)
    globals()[name] = value
    return value
