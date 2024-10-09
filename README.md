# Bus Data Management

## Overview

The Bus Data Management is a Streamlit-based web application designed to fetch, scrape, and manage bus service data. This application provides an interface for users to dynamically filters with bus service information, and manage database operations.

## Features

- **Data Fetching**: Connect to databases and retrieve existing bus service data.
- **Web Scraping**: Scrape new bus service data from RedBus.
- **Bus Selection**: Browse and interact with available bus services.
- **Data Management**: Update and maintain accurate bus service information.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.7+
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Pushparaj95/Bus_Data_Management.git
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application:

1. Run the Streamlit app:
   ```
   streamlit run Streamlit_main.py
   ```

2. Open your web browser and go to `http://localhost:8501` (or the address provided in the terminal).

## Application Structure

- `Streamlit_main.py`: Main application file containing the Streamlit interface.
- `Scraper.py`: Contains web scraping functionality for RedBus data.
- `BusApp.py`: Handles bus data dynamic filters and UI for filtering page.
- `DataHandler.py`: Manages database operations and data processing.

## Configuration

To configure the database connection:

1. Open the `DataBase` section in UI.
2. Update the following variables with your database information:
   - `host`
   - `user`
   - `password`
   - `database`
   - `table`

To scrape data from RedBus:

1. Open the `Scrape Data` section in UI.
2. Provide Thread Count, Number of services and date to scrape date.
3. Then Select, Select Bus and perform Dynamic Filtering.

**NOTE**:
1. **Thread Count**: count of parallel scraping using Chrome.
2. **Number of Services**: No of Government Services data to be scraped in RedBus.
3. **Date**: Date of data to be scraped.

## Acknowledgements

- [Streamlit](https://streamlit.io/) for the web application framework.
- RedBus for providing bus service data.