import pandas
import mplfinance as mpf
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

tcs = pandas.read_csv(
    "/home/palash/dev/stock-app/StockAppApi/database/ohlc/day/RELIANCE.csv", index_col=0, parse_dates=True).tail(80)
image_path = "/home/palash/dev/stock-app/StockAppApi/processes/python/testers/test.png"
mpf.plot(tcs.tail(80), style='yahoo', savefig=image_path)

# Open the PNG file
img = Image.open(image_path)
# Create an ImageDraw object
draw = ImageDraw.Draw(img)

# Define the font and size
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)

# Define the text and position
text = "Text to add"
position = (10, 10)

# Draw the text on the image
draw.text(position, text, font=font, fill='black')

# Save the modified image
img.save("modified_image.png")


'''
divergence_query = f"macdhistdivergencescan --ticker RELIANCE --interval day --do get --window 20 --n 80 --plot 1 --save_plot /home/palash/dev/stock-app/StockAppApi/database/plot/day"

configFolder = "StockAppApi/configuration/"
config = read_config(configFolder + "config.yaml")

# Initialize the logger from news server
selected_stocks_yaml = configFolder + "selected_stocks.yaml"
indicator_config_yaml = configFolder + "indicator.yaml"
commandHandler = CommandHandler(
    selected_stocks_yaml=selected_stocks_yaml, indicator_config_yaml=indicator_config_yaml)

macd_ret = commandHandler.execute(message=divergence_query, is_rest=False).obj['RELIANCE']
# bulls = macd_ret.where(macd_ret['macdhist'] > 0, 0)
bulls = [np.nan for _ in range(80)]
bears = [np.nan for _ in range(80)]
for i in range(tcs.shape[0]):
    if macd_ret.iloc[i]['macdhist_divergence'] > 0:
        bulls[i] = tcs.iloc[i]['Close']*0.99
    elif macd_ret.iloc[i]['macdhist_divergence'] < 0:
        bears[i] = tcs.iloc[i]['Close']*1.05


apd_bull = mpf.make_addplot(bulls, type='scatter', markersize=200, marker='^')
apd_bear = mpf.make_addplot(bears, type='scatter', markersize=200, marker='v')

mpf.plot(tcs.tail(80), addplot=[apd_bull, apd_bear], style='yahoo', savefig="/home/palash/dev/stock-app/StockAppApi/database/plot/day/RELIANCE.png")
'''