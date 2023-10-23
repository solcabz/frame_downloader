import requests
import pytz
from datetime import datetime
import os
import tkinter as tk
from tkinter import filedialog

def get_asset_name(asset_id, token):
    url = f"https://api.frame.io/v2/assets/{asset_id}"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        asset_data = response.json()
        asset_name = asset_data.get("name")

        # Get the base name without the extension
        base_name, _ = os.path.splitext(asset_name)

        return base_name
    else:
        print(f"Error fetching asset details. Status code: {response.status_code}")
        return None

def get_all_comments(asset_id, token):
    url = f"https://api.frame.io/v2/assets/{asset_id}/comments"
    all_comments = []
    headers = {"Authorization": f"Bearer {token}"}
    page = 1

    while True:
        query = {"page": page}
        response = requests.get(url, headers=headers, params=query)

        if response.status_code == 200:
            data = response.json()
            comments = data
            all_comments.extend(comments)

            if len(comments) > 0:
                page += 1
            else:
                break
        else:
            print(f"Error fetching comments. Status code: {response.status_code}")
            break

    return all_comments

def save_comments_to_file(comments, file_path):
    philippine_tz = pytz.timezone('Asia/Manila')

    # Remove '.jpg' from asset_name
    asset_name = file_path.replace('.jpg', '')

    with open(f"{asset_name}.txt", 'w', encoding='utf-8') as file:
        for comment in comments:
            owner = comment['owner']['name']
            text = comment['text']
            inserted_at = comment.get('inserted_at')
            file.write(f"{owner}: {text}")
            if inserted_at:
                inserted_at = inserted_at.replace('T', ' ').split('.')[0] # Remove 'T' and microseconds
                inserted_at = datetime.strptime(inserted_at, '%Y-%m-%d %H:%M:%S')
                inserted_at = inserted_at.replace(tzinfo=pytz.utc)
                inserted_at = inserted_at.astimezone(philippine_tz)
                inserted_at = inserted_at.strftime('%m/%d/%Y %I:%M %p') # 12-hour format with AM/PM
                file.write(f" (Date: {inserted_at} )")
            file.write("\n")

def download_original_asset(asset_id, token, directory_path):
    url = f"https://api.frame.io/v2/assets/{asset_id}"

    query = {
        "include_deleted": "true",
        "type": "file"
    }

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers, params=query)

    if response.status_code == 200:
        data = response.json()
        original_url = data['original']
        asset_name = data['name']  # Get the asset name

        # Download the original asset
        original_response = requests.get(original_url)

        if original_response.status_code == 200:
            file_path = os.path.join(directory_path, f"{asset_name}")  # Save in the specified directory
            with open(file_path, 'wb') as f:
                f.write(original_response.content)
            print(f"Original asset downloaded successfully as {file_path}")
        else:
            print(f"Error downloading original asset. Status code: {original_response.status_code}")
    else:
        print(f"Error getting asset information. Status code: {response.status_code}")

def get_asset_comments():
    asset_id = asset_id_entry.get()
    token = "fio-u-KJkLXQoOUTNECbWLrqUrOttbODo24OHQshin_4TpJy3t8_G8L1KOpx0SR-MkcqkP"
    asset_name = get_asset_name(asset_id, token)

    if asset_name is not None:
        # Prompt user to choose a directory
        directory_path = filedialog.askdirectory()

        if directory_path:
            # Download original asset
            download_original_asset(asset_id, token, directory_path)

            # Get comments
            all_comments = get_all_comments(asset_id, token)

            # Save comments to file
            file_path = os.path.join(directory_path, f"{asset_name}_comments")
            save_comments_to_file(all_comments, file_path)

            # Display results
            result_label.config(text=f"Assets saved to {file_path}")
        else:
            result_label.config(text="No directory selected. Files not saved.")
    else:
        result_label.config(text="Could not retrieve asset name. Files not saved.")

# Create a simple GUI using Tkinter
root = tk.Tk()
root.title("Frame.io Assets Downloader")

# Labels and Entry fields
tk.Label(root, text="Asset ID:").pack(pady=(10, 0))
asset_id_entry = tk.Entry(root)
asset_id_entry.pack(pady=(0, 10))

# Button to trigger the comment download
download_button = tk.Button(root, text="Download Comments", command=get_asset_comments)
download_button.pack(pady=(10, 20))

# Label to display result
result_label = tk.Label(root, text="")
result_label.pack()

root.mainloop()
