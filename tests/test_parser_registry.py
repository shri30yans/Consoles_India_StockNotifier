from commerce_platform.stock.parsers.registry import get_parser_for_source


def test_registry_handles_playwright_suffix() -> None:
    assert get_parser_for_source("amazon") is not None
    assert get_parser_for_source("ajio_playwright") is not None


def test_registry_raises_for_unknown_source() -> None:
    try:
        get_parser_for_source("unknown_source")
        assert False, "expected ValueError for unknown parser source"
    except ValueError:
        pass

