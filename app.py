import os
import tkinter as tk
from tkinter import messagebox
import requests
import threading
import subprocess

# Function to set target temperature
def set_target_temp():
    target_temp = entry.get()
    if target_temp:
        try:
            response = requests.post('http://localhost:5000/set_target_temp', json={'target_temp': target_temp})
            if response.status_code == 200:
                result = response.json()
                messagebox.showinfo("Success", result['message'])
            else:
                messagebox.showerror("Error", "Failed to set target temperature")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    else:
        messagebox.showwarning("Input Error", "Please enter a valid target temperature")

# Function to create and run the tkinter GUI
def run_tkinter_gui():
    root = tk.Tk()
    root.title("Temperature Control")

    # Set the window to fullscreen
    root.attributes('-fullscreen', True)

    label = tk.Label(root, text="Enter Target Temperature (°C):")
    label.pack(pady=10)

    global entry
    entry = tk.Entry(root)
    entry.pack(pady=5)

    button = tk.Button(root, text="Set Temperature", command=set_target_temp)
    button.pack(pady=20)

    root.mainloop()

if __name__ == '__main__':
    log_file = 'app.log'

    if os.path.exists(log_file) and os.access(log_file, os.W_OK):
        print(f"Write permissions are available for {log_file}")
    else:
        print(f"No write permissions for {log_file} or the file does not exist")

    with app.app_context():
        db.create_all()
        threading.Thread(target=save_temp_to_db, daemon=True).start()

    # Set the DISPLAY environment variable
    os.environ['DISPLAY'] = ':1'

    # Verify the DISPLAY environment variable
    if os.environ.get('DISPLAY') == ':1':
        print("DISPLAY environment variable is set correctly")

    # Check if the display is available
    try:
        subprocess.run(['xrandr'], check=True)
        print("Display is available")
    except subprocess.CalledProcessError:
        print("Display is not available")
        exit(1)

    # Start the tkinter GUI in a separate thread
    threading.Thread(target=run_tkinter_gui, daemon=True).start()

    app.run(host='0.0.0.0', port=5000, debug=False)