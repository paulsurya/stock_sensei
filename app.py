import streamlit as st
import dataCollecter as dc

st.title("welcome to stock sensei")
ticker = st.text_input("Enter a stock ticker",value='AAPL')

AlClient = dc.AlphaData()

st.write(AlClient.getDaily(ticker=ticker))