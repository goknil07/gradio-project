import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import gradio as gr
from datetime import datetime, timedelta

# Tarihleri otomatik hesaplayan fonksiyon
def calculate_dates(time_range):
    today = datetime.today()
    if time_range == "Son 6 Ay":
        start_date = (today - timedelta(days=182)).strftime("%Y-%m-%d")
    elif time_range == "Son 1 Yıl":
        start_date = (today - timedelta(days=365)).strftime("%Y-%m-%d")
    elif time_range == "Son 2 Yıl":
        start_date = (today - timedelta(days=730)).strftime("%Y-%m-%d")
    else:
        start_date = ""
    end_date = today.strftime("%Y-%m-%d")
    return start_date, end_date

# Buy/Sell noktalarını belirleyen fonksiyon
def identify_signals(closing_prices, short_term_ma, long_term_ma):
    signals = pd.DataFrame(index=closing_prices.index)
    signals['Buy'] = (short_term_ma > long_term_ma) & (short_term_ma.shift(1) <= long_term_ma.shift(1))
    signals['Sell'] = (short_term_ma < long_term_ma) & (short_term_ma.shift(1) >= long_term_ma.shift(1))
    return signals

# Fonksiyon: Kullanıcı girişlerine göre verileri işler ve grafik oluşturur
def handle_inputs(time_range, start_date, end_date, stock_symbol):
    if time_range != "Manuel":
        start_date, end_date = calculate_dates(time_range)

    try:
        t1 = datetime.strptime(start_date, "%Y-%m-%d")
        t2 = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return "Lütfen tarih formatını (YYYY-MM-DD) doğru girin.", None

    if t1 > t2:
        return "Başlangıç tarihi bitiş tarihinden büyük olamaz.", None

    if stock_symbol.strip():
        try:
            stock = yf.Ticker(stock_symbol)
            hist = stock.history(start=start_date, end=end_date)
            closing_prices = hist['Close']
        except Exception as e:
            return f"Veri çekilirken hata oluştu: {str(e)}", None
    else:
        return "Lütfen geçerli bir hisse senedi sembolü girin.", None

    if closing_prices.empty:
        return "Belirtilen tarih aralığında veri bulunamadı.", None

    # Hareketli ortalamaları hesapla
    short_term_ma = closing_prices.rolling(window=20).mean()
    long_term_ma = closing_prices.rolling(window=50).mean()

    # Buy/Sell sinyalleri belirle
    signals = identify_signals(closing_prices, short_term_ma, long_term_ma)

    # Grafik oluşturma
    plt.figure(figsize=(14, 8))
    plt.plot(closing_prices, label=f'{stock_symbol} Closing Prices', color='blue')
    plt.plot(short_term_ma, label='20-Day Moving Average', color='orange')
    plt.plot(long_term_ma, label='50-Day Moving Average', color='green')

    # Buy/Sell noktalarını işaretle
    buy_signals = closing_prices[signals['Buy']]
    sell_signals = closing_prices[signals['Sell']]
    plt.scatter(buy_signals.index, buy_signals, label='Buy Signal', marker='^', color='green', s=100)
    plt.scatter(sell_signals.index, sell_signals, label='Sell Signal', marker='v', color='red', s=100)

    plt.title(f'{stock_symbol} Closing Prices with Buy/Sell Signals')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.legend()
    plt.grid()

    # Grafiği kaydet
    grafik_dosyasi = "grafik.png"
    plt.savefig(grafik_dosyasi)
    plt.close()

    return f"Başlangıç Tarihi: {start_date}\nBitiş Tarihi: {end_date}", grafik_dosyasi

# Gradio arayüzü
with gr.Blocks() as demo:
    gr.Markdown("## Hisse Senedi Verileri: Kapanış Fiyatları, Hareketli Ortalamalar ve Buy/Sell Sinyalleri")

    with gr.Row():
        time_range = gr.Radio(["Son 6 Ay", "Son 1 Yıl", "Son 2 Yıl", "Manuel"], label="Zaman Aralığını Seçin")
    
    with gr.Row():
        start_date = gr.Textbox(label="Başlangıç Tarihi (YYYY-MM-DD)", placeholder="Örn: 2024-01-01")
        end_date = gr.Textbox(label="Bitiş Tarihi (YYYY-MM-DD)", placeholder="Örn: 2024-06-01")

    stock_symbol = gr.Textbox(
        label="Hisse Senedi Sembolü (Örn: MSFT, AAPL)", 
        placeholder="Hisse senedi sembolünü girin",
        lines=1
    )

    run_button = gr.Button("Çalıştır")
    result_text = gr.Textbox(label="Sonuç")
    grafik_output = gr.Image(label="Grafik Çıktısı")

    run_button.click(
        handle_inputs, 
        inputs=[time_range, start_date, end_date, stock_symbol], 
        outputs=[result_text, grafik_output]
    )

# Uygulamayı başlat
demo.launch()