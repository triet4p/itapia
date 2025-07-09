from app.technical.analysis_engine.intraday import IntradayAnalysisEngine

def test_intraday_engine_integration(sample_intraday_data_for_analysis):
    """
    Test tích hợp, kiểm tra xem Facade có điều phối đúng và tạo báo cáo cuối cùng không.
    """
    engine = IntradayAnalysisEngine(sample_intraday_data_for_analysis)
    report = engine.get_analysis_report()
    
    # 1. Kiểm tra cấu trúc cấp cao nhất
    assert "current_status" in report
    assert "key_levels" in report
    assert "momentum" in report
    
    # 2. Kiểm tra một vài giá trị từ các module con để đảm bảo chúng được gọi
    # Từ StatusAnalyzer
    assert report["current_status"]["rsi_status"] == "Overbought"
    # Từ LevelIdentifier
    assert report["key_levels"]["opening_price"] == 150.0
    # Từ MomentumAnalyzer
    assert report["momentum"]["macd_crossover"] == "Bullish"

    print("\n--- Intraday Integration Test Report ---")
    import json
    print(json.dumps(report, indent=2))