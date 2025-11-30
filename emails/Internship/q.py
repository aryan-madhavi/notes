import os
import requests
import time

# Define the webhook URL
webhook_url = "https://xomov61802aupvs.app.n8n.cloud/webhook/dcfa33e8-4085-4486-9b05-a483adc12972"

# Get the current directory (where the script is located)
current_dir = os.path.dirname(os.path.abspath(__file__))

# List of specific files to upload
target_files = [
    "12-06-2025.pdf",
    "01-07-2025.pdf",
    "14-07-2025.pdf",
    "12-09-2025.pdf"
]

# Function to extract sorting key (month, day) from filename
def sort_key(filename):
    try:
        base = filename[:-4]  # remove '.pdf'
        day, month, year = base.split('-')
        return (int(month), int(day))
    except Exception:
        return (0, 0)

# Filter only files that exist in the directory from the target list
existing_files = [f for f in target_files if os.path.isfile(os.path.join(current_dir, f))]

# Sort the filtered files by month, then day
existing_files.sort(key=sort_key)

# Iterate through sorted files and send POST request
for filename in existing_files:
    file_path = os.path.join(current_dir, filename)
    with open(file_path, "rb") as f:
        files = {"file": (filename, f, "application/pdf")}
        try:
            response = requests.post(webhook_url, files=files)
            print(f"Uploaded '{filename}': Status {response.status_code}")
            print("Response content:")
            print(response.text)
            print("------")  # Separator
        except Exception as e:
            print(f"Failed to upload '{filename}': {e}")
            print("------")
    time.sleep(5)  # Wait 5 seconds before the next request
