# IMPORTS 
import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *

# SET CONSTANTS 
SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_SYMBOL = 'BTCUSD'
TRADE_QUANTITY = 0.05

# Create DS to hold closing data
closes = []
# Create flag for market position 
in_position = False
# Establish connection to API 
client = Client(config.API_KEY, config.API_SECRET, tld='us')

# HELPER FUNCTIONS 
def order(side, quantity, symbol,order_type=ORDER_TYPE_MARKET):
    """Helper function to package crypto order (Buy/Sell) to API"""
    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print(f"an exception occured - {e}")
        return False

    return True

def on_open(ws):
    """Helper function to communicate websocket successfully connected"""
    print('opened connection')

def on_close(ws):
    """Helper function to communicate websocket successfully disconnected"""
    print('closed connection')

def on_message(ws, message):
    """Helper function to parse, collect, and analyze price data"""
    # Get global context of closes, in_position
    global closes, in_position
    
    # Load message from JSON and print 
    print('received message')
    json_message = json.loads(message)
    pprint.pprint(json_message)
    
    # Get price candlestick
    candle = json_message['k']
    # Check for candlestick close
    is_candle_closed = candle['x']
    close = candle['c']

    # Collect close price data 
    if is_candle_closed:
        print(f"candle closed at {close}")
        closes.append(float(close))
        print("closes")
        print(closes)
        # Check if we have enough data to do analysis 
        if len(closes) > RSI_PERIOD:
            # Convert to numpy array and find RSI value using ta-lib 
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            print("all rsis calculated so far")
            print(rsi)
            last_rsi = rsi[-1]
            print(f"the current rsi is {last_rsi}")
            # Check for Overbought status
            if last_rsi > RSI_OVERBOUGHT:
                # If in_position and Overbought, sell and set in_position to False
                if in_position:
                    print("Overbought! Sell! Sell! Sell!")
                    # put binance sell logic here
                    order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = False
                else:
                    print("It is overbought, but we don't own any. Nothing to do.")
            # Check for Oversold status 
            if last_rsi < RSI_OVERSOLD:
                if in_position:
                    print("It is oversold, but you already own it, nothing to do.")
                else:
                    print("Oversold! Buy! Buy! Buy!")
                    # Oversold and not in_position, Buy, and set in_position to True 
                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = True

# Launch websocket with helper function bindings  
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
