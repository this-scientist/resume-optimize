from app.services.crawl_pacing import CrawlPacingParams, gap_seconds_before_next_fetch


def test_gap_zero_chars_uses_min():
    g = gap_seconds_before_next_fetch(
        0,
        CrawlPacingParams(jitter_ratio=0, min_delay_sec=2.0, max_delay_sec=100.0),
    )
    assert g == 2.0


def test_gap_matches_half_reading_time_no_jitter():
    # 800 字 @ 400 字/分钟 => 2 分钟读完 => 间隔 60 秒
    g = gap_seconds_before_next_fetch(
        800,
        CrawlPacingParams(
            chars_per_minute=400.0,
            min_delay_sec=1.0,
            max_delay_sec=500.0,
            jitter_ratio=0.0,
        ),
    )
    assert abs(g - 60.0) < 0.01


def test_gap_respects_max_cap():
    g = gap_seconds_before_next_fetch(
        1_000_000,
        CrawlPacingParams(
            chars_per_minute=400.0,
            min_delay_sec=2.0,
            max_delay_sec=90.0,
            jitter_ratio=0.0,
        ),
    )
    assert g == 90.0
