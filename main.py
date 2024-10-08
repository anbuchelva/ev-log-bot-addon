import requests
import json
from dotenv import load_dotenv
import os
import base64

load_dotenv()

scooter_id = os.getenv("scooter_id")
api_token = os.getenv("api_token")
webhook_url = os.getenv("webhook_url")


def get_ride_details(scooter_id, api_token, limit=None, sort_order="asc"):
    url = f"https://cerberus.ather.io/api/v1/triplogs?scooter={scooter_id}&sort=start_time_tz%20{sort_order}"
    if limit is not None:
        url += f"&limit={limit}"
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching trip logs for scooter {scooter_id}: {response.status_code}")
        return None


def update_ghseet_data(rides):
    if not rides:  # Check if rides is empty
        print("No ride data to process.")
        return

    get_id_url = f"{webhook_url}?getids=true"
    get_id_response = requests.get(get_id_url)
    ids_from_sheet = get_id_response.json()
    ids_from_sheet_set = set(ids_from_sheet)

    ids_from_ride_data = [ride["id"] for ride in rides]

    # Find new IDs that are not in ids_from_sheet
    new_ids = sorted([id for id in ids_from_ride_data if id not in ids_from_sheet_set])
    print("New IDs:", new_ids)

    # Extract dictionary values for new IDs
    new_ride_data = sorted([ride for ride in rides if ride["id"] in new_ids], key=lambda x: x["id"])
    # print("New ride data:", new_ride_data)

    if not new_ride_data:  # Check if there are new rides to send
        print("No new ride data to send.")
        return

    telegram_alert = True

    for ride in new_ride_data:
        data = json.dumps(ride)
        encoded_data = base64.b64encode(data.encode()).decode()
        params = {"rideData": encoded_data, "telegramAlert": str(telegram_alert).lower()}

        try:
            response = requests.post(webhook_url, json=params)
            response.raise_for_status()
            print(f"Response from Google Apps Script for ride ID {ride['id']} {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Request error for ride ID {ride['id']}")


ride_data = get_ride_details(scooter_id, api_token, 20, "desc")
update_ghseet_data(ride_data)
