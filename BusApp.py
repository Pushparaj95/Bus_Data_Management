import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error


class BusApp:
    def __init__(self, host, user, password, database, table):
        self.db_config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }
        self.connection = None
        self.df = None
        self.table = table

    def create_db_connection(self):
        """
        Method to create database connection with mysql.Connector
        :return: boolean True when connected, else False
        """
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            if self.connection.is_connected():
                return True
        except Error as e:
            st.error(f"Error while connecting to MySQL: {e}")
            return False

    def fetch_bus_data(self):
        """
        Method to retrieve all data from given table, and converts to DataFrame
        :return: boolean True when Success, else False
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = f"SELECT * FROM {self.table}"
            cursor.execute(query)
            data = cursor.fetchall()
            self.df = pd.DataFrame(data)
            return True
        except Error as e:
            st.error(f"Error while fetching data: {e}")
            return False

    @staticmethod
    def format_timedelta(td):
        """
        custom method to change timedelta object to readable format as HH:MM:SS
        :param td: timedelta values to be formatted
        :return: converted time format as str
        """
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    @staticmethod
    def to_full_time_format(time_string):
        return time_string.strip() + ":00"

    def setup_ui(self):
        """
        Custom method to set up UI
        """
        title = "Bus Selection App"
        title_format = (f'<p style="text-align: center; font-family: Arial; color: #000000; font-size: 40px; '
                        f'font-weight: bold;">{title}</p>')
        st.markdown(title_format, unsafe_allow_html=True)

        if not self.create_db_connection() or not self.fetch_bus_data():
            return

        st.subheader("Search and Filter")
        self.setup_filters()

    def setup_filters(self):
        """
        Custom method to set up filters in UI
        """
        col1, col2, col3 = st.columns(3)

        with col1:
            routes = ["All"] + sorted(self.df["route"].unique())
            st.selectbox("Select Route", routes, key="route")

            seat_types = ["All", "Sleeper", "Semi Sleeper", "Seater"]
            st.selectbox("Select Seat Type", seat_types, key="seat_type")

        with col2:
            ac_types = ["All", "AC", "NON AC"]
            st.selectbox("Select AC Type", ac_types, key="ac_type")

            st.slider("Minimum Rating", 1.0, 5.0, 1.0, 0.5, key="min_rating")

        with col3:
            time_ranges = ["All", "00:00-06:00", "06:00-12:00", "12:00-18:00", "18:00-00:00"]
            st.selectbox("Select Time Range", time_ranges, key="time_range")

            st.number_input("Maximum Fare", min_value=0, step=500, value=int(self.df["price"].max()), key="max_fare")

        if st.button("Show Buses"):
            self.filter_and_display_results()

    def filter_and_display_results(self):
        """
        Method for dynamic filtering in database with user inputs
        """
        filtered_df = self.df.copy()

        # Apply filters
        if st.session_state.route != "All":
            filtered_df = filtered_df[filtered_df["route"] == st.session_state.route]

        if st.session_state.seat_type != "All":
            filtered_df = filtered_df[
                filtered_df["bus_type"].str.contains(st.session_state.seat_type, case=False, na=False)]

        if st.session_state.ac_type != "All":
            if st.session_state.ac_type == "NON AC":
                filtered_df = filtered_df[
                    filtered_df["bus_type"].str.contains(r'\bnon\b', case=False, na=False) |
                    ~filtered_df["bus_type"].str.contains(r'AC|A/C|HVAC', case=False, na=False)]
            else:
                filtered_df = filtered_df[
                    filtered_df["bus_type"].str.contains(r'^(?=.*\b(?:AC|A/C|HVAC)\b)(?!.*\b(?:NON|Non)\b).*', na=False)]

        filtered_df = filtered_df[filtered_df["rating"] >= st.session_state.min_rating]

        if st.session_state.time_range != "All":
            start_time, end_time = st.session_state.time_range.split("-")
            start_time = pd.to_timedelta(self.to_full_time_format(start_time))
            end_time = pd.to_timedelta(self.to_full_time_format(end_time))

            if start_time < end_time:
                filtered_df = filtered_df[
                    (filtered_df["departure_time"] >= start_time) & (filtered_df["departure_time"] < end_time)]
            else:
                filtered_df = filtered_df[
                    (filtered_df["departure_time"] >= start_time) | (filtered_df["departure_time"] < end_time)]

        filtered_df = filtered_df[filtered_df["price"] <= st.session_state.max_fare]

        # Format times
        filtered_df['departure_time'] = filtered_df['departure_time'].apply(self.format_timedelta)
        filtered_df['arrival_time'] = filtered_df['arrival_time'].apply(self.format_timedelta)

        # Adding clickable URL
        filtered_df['url'] = filtered_df['url'].apply(lambda x: f'<a href="{x}" target="_blank">Click here</a>')

        # Display results
        sub_header = "Available Buses"
        sub_header_format = (f'<p style="text-align: center; font-family: Arial; color: #000000; font-size: 25px; '
                             f'font-weight: bold;">{sub_header}</p>')
        st.markdown(sub_header_format, unsafe_allow_html=True)

        if not filtered_df.empty:
            st.markdown(filtered_df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("No buses found matching your criteria. Please try different filters.")

    def run(self):
        self.setup_ui()


if __name__ == "__main__":
    # Run this class with database credentials to create dynamic filtering page
    app = BusApp(
        host='localhost',  # Give your Host name
        user='root',  # Give your username
        password='Your password',  # Give your password
        database='Your database name',  # Give your database name
        table='Your database table')  # Give your table name
    app.run()

    # Run the below code in terminal
    # streamlit run BusApp.py