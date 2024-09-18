import tkinter as tk
from tkinter import messagebox, scrolledtext
import socket
from concurrent.futures import ThreadPoolExecutor
from zk import ZK
import json

# Function to check if a specific port is open on an IP
def is_port_open(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)  # Timeout of 1 second for each connection
    try:
        s.connect((ip, port))
        s.close()
        return True
    except Exception:
        return False

# Function to scan the network for devices on the given port in a specific range
def scan_for_device_on_port(port, start_ip, end_ip):
    try:
        start_ip_suffix = int(start_ip.split('.')[-1])
        end_ip_suffix = int(end_ip.split('.')[-1])
        network_prefix = ".".join(start_ip.split('.')[:-1])

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for i in range(start_ip_suffix, end_ip_suffix + 1):
                ip = f"{network_prefix}.{i}"
                futures.append(executor.submit(is_port_open, ip, port))

            for future in futures:
                ip = f"{network_prefix}.{start_ip_suffix + futures.index(future)}"
                if future.result():
                    return ip
    except Exception as e:
        messagebox.showerror("Error", f"Error in IP range: {e}")
    return None

# Function to fetch raw data from the eSSL Magnum device
def fetch_raw_data(ip_address, log_area):
    zk = ZK(ip_address, port=4370, timeout=5, password=123)  # Replace with actual password if necessary
    try:
        conn = zk.connect()
        conn.disable_device()
        attendance = conn.get_attendance()
        raw_data = []
        for log in attendance:
            raw_data.append(log.__dict__)

        conn.enable_device()
        conn.disconnect()

        with open('attendance_logs.json', 'w') as json_file:
            json.dump(raw_data, json_file, indent=4, default=str)

        log_area.insert(tk.END, f"Fetched {len(raw_data)} raw logs from {ip_address}\n")
        return raw_data
    except Exception as e:
        messagebox.showerror("Error", f"Error: {e}")
        return None

# Function to remove user by ID from the device
def remove_user(ip_address, user_id):
    zk = ZK(ip_address, port=4370, timeout=5, password=123)  # Replace with actual password if necessary
    try:
        conn = zk.connect()
        conn.disable_device()

        # Delete the user based on the user_id
        conn.delete_user(user_id=user_id)

        conn.enable_device()
        conn.disconnect()

        messagebox.showinfo("Success", f"User {user_id} has been successfully removed from the device.")
    except Exception as e:
        messagebox.showerror("Error", f"Error: {e}")

# Tkinter GUI Application
def run_app():
    window = tk.Tk()
    window.title("eSSL Magnum Network Scanner and Data Fetcher")

    # IP Range Input
    tk.Label(window, text="Start IP address:").grid(row=0, column=0, padx=10, pady=5)
    start_ip_entry = tk.Entry(window)
    start_ip_entry.grid(row=0, column=1, padx=10, pady=5)
    start_ip_entry.insert(0, "192.168.1.33")

    tk.Label(window, text="End IP address:").grid(row=1, column=0, padx=10, pady=5)
    end_ip_entry = tk.Entry(window)
    end_ip_entry.grid(row=1, column=1, padx=10, pady=5)
    end_ip_entry.insert(0, "192.168.1.254")

    # Log Area
    log_area = scrolledtext.ScrolledText(window, width=50, height=10)
    log_area.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    # Function to scan for device and fetch data
    def scan_and_fetch():
        start_ip = start_ip_entry.get()
        end_ip = end_ip_entry.get()
        log_area.insert(tk.END, f"Scanning network from {start_ip} to {end_ip}...\n")
        ip_address = scan_for_device_on_port(4370, start_ip, end_ip)
        if ip_address:
            log_area.insert(tk.END, f"Device found at {ip_address}. Fetching data...\n")
            fetch_raw_data(ip_address, log_area)
        else:
            messagebox.showerror("Error", f"No eSSL Magnum device found in the IP range {start_ip} to {end_ip}.")

    # Function to remove user
    def remove_user_by_id():
        start_ip = start_ip_entry.get()
        end_ip = end_ip_entry.get()
        user_id = user_id_entry.get()
        if user_id:
            ip_address = scan_for_device_on_port(4370, start_ip, end_ip)
            if ip_address:
                remove_user(ip_address, user_id)
            else:
                messagebox.showerror("Error", "No eSSL Magnum device found to remove the user.")
        else:
            messagebox.showerror("Error", "Please provide a valid user ID.")

    # Buttons
    fetch_button = tk.Button(window, text="Scan and Fetch Data", command=scan_and_fetch)
    fetch_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    # Remove user section
    tk.Label(window, text="Enter User ID to remove:").grid(row=3, column=0, padx=10, pady=5)
    user_id_entry = tk.Entry(window)
    user_id_entry.grid(row=3, column=1, padx=10, pady=5)

    remove_button = tk.Button(window, text="Remove User", command=remove_user_by_id)
    remove_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    window.mainloop()

# Run the app
if __name__ == "__main__":
    run_app()
