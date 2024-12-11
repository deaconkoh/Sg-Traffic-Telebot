import requests
import pandas as pd
import os
import re
import folium
from folium import PolyLine
from tabulate import tabulate
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def get_traffic_info(headers, payload={}):
    traffic_info_url = "https://datamall2.mytransport.sg/ltaodataservice/TrafficIncidents"

    response = requests.request("GET", traffic_info_url, headers=headers, data=payload)
    r_dict = response.json()
    traffic_info_df = pd.DataFrame(r_dict["value"])
    traffic_info_df["Time"] = traffic_info_df["Message"].apply(lambda x: x.split()[0])
    traffic_info_df["Message"] = traffic_info_df["Message"].apply(lambda x: ' '.join(x.split()[1:]))
    traffic_info_df['Expressway'] = traffic_info_df['Message'].apply(lambda x: re.search(r'\b(TPE|SLE|AYE|ECP|PIE|CTE|BKE)\b', x).group(0) if re.search(r'\b(TPE|SLE|AYE|ECP|PIE|CTE|BKE)\b', x) else "Others")
    
    location = ["AYE", "CTE", "TPE", "BKE", "PIE", "SLE", "ECP", "Others"]
    filtered_dfs = {i: traffic_info_df[traffic_info_df["Expressway"] == i] for i in location}
    return filtered_dfs

def get_travel_time(headers, payload={}):
    travel_timing_url = "https://datamall2.mytransport.sg/ltaodataservice/EstTravelTimes"
    response = requests.request("GET", travel_timing_url, headers=headers, data=payload)
    r_dict = response.json()
    temp_df = pd.DataFrame(r_dict["value"])
    
    temp_df["Path"] = temp_df["StartPoint"] + " -> " + temp_df["EndPoint"]
    expressways = ["AYE", "CTE", "TPE", "BKE", "PIE", "SLE", "ECP"]
    filtered_dfs = {name: temp_df[temp_df["Name"] == name] for name in expressways}
    
    return filtered_dfs


def load_map(filtered_dfs, user_input):
    singapore_map = folium.Map(location=[1.3521, 103.8198], zoom_start=12)
    
    filtered_data = filtered_dfs[user_input]

    # Plot Incident Markers
    for _, row in filtered_data.iterrows():
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=f"{row['Message']} ({row['Time']})",
            tooltip=row["Expressway"],
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(singapore_map)

    # Save the map
    singapore_map.save(f"{user_input}_expressway_map.html")
    

def save_map_as_image(map_file, screenshot_file="map_screenshot.png"):
    # Set up Selenium with headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(executable_path="/Filepath/To/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Open the map file in the browser
    driver.get(f"file://{os.path.abspath(map_file)}")
    driver.set_window_size(1200, 800)  # Adjust the size as needed

    # Take a screenshot
    driver.save_screenshot(screenshot_file)
    driver.quit()

    return screenshot_file


def traffic_info_as_text(filtered_dfs, expressway):
    """Format traffic data as plain text without latitude and longitude, with proper numbering."""
    if expressway in filtered_dfs and not filtered_dfs[expressway].empty:
        df = filtered_dfs[expressway].reset_index(drop=True)  # Reset index for proper numbering
        result = [f"Traffic Info for {expressway}:\n"]
        for idx, row in df.iterrows():
            incident_info = (
                f"{idx + 1}. Time: {row['Time']}\n"
                f"   Incident: {row['Message']}\n"
            )
            result.append(incident_info)
        return "\n".join(result)
    else:
        return f"No traffic information available for {expressway}."
    
def travel_time_as_text(filtered_dfs, expressway):
    """Format travel time data as plain text with proper numbering."""
    if expressway in filtered_dfs and not filtered_dfs[expressway].empty:
        df = filtered_dfs[expressway].reset_index(drop=True)  # Reset index for proper numbering
        result = [f"Estimated Travel Time for {expressway}:\n"]
        for idx, row in df.iterrows():
            travel_info = (
                f"{idx + 1}. Route: {row['StartPoint']} -> {row['EndPoint']}\n"
                f"   Estimated Time: {row['EstTime']} minute{'s' if row['EstTime'] > 1 else ''}\n"
            )
            result.append(travel_info)
        return "\n".join(result)
    else:
        return f"No travel time information available for {expressway}."