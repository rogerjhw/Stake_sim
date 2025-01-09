import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

df = pd.read_csv('/Users/rogerwhite/Desktop/large_data.csv')

sub_df = df.set_index('Athlete')
sub_df = sub_df[['Activity','Amount Earned','Team','End Time']].sort_values('End Time', ascending = False)

st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="expanded")

tab1, tab2 = st.tabs(["Insights", "Athletes"])

#alt.themes.enable("dark")

fake_df = pd.DataFrame()

fake_df['Teams'] = ['Football','Mens Basketball', 'Womens Volleyball', 'Baseball', 'Womens Basketball']
fake_df['Spending'] = ['12.7K','4.3K','3.4K','2.3K','1.3K']
fake_df.set_index('Teams', inplace= True)

att_df =  pd.DataFrame()
att_df['Team'] = ['Football','M Basketball','W Volleyball', 'Baseball', 'W Basketball']
att_df['Percentage'] = [0.53,0.18,0.14,0.10,0.05]

fig_2 = px.pie(att_df, names = 'Team', values = 'Percentage')
fig_2.update_traces(hole=0.75)
fig_2.update_layout(
    title = '% Allocation',
    width=250,  # Set width
    height=250,
    showlegend = False,
    margin=dict(t=40, b=40, l=75, r=75),
    
)

fig_2.update_traces(textinfo='label+percent', textposition='outside')

with tab1:

    st.markdown('#### Insights Dashboard')
    col = st.columns((1.5, 4.5, 2), gap='medium')

    with col[0]:
        #st.markdown('#### Spending Dashboard')
        container = st.container(border=True)
        container.metric(label= 'July Spending', value= '24K', delta= str(12) + '% MoM', delta_color = 'inverse')
        st.markdown('###### Spending By Team')
        st.dataframe(fake_df)
        container_2 = st.container(border = True)
        st.plotly_chart(fig_2)

    fake_df = pd.read_csv('/Users/rogerwhite/Desktop/fake_data_2.csv')
    fig = px.line(fake_df, x='Month', y='Amount', color='Team', line_shape='spline', title='Monthly Earnings by Team')
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Amount (K)',
        title= {
            'text': 'Team Spending By Month',
            'x': 0,         # Align the title to the left
            'xanchor': 'left'  # Anchor the title to the left
        }, 
        width = 800
    )

    with col[1]:
        container = st.container(border=True)
        container.plotly_chart(fig)
        

    with col[2]:
        container = st.container(border = True)
        container.metric(label = 'July Attendance', value = '96%', delta = str(1) + '% MoM')
        st.markdown('###### Recent Activities')
        st.dataframe(sub_df)


with tab2:
    
# DataFrame for a single day's worth of activities with different categories
    df = pd.DataFrame([
        dict(Task="ECON 101", Start='2024-07-30 9:00:00', Finish='2024-07-30 9:50:00', Category="Class"),
        dict(Task="AMST 215", Start='2024-07-30 11:00:00', Finish='2024-07-30 12:20:00', Category="Class"),
        dict(Task="Academic Counseling", Start='2024-07-30 13:00:00', Finish='2024-07-30 13:30:00', Category="Counseling"),
        dict(Task="Tutoring", Start='2024-07-30 14:15:00', Finish='2024-07-30 14:45:00', Category="Tutoring")
    ])

    # Convert the Start and Finish columns to datetime
    df['Start'] = pd.to_datetime(df['Start'])
    df['Finish'] = pd.to_datetime(df['Finish'])

    # Define a soft color palette for the categories
    color_map = {
        "Class": "lightblue",
        "Counseling": "lightgreen",
        "Tutoring": "lightcoral"
    }

    # Create the figure
    fig = go.Figure()

    # Loop through the unique categories and add the tasks to the timeline
    for category in df['Category'].unique():
        category_df = df[df['Category'] == category]
        
        for i, row in category_df.iterrows():
            hover_template = (
                f"<b>{row['Task']} ({category})</b><br>"
                f"Start: {row['Start'].strftime('%H:%M')}<br>"
                f"End: {row['Finish'].strftime('%H:%M')}<extra></extra>"
            )
            
            fig.add_trace(go.Scatter(
                x=[row['Start'], row['Finish']],
                y=[category, category],
                mode='lines',
                line=dict(width=30, color=color_map[category]),
                hovertemplate=hover_template,
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['Start'], row['Finish']],
                y=[category, category],
                mode='markers',
                marker=dict(size=30, symbol='circle', color=color_map[category]),
                hoverinfo='skip',  # Skips hover info for the markers
                showlegend=False
            ))

    # Update layout
    fig.update_layout(
        title='Chipper Jones 7/30 Schedule',
        yaxis=dict(
            tickvals=[category for category in df['Category'].unique()],
            ticktext=[category for category in df['Category'].unique()],
            showgrid=False,
            zeroline=False
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False
        ),
        height=400
    )

    # Show the figure

    st.markdown('#### Athlete Dashboard')
    col = st.columns((1.5, 4.5, 2), gap='medium')

    total_amount = 8400  # Total amount to be paid out
    paid_out = 3450       # Amount already paid out

        # Amount already paid out
    remainder = total_amount - paid_out  # Amount remaining to be paid out

    remaining_percentage = (remainder / total_amount) * 100

    with col[0]:

        st.selectbox('Select athlete',
                     (list(sub_df.index.unique())))
        
        container = st.container(border = True)
        container.metric(label = "Today's Earnings", value = '$120')
        container.metric(label = 'Attendance', value = '4/4')
        
    with col[1]:
        st.date_input('Select Date')
        st.plotly_chart(fig)

    with col[2]:
        container= st.container(border = True)
        container.metric(label = 'Total remaining contract', value = '$4,950')
        container.metric(label = 'Total paid')