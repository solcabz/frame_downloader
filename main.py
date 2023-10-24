import requests
import pytz
from datetime import datetime
import os
import tkinter as tk
from tkinter import filedialog

# Define a global queue to store asset IDs
asset_id_queue = []

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

def create_folder(asset_name):
    # Create a folder with the asset name in 'C:\Downloads'
    folder_path = os.path.join('F:\\Downloads\Frame_ioDownloadFiles'  ,asset_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def add_asset_to_queue():
    asset_id = asset_id_entry.get()
    if asset_id:
        asset_id_queue.append(asset_id)
        queue_listbox.insert(tk.END, asset_id)
        asset_id_entry.delete(0, tk.END)

def process_queue():
    token_1 = "fio-u-LVdUIB1ObqZS724Ov-vgR8GaZmnf3ElrNmQ9JT2iT7UFzz1FvkFlgfk9xiyBcDun"
    token_2 = "fio-u-SdwWJMiLPq1cD5cHkBlhlBELKS8wo6PHevhJYDQ6Gs4WJvpeWOS0gdmJWKFJYJfT"

    while asset_id_queue:
        asset_id = asset_id_queue.pop(0)
        asset_name = get_asset_name(asset_id, token_1)

        if asset_name is None:
            asset_name = get_asset_name(asset_id, token_2)

        if asset_name is not None:
            folder_path = create_folder(asset_name)

            download_original_asset(asset_id, token_1, folder_path)  # You can use token_2 here if needed
            all_comments = get_all_comments(asset_id, token_1)  # You can use token_2 here if needed

            file_path = os.path.join(folder_path, f"{asset_name}_comments")
            save_comments_to_file(all_comments, file_path)

            result_label.config(text=f"Assets saved to {file_path}")
        else:
            result_label.config(text="Could not retrieve asset name. Files not saved.")

def remove_asset_from_queue():
    selected_index = queue_listbox.curselection()

    if selected_index:
        selected_asset_id = queue_listbox.get(selected_index)
        asset_id_queue.remove(selected_asset_id)
        queue_listbox.delete(selected_index)

def clear_queue():
    queue_listbox.delete(0, tk.END)  # Delete all items from the listbox
    asset_id_queue.clear()  # Clear the global asset_id_queue list

# Create a simple GUI using Tkinter
root = tk.Tk()
root.geometry('650x480')
root.resizable(width=False, height=False)
root.title("Frame.io Assets Downloader")
root.configure(bg='#3D3A3A')

color1 = '#020f12'
color2 = '#F4A125'
color3 = '#EABF7F'
color4 = '#BE7303'
color5 = 'BLACK'

# Labels and Entry fields
tk.Label(root, text="Asset ID:", background='#3D3A3A', foreground='WHITE').pack(pady=(10, 0))
asset_id_entry = tk.Entry(root, width=18, font=('Arial', 12), background='#D9D9D9')
asset_id_entry.pack(pady=(0, 10))

button_frame = tk.Frame(root, background='#3D3A3A')
button_frame.pack()

# Button to add asset to queue
add_to_queue_button = tk.Button(button_frame,
                                background=color2,
                                activebackground=color3,
                                width='18', height=2,
                                highlightbackground=color4,
                                highlightthickness=2,
                                highlightcolor='WHITE',
                                border=0,
                                cursor='hand2',
                                font=('Arial'),
                                text="Add to Queue",
                                command=add_asset_to_queue)
add_to_queue_button.pack(side='left', padx=(0, 5))

# Button to remove asset from queue
remove_from_queue_button = tk.Button(button_frame,
                                     background=color2,
                                     activebackground=color3,
                                     width='18', height=2,
                                     highlightbackground=color4,
                                     highlightthickness=2,
                                     highlightcolor='WHITE',
                                     border=0,
                                     cursor='hand2',
                                     font=('Arial'),
                                     text="Remove from Queue",
                                     command=remove_asset_from_queue)
remove_from_queue_button.pack(side='right', padx=(5, 0))


tk.Label(root, text="Asset ID List:", background='#3D3A3A', foreground='WHITE').pack(pady=(10, 0))
# Listbox to display the queue
queue_listbox = tk.Listbox(root, width=70, background='#D9D9D9')
queue_listbox.pack(pady=(10, 20))

button_frame2 = tk.Frame(root, background='#3D3A3A')
button_frame2.pack()

# Button to start processing queue
process_queue_button = tk.Button(button_frame2,
                                 background=color2,
                                 activebackground=color3,
                                 width='18', height=2,
                                 highlightbackground=color4,
                                 highlightthickness=2,
                                 highlightcolor='WHITE',
                                 border=0,
                                 cursor='hand2',
                                 font=('Arial'),
                                 text="Process Queue",
                                 command=process_queue)
process_queue_button.pack(side='left', padx=(5, 5))

# Button to clear the queue
clear_queue_button = tk.Button(button_frame2,
                               background=color2,
                               activebackground=color3,
                               width='18', height=2,
                               highlightbackground=color4,
                               highlightthickness=2,
                               highlightcolor='WHITE',
                               border=0,
                               cursor='hand2',
                               font=('Arial'),
                               text="Clear All Queue",
                               command=clear_queue)
clear_queue_button.pack(side='right', padx=(5, 5))

# Label to display result
result_label = tk.Label(root, text="", foreground='WHITE', background='#3D3A3A')
result_label.pack()

root.mainloop()