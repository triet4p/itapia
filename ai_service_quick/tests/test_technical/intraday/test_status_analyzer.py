import pandas as pd
from app.technical.analysis_engine.intraday.status_analyzer import IntradayStatusAnalyzer

def test_status_analyzer(sample_intraday_data_for_analysis):
    analyzer = IntradayStatusAnalyzer(sample_intraday_data_for_analysis)
    report = analyzer.analyze_current_status()

    assert "price_vs_vwap" in report
    assert "price_vs_open" in report
    assert "rsi_status" in report
    assert "evidence" in report

    # Giá cuối cùng là 156.0, VWAP cuối là 155.2 -> Above
    assert report["price_vs_vwap"] == "Above"
    # Giá mở cửa là 150.0 -> Positive
    assert report["price_vs_open"] == "Positive"
    # RSI là 80 -> Overbought
    assert report["rsi_status"] == "Overbought"
    
    assert report["evidence"]["current_price"] == 156.0