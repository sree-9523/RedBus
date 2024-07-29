# Redbus Data Scraping with Selenium & Dynamic Filtering using Streamlit
A project of Web-Scraping to extract bus details of different routes from the official website of RedBus.
## Features
* The first step is to set up a MySQL database named 'redbus' and create a table named 'bus_routes' 
* The next step automates web browsing using Selenium WebDriver and scrapes bus route details from RedBus website
* Finally, the development of a user-friendly Streamlit application for data filtering.
## Prerequisites
- Python 3.12
- Chrome WebDriver
- MySQL server
- Required Python packages (install using `pip install -r requirements.txt`):
  - selenium
  - mysql-connector-python
## Database Setup
1. Install the required dependencies.
2. Set up a MySQL database named 'redbus' and create a table named 'bus_routes' with the following structure:
```sql
CREATE TABLE bus_routes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  route_name VARCHAR(255),
  route_link VARCHAR(255),
  busname VARCHAR(255),
  bustype VARCHAR(50),
  departing_time DATETIME,
  duration VARCHAR(50),
  reaching_time DATETIME,
  star_rating FLOAT,
  price FLOAT,
  seats_available INT
);
```
#### Table Preview
![Screenshot 2024-07-29 205657](https://github.com/user-attachments/assets/dc09d427-9425-4e08-927e-abebe5f3cf0e)
## Data Scraping
### 1. ***State Bus.py*** (eg., rsrtc.py)
* Import necessary libraries and modules for time delays, web scraping, database connectivity, and date-time operations.
```python
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import mysql.connector
from datetime import datetime
```


* Define a function to click an element specified by XPath, with retries if the element is not clickable immediately.
 ```python
  def click_element(driver, xpath, timeout=10, retries=3):
    for attempt in range(retries):
        try:
            wait = WebDriverWait(driver, timeout)
            element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(2)
            element.click()
            return
        except (TimeoutException, StaleElementReferenceException) as e:
            if attempt == retries - 1:
                print(f"Failed to click element after {retries} attempts. Error: {str(e)}")
                raise
            print(f"Attempt {attempt + 1} failed. Retrying...")
            driver.refresh()  # Refresh the page and try again
```
  
* Update the db_config dictionary in the script with the MySQL connection details.
```python
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'redbus'
}
```
* Import specific exceptions from the Selenium library for error handling.
```python
  from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
```
* Initialize the Selenium WebDriver for Chrome.
 ```python
 driver = webdriver.Chrome()  # or whichever browser you're using
```
* Opens the RedBus website.
```python
driver.get("https://www.redbus.in/")
```
* Wait for the "View All" link to be present, scrolls to it, and clicks it.
```python
wait = WebDriverWait(driver, 5)  # wait up to 5 seconds
view_all = wait.until(EC.presence_of_element_located((By.XPATH, "//a[@href='https://www.redbus.in/online-booking/rtc-directory']")))
driver.execute_script("arguments[0].scrollIntoView(true);", view_all)
view_all.click()
time.sleep(3)
```
* Navigates directly to the RTC directory page on RedBus.
```python
driver.get("https://www.redbus.in/online-booking/rtc-directory")
time.sleep(5)
```
* Uses the click_element function to click the RSRTC link and waits for the page to load.
```python
click_element(driver, "//a[normalize-space()='RSRTC']", timeout=5)
time.sleep(7)
```
* Waits for the operator option element to be present, scrolls to it, and clicks it.
```python
operator_opt1 = wait.until(EC.presence_of_element_located((By.XPATH, "//div[normalize-space()='2']")))
driver.execute_script("arguments[0].scrollIntoView(true);", operator_opt1)
time.sleep(3)
operator_opt1.click()
```

* Finds the RSRTC bus route element and retrieves its text.
```python
RSRTC_bus_routes = wait.until(EC.presence_of_element_located((By.XPATH, "//a[@title='Jaipur (Rajasthan) to Mathura']")))
RSRTC_bus_routes_text = RSRTC_bus_routes.text
```
* Clicks on the RSRTC bus route link using JavaScript.
```python
time.sleep(3)
driver.execute_script("arguments[0].click();", RSRTC_bus_routes)
```
* Sets the RSRTC route link to a specific URL.
```python
RSRTC_route_link = "https://www.redbus.in/bus-tickets/jaipur-to-mathura?fromCityId=807&toCityId=747&fromCityName=Jaipur&toCityName=Mathura&busType=Any&srcCountry=null&destCountry=IND&onward=29-Jul-2024"
```
* Defines a function to insert bus route details into a MySQL database.
```python
def insert_bus_route(bus_details):
    global cursor, connection
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # SQL query to insert data
        query = """
        INSERT INTO bus_routes
        (route_name, route_link, busname, bustype, departing_time, duration,
        reaching_time, star_rating, price, seats_available)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Convert departing_time and reaching_time to datetime objects
        d_time = '29-Jul-2024 00:00'
        if (bus_details['departure_time']) != '':
            d_time = '29-Jul-2024 ' + bus_details['departure_time']

        a_time = '29-Jul-2024 00:00'
        if (bus_details['arrival_dt']) != '':
            a_time = bus_details['arrival_dt'] + bus_details['arrival_time']

        departing_time = datetime.strptime(d_time, '%d-%b-%Y %H:%M')
        reaching_time = datetime.strptime(a_time, '%d-%b-%Y %H:%M')

        # Prepare data for insertion
        data = (
            bus_details['bus_route_name'],
            bus_details['bus_route_link'],
            bus_details['bus_name'],
            bus_details['bus_type'],
            departing_time,
            bus_details['duration'],
            reaching_time,
            float(bus_details['rating'].split()[0]),  # Assuming rating is in format "4.5 stars"
            float(bus_details['ticket_fare'].replace('INR ', '').strip()),  # Remove 'INR'
            int(bus_details['seats_availability'].split()[0])  # Assuming format is "X seats available"
        )

        # Execute the query
        cursor.execute(query, data)
        connection.commit()
        print(f"Successfully inserted bus route: {bus_details['bus_route_name']}")

    except mysql.connector.Error as error:
        print(f"Failed to insert record into bus_routes table: {error}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
```
**Important Note: For _d_time_ and _a_time_ the dates need to be changed manually as per preference**

* Opens the RSRTC route link in the browser.
```python
driver.get(RSRTC_route_link)
```
* Waits for the operator filter input to be present, scrolls to it, and clicks it.
```python
operator_opt = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='opfilter']")))
driver.execute_script("arguments[0].scrollIntoView(true);", operator_opt)
operator_opt.click()
time.sleep(1)
```
* Waits for the RSRTC operator label to be present, scrolls to it, and clicks it.
```python
apply_button = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='button btn-apply op-apply']")))
driver.execute_script("arguments[0].scrollIntoView(true);", apply_button)
apply_button.click()
time.sleep(3)
```
* Waits for the apply button to be present, scrolls to it, and clicks it.
```python
apply_button = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='button btn-apply op-apply']")))
driver.execute_script("arguments[0].scrollIntoView(true);", apply_button)
apply_button.click()
time.sleep(3)
```
* Defines a function to scroll to the bottom of the page repeatedly to load more bus results.
```python
def scroll_and_load():
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Wait for page to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
```
* Calls the scroll_and_load function to load all bus items, then waits for all bus elements to be present.
```python
scroll_and_load()
time.sleep(5)
bus_items = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "bus-item")))
```
* Iterates through each bus item, extracts its details, prints them, and inserts them into the database.
```python
for bus in bus_items:
    try:
        # Check for next day arrival
        arrival_dt = '29-Jul-2024 '  # Default to same day
        next_day_element = bus.find_elements(By.CLASS_NAME, "next-day-dp-lbl")
        if next_day_element:
            arrival_dt = next_day_element[0].text + '-2024 '

        new_rating = '0.0'
        try:
            rating = bus.find_element(By.CLASS_NAME, "rating-sec").text
            if rating != 'New':
                new_rating = rating
        except NoSuchElementException:
            pass

        # Extract bus details
        bus_details = {
            'bus_route_name': RSRTC_bus_routes_text,
            'bus_route_link': RSRTC_route_link,
            'bus_name': bus.find_element(By.CLASS_NAME, "travels").text,
            'bus_type': bus.find_element(By.CLASS_NAME, "bus-type").text,
            'departure_time': bus.find_element(By.CLASS_NAME, "dp-time").text,
            'arrival_time': bus.find_element(By.CLASS_NAME, "bp-time").text,
            'duration': bus.find_element(By.CLASS_NAME, "dur").text,
            'ticket_fare': bus.find_element(By.CLASS_NAME, "fare").text,
            'seats_availability': bus.find_element(By.CLASS_NAME, "seat-left").text,
            'rating': new_rating,
            'arrival_dt': arrival_dt
        }

        # Print the extracted details
        print(bus_details)

        # Insert into database
        time.sleep(1)
        insert_bus_route(bus_details)

    except Exception as e:
        print(f"Error extracting details for a bus: {str(e)}")
```
**Important Note: Manually set the _arrival_dt_ to the same date as a_time and d_time. Also, to handle new buses or buses with no rating, a default new_rating is set to 0.0 and by passes using try and except**

* Keeps the browser open, allowing the user to manually close it by pressing Ctrl+C. Ensures the driver quits properly when exiting.
```python
time.sleep(2)
print("Browser will stay open. Press Ctrl+C to exit.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    driver.quit()
```

### 2. ***private.py***
* Import necessary libraries and modules for time delays, web scraping, database connectivity, and date-time operations.
```python
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import mysql.connector
from datetime import datetime
```
* Define a function to click an element specified by XPath, with retries if the element is not clickable immediately.
 ```python
  def click_element(driver, xpath, timeout=10, retries=3):
    for attempt in range(retries):
        try:
            wait = WebDriverWait(driver, timeout)
            element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(2)
            element.click()
            return
        except (TimeoutException, StaleElementReferenceException) as e:
            if attempt == retries - 1:
                print(f"Failed to click element after {retries} attempts. Error: {str(e)}")
                raise
            print(f"Attempt {attempt + 1} failed. Retrying...")
            driver.refresh()  # Refresh the page and try again
```
  
* Update the db_config dictionary in the script with the MySQL connection details.
```python
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'redbus'
}
```
* Import specific exceptions from the Selenium library for error handling.
```python
  from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
```
* Initialize the Selenium WebDriver for Chrome.
 ```python
 driver = webdriver.Chrome()  # or whichever browser you're using
```
* Opens the RedBus website.
```python
driver.get("https://www.redbus.in/")
```
* Wait for the "View All" link to be present, scrolls to it, and clicks it.
```python
wait = WebDriverWait(driver, 5)  # wait up to 5 seconds
view_all = wait.until(EC.presence_of_element_located((By.XPATH, "//a[@href='https://www.redbus.in/online-booking/rtc-directory']")))
driver.execute_script("arguments[0].scrollIntoView(true);", view_all)
view_all.click()
time.sleep(3)
```
* Navigates directly to the RTC directory page on RedBus.
```python
driver.get("https://www.redbus.in/online-booking/rtc-directory")
time.sleep(5)
```
* Uses the click_element function to click the RSRTC link and waits for the page to load.
```python
click_element(driver, "//a[normalize-space()='RSRTC']", timeout=5)
time.sleep(7)
```
* Waits for the operator option element to be present, scrolls to it, and clicks it.
```python
operator_opt1 = wait.until(EC.presence_of_element_located((By.XPATH, "//div[normalize-space()='2']")))
driver.execute_script("arguments[0].scrollIntoView(true);", operator_opt1)
time.sleep(3)
operator_opt1.click()
```

* Finds the private bus route element and retrieves its text.
```python
private_bus_routes = wait.until(EC.presence_of_element_located((By.XPATH, "//a[@title='Jaipur (Rajasthan) to Mathura']")))
private_bus_routes_text = private_bus_routes.text
```
* Clicks on the private bus route link using JavaScript.
```python
time.sleep(3)
driver.execute_script("arguments[0].click();", private_bus_routes)
```
* Sets the private route link to a specific URL.
```python
private_bus_route_link = "https://www.redbus.in/bus-tickets/jaipur-to-mathura?fromCityId=807&toCityId=747&fromCityName=Jaipur&toCityName=Mathura&busType=Any&srcCountry=null&destCountry=IND&onward=29-Jul-2024"
```
* Defines a function to insert bus route details into a MySQL database.
```python
def insert_bus_route(bus_details):
    global cursor, connection
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # SQL query to insert data
        query = """
        INSERT INTO bus_routes
        (route_name, route_link, busname, bustype, departing_time, duration,
        reaching_time, star_rating, price, seats_available)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Convert departing_time and reaching_time to datetime objects
        d_time = '29-Jul-2024 00:00'
        if (bus_details['departure_time']) != '':
            d_time = '29-Jul-2024 ' + bus_details['departure_time']

        a_time = '29-Jul-2024 00:00'
        if (bus_details['arrival_dt']) != '':
            a_time = bus_details['arrival_dt'] + bus_details['arrival_time']

        departing_time = datetime.strptime(d_time, '%d-%b-%Y %H:%M')
        reaching_time = datetime.strptime(a_time, '%d-%b-%Y %H:%M')

        # Prepare data for insertion
        data = (
            bus_details['bus_route_name'],
            bus_details['bus_route_link'],
            bus_details['bus_name'],
            bus_details['bus_type'],
            departing_time,
            bus_details['duration'],
            reaching_time,
            float(bus_details['rating'].split()[0]),  # Assuming rating is in format "4.5 stars"
            float(bus_details['ticket_fare'].replace('INR ', '').strip()),  # Remove 'INR'
            int(bus_details['seats_availability'].split()[0])  # Assuming format is "X seats available"
        )

        # Execute the query
        cursor.execute(query, data)
        connection.commit()
        print(f"Successfully inserted bus route: {bus_details['bus_route_name']}")

    except mysql.connector.Error as error:
        print(f"Failed to insert record into bus_routes table: {error}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
```
**Important Note: For _d_time_ and _a_time_ the dates need to be changed manually as per preference**
* Opens the private bus route link in the browser.
```python
driver.get(private_bus_route_link)
```
* Defines a function to scroll to the bottom of the page repeatedly to load more bus results.
```python
def scroll_and_load():
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Wait for page to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
```
* Calls the scroll_and_load function to load all bus items, then waits for all bus elements to be present.
```python
scroll_and_load()
time.sleep(5)
bus_items = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "bus-item")))
```
* Iterates through each bus item, extracts its details, prints them, and inserts them into the database.
```python
for bus in bus_items:
    try:
        # Check for next day arrival
        arrival_dt = '29-Jul-2024 '  # Default to same day
        next_day_element = bus.find_elements(By.CLASS_NAME, "next-day-dp-lbl")
        if next_day_element:
            arrival_dt = next_day_element[0].text + '-2024 '

        new_rating = '0.0'
        try:
            rating = bus.find_element(By.CLASS_NAME, "rating-sec").text
            if rating != 'New':
                new_rating = rating
        except NoSuchElementException:
            pass

        # Extract bus details
        bus_details = {
            'bus_route_name': private_bus_routes_text,
            'bus_route_link': private_bus_route_link,
            'bus_name': bus.find_element(By.CLASS_NAME, "travels").text,
            'bus_type': bus.find_element(By.CLASS_NAME, "bus-type").text,
            'departure_time': bus.find_element(By.CLASS_NAME, "dp-time").text,
            'arrival_time': bus.find_element(By.CLASS_NAME, "bp-time").text,
            'duration': bus.find_element(By.CLASS_NAME, "dur").text,
            'ticket_fare': bus.find_element(By.CLASS_NAME, "fare").text,
            'seats_availability': bus.find_element(By.CLASS_NAME, "seat-left").text,
            'rating': new_rating,
            'arrival_dt': arrival_dt
        }

        # Print the extracted details
        print(bus_details)

        # Insert into database
        time.sleep(1)
        insert_bus_route(bus_details)

    except Exception as e:
        print(f"Error extracting details for a bus: {str(e)}")
```
**Important Note: Manually set the _arrival_dt_ to the same date as a_time and d_time. Also, to handle new buses or buses with no rating, a default new_rating is set to 0.0 and by passes using try and except**

* Keeps the browser open, allowing the user to manually close it by pressing Ctrl+C. Ensures the driver quits properly when exiting.
```python
time.sleep(2)
print("Browser will stay open. Press Ctrl+C to exit.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    driver.quit()
```

## Streamlit Application

* Import necessary libraries for building the Streamlit app, connecting to the MySQL database, data manipulation with pandas, creating visualizations with Plotly, and handling date and time operations.
```python
import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
```
* Defines a function to establish a connection to the MySQL database. The @st.cache_resource decorator is used to cache the database connection, improving performance by reusing the connection.
```python
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
```
* Calls the get_connection function to establish and store the database connection.
```python
conn = get_connection()
```
* Defines a function to load all data from the bus_routes table in the database. The @st.cache_data decorator caches the loaded data to avoid reloading it multiple times.
```python
@st.cache_data
def load_data():
    query = "SELECT * FROM bus_routes"
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data
```
* Calls the load_data function to fetch data from the database and stores it in a pandas DataFrame.
```python
st.sidebar.header('Filter Bus Routes')
```
* Adds a header to the sidebar for filtering bus routes.
```python
st.sidebar.header('Filter Bus Routes')
```
* Creates sidebar widgets for filtering the bus routes by route name, bus name, bus type, star rating, and price range.
```python
route_name = st.sidebar.multiselect('Select Route', options=df['route_name'].unique())
busname = st.sidebar.multiselect('Select Bus Name', options=df['busname'].unique())
bustype = st.sidebar.multiselect('Select Bus Type', options=df['bustype'].unique())
star_rating = st.sidebar.slider('Minimum Star Rating', 0.0, 5.0, 0.0, 0.5)
price_range = st.sidebar.slider('Price Range',
                                min_value=float(df['price'].min()),
                                max_value=float(df['price'].max()),
                                value=(float(df['price'].min()), float(df['price'].max())))
```                               
* Calculates the minimum and maximum departing dates from the data and creates a date range filter in the sidebar.
```python
min_date = df['departing_time'].min().date()
max_date = df['departing_time'].max().date()

# Ensure the default end date doesn't exceed max_date
default_end_date = min(min_date + timedelta(days=18), max_date)

date_range = st.sidebar.date_input('Select Date Range',
                                   value=[min_date, default_end_date],
                                   min_value=min_date,
                                   max_value=max_date)
```


* Constructs an SQL query based on the selected filters. The params list is used to store the filter values to be passed to the query.
```python
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
```
* Executes the constructed SQL query with the filter parameters and fetches the filtered data, storing it in a pandas DataFrame.
```python
cursor = conn.cursor(dictionary=True)
cursor.execute(query, tuple(params))
filtered_data = cursor.fetchall()
filtered_df = pd.DataFrame(filtered_data)
```
* Displays the number of filtered bus routes and the filtered data in a table format.
```python
st.write(f'Showing {len(filtered_df)} bus routes')
st.dataframe(filtered_df)
```
* If the filtered data is not empty, creates and displays visualizations for:
   * Price distribution by bus name using a box plot.
   * Average rating by bus name using a bar chart.
   * Available seats by bus type using a bar chart.

```python
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
```
* Closes the database connection if it is still connected. This ensures that the connection is properly closed when the app finishes execution.

```python
if conn.is_connected():
    conn.close()
```

## Streamlit Interface
![Screenshot 2024-07-29 235642](https://github.com/user-attachments/assets/fbdec088-4d23-4f3f-9eba-bf6bb8ebf59a)
















