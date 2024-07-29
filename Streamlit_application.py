import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta


# Database connection
@st.cache_resource
def get_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='redbus',
            user='root',
            password=''
        )
        return connection
    except mysql.connector.Error as e:
        st.error(f"Error connecting to MySQL database: {e}")
        return None


conn = get_connection()


# Load data
@st.cache_data
def load_data():
    query = "SELECT * FROM bus_routes"
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data


data = load_data()
df = pd.DataFrame(data)

# Sidebar filters
st.sidebar.header('Filter Bus Routes')

route_name = st.sidebar.multiselect('Select Route', options=df['route_name'].unique())
busname = st.sidebar.multiselect('Select Bus Name', options=df['busname'].unique())
bustype = st.sidebar.multiselect('Select Bus Type', options=df['bustype'].unique())
star_rating = st.sidebar.slider('Minimum Star Rating', 0.0, 5.0, 0.0, 0.5)
price_range = st.sidebar.slider('Price Range',
                                min_value=float(df['price'].min()),
                                max_value=float(df['price'].max()),
                                value=(float(df['price'].min()), float(df['price'].max())))

# Date range filter
min_date = df['departing_time'].min().date()
max_date = df['departing_time'].max().date()

# Ensure the default end date doesn't exceed max_date
default_end_date = min(min_date + timedelta(days=18), max_date)

date_range = st.sidebar.date_input('Select Date Range',
                                   value=[min_date, default_end_date],
                                   min_value=min_date,
                                   max_value=max_date)

# Construct SQL query based on filters
query = "SELECT * FROM bus_routes WHERE 1=1"
params = []

if route_name:
    query += " AND route_name IN (%s)" % ','.join(['%s'] * len(route_name))
    params.extend(route_name)
if busname:
    query += " AND busname IN (%s)" % ','.join(['%s'] * len(busname))
    params.extend(busname)
if bustype:
    query += " AND bustype IN (%s)" % ','.join(['%s'] * len(bustype))
    params.extend(bustype)

query += " AND star_rating >= %s"
params.append(star_rating)

query += " AND price BETWEEN %s AND %s"
params.extend([price_range[0], price_range[1]])

query += " AND DATE(departing_time) BETWEEN %s AND %s"
params.extend([date_range[0], date_range[1]])

# Execute query and get filtered data
cursor = conn.cursor(dictionary=True)
cursor.execute(query, tuple(params))
filtered_data = cursor.fetchall()
filtered_df = pd.DataFrame(filtered_data)

# Display filtered data
st.write(f'Showing {len(filtered_df)} bus routes')
st.dataframe(filtered_df)

# Visualizations
if not filtered_df.empty:
    st.write('Price Distribution by Bus Name')
    fig = px.box(filtered_df, x='busname', y='price', title='Price Distribution by Bus Type')
    st.plotly_chart(fig)

    st.write('Average Rating by Bus Name')
    avg_rating = filtered_df.groupby('busname')['star_rating'].mean().sort_values(ascending=False)
    st.bar_chart(avg_rating)

    st.write('Available Seats by Bus Type')
    seats_by_type = filtered_df.groupby('bustype')['seats_available'].sum().sort_values(ascending=False)
    st.bar_chart(seats_by_type)

# Close database connection
if conn.is_connected():
    conn.close()
