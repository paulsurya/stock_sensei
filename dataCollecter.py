from datetime import date,timedelta
from alpha_vantage.timeseries import *
import os

class FinnhubData():
    def __init__(self):
        import finnhub as fb
        self.client = fb.Client(api_key=os.getenv('finnhubKey'))
    
    def getProfile(self,ticker):
        data = self.client.company_profile2(symbol = ticker)
        return {
            'name':data['name'],
            'country':data['country'],
            'sector':data['finnhubIndustry'],
            'logo':data['logo'],
            'website':data['weburl']
        }
    
    def getSentiment(self,ticker:str):
        startData = date.today() - timedelta(days=3)
        endData = date.today()
        data = self.client.stock_insider_sentiment(ticker,startData,endData)

        return data['data'][:int(len(data['data'])/2)]
    
class AlphaData():
    def __init__(self):
        self.apiKey = os.getenv('alphaKey')
    
    def getDaily(self,ticker):
        ts = TimeSeries(key=self.apiKey,output_format='pandas') # type: ignore
        data,mean = ts.get_daily(symbol=ticker,outputsize='compact')
        return data
