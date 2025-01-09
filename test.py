import pandas as pd
import streamlit as st
from pathlib import Path
from PIL import Image
from io import BytesIO
import base64
import numpy as np
from prices import get_team_prices
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import base64
from transformers import pipeline
from datetime import timedelta
import random

st.set_page_config(layout="wide")

@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="t5-small")  # Use a lightweight model

summarizer = load_summarizer()

def image_to_base64(img):
    if img:
        with BytesIO() as buffer:
            img.save(buffer, "png")
            return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
    return None

logo_path = 'Stakeholder_logo_sm.jpg'
logo_img = Image.open(logo_path)

#st.image(logo_img, use_column_width = False, width = 150)

tab1, tab2, tab3 = st.tabs(["Market", "Tokens", "About"])

with tab1:
    col = st.columns((2.5, 5, 2.5), gap='medium')

team_df = pd.read_csv('/Users/rogerwhite/Desktop/Stakeholder_data/teams.csv')
price_df = pd.read_csv('/Users/rogerwhite/Desktop/Stakeholder_data/prices.csv')
yield_df = pd.read_csv('/Users/rogerwhite/Desktop/Stakeholder_data/yield.csv')
leader_df = pd.read_csv('/Users/rogerwhite/Desktop/Stakeholder_data/leaderboard.csv')

# Paths to local logos (update paths to match your actual files)
logo_paths = [f"./images/logo_{i}.png" for i in range(0, len(team_df))]
for path in logo_paths:
    assert Path(path).exists(), f"Logo not found: {path}"

# Helper function to load and process images
def get_image_from_disk(path_to_image):
    return Image.open(path_to_image)

def create_spark(team, color, days = 364, height = 50, width = 110):
    
    y1 = price_df[team]
    fig = px.line(y1.iloc[-days:], facet_row_spacing=0.01, height=height, width=width)

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
    buffer = BytesIO()
    fig.write_image(buffer, format="png", scale=1)
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"

# Generate team dataset
@st.cache_data
def get_team_dataset():
    teams = team_df['School']
    prices = team_df['Price']
    yields = team_df['Per Yield']
    abbreviations = team_df['Abbreviation']
    conference = team_df['Conference']

    data = []
    for i, team in enumerate(teams):
        logo_base64 = image_to_base64(get_image_from_disk(logo_paths[i]))

        sparkline_base64 = create_spark(team.lower(), team_df['Color'].iloc[i])

        combined_name = f"{team} [{abbreviations[i]}]"
        ytd_change = ((price_df[team.lower()].iloc[-1] - price_df[team.lower()].iloc[-364])/price_df[team.lower()].iloc[-364])*100


        data.append(
            
            {
                "Team": combined_name,
                "Logo": logo_base64,
                "Price": price_df[team.lower()].iloc[-1],
                "Yield": yields[i] * 100,
                "Performance": sparkline_base64,
                "YTD": ytd_change,
                "Conference": conference.iloc[i]
            }
        )
    return pd.DataFrame(data)

# Configure columns for st.dataframe
column_configuration = {
    "Team": st.column_config.TextColumn(
        "Team", help="Team name", max_chars=50, width="medium"
    ),
    "Logo": st.column_config.ImageColumn(
        "", help="Team logo", width="small"
    ),
    "Price": st.column_config.NumberColumn(
        "Price", help="Price of the team", width="small", format="$%.2f"
    ),
    "Yield": st.column_config.NumberColumn(
        "Yield", help="Yield percentage", width="small", format="%.2f%%"
    ),
    "Performance": st.column_config.ImageColumn(
        "", help="Historical performance (sparkline)", width="small"
    ),
    "YTD": st.column_config.NumberColumn(
        "YTD", help="YTD performance", width="small", format="%.2f%%"
    ),
    "Conference": st.column_config.TextColumn(
        "Conference", help="Conference", width="medium"
)}

# Load dataset

main_df = get_team_dataset()
main_df = main_df[["Logo", "Team", "Price", "Yield","YTD","Performance","Conference"]].sort_values(by="Price", ascending=False).reset_index(drop=True)
main_df.index = main_df.index + 1

with col[1]:
    conferences = ['All FBS'] + list(team_df['Conference'].unique())
    conference = st.selectbox('Select conference', conferences)
    if conference == "All FBS":
        st.dataframe(
        main_df[["Logo", "Team", "Price", "Yield","YTD","Performance"]],
        column_config=column_configuration,
        use_container_width=True,
        hide_index=False,
    )  # Include all teams if "All Conferences" is selected
    else:
        filtered_df = main_df[main_df['Conference'] == conference].reset_index(drop = True)
        filtered_df.index += 1
        st.dataframe(
        filtered_df[["Logo", "Team", "Price", "Yield","YTD","Performance"]],
        column_config=column_configuration,
        use_container_width=True,
        hide_index=False,
    )
    leader_df.index += 1  # Set rank as index
    leader_df.rename_axis("Rank", inplace=True)
    leader_df['P/L'] = leader_df['Yield']
    
    col = st.columns((5, 5), gap='small')
    with col[0]:
        st.markdown('#### Leaderboard')
        st.dataframe(leader_df[['Username','P/L']])
    with col[1]:
        st.markdown('#### Overview')
        container = st.container(border = True)
        reserve_pool = 13400
        container.metric(label = 'Reserve pool', value = f'${reserve_pool:,.2f}', delta = 0)
        container.metric(label = 'Token supply (per team)', value = 100, delta = 0)
        container.metric(label = '24hr Volume', value = 0, delta = 0)
        

with tab2:
    col = st.columns((2.5, 5, 2.5), gap='medium')

with col[1]:
    
    teams = team_df['School']
    team = st.selectbox('Pick a team',teams)

    abb = team_df[team_df['School']==team]['Abbreviation'].values[0]

    end_date = pd.Timestamp("2024-11-14")  # Set end date to November 14th
    date_range = pd.date_range(end=end_date, periods=len(price_df.index))
    formatted_dates = date_range.strftime('%m/%d/%Y')
    
    color = str(team_df[team_df['School'] == team]['Color']).split()[1]
    alt_color = str(team_df[team_df['School'] == team]['Alt Color']).split()[1]

    logo_value = main_df[main_df["Team"].str.split("[").str[0].str.strip() == team]['Logo']
    logo_path = logo_value.values[0]

    base64_data = logo_path.split(",")[1]
    image_data = base64.b64decode(base64_data)
    image = Image.open(BytesIO(image_data))


    if alt_color.lower() in ["#ffffff", "white"]:
        alt_color = '#e3e3e3'

    x = formatted_dates 
    y1 = price_df[team.lower()]
    y2 = (yield_df[team.lower()]/price_df[team.lower()])*100

    nominal_y2 = yield_df[team.lower()]


    # Update layout
    st.markdown(
        f"""
        <div style="display: flex; align-items: center;">
            <img src="data:image/png;base64,{base64_data}" style="width:65px; margin-right: 10px;">
        </div>
        """,
        unsafe_allow_html=True
        )
    current_price = y1.iloc[-1]
    previous_price = y1.iloc[-2]
    delta = current_price - previous_price 
    percent_change = (delta / previous_price) * 100

    st.metric(label = abb, value = f"${current_price:,.2f}", delta=f"{percent_change:.2f}%")
    
    timeframe = len(y1)

    col1, col2, col3, col4 = st.columns([0.85, 0.9, 0.9, 7.6])  # Three equally spaced columns

    with col1:
        if st.button('6m'):
            timeframe = 182

    with col2:
        if st.button('YTD'):
            timeframe = 364

    with col3:
        if st.button('Max'):
            timeframe = len(y1)

    fig = make_subplots(
            rows=2, cols=1,  # Two rows, one column
            shared_xaxes=True,  # Share the x-axis
            row_heights=[0.7, 0.3],  # Top chart is larger
            vertical_spacing=0.05  # Space between the plots
        )

    fig.add_trace(
            go.Scatter(x=x[-timeframe:], y=y1[-timeframe:], mode='lines', name='Price' , line = dict(color=color), text=[f"Date: {date}, Price: ${price:.2f}" for date, price in zip(x[-timeframe:], y1[-timeframe:])],  # Custom hover text
        hoverinfo="text"),
            row=1, col=1 # Top row
        )

        # Add the second line chart
    fig.add_trace(
            go.Scatter(x=x[-timeframe:], y=y2[-timeframe:], mode='lines', name='% Yield', line = dict(color=alt_color), text=[f"Date: {date}, Yield: {y:.2f}%" for date, y in zip(x[-timeframe:], y2[-timeframe:])],
        hoverinfo = "text"),
            row=2, col=1  # Bottom row
        )

        # Update layout
    fig.update_layout(
            height=400,
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor='white',# Total height of the figure
            showlegend=True
        )

    fig.update_yaxes(
            showgrid=True,  # Show x-axis gridlines
            gridcolor='lightgray',  # Set gridline color to light gray
            zeroline=False,  # Remove x-axis zero line
            linecolor='white'  # Change x-axis line color to black
        )
    fig.update_xaxes(
        tickmode="auto",  # Automatically adjust ticks
        nticks=6,         # Specify the number of ticks to display
        tickformat="%b %Y"  # Format: e.g., "Jan 2024"
    )

    fig.update_yaxes(title_text="Price", row=1, col=1)  # Top chart y-axis
    fig.update_yaxes(title_text="% Yield", row=2, col=1)  # Bottom chart y-axis
        # Show the figure


    st.plotly_chart(fig)
    st.markdown('#####')
    col = st.columns((5,5), gap='large')

    with col[0]:
        container = st.container(border=True)
        with st.spinner("Generating summary..."):
            # Generate a summary
            summary_input = f"Provide a summary of the {team} NCAA football team, focusing on their achievements, history, and recent performance."
            summary = summarizer(summary_input, max_length=13, min_length=6, do_sample=False)
            container.write(f"""**Summary for {team}:** {summary[0]['summary_text']} The goal of this summary is to provide a weekly update on the team's recent performance
                aswell as the team's outlook going forward. An example would be providing a short summary of the recent game result, highlighting player performances, 
                team metrics, etc., followed by expectations for next week's game and how that result may affect the team's standing.""")
    
    with col[1]:
        team_names_only = main_df['Team'].str.split(" \\[", expand=True)[0]

# Find the index where the team name matches the search_team
        matching_index = team_names_only[team_names_only == team].index
        container = st.container(border=True)
        container.metric(label = 'Current yield', value = f"{y2.iloc[-1]:.2f}%")
        container.metric(label = 'Lifetime payout', value = f"${nominal_y2[1::28].sum()/13:.2f}")
        container.metric(label = 'Stakeholder rank', value = f"#{matching_index.tolist()[0]}")
    
    comments = [
    {"user": "Alice", "timestamp": "2025-01-09 10:30", "text": "This is a great app! 😊"},
    {"user": "Bob", "timestamp": "2025-01-09 11:00", "text": "I found a small issue on the main page."},
    {"user": "Charlie", "timestamp": "2025-01-09 11:15", "text": "Thanks for pointing that out, Bob!"},
]

    st.markdown('#####')
    #st.markdown('#### Comments')
    st.markdown(
        """
        <div style="display: flex; flex-direction: column; margin-bottom: 10px;">
            <h4 style="margin: 0;">Comments</h4>
            <hr style="margin: 5px 0; border: none; height: 1px; background-color: #ddd;" />
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Display Comments
    for comment in comments:
        st.markdown(
            f"""
            <div style="border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; border-radius: 5px;">
                <strong>{comment['user']}</strong> <span style="color: #888;">({comment['timestamp']})</span>
                <p style="margin-top: 10px;">{comment['text']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


with tab3:
    col1, col2, col3 = st.columns([3, 4, 3])
    
    with col2:
        st.markdown('##### ')
        st.markdown('### About Stakeholder')
        st.write("""Stakeholder is a platform that hosts a skill based competition where users can buy and
                    sell tokens associated with college football teams (with the goal of expanding to
                    professional sports). Users indirectly compete against each other in exercising predictive
                    skill to determine which teams will perform better than others.""")
        
        expand = st.expander("The launch: College Football Team Tokens", icon="🚀")
        expand.markdown("""The platform will initially auction 100 team tokens per 134 FBS teams (13,400 total
                    tokens) at \$1.00 a piece. These tokens will be backed by an initial reserve pool of \$13,400
                    worth of USDC supplied by Stakeholder. Tokens that don’t receive bids above \$1.00 will
                    remain locked until we opt to lower their starting bid at a later date.""")
        
        expand = st.expander("Reserve pooling", icon="💰")
        expand.markdown("""The reserve pool is the pool of money that is dedicated to earning yield and paying token holders.""")

        expand = st.expander("Payouts", icon="🏆")
        expand.markdown("""Each token represents a stake in the reserve pool. When the reserve pool earns interest,
                    that interest is given back to token holders. 
                    Tokens associated with teams that perform better receive a larger stake of the reserve.
                    Specifically, the payout formula takes into account a team’s position in the AP top 25
                    ranking. The more votes a team receives from the AP committee, the larger share of the
                    payout pool they earn.""")

        st.markdown('##### ')
        st.markdown('### How it works')
        st.write("""Example, if the \#1 ranked team Georgia  received 1,550 points and there were 20,160
                    points total, they would receive 1,550/20,160 = 7.7\% of the monthly payout.
                    If the monthly payout from the reserve pool was \$1,000 total, then \$77 would be
                    distributed to Georgia token holders.""")
        
        st.markdown('##### ')
        st.markdown('### FAQs')
        expand = st.expander("How often are payouts made?", icon=":material/info:")
        expand.markdown("""Payouts will be monthly. In order to receive payouts for any given month and token, the
                    owner of the token must have purchased the token on or before the ex-payout date. For
                    example, in 2024 the first AP ranking was released on *August 12, 2024*. In order to be
                    eligible for the August payout, one must have bought and held a token before *July 12,
                    2024*. The next payout would then take place on September 12, 2024 and be determined
                    by that week's rankings.""")
        
        expand = st.expander("What determines prices?", icon=":material/info:")
        expand.markdown("""Prices will be dictated purely by supply and demand. The payouts are designed to be a
                    guiding hand for price action, but ultimately, it will be up to the market to determine each
                    token’s price.""")
        
        expand = st.expander("Do the tokens expire?", icon=":material/info:")
        expand.markdown("""Nope. The tokens are designed to exist in perpetuity.""")

        
                            
    






