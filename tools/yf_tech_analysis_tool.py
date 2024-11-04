import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from crewai_tools import tool

@tool
def yf_tech_analysis(stock_symbol: str, period: str = "1y"):
    """
    Perform a comprehensive technical analysis on the given stock symbol.
    
    Args:
        stock_symbol (str): The stock symbol to analyze.
        period (str): The time period for analysis. Default is "1y" (1 year).
    
    Returns:
        dict: A dictionary with the detailed technical analysis results.
    """
    try:
        # Download data
        stock = yf.Ticker(stock_symbol)
        hist = stock.history(period=period)
        
        if hist.empty:
            return {"error": "No data available for the specified stock symbol"}
        
        # Get the most recent data point
        latest_close = float(hist['Close'].iloc[-1])
        latest_volume = float(hist['Volume'].iloc[-1])
        
        # Calculate basic statistics
        high_52week = float(hist['High'].max())
        low_52week = float(hist['Low'].min())
        avg_volume = float(hist['Volume'].mean())
        
        # Calculate 50-day and 200-day moving averages
        ma_50 = float(hist['Close'].rolling(window=50).mean().iloc[-1])
        ma_200 = float(hist['Close'].rolling(window=200).mean().iloc[-1])
        
        # Calculate RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = float(100 - (100 / (1 + rs)).iloc[-1])
        
        # Calculate MACD
        exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd = float(exp1.iloc[-1] - exp2.iloc[-1])
        signal = float(hist['Close'].ewm(span=9, adjust=False).mean().iloc[-1])
        
        # Calculate Bollinger Bands
        ma_20 = hist['Close'].rolling(window=20).mean()
        std_20 = hist['Close'].rolling(window=20).std()
        upper_band = float(ma_20.iloc[-1] + (std_20.iloc[-1] * 2))
        lower_band = float(ma_20.iloc[-1] - (std_20.iloc[-1] * 2))
        
        # Prepare analysis results
        analysis = {
            "price_data": {
                "current_price": latest_close,
                "52_week_high": high_52week,
                "52_week_low": low_52week,
                "volume": latest_volume,
                "average_volume": avg_volume
            },
            "technical_indicators": {
                "moving_averages": {
                    "MA_50": ma_50,
                    "MA_200": ma_200
                },
                "rsi": rsi,
                "macd": {
                    "macd_line": macd,
                    "signal_line": signal
                },
                "bollinger_bands": {
                    "upper": upper_band,
                    "lower": lower_band
                }
            },
            "analysis": {
                "trend": "Bullish" if latest_close > ma_200 else "Bearish",
                "rsi_signal": "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral",
                "macd_signal": "Bullish" if macd > signal else "Bearish",
                "volume_analysis": "Above Average" if latest_volume > avg_volume else "Below Average"
            }
        }
        
        return analysis
        
    except Exception as e:
        return {"error": f"An error occurred during analysis: {str(e)}"}