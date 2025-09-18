from app.analysis.technical.analysis_engine.intraday.momentum_analyzer import IntradayMomentumAnalyzer

def test_momentum_analyzer(sample_intraday_data_for_analysis):
    # Tăng volume của cây nến cuối để test Volume Spike
    data = sample_intraday_data_for_analysis.copy()
    data.iloc[-1, data.columns.get_loc('volume')] = 200000

    analyzer = IntradayMomentumAnalyzer(data)
    report = analyzer.analyze_momentum_and_volume()
    
    assert "macd_crossover" in report
    assert "volume_status" in report
    assert "opening_range_status" in report
    assert "evidence" in report

    # MACD line (1.5) > Signal line (1.2) -> Bullish
    assert report["macd_crossover"] == "Bullish"
    # Volume cuối (200000) lớn hơn nhiều so với trung bình (~30000) -> High Volume Spike
    assert report["volume_status"] == "High Volume Spike"
    # Giá cuối (156.0) > OR High (151.5) -> Bullish Breakout
    assert report["opening_range_status"] == "Bullish Breakout"