"""
CarbonIt Secure Messenger - Decentralized P2P Encrypted Chat
Copyright (C) 2025 Edwin Sam K Reju

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

DISCLAIMER: This software is intended for legal and ethical use only.
The authors and contributors are not responsible for any illegal,
malicious, or unauthorized use of this software. Users assume full
responsibility for complying with all applicable laws in their jurisdiction.
"""
import socket
import socks
import threading
import time
import os

# --- Configuration ---
SOCKS_HOST = '127.0.0.1'
SOCKS_PORT = 9050  # Tor Daemon SOCKS port (from torrc)
LISTEN_HOST = '127.0.0.1'
LISTEN_PORT = 6543 # Local port to receive Tor-forwarded traffic (from torrc)

# --- CRITICAL CHANGE: Update path to the 'msg' folder ---
# The path must be absolute or relative to where 3_start_messenger.bat is run
ONION_ADDRESS_FILE = r"msg\hostname"
CONTACT_FILE = r'msg\contact.txt'

# --- Global State ---
MY_ONION_ADDRESS = "" 
CONTACTS = {}

#contacts
def load_contacts():
    """Loads contacts from the contact.txt file into a dictionary."""
    contacts = {}
    if not os.path.exists(CONTACT_FILE):
        return contacts  # Return empty dict if file doesn't exist
        
    try:
        with open(CONTACT_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    # Split only on the first '='
                    name, onion = line.split('=', 1)
                    contacts[name.strip()] = onion.strip()
    except Exception as e:
        print(f"[ERROR] Could not read {CONTACT_FILE}: {e}")
    return contacts

# --- 1. The Listener (Receiving Thread) ---
def listener_thread():
    """Listens for incoming connections from other .onion addresses."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((LISTEN_HOST, LISTEN_PORT))
            s.listen(1)
            print(f"\n[LISTENER] Node is listening for incoming messages on port {LISTEN_PORT}...")
            
            while True:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if data:
                        print(f"\n\n--- INCOMING MESSAGE ---\n{data.decode('utf-8')}\n------------------------")
                        conn.sendall(b"ACK: Message received.")
                    print(f"\n(Type 'send <contact> <message>' or 'quit'): ", end="", flush=True)

        except Exception as e:
            print(f"\n[ERROR] Listener thread failed. Is port {LISTEN_PORT} free? Error: {e}")


# --- 2. The Sender (Client Function) ---
def send_message(target_onion, message):
    """Connects to a target .onion address via the Tor SOCKS proxy."""
    
    socks.set_default_proxy(socks.SOCKS5, SOCKS_HOST, SOCKS_PORT)
    s = socks.socksocket()
    
    try:
        print(f"[*] Connecting to {target_onion} via Tor...")
        s.connect((target_onion, LISTEN_PORT))
        
        s.sendall(message.encode('utf-8'))
        
        response = s.recv(1024)
        print(f"[SENT] Success. Target responded: {response.decode('utf-8')}")
        
    except socks.ProxyConnectionError:
        print("\n[ERROR] Proxy connection failed. Is the Tor Daemon running on 9050?")
    except ConnectionRefusedError:
        print("\n[ERROR] Connection refused. Is the target node's listener running?")
    except Exception as e:
        print(f"\n[ERROR] Failed to send message: {e}")
        
    finally:
        s.close()

# --- 3. Main Chat Loop ---
def main_chat_loop():
    global MY_ONION_ADDRESS, CONTACTS # <-- Add CONTACTS here
    
    # Read our own .onion address from the file
    try:
        # Use 'with open' to automatically handle closing the file
        with open(ONION_ADDRESS_FILE, 'r') as f:
            MY_ONION_ADDRESS = f.read().strip()
            print(f"\n[*] Your P2P Node ID (Share this!): {MY_ONION_ADDRESS}")
    except FileNotFoundError:
        print(f"\n[!] FATAL ERROR: Cannot find the 'hostname' file at {ONION_ADDRESS_FILE}. Is Tor running and did it create the 'msg' folder?")
        return
        
    # --- Load external contacts ---
    CONTACTS = load_contacts() # <-- Add this line

    print("\n--- P2P Anonymous Messenger Node Initialized ---")
    print(f"Current Contacts: {', '.join(CONTACTS.keys()) if CONTACTS else 'None. Use contact.py to add contacts!'}")
    
    while True:
        try:
            user_input = input(f"\n(Type 'send <contact> <message>' or 'quit'): ").strip()
            
            if user_input.lower() == 'quit':
                break
                
            if user_input.lower().startswith('send'):
                parts = user_input.split(maxsplit=2)
                if len(parts) < 3:
                    print("Usage: send <contact_name> <message>")
                    continue
                
                contact_name = parts[1].lower()
                message_content = parts[2]
                
                if contact_name not in CONTACTS:
                    print(f"Unknown contact: {contact_name}.")
                    continue

                target_onion = CONTACTS[contact_name]
                
                full_message = f"From: {MY_ONION_ADDRESS}\nMessage: {message_content}"
                send_message(target_onion, full_message)

        except KeyboardInterrupt:
            break

# --- Execution ---
if __name__ == "__main__":
    listener = threading.Thread(target=listener_thread, daemon=True)
    listener.start()
    
    main_chat_loop()
    
    print("\n[INFO] Messenger Node shutting down...")
    time.sleep(1)
