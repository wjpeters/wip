from app.research import parse_feed, cluster_news


def test_changed_snippet_same_headline_is_new_revision_not_duplicate():
    a = "<rss><channel><item><title>Example</title><link>https://example.invalid/article</link><pubDate>Thu, 24 Sep 2026 12:00:00 GMT</pubDate><description>First report</description></item></channel></rss>"
    b = a.replace("First report", "Corrected report")
    kwargs = dict(
        publisher="SYNTHETIC", family="fixture", region="EU", license_display=True
    )
    first = parse_feed(a, **kwargs)[0]
    second = parse_feed(b, **kwargs)[0]
    second["revision"] = 2
    assert first["fingerprint"] != second["fingerprint"]
    assert len(cluster_news([first, second])) == 1


def test_news_api_contract_preserves_source_rights_and_revisions():
    import json
    import pytest
    from app.research import parse_news_api

    raw = json.dumps(
        {
            "articles": [
                {
                    "title": "SYNTHETIC NEWS",
                    "url": "https://example.invalid/news",
                    "published_at": "2026-09-24T12:00:00Z",
                    "snippet": "fixture",
                    "language": "nl",
                    "instruments": ["BTC"],
                }
            ]
        }
    )
    params = dict(publisher="Fixture", family="fixture", region="EU")
    with pytest.raises(PermissionError):
        parse_news_api(raw, **params)
    item = parse_news_api(raw, license_display=True, **params)[0]
    assert item["quality"] == "UNVERIFIED_SOURCE" and item["instruments"] == ["BTC"]
