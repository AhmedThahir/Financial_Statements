from common import *
common_styles()
sidebar()
import os
import streamlit as st
import datetime
import pandas as pd
from yahooquery import Ticker
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List

@st.cache_data(ttl=60*60)
def get_stock_data(history_args, symbol, online: str):
	
	args_list = [arg for arg in history_args.values() if arg is not None]

	file = f"./data/{symbol}_{'_'.join(args_list)}.csv"

	index_col = "date"
	if online:
		df = st.session_state["tickers"].history(**history_args)

		if index_col in df.index.names:
			df = df.reset_index()
			df[index_col] = pd.to_datetime(df[index_col], format='%Y-%m-%d %H:%M:%S', utc=False)#.dt.tz_localize(None)
			df = df.set_index([index_col, "symbol"])
			# df = df.asfreq(freq="D")
		
		if not os.path.exists("./data"):
			os.mkdir("./data")
		
		df.to_csv(file, index=True)
	else:
		try:
			df = pd.read_csv(file, index_col=[index_col, "symbol"], parse_dates=True)
		except Exception:
			display_backup_missing()
			return None
	return df

@st.cache_data(ttl=60*60)
def get_returns(df, horizon=1):
    return df.diff(horizon)

def stocks(tickers, symbol, strings: dict, online):
	"""Provides an illustration of the `Ticker.history` method

	Arguments:
		tickers {Ticker} -- A yahaooquery Ticker object
		symbol {List[str]} -- A list of symbol
	"""
	st.header("Historical Pricing")
	
	history_args = {
		"period": "1y",
		"interval": "1d",
		"start": datetime.datetime.now() - datetime.timedelta(days=365),
		"end": None,
	}

	c1, c2, c3 = st.columns([1, 1, 1])

	with c1:
		option_1 = st.selectbox("Period or Start / End Dates", ["Period", "Dates"], 0)
	
	if option_1 == "Period":
		with c2:
			history_args["period"] = st.selectbox(
				"Period", options=Ticker.PERIODS, index=9  # pylint: disable=protected-access
			)

		history_args["start"] = None
		history_args["end"] = None
	else:
		with c2:
			history_args["start"] = st.date_input("Start Date", value=history_args["start"])
			history_args["end"] = st.date_input("End Date")
		
		history_args["period"] = None

	with c3:
		# history_args["interval"] = "1m"
		history_args["interval"] = st.selectbox(
			"Interval", options=Ticker.INTERVALS, index=8  # pylint: disable=protected-access
		)
	
	df = get_stock_data(history_args, symbol, online)
	df_returns = df.pipe(get_returns)
 
	with st.sidebar:
		options_internal = [
			"Candlestick",
			"Line Chart (Absolute)",
			"Returns Series",
			"Returns Distribution"
		]
		menu_internal = st.radio(
			label = "Views",
			options = options_internal
		)

	if menu_internal == options_internal[0]:
		df_to_show = df
		fig = go.Figure(go.Ohlc(
			x=df.index.get_level_values("date"),
			open=df['open'],
			high=df['high'],
			low=df['low'],
			close=df['close']
		))
  
		range_breaks = [
			dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
		]
		
		if history_args["interval"] == "1h":
			range_breaks.append(dict(bounds=[16, 9], pattern="hour"))  # hide hours outside of 9.30am-4pm
			# dict(values=["2020-12-25", "2021-01-01"])  # hide holidays (Christmas and New Year's, etc)

		fig.update_xaxes(
			rangebreaks=range_breaks
		)
	elif menu_internal == options_internal[1]:
		df_to_show = df
		fig = go.Figure(go.Scatter(
			x = df.index.get_level_values("date"),
			y = df['close']
		))
	elif menu_internal == options_internal[2]:
		df_to_show = df_returns
		fig = go.Figure(go.Scatter(
			x = df_returns.index.get_level_values("date"),
			y = df_returns['close']
		))
	elif menu_internal == options_internal[3]:
		df_to_show = df_returns
		fig = go.Figure(go.Histogram(
			x = df_returns['close']
		))
	else:
		st.stop()

	st.plotly_chart(
		fig,
		use_container_width=True,
		config = config
	)

	st.dataframe(
		df_to_show,
		use_container_width=True,
	)

stocks(st.session_state["tickers"], st.session_state["symbol"], st.session_state["strings"], st.session_state["online"])