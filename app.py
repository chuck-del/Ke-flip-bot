import requests, time, threading
from flask import Flask

app = Flask(__name__)
NTFY_TOPIC = "ke-flip-gap-028"

def send_ntfy(msg):
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode('utf-8'), headers={"Title": "GAP FLIP"})
        print(f"Sent ntfy: {msg}", flush=True)
    except Exception as e:
        print(e, flush=True)

def get_binance_price(side):
    try:
        r = requests.post("https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search",
            json={"asset":"USDT","fiat":"KES","tradeType":side,"pageSize":20,"payTypes":["MPESA"]}, timeout=10)
        for ad in r.json()['data']:
            p = float(ad['adv']['price'])
            if p < 128 or p > 132: continue
            if float(ad['advertiser']['monthFinishRate']) < 0.95: continue
            if ad['adv']['minSingleTransAmount'] > 10000: continue
            if ad['adv']['maxSingleTransAmount'] < 10000: continue
            return p
    except: return None
    return None

def get_bybit_price(side):
    try:
        r = requests.post("https://api2.bybit.com/fiat/otc/item/online",
            json={"userId":"","tokenId":"USDT","currencyId":"KES","payment":["14"],"side":str(side),"size":"20","page":"1","amount":"10000"}, timeout=10)
        for item in r.json()['result']['items']:
            p = float(item['price'])
            if p < 128 or p > 132: continue
            if float(item['recentExecuteRate']) < 95: continue
            return p
    except: return None
    return None

def check_loop():
    # send test on start so you know bot is alive
    send_ntfy("Bot started - checking Binance vs Bybit every 20 sec. If gap >0.50 you will get alarm.")
    while True:
        try:
            bin_buy = get_binance_price("BUY")
            bin_sell = get_binance_price("SELL")
            by_buy = get_bybit_price(0)
            by_sell = get_bybit_price(1)
            print(f"Bin Buy {bin_buy} Sell {bin_sell} | Bybit Buy {by_buy} Sell {by_sell}", flush=True)
            if bin_buy and by_sell:
                gap1 = round(by_sell - bin_buy, 2)
                if gap1 >= 0.50:
                    msg = f"GAP {gap1} FLIP NOW Buy Binance {bin_buy} -> Sell Bybit {by_sell} Profit {int(gap1*76)} KES per $100"
                    send_ntfy(msg)
            if by_buy and bin_sell:
                gap2 = round(bin_sell - by_buy, 2)
                if gap2 >= 0.50:
                    msg = f"GAP {gap2} FLIP NOW Buy Bybit {by_buy} -> Sell Binance {bin_sell} Profit {int(gap2*76)} KES per $100"
                    send_ntfy(msg)
        except Exception as e:
            print(e, flush=True)
        time.sleep(20)

threading.Thread(target=check_loop, daemon=True).start()

@app.route("/")
def home():
    return "Bot Running - ke-flip ntfy only"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
