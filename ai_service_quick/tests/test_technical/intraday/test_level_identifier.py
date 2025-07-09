from app.technical.analysis_engine.intraday.level_identifier import IntradayLevelIdentifier

def test_level_identifier(sample_intraday_data_for_analysis):
    analyzer = IntradayLevelIdentifier(sample_intraday_data_for_analysis)
    report = analyzer.identify_key_levels()
    
    expected_keys = ['day_high', 'day_low', 'opening_price', 'vwap', 'or_30m_high', 'or_30m_low']
    for key in expected_keys:
        assert key in report

    # Kiểm tra các giá trị
    assert report['opening_price'] == 150.0
    # Giá high cuối cùng là 156.0 + random, nhưng close cuối là 156, nên day_high ít nhất là 156
    assert report['day_high'] >= 156.0
    assert report['or_30m_high'] == 151.50