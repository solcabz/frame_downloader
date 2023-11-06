import requests
import pytz
from datetime import datetime
import os
import customtkinter as ctk
from CTkListbox import *
import tkinter as tk
import tkinter.messagebox as messagebox
import threading
from tkinter import PhotoImage

# Define a global queue to store asset IDs
asset_id_queue = []
asset_id_queue_processed = []  # List to keep track of processed assets

# Define tokens
token1 = "fio-u-LVdUIB1ObqZS724Ov-vgR8GaZmnf3ElrNmQ9JT2iT7UFzz1FvkFlgfk9xiyBcDun"
token2 = "fio-u-SdwWJMiLPq1cD5cHkBlhlBELKS8wo6PHevhJYDQ6Gs4WJvpeWOS0gdmJWKFJYJfT"

def get_asset_name_with_tokens(asset_id):
    for token in [token1, token2]:
        asset_name = get_asset_name(asset_id, token)
        if asset_name is not None:
            return asset_name
    return None

def get_all_comments_with_tokens(asset_id):
    for token in [token1, token2]:
        comments = get_all_comments(asset_id, token)
        if comments:
            return comments
    return []

def download_original_asset_with_tokens(asset_id, directory_path):
    for token in [token1, token2]:
        success = download_original_asset(asset_id, token, directory_path)
        if success:
            return True
    return False


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
                inserted_at = inserted_at.replace('T', ' ').split('.')[0]  # Remove 'T' and microseconds
                inserted_at = datetime.strptime(inserted_at, '%Y-%m-%d %H:%M:%S')
                inserted_at = inserted_at.replace(tzinfo=pytz.utc)
                inserted_at = inserted_at.astimezone(philippine_tz)
                inserted_at = inserted_at.strftime('%m/%d/%Y %I:%M %p')  # 12-hour format with AM/PM
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
            return True
        else:
            print(f"Error downloading original asset. Status code: {original_response.status_code}")
    else:
        print(f"Error getting asset information. Status code: {response.status_code}")
    return False

def create_folder(asset_name):
    # Create a folder with the asset name in 'C:\Downloads'
    folder_path = os.path.join('F:\\Downloads\\Frame_ioDownloadFiles', asset_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def add_asset_to_queue():
    asset_id = asset_id_entry.get()
    if asset_id:
        if asset_id in asset_id_queue:
            messagebox.showinfo("Duplicate Asset ID", "This asset ID is already in the queue.")
        else:
            asset_id_queue.append(asset_id)
            queue_listbox.insert(ctk.END, asset_id)
            asset_id_entry.delete(0, ctk.END)


def process_asset(asset_id):
    asset_name = get_asset_name_with_tokens(asset_id)

    if asset_name is not None:
        folder_path = create_folder(asset_name)

        download_success = download_original_asset_with_tokens(asset_id, folder_path)
        if download_success:
            all_comments = get_all_comments_with_tokens(asset_id)

            file_path = os.path.join(folder_path, f"{asset_name}_comments")
            save_comments_to_file(all_comments, file_path)

            result_label.configure(text=f"Assets saved to {folder_path}")
            asset_id_queue_processed.append(asset_id)  # Add processed asset to the list
        else:
            result_label.configure(text="Error downloading asset.")
    else:
        result_label.configure(text="Could not retrieve asset name. Files not saved.")


def open_folder():
    folder_path = result_label.cget("text")
    os.startfile(folder_path)


def set_result_label_text(text):
    result_label.configure(text=text)
    result_label.bind("<Button-1>", lambda e: open_folder)


def process_queue():
    loading_indicator.start()

    def process_assets():
        while asset_id_queue:
            asset_id = asset_id_queue.pop(0)
            success = process_asset(asset_id)
            progress_value = (len(asset_id_queue) + 1) / (len(asset_id_queue) + len(asset_id_queue_processed) + 1)
            loading_indicator.set(progress_value)
            mode = loading_indicator.cget("mode")
            if mode == "indeterminate":
                loading_indicator.configure(mode="determinate")

        loading_indicator.stop()

    def process_asset(asset_id):
        for token in [token1, token2]:  # Replace with your actual tokens (e.g., token1, token2)
            asset_name = get_asset_name(asset_id, token)

            if asset_name is not None:
                folder_path = create_folder(asset_name)

                download_success = download_original_asset(asset_id, token, folder_path)
                if download_success:
                    all_comments = get_all_comments(asset_id, token)

                    file_path = os.path.join(folder_path, f"{asset_name}_comments")
                    save_comments_to_file(all_comments, file_path)

                    result_label.configure(text=f"Assets saved to {folder_path}")
                    asset_id_queue_processed.append(asset_id)  # Add processed asset to the list
                    return True
                else:
                    result_label.configure(text="Error downloading asset.")
                    return False

        result_label.configure(text="Could not retrieve asset name. Files not saved.")
        return False

    processing_thread = threading.Thread(target=process_assets)
    processing_thread.start()

def remove_asset_from_queue():
    selected_index = queue_listbox.curselection()

    if selected_index is not None:
        selected_asset_id = queue_listbox.get(selected_index)
        asset_id_queue.remove(selected_asset_id)
        queue_listbox.delete(selected_index)


def clear_queue():
    queue_listbox.delete(0, ctk.END)  # Delete all items from the listbox
    asset_id_queue.clear()  # Clear the global asset_id_queue list

# Create window
window = ctk.CTk()
window.title('Iconiqlast Frame App')
window.geometry("610x490")

# Calculate center coordinates
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x_coordinate = (screen_width - 610) / 2  # Adjusted for the window width
y_coordinate = (screen_height - 490) / 2  # Adjusted for the window height

# Set window position
window.geometry(f"610x490+{int(x_coordinate)}+{int(y_coordinate)}")

#widget
# Check if the image file is loading correctly
frame1 = ctk.CTkFrame(window, width=450)
frame1.grid(row=1, column=0, padx=20, pady=20)

asset_id_entry = ctk.CTkEntry(frame1, width=350)
asset_id_entry.grid(row=0, column=0, padx=20, pady=20)

button = ctk.CTkButton(frame1,
                       text="Add Id to Queue",
                       command=add_asset_to_queue,
                       fg_color="#ED7D31",
                       hover_color="#FFA559",
                       text_color="#FAF0E6",
                       corner_radius=8
                       )
button.grid(row=0, column=1, padx=20, pady=20)

frame2 = ctk.CTkFrame(window, width=450)
frame2.grid(row=2, column=0, padx=20, pady=(0, 20))

button = ctk.CTkButton(frame2,
                       text="Process Queue",
                       fg_color="#ED7D31",
                       hover_color="#FFA559",
                       text_color="#FAF0E6",
                       corner_radius=8,
                       command=process_queue
                       )
button.grid(row=0, column=0, padx=10, pady=20, sticky="n")

button = ctk.CTkButton(frame2,
                       text="Remove from Queue",
                       fg_color="#ED7D31",
                       hover_color="#FFA559",
                       text_color="#FAF0E6",
                       corner_radius=8,
                       command=remove_asset_from_queue
                       )
button.grid(row=0, column=1, padx=10, pady=20, sticky="n")

button = ctk.CTkButton(frame2,
                       text="Remove All from Queue",
                       fg_color="#ED7D31",
                       hover_color="#FFA559",
                       text_color="#FAF0E6",
                       corner_radius=8,
                       command=clear_queue
                       )
button.grid(row=0, column=2, padx=10, pady=20, sticky="n")

queue_listbox = CTkListbox(frame2, width=520)
queue_listbox.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10))

loading_indicator = ctk.CTkProgressBar(window,
                                       mode='determinate',
                                       progress_color = '#ED7D31',
                                       orientation="horizontal"
                                       )
mode = loading_indicator.cget("mode")
print(f"The current mode is: {mode}")
value = loading_indicator.get()
loading_indicator.grid(row=3, column=0, pady=(0, 0))

result_label = ctk.CTkLabel(window, text="", cursor="hand2")
result_label.grid(row=4, column=0, padx=20, pady=(0, 20))

#run
window.mainloop()
