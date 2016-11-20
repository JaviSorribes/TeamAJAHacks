from flask import Flask, request, render_template
from random import choice
import os
import urllib.request, urllib.parse, urllib.error, json
import datetime
import pandas_datareader.data as pdr

app = Flask(__name__)

#Main Stocks library
stocks = []
watchlist = []
stock_set = {}

###DEFAULTS:
date = datetime.date(2000, 1, 3)
end = datetime.date(2016, 11, 11)
money = 100000

class Stock:
    def __init__(self, symbol, quantity, purch_date, init_price):
        self.symbol = symbol
        self.quantity = quantity
        self.purch_date = purch_date
        self.init_price = init_price
        self.earnings = 0
        self.last_price = init_price
        self.last_earning = 0
        self.change = 0


class Stock_base:
    def __init__(self, symbol, quantity, price):
        self.symbol = symbol
        self.quantity = quantity
        self.last_price = price
        self.earnings = 0

    def __eq__(self, other):
        if self.symbol == other.symbol:
            return True

    def __hash__(self):
        return self.symbol.__hash__()

@app.route("/") #asking the user for dates
def index():
    yesterday = (datetime.date.today() - datetime.timedelta(days=1))
    return render_template('index.html', yesterday=yesterday.isoformat()) #needs the day before today


@app.route("/start")
def start():
    global date, end
    s_date = request.args['start_date'].split("-")
    e_date = request.args['end_date'].split("-")
    date = datetime.date(int(s_date[0]),int(s_date[1]),int(s_date[2]))
    end = datetime.date(int(e_date[0]),int(e_date[1]),int(e_date[2]))
    money = int(request.args['money'])
    return render_template('page.html', date = date, stock = stocks, watchlist= watchlist, stock_set=stock_set.values(), money=money)


@app.route('/stocks')
def trade():
    global money
    symbol = request.args['symbol']
    quant = request.args['quantity']
    quantity = int(quant) if quant else 0
    q = get_quotes(symbol, date, end)
    if is_symbol(symbol):
        s = Stock(symbol, quantity, date, float(q['Open']))
        sb = Stock_base(symbol, quantity, float(q['Open']))
        if request.args['action'] == 'watchlist':
            watchlist.append(s)
        elif request.args['action'] == 'buy':
            money -= quantity*s.init_price
            if stock_set.get(symbol):
                stock_set[symbol].quantity += quantity
            else:
                stock_set[symbol] = sb

            for i in range(len(stocks)):
                if stocks[i].symbol==s.symbol and stocks[i].purch_date==s.purch_date: #already there for that date
                    stocks[i].quantity += s.quantity
                    break
            else:
                stocks.append(s)
        elif request.args['action'] == 'sell':
            money += quantity * s.init_price
            sb = Stock_base(symbol, 0-quantity, float(q['Open']))
            if stock_set.get(symbol):
                stock_set[symbol].quantity -= quantity
            else:
                stock_set[symbol] = sb

            for i in range(len(stocks)):
                if stocks[i].symbol==s.symbol and stocks[i].purch_date==s.purch_date: #already there for that date
                    stocks[i].quantity -= s.quantity
                    break
            else:
                stocks.append(s)

    else: #not a valid symbol (or maybe not a valid date for that symbol)
        pass #print out some error

    return render_template('page.html', date=date, stocks=stocks, watchlist= watchlist, stock_set=stock_set.values(), money=money)


def is_trading_day(date):
    if len(get_quotes('YHOO', date, end)) != 0:
        return True
    else:
        return False


def earning():
    global money
    for s,y in stock_set.items():
        if is_symbol(s):
            q = get_quotes(y.symbol, date, end)
            diff = q['Open'] - y.last_price
            y.last_price = q['Open']
            y.earnings += diff*y.quantity
            money += diff*y.quantity

def get_quotes(symbol, start_date, end_date):
    try:
        pdr.DataReader(symbol, 'yahoo', start_date, end_date)
        stock = pdr.DataReader(symbol, 'yahoo', start_date, end_date)
        return stock.ix[start_date.isoformat()]
    except:
        return []

def is_symbol(symbol):
    return len(get_quotes(symbol,date,end)) != 0

@app.route('/advance')
def advance():
    global  date

    time_amount = request.args['advance']
    if time_amount == 'Day':
        date += datetime.timedelta(days= 1)
    elif time_amount == 'Week':
        date += datetime.timedelta(weeks= 1)
    elif time_amount == 'Month':
        if date.month<12:
            date = date.replace(month=date.month+1)
        else:
            date = date.replace(year=date.year+1, month=1)
    elif time_amount == 'Year':
        date = date.replace(year=date.year + 1)
    elif time_amount == 'Decade':
        date = date.replace(year=date.year + 10)

    if date > end:
        earning()
        return render_template('page.html', date=date, stocks=stocks, watchlist=watchlist, stock_set=stock_set.values())

    while not is_trading_day(date):
        date += datetime.timedelta(days=1)
    earning()
    return render_template('page.html', date=date, stocks=stocks, watchlist=watchlist, stock_set=stock_set.values(), money = money)

def earnings(stock):
    q = get_quotes(stock.symbol, date, end)
    open_price = q['Open']
    
if __name__ == '__main__':
    app.run()
