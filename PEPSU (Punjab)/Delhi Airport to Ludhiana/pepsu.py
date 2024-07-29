
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import mysql.connector
from datetime import datetime

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

# Database connection configuration
db_config = {
    'host': 'localhost',  # Usually 'localhost' for phpMyAdmin
    'user': 'root',
    'password': '',
    'database': 'redbus'
}

from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException

# Initialize the webdriver
driver = webdriver.Chrome()  # or whichever browser you're using

# Navigate to the RedBus website
driver.get("https://www.redbus.in/")

wait = WebDriverWait(driver, 5)  # wait up to 5 seconds
view_all = wait.until(EC.presence_of_element_located((By.XPATH, "//a[@href='https://www.redbus.in/online-booking/rtc-directory']")))
driver.execute_script("arguments[0].scrollIntoView(true);", view_all)
view_all.click()
time.sleep(3)

driver.get("https://www.redbus.in/online-booking/rtc-directory")
time.sleep(5)

click_element(driver, "//a[@href='/online-booking/pepsu']", timeout=5)
time.sleep(7)

operator_opt1 = wait.until(EC.presence_of_element_located((By.XPATH, "//div[normalize-space()='2']")))
driver.execute_script("arguments[0].scrollIntoView(true);", operator_opt1)
time.sleep(3)
operator_opt1.click()

PEPSU_bus_routes = wait.until(EC.presence_of_element_located((By.XPATH, "//a[@title='Delhi Airport to Ludhiana']")))
PEPESU_bus_routes_text = PEPSU_bus_routes.text

time.sleep(3)

driver.execute_script("arguments[0].click();", PEPSU_bus_routes)

PEPSU_route_link = "https://www.redbus.in/bus-tickets/delhi-airport-to-ludhiana?fromCityId=94113&toCityId=736&fromCityName=Delhi%20Airport&toCityName=Ludhiana&busType=Any&srcCountry=IND&destCountry=IND&onward=26-Jul-2024"

# by operator
# Function to insert data into the database

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
        d_time = '26-Jul-2024 00:00'
        if (bus_details['departure_time']) != '':
            d_time = '26-Jul-2024 ' + bus_details['departure_time']

        a_time = '26-Jul-2024 00:00'
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


driver.get(PEPSU_route_link)

pepsu_operator = wait.until(EC.presence_of_element_located((By.XPATH, "//ul[5]//li[1]//label[1]")))
driver.execute_script("arguments[0].scrollIntoView(true);", pepsu_operator)
pepsu_operator.click()
time.sleep(1)

# Function to scroll and load more buses
def scroll_and_load():
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Wait for page to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


# Scroll to load all buses
scroll_and_load()
time.sleep(5)
bus_items = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "bus-item")))

for bus in bus_items:
    try:
        # Check for next day arrival
        arrival_dt = '26-Jul-2024 '  # Default to same day
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
            'bus_route_name': PEPESU_bus_routes_text,
            'bus_route_link': PEPSU_route_link,
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

time.sleep(2)

# Keep the browser open
print("Browser will stay open. Press Ctrl+C to exit.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    driver.quit()
