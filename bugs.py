import pandas as pd
import streamlit as st
from pathlib import Path
from PIL import Image
from io import BytesIO
import base64
import numpy as np
from prices import get_team_prices
import plotly.express as px

reserve_pool = 13400
annual_yield = 0.04
annual_payout = reserve_pool*annual_yield

team_df = pd.read_csv('/Users/rogerwhite/Desktop/Stakeholder_data/teams.csv')
conference_df = pd.read_csv('/Users/rogerwhite/Desktop/Stakeholder_data/Conference_Share_Per_Team_Per_Day.csv')
daily_df = pd.read_csv('/Users/rogerwhite/Desktop/Stakeholder_data/Daily_AP_Votes_Data.csv')

def create_spark(team, conference, days = 90, height = 50, width = 100):
  
  y = get_team_prices(team.lower(), conference)

  for index, row in team_df.iterrows():
    if team == row['School'].lower():
      color = row['Color']
  
  fig = px.line(y1['Price'][-days:], facet_row_spacing=0.01, height=height, width=width)

  fig.update_xaxes(visible=False, fixedrange=True)
  fig.update_yaxes(visible=False, fixedrange=True)

  # remove facet/subplot labels
  fig.update_layout(annotations=[], overwrite=True)

  # strip down the rest of the plot
  fig.update_layout(
      showlegend=False,
      plot_bgcolor="white",
      margin=dict(t=10,l=10,b=10,r=10)
  )
  fig.update_traces(line_color=color)
  return fig.show()

  teams = team_df['School']
  conference = team_df['Conference']

  for i, team in enumerate(teams):
    sparkline_image = create_sparkline(team.lower(), conference[i])
    print(i)

