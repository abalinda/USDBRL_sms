import requests
import os
from twilio.rest import Client
from datetime import datetime, timedelta

STOCK = "USDBRL"

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
news_url = "https://newsapi.org/v2/everything"

alphavantage_api_key = os.environ.get("alphavantage_api_key")
news_api_key = os.environ.get("news_api_key")
stock_params_fx_rate = {
    "function": "CURRENCY_EXCHANGE_RATE",
    "from_currency": "BRL",
    "to_currency": "USD",
    "apikey": alphavantage_api_key,
}

stock_params_fx_daily = {
    "function": "FX_DAILY",
    "from_symbol": "USD",
    "to_symbol": "BRL",
    "apikey": alphavantage_api_key,
    "outputsize": "compact",
}

news_parameters = {
    "q": "USD-BRL OR BRL-USD OR USDBRL OR BRLUSD OR BRL OR DXY",
    "searchIn": "title,description",
    "apiKey": news_api_key,
    "domains": "barchart.com,financialjuice.com,globo.com,forex.com,biztoc.com,www.tradingview.com,finance.yahoo.com/currencies,fxtimes.com,forexcrunch.com,ft.com,bloomberg.com,dailyfx.com,forexlive.com,marketpulse,investing.com,xpinvestimentos.com,financemagnates.com,dailyforex.com,cnbc.com,myfxbook.com",
    "sortBy": "relevancy",
}

twilio_SID = os.environ.get("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.environ.get("TWILIO_AUT_TOKEN")
client = Client(twilio_SID, twilio_auth_token)
my_twilio_number = os.environ.get("my_twilio_number")
my_br_number = os.environ.get("my_br_number")

# GET TODAY DATE
today_date = datetime.today()
# GET YESTERDAY DATE
yesterday_date = today_date - timedelta(days=1)
# GET ZAVCHERA
zavchera_date = today_date - timedelta(days=2)

# list of weekend days (sat,sun)
weekend_days = [5, 6]


# find last working day if any of the dates are weekend days
def get_closest_working_day(date):
    while date.weekday() in weekend_days:
        date -= timedelta(days=1)
    return date


# getting most recent workday
closest_working_day_today = get_closest_working_day(today_date)
# format it to YYYY-MM-DD
closest_working_day_today_formatted = closest_working_day_today.strftime("%Y-%m-%d")
# last workday before most recent one
closest_working_day_yesterday = get_closest_working_day(yesterday_date)
# formatted
closest_working_day_yesterday_formatted = closest_working_day_yesterday.strftime(
    "%Y-%m-%d"
)
# idem...
closest_working_day_zavchera = get_closest_working_day(zavchera_date)
closest_working_day_zavchera_formatted = closest_working_day_zavchera.strftime(
    "%Y-%m-%d"
)

# final mutable list of the last three working days (including today if work day)
days = [
    closest_working_day_today_formatted,
    closest_working_day_yesterday_formatted,
    closest_working_day_zavchera_formatted,
]


# getting raw data for USDBRL
r2 = requests.get(STOCK_ENDPOINT, params=stock_params_fx_daily)
r2 = requests.get(STOCK_ENDPOINT, params=stock_params_fx_daily)
r2.raise_for_status()
raw_data2 = r2.json()

# isolating the closing price of USDBRL for the last three working days
rates = []
for day in days:
    day_rate = float(raw_data2["Time Series FX (Daily)"][day]["4. close"])
    rates.append(day_rate)

print(rates)

# get differnece between the price yesterday and the day before yesterday in %
tdy_price = rates[0]
yst_price = rates[1]
percentage_differnece = ((tdy_price - yst_price) / yst_price) * 100


# function to get news regarding USDBRL (not very good, need to find an alternative source)
def get_news():
    news_r = requests.get(news_url, news_parameters)
    news_r.raise_for_status()
    raw_news = news_r.json()
    return raw_news


# send SMS function showing the % difference in USDBRL and a headline
def send_sms(percent_diff, to_number):
    # vesgigial residue, if needed more than 1 SMS we can edit the range
    for n in range(0, 1):
        if percent_diff > 0:
            message = client.messages.create(
                body=f"🤩USDBRL: 🔺{format(percent_diff, '.3f')}% \nHeadline: {get_news()['articles'][n]['title']}",
                from_=my_twilio_number,
                to=to_number,
            )
            print(message.sid)
        else:
            message = client.messages.create(
                body=f"😕USDBRL: 🔻{format(percent_diff, '.3f')}% \nHeadline: {get_news()['articles'][n]['title']}",
                from_=my_twilio_number,
                to=to_number,
            )
            print(message.sid)


def main():
    if abs(percentage_differnece) > 0.3:
        send_sms(percentage_differnece, my_br_number)
    else:
        print("Too small of a difference in USDBRL price")


main()
