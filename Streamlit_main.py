import streamlit as st
from streamlit_option_menu import option_menu
import Scraper
from BusApp import BusApp
from DataHandler import DataHandler

# Initialize session state variables
for key in ['user_txt', 'database_txt', 'host_txt', 'table_txt', 'password_txt']:
    if key not in st.session_state:
        st.session_state[key] = ''


def fetch_data(user, password, host, database, table):
    try:
        db_manager = DataHandler(host=host, user=user, password=password, database=database)
        db_manager.connect()
        st.write("Connecting to database...")

        data = db_manager.execute_query(f"SELECT * FROM {table};")

        if data:
            st.session_state.data = data
            st.write("Data fetched successfully!")
        else:
            st.write(f"No data found in table {table}.")
        db_manager.disconnect()
    except Exception as e:
        st.error(f"Error: {e}")
        st.error("Please check the entered credentials.")
        st.write("Prerequisite: Database and table needs to be present to proceed!")


def display_homepage():
    st.title("Welcome to the Bus Data Management System")

    st.write("""
    This application allows you to fetch, scrape, and manage bus service data. 
    Here's how to navigate through the different sections:
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Fetch Data")
        st.write("""
        - Enter your database credentials
        - Check the connection
        - Set up scraping parameters
        - Initiate data scraping
        """)

    with col2:
        st.subheader("Select Bus")
        st.write("""
        - Browse available bus services
        - View detailed information
        - Perform actions on selected buses
        """)

    st.write("""
    To get started, select an option from the menu on the left.
    """)


# Sidebar
with st.sidebar:
    option = option_menu(
        menu_title="Menu",
        options=["Home", "Fetch Data", "Select Bus"],
        icons=["house-heart", "database-fill-up", "bus-front"],
        menu_icon="cast",
        default_index=0,
    )

# Home
if option == 'Home':
    display_homepage()

# Fetch Data
elif option == 'Fetch Data':
    st.header("Database Credentials")
    cols = st.columns(3)
    fields = [('User', 'user_txt'), ('Password', 'password_txt'),
              ('Host', 'host_txt'),  ('Database', 'database_txt'),
              ('Table', 'table_txt')]

    for i, (label, key) in enumerate(fields):
        with cols[i % 3]:
            st.session_state[key] = st.text_input(label, value=st.session_state[key],
                                                  type='password' if label == 'Password' else 'default')

    if st.button('Check Credentials'):
        fetch_data(**{k: st.session_state[v] for k, v in zip(['user', 'password', 'host', 'database', 'table'],
                                                             ['user_txt', 'password_txt', 'host_txt', 'database_txt',
                                                              'table_txt'])})

    st.header("Scrape Data from RedBus")
    col1, col2 = st.columns(2)
    with col1:
        thread_count = st.number_input("Thread Count", min_value=1, step=1, value=1)
        date_selector = st.date_input("Select a date to Scrape data from RedBus")
    with col2:
        services_count = st.number_input("Number of Services", min_value=1, step=1, value=1)
        st.write('<div style="height: 28px;"></div>', unsafe_allow_html=True)

        if st.button('Start Scrape'):
            if thread_count > services_count:
                st.error("Thread Count must not be greater than Number of services")
            elif not st.session_state.database_txt:
                st.error("Please enter database details to proceed")
            else:
                with st.spinner('Scraping data...'):
                    date = date_selector.strftime("%d-%b-%Y")
                    scraped_data = Scraper.scrape_data_parallely(thread_count, services_count, date)
                    data_handler = DataHandler(
                        **{k: st.session_state[v] for k, v in zip(['host', 'user', 'password', 'database'],
                                                                  ['host_txt', 'user_txt', 'password_txt',
                                                                   'database_txt'])})
                    data_handler.add_scraped_data_to_database(st.session_state.table_txt, scraped_data)
                    st.success('Scraping Completed!')

    st.markdown("""
    **NOTE**: 
    - **Thread Count**: count of parallel scraping using Chrome.
    - **Number of Services**: No of Government Services data to be scraped in RedBus.
    """)

# Select Buses
elif option == 'Select Bus':
    if not st.session_state.database_txt or not st.session_state.host_txt:
        st.error("Please enter database details in Fetch Data page to proceed")
    else:
        app = BusApp(**{k: st.session_state[v] for k, v in zip(['host', 'user', 'password', 'database', 'table'],
                                                               ['host_txt', 'user_txt', 'password_txt', 'database_txt',
                                                                'table_txt'])})
        app.run()
