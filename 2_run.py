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
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext, filedialog
import socket
import socks
import threading
import time
import os
import queue
import subprocess
import json
import re
import math
import base64
import struct 
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
SOCKS_HOST = '127.0.0.1'
SOCKS_PORT = 9050
LISTEN_HOST = '127.0.0.1'
LISTEN_PORT = 6543
# Adjust these paths if your folder structure is different
CONTACT_FILE = os.path.join('msg', 'contact.txt')
ONION_ADDRESS_FILE = os.path.join('msg', 'hostname')

# --- PROTOCOL CONFIG ---
CHUNK_SIZE = 9037
HEADER_SIZE = 4           
NUM_PARALLEL_STREAMS = 73  # Number of concurrent circuits/threads for file transfer

# Windows-specific flag for hidden subprocesses
try:
    CREATE_NEW_CONSOLE = subprocess.CREATE_NEW_CONSOLE
except AttributeError:
    CREATE_NEW_CONSOLE = 0

# ==========================================
#            BACKEND LOGIC
# ==========================================

class MessengerBackend:
    def __init__(self, message_callback, status_callback, file_callback):
        self.message_callback = message_callback
        self.status_callback = status_callback
        self.file_callback = file_callback 
        self.stop_event = threading.Event()
        self.my_onion = "Initializing..."
        self.contacts = {}
        self.file_buffers = {}
        
        self.load_contacts()
        threading.Thread(target=self.load_onion_address, daemon=True).start()

    # --- Protocol Helper ---
    def _send_packet(self, sock, data_dict):
        json_data = json.dumps(data_dict).encode('utf-8')
        header = struct.pack('!I', len(json_data)) 
        sock.sendall(header + json_data)

    def _read_all(self, sock, n):
        data = b''
        sock.settimeout(1.0) 
        while len(data) < n:
            try:
                chunk = sock.recv(n - len(data))
                if not chunk:
                    raise ConnectionError("Socket closed during read.")
                data += chunk
            except socket.timeout:
                if self.stop_event.is_set():
                    raise ConnectionError("Thread stopped.")
                continue 
        return data

    # --- Tor and Contact Management ---
    def load_onion_address(self):
        self.status_callback("Connecting")
        attempts = 0
        while attempts < 5:
            if os.path.exists(ONION_ADDRESS_FILE):
                try:
                    with open(ONION_ADDRESS_FILE, 'r') as f:
                        address = f.read().strip()
                        if address.endswith(".onion"):
                            self.my_onion = address
                            self.status_callback("Ready")
                            return
                except Exception:
                    pass
            time.sleep(1)
            attempts += 1
        
        self.my_onion = "Tor Not Ready / Hostname Missing"
        self.status_callback("Error")

    def load_contacts(self):
        self.contacts = {}
        if os.path.exists(CONTACT_FILE):
            try:
                with open(CONTACT_FILE, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                parts = line.split('=', 2)
                                if len(parts) == 3:
                                    number, name, onion = parts
                                    self.contacts[number.strip()] = {'name': name.strip(), 'onion': onion.strip()}
                            except ValueError:
                                pass
            except Exception as e:
                print(f"[Backend] Error loading contacts: {e}")

    def save_contacts(self):
        try:
            os.makedirs(os.path.dirname(CONTACT_FILE), exist_ok=True)
            with open(CONTACT_FILE, 'w') as f:
                for number, details in self.contacts.items():
                    f.write(f"{number}={details['name']}={details['onion']}\n")
        except Exception as e:
            print(f"[Backend] Error saving contacts: {e}")

    def add_contact(self, name, onion):
        max_id = 0
        for pid in self.contacts:
            try:
                max_id = max(max_id, int(pid))
            except:
                pass
        new_id = str(max_id + 1)
        self.contacts[new_id] = {'name': name, 'onion': onion}
        self.save_contacts()
        return new_id

    def edit_contact(self, contact_id, new_name, new_onion):
        if contact_id in self.contacts:
            self.contacts[contact_id] = {'name': new_name, 'onion': new_onion}
            self.save_contacts()

    def delete_contact(self, contact_id):
        if contact_id in self.contacts:
            del self.contacts[contact_id]
            self.save_contacts()

    def start_listener(self):
        threading.Thread(target=self._listener_thread, daemon=True).start()

    def _listener_thread(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((LISTEN_HOST, LISTEN_PORT))
                s.listen(5)
                
                while not self.stop_event.is_set():
                    try:
                        s.settimeout(1.0)
                        conn, addr = s.accept()
                        threading.Thread(target=self._handle_incoming_connection, args=(conn, addr), daemon=True).start()
                    except socket.timeout:
                        continue
                    except Exception:
                        pass
        except Exception as e:
            self.status_callback("BindError")

    def _handle_incoming_connection(self, conn, addr):
        try:
            with conn:
                header = self._read_all(conn, HEADER_SIZE)
                msg_len = struct.unpack('!I', header)[0]
                if msg_len > 0:
                    full_payload = self._read_all(conn, msg_len)
                    msg = full_payload.decode('utf-8')
                    
                    try:
                        data = json.loads(msg)
                        self.message_callback(data) 
                        conn.sendall(b"ACK")
                    except json.JSONDecodeError:
                        conn.sendall(b"NACK_JSON")
        except Exception:
            pass 

    # --- NEW: Status Check ---
    def check_contact_status(self, target_onion, callback):
        """Attempts a quick connection to check if the remote host is reachable."""
        def _check():
            socks.set_default_proxy(socks.SOCKS5, SOCKS_HOST, SOCKS_PORT)
            s = socks.socksocket()
            try:
                s.settimeout(5) # Quick timeout
                s.connect((target_onion, LISTEN_PORT))
                callback(True) # Success: Online
            except Exception:
                callback(False) # Failure: Offline
            finally:
                s.close()
        threading.Thread(target=_check, daemon=True).start()

    # --- SENDING LOGIC (CHAT) ---
    def send_message(self, target_onion, message, success_callback, error_callback):
        data_packet = {
            "type": "chat",
            "sender_onion": self.my_onion,
            "content": message
        }

        def _send():
            socks.set_default_proxy(socks.SOCKS5, SOCKS_HOST, SOCKS_PORT)
            s = socks.socksocket()
            try:
                s.settimeout(60)
                s.connect((target_onion, LISTEN_PORT))
                self._send_packet(s, data_packet)
                resp = s.recv(1024).decode('utf-8')
                
                if resp == "ACK":
                    success_callback("Delivered")
                else:
                    error_callback(f"No ACK received: {resp}")
            except Exception as e:
                error_callback(f"Error: {str(e)[:50]}...")
            finally:
                s.close()
                
        threading.Thread(target=_send, daemon=True).start()

    # --- UPDATED: SENDING LOGIC (PARALLEL FILE TRANSFER) ---
    
    def _send_chunk_worker(self, chunk_index, total_chunks, file_path, file_name, target_onion, 
                           progress_callback, error_callback, file_offset_map, progress_lock, total_sent):
        socks.set_default_proxy(socks.SOCKS5, SOCKS_HOST, SOCKS_PORT)
        s = socks.socksocket()
        s.settimeout(60) 
        
        try:
            s.connect((target_onion, LISTEN_PORT))
            
            chunk_start_offset = file_offset_map[chunk_index]
            with open(file_path, 'rb') as f:
                f.seek(chunk_start_offset)
                chunk_data = f.read(CHUNK_SIZE)

            if not chunk_data:
                raise Exception("Failed to read chunk data.")

            encoded_chunk = base64.b64encode(chunk_data).decode('utf-8')
            
            packet = {
                "type": "file_chunk", "sender_onion": self.my_onion, "filename": file_name,
                "file_id": file_path, "chunk_index": chunk_index, "total_chunks": total_chunks, "data": encoded_chunk
            }
            
            self._send_packet(s, packet)
            
            resp = s.recv(1024).decode('utf-8')
            if resp != "ACK":
                raise Exception(f"No ACK received for chunk {chunk_index}.")
                
            with progress_lock:
                total_sent[0] += 1
                progress_callback(total_sent[0], total_chunks)

        except Exception as e:
            error_callback(f"Parallel File Send Error (Chunk {chunk_index}): {str(e)[:50]}...")
        finally:
            s.close()


    def send_file(self, target_onion, file_path, success_callback, error_callback, progress_callback):
        
        file_name = os.path.basename(file_path)
        
        def _send_file_thread():
            try:
                file_size = os.path.getsize(file_path)
                total_chunks = math.ceil(file_size / CHUNK_SIZE)
                
                self.file_callback(f"FILE SYSTEM: Starting parallel file transfer: {file_name} ({total_chunks} chunks)")
                
                file_offset_map = {i: i * CHUNK_SIZE for i in range(total_chunks)}
                progress_lock = threading.Lock()
                total_sent = [0]
                chunk_indices = list(range(total_chunks))

                with ThreadPoolExecutor(max_workers=NUM_PARALLEL_STREAMS) as executor:
                    futures = [
                        executor.submit(
                            self._send_chunk_worker, chunk_index, total_chunks, file_path, file_name, 
                            target_onion, progress_callback, error_callback, file_offset_map, progress_lock, total_sent
                        )
                        for chunk_index in chunk_indices
                    ]
                    for future in futures:
                        future.result() 

                if total_sent[0] == total_chunks:
                    success_callback("Parallel file transfer complete")
                else:
                    error_callback(f"Parallel transfer failed. Only {total_sent[0]}/{total_chunks} chunks sent.")
                    
            except Exception as e:
                error_callback(f"Critical Parallel File Error: {str(e)[:50]}...")
        
        threading.Thread(target=_send_file_thread, daemon=True).start()

    # --- UPDATED: RECEIVING LOGIC (with Throttling) ---
    def process_file_chunk(self, data):
        sender_onion = data['sender_onion']
        file_id = data['file_id']
        chunk_index = data['chunk_index']
        total_chunks = data['total_chunks']
        file_name = data['filename']
        encoded_data = data['data']
        transfer_key = f"{sender_onion}_{file_id}"
        
        if transfer_key not in self.file_buffers:
            self.file_buffers[transfer_key] = {
                'name': file_name, 'total': total_chunks, 'received': set(),
                'chunks': {}, 'start_time': time.time(), 'last_percent': 0 
            }
            self.file_callback(f"FILE SYSTEM: Starting file receipt: {file_name} ({total_chunks} chunks)")

        buffer = self.file_buffers[transfer_key]
        
        if chunk_index not in buffer['received']:
            buffer['chunks'][chunk_index] = base64.b64decode(encoded_data)
            buffer['received'].add(chunk_index)
            
            progress = len(buffer['received'])
            current_percent = round(progress / buffer['total'] * 100)
            
            # Throttle progress reporting to 5% intervals or start/end
            if progress == buffer['total'] or current_percent >= buffer['last_percent'] + 5 or progress == 1:
                buffer['last_percent'] = current_percent
                # Sending percentage update for the dedicated status label
                self.file_callback(f"Receiving {file_name}: {current_percent}% ({progress}/{buffer['total']})")


        if len(buffer['received']) == buffer['total']:
            try:
                sorted_chunks = [buffer['chunks'][i] for i in range(buffer['total'])]
                file_content = b''.join(sorted_chunks)
                
                save_dir = "received_files"
                os.makedirs(save_dir, exist_ok=True)
                
                safe_file_name = "".join(c for c in file_name if c.isalnum() or c in ('.', '_', '-')).strip()
                if not safe_file_name: safe_file_name = "received_file"
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(save_dir, f"{timestamp}_{safe_file_name}")
                
                with open(save_path, 'wb') as f:
                    f.write(file_content)
                
                del self.file_buffers[transfer_key]
                self.file_callback(f"File received successfully: {file_name}\nSaved to: {save_path}")
                self.message_callback({'type': 'system', 'content': f"RECEIVED FILE: {file_name} -> {os.path.basename(save_path)}"})

            except Exception as e:
                self.file_callback(f"File reassembly error for {file_name}: {e}")

# ==========================================
#              GUI IMPLEMENTATION
# ==========================================

class CarbonItApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CarbonIt Secure Messenger")
        self.root.geometry("950x650")
        self.root.configure(bg="#101010") 
        
        self.colors = {
            "bg_dark": "#050505", "bg_panel": "#121212", "fg_primary": "#00e5ff", "fg_secondary": "#b0b0b0",
            "fg_text": "#ffffff", "accent_hover": "#00acc1", "bubble_me": "#006064", "bubble_peer": "#263238",
            "error": "#ff5252", "success": "#00ff00"
        }
        
        self.setup_styles() # **FIXED: Now points to implemented method**
        
        self.msg_queue = queue.Queue()
        self.tor_status = "Disconnected"
        self.current_target_onion = None
        self.current_target_name = None 
        self.file_transfer_in_progress = False
        
        # --- NEW: Status Check Variables ---
        self.status_refresh_id = None 
        self.contact_is_online = False 
        # -----------------------------------

        self.setup_ui()

        self.backend = MessengerBackend(self.on_incoming_data, self.update_tor_status, self.on_file_transfer_status)
        self.backend.start_listener()

        self.update_contact_list()
        self.check_tor_status_loop()
        self.process_message_queue()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("TFrame", background=self.colors["bg_dark"])
        style.configure("Panel.TFrame", background=self.colors["bg_panel"], relief="flat")
        
        style.configure("TLabel", background=self.colors["bg_panel"], foreground=self.colors["fg_text"], font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"), foreground=self.colors["fg_primary"])
        style.configure("Status.TLabel", font=("Consolas", 9), foreground=self.colors["fg_secondary"])
        
        style.configure("TButton", font=("Segoe UI", 9, "bold"), background=self.colors["bg_panel"], 
                        foreground=self.colors["fg_primary"], borderwidth=1, relief="solid")
        style.map("TButton", background=[("active", self.colors["accent_hover"])], foreground=[("active", "white")])
        
        style.configure("Send.TButton", background=self.colors["fg_primary"], foreground="black", borderwidth=0)
        style.map("Send.TButton", background=[("active", "white")])

    def setup_ui(self):
        # === TOP BAR (Status) ===
        top_bar = ttk.Frame(self.root, style="Panel.TFrame", padding=10)
        top_bar.pack(fill=tk.X, pady=(0, 2))
        
        # Status Light
        self.status_canvas = tk.Canvas(top_bar, width=12, height=12, bg=self.colors["bg_panel"], highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT, padx=(0, 8))
        self.status_light = self.status_canvas.create_oval(2, 2, 10, 10, fill="red", outline="")
        
        self.lbl_status = ttk.Label(top_bar, text="Disconnected", style="Status.TLabel")
        self.lbl_status.pack(side=tk.LEFT)
        
        self.lbl_onion = tk.Label(top_bar, text="Initializing Address...", 
                                  bg=self.colors["bg_panel"], fg=self.colors["fg_primary"], 
                                  font=("Consolas", 11, "bold"), cursor="hand2")
        self.lbl_onion.pack(side=tk.LEFT, padx=20, fill=tk.X, expand=True)
        self.lbl_onion.bind("<Button-1>", self.copy_onion)
        
        ttk.Button(top_bar, text="⟳ RESTART TOR", command=self.refresh_tor).pack(side=tk.RIGHT)

        # === MAIN CONTENT AREA ===
        content = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.colors["bg_dark"], sashwidth=4, relief="flat")
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- LEFT PANEL (Contacts) ---
        left_panel = ttk.Frame(content, style="Panel.TFrame", width=250)
        content.add(left_panel, stretch="never")
        
        ttk.Label(left_panel, text="CONTACTS", style="Header.TLabel").pack(fill=tk.X, padx=10, pady=10)
        
        self.contact_list = tk.Listbox(left_panel, bg="#0a0a0a", fg="white", 
                                       selectbackground=self.colors["fg_primary"], selectforeground="black",
                                       borderwidth=0, highlightthickness=0, font=("Segoe UI", 11), activestyle="none")
        self.contact_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.contact_list.bind("<<ListboxSelect>>", self.on_contact_select)
        
        btn_frame = ttk.Frame(left_panel, style="Panel.TFrame")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(btn_frame, text="+ ADD", command=self.add_contact_ui, width=6).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(btn_frame, text="EDIT", command=self.edit_contact_ui, width=6).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(btn_frame, text="DEL", command=self.remove_contact_ui, width=6).pack(side=tk.RIGHT)

        # --- RIGHT PANEL (Chat) ---
        right_panel = ttk.Frame(content, style="Panel.TFrame")
        content.add(right_panel, stretch="always")
        
        # Header Frame to hold text and status dot (NEW/RESTORED)
        header_frame = ttk.Frame(right_panel, style="Panel.TFrame")
        header_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # Status Dot Canvas for Contact
        self.contact_status_canvas = tk.Canvas(header_frame, width=12, height=12, bg=self.colors["bg_panel"], highlightthickness=0)
        self.contact_status_canvas.pack(side=tk.RIGHT, padx=(10, 0))
        # Initial color: gray (unknown)
        self.contact_status_light = self.contact_status_canvas.create_oval(2, 2, 10, 10, fill="#505050", outline="") 

        # Chat Header Label
        self.chat_header = ttk.Label(header_frame, text="Select a contact to encrypt communications", style="Header.TLabel")
        self.chat_header.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Chat History
        self.chat_log = scrolledtext.ScrolledText(right_panel, bg="#000000", fg="#e0e0e0", 
                                                  font=("Segoe UI", 11), borderwidth=0, state='disabled',
                                                  wrap=tk.WORD, insertbackground="white")
        self.chat_log.pack(fill=tk.BOTH, expand=True, padx=20)
        
        self.chat_log.tag_config("me", foreground="#ffffff", background=self.colors["bubble_me"], 
                                 lmargin1=100, lmargin2=100, rmargin=10, justify="right", spacing1=5, spacing3=5)
        self.chat_log.tag_config("peer", foreground="#ffffff", background=self.colors["bubble_peer"], 
                                 lmargin1=10, lmargin2=10, rmargin=100, justify="left", spacing1=5, spacing3=5)
        self.chat_log.tag_config("system", foreground=self.colors["fg_secondary"], justify="center", font=("Segoe UI", 9, "italic"))
        self.chat_log.tag_config("timestamp_me", foreground="gray", justify="right", font=("Consolas", 8))
        self.chat_log.tag_config("timestamp_peer", foreground="gray", justify="left", font=("Consolas", 8))

        # File transfer status/progress bar
        self.file_status_label = ttk.Label(right_panel, text="", style="Status.TLabel", foreground=self.colors["fg_primary"])
        self.file_status_label.pack(fill=tk.X, padx=20, pady=(5, 0))
        
        # Input Area
        input_area = ttk.Frame(right_panel, style="Panel.TFrame", padding=20)
        input_area.pack(fill=tk.X)
        
        self.msg_entry = tk.Entry(input_area, bg="#1c1c1c", fg="white", font=("Segoe UI", 11), 
                                  insertbackground=self.colors["fg_primary"], relief="flat")
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        self.msg_entry.bind("<Return>", self.send_message)
        
        ttk.Button(input_area, text="FILE", command=self.send_file_ui).pack(side=tk.LEFT, padx=(0, 5))
        self.btn_send = ttk.Button(input_area, text="SEND >", style="Send.TButton", command=self.send_message)
        self.btn_send.pack(side=tk.RIGHT)

    # ==========================================
    #                 LOGIC
    # ==========================================

    def check_tor_status_loop(self):
        # ... (Omitted: Tor status loop - this runs periodically) ...
        status = self.tor_status
        color = "#333333" 
        text = "Initializing..."
        
        if status == "Ready":
            color = self.colors["success"] 
            text = "SECURE CONNECTION ESTABLISHED"
            self.lbl_onion.config(text=f"{self.backend.my_onion}")
        elif status == "Connecting":
            color = "#ffa500" 
            text = "Connecting to Tor Network..."
        elif status == "Error" or status == "BindError":
            color = self.colors["error"] 
            text = "Tor Connection Failed"
            self.lbl_onion.config(text="Tor Address Unavailable")
            
        self.status_canvas.itemconfig(self.status_light, fill=color)
        self.lbl_status.config(text=text)
        
        self.root.after(2000, self.check_tor_status_loop)

    def update_tor_status(self, status):
        self.tor_status = status

    def process_message_queue(self):
        try:
            while True:
                msg_type, content = self.msg_queue.get_nowait()
                if msg_type == "data":
                    self.process_incoming_data_dict(content)
                elif msg_type == "system":
                    self.add_bubble(content, "system")
                elif msg_type == "file_status":
                    # Only update the dedicated label for progress updates
                    self.file_status_label.config(text=content)

        except queue.Empty:
            pass
        self.root.after(100, self.process_message_queue)

    def on_incoming_data(self, data_dict):
        self.msg_queue.put(("data", data_dict))

    def process_incoming_data_dict(self, data):
        try:
            if data.get('type') == 'chat':
                self.parse_incoming_chat(data['content'])
            
            elif data.get('type') == 'file_chunk':
                self.backend.process_file_chunk(data)
                
            elif data.get('type') == 'system':
                self.add_bubble(data['content'], 'system')
                
        except Exception as e:
            self.add_bubble(f"ERROR processing incoming data: {e}", "system")

    def parse_incoming_chat(self, full_msg):
        try:
            lines = full_msg.split('\nMessage:', 1)
            sender_onion = lines[0].replace("From:", "").strip()
            text = lines[1].strip()
            
            sender_name = next((c['name'] for c in self.backend.contacts.values() if c['onion'] == sender_onion), "Unknown")
            
            self.add_bubble(f"{sender_name}:\n{text}", "peer")
            
            # If we successfully received a chat, the contact is online
            if not self.contact_is_online:
                self.update_contact_online_status(True) 
        except:
            self.add_bubble(f"Raw Data:\n{full_msg}", "peer")

    def add_bubble(self, text, tag):
        ts = datetime.now().strftime("%H:%M")
        self.chat_log.config(state='normal')
        
        ts_tag = "timestamp_me" if tag == "me" else "timestamp_peer"
        self.chat_log.insert(tk.END, f"\n{ts}\n", ts_tag)
        
        padding = "   "
        self.chat_log.insert(tk.END, f"{padding}{text}{padding}", tag)
        self.chat_log.insert(tk.END, "\n", tag)
        
        self.chat_log.see(tk.END)
        self.chat_log.config(state='disabled')

    # --- UPDATED: FILE STATUS LOGIC (Filtering) ---
    def on_file_transfer_status(self, message):
        # 1. Always update the dedicated status label
        self.msg_queue.put(("file_status", message))
        
        # 2. Add only START, END, or ERROR messages to the chat log
        if "ERROR" in message.upper() or "SUCCESSFULLY" in message.upper() or "COMPLETE" in message.upper() or "STARTING" in message.upper():
             if "SUCCESSFULLY" in message.upper() or "COMPLETE" in message.upper():
                 self.file_transfer_in_progress = False
                 # If file transfer succeeds, confirm status is online
                 if not self.contact_is_online:
                     self.update_contact_online_status(True)
             if "ERROR" in message.upper():
                 self.file_transfer_in_progress = False
                 # If transfer fails, assume offline and restart check
                 self.update_contact_online_status(False)
                 self.start_status_refresh_loop()

             self.add_bubble(f"FILE SYSTEM: {message}", "system")

    def send_message(self, event=None):
        if self.tor_status != "Ready":
            messagebox.showerror("Error", "Tor is not connected.")
            return
            
        text = self.msg_entry.get().strip()
        if not text or not self.current_target_onion:
            return
            
        self.msg_entry.delete(0, tk.END)
        self.add_bubble(text, "me")
        
        full_msg = f"From: {self.backend.my_onion}\nMessage: {text}"
        
        def success(msg): 
            self.msg_queue.put(("system", f"✓ {msg}"))
            # If successful, confirm the status is online
            if not self.contact_is_online:
                self.update_contact_online_status(True)

        def fail(err): 
            self.msg_queue.put(("system", f"✗ {err}"))
            # If sending fails, assume offline and restart the check loop
            self.update_contact_online_status(False) 
            self.start_status_refresh_loop()

        self.backend.send_message(self.current_target_onion, full_msg, success, fail)

    def send_file_ui(self):
        if not self.current_target_onion:
            messagebox.showwarning("Warning", "Please select a contact first.")
            return

        if self.file_transfer_in_progress:
            messagebox.showwarning("Warning", "A file transfer is already in progress.")
            return

        file_path = filedialog.askopenfilename(title="Select File to Send")
        if file_path:
            if os.path.getsize(file_path) > 50 * 1024 * 1024: 
                messagebox.showerror("Error", "File size limit is 50MB for reliable transfer.")
                return

            self.file_transfer_in_progress = True
            
            def success(msg): self.msg_queue.put(("system", f"✓ {msg}"))
            def fail(err): self.msg_queue.put(("system", f"✗ {err}"))
                
            def progress(current, total):
                current_percent = round(current/total*100)
                status_text = f"Sending {os.path.basename(file_path)}: {current_percent}% ({current}/{total}) | Streams: {NUM_PARALLEL_STREAMS}"
                self.msg_queue.put(("file_status", status_text))

            self.backend.send_file(self.current_target_onion, file_path, success, fail, progress)

    # --- Contact Status Logic (NEW/RESTORED) ---
    def start_status_refresh_loop(self):
        """Starts or restarts the periodic contact status check every 37 seconds."""
        if self.status_refresh_id is not None:
            self.root.after_cancel(self.status_refresh_id)
            self.status_refresh_id = None
            
        if not self.current_target_onion:
            return

        def refresh_check():
            if self.contact_is_online:
                self.chat_header.config(text=f"ENCRYPTED CHANNEL: {self.current_target_name}")
                return

            if self.tor_status == "Ready" and self.current_target_onion and self.current_target_name:
                self.chat_header.config(text=f"ENCRYPTED CHANNEL: {self.current_target_name} (Checking status...)")
                self.contact_status_canvas.itemconfig(self.contact_status_light, fill="#505050") # Gray (Checking)

                self.backend.check_contact_status(self.current_target_onion, self.update_contact_online_status)

            self.status_refresh_id = self.root.after(37000, refresh_check) 

        refresh_check() 

    def update_contact_online_status(self, is_online):
        """Callback to update the contact's status dot color and header text."""
        self.contact_is_online = is_online
        
        if self.current_target_name:
            color = self.colors["success"] if is_online else self.colors["error"]
            self.contact_status_canvas.itemconfig(self.contact_status_light, fill=color)
            self.chat_header.config(text=f"ENCRYPTED CHANNEL: {self.current_target_name}") 
        else:
            self.chat_header.config(text="Select a contact to encrypt communications")
    # --- End Contact Status Logic ---


    def update_contact_list(self):
        self.contact_list.delete(0, tk.END)
        for cid, data in self.backend.contacts.items():
            self.contact_list.insert(tk.END, f"[{cid}] {data['name']}")

    def on_contact_select(self, event):
        selection = self.contact_list.curselection()
        if selection:
            idx = selection[0]
            text = self.contact_list.get(idx)
            cid = text.split(']')[0].replace('[', '')
            data = self.backend.contacts.get(cid)
            
            if data:
                self.current_target_onion = data['onion']
                self.current_target_name = data['name']
                
                # Reset state flags
                self.contact_is_online = False
                
                self.chat_header.config(text=f"ENCRYPTED CHANNEL: {data['name']}")
                self.chat_log.config(state='normal')
                self.chat_log.delete(1.0, tk.END)
                self.chat_log.config(state='disabled')
                self.file_status_label.config(text="")
                
                self.add_bubble(f"Secure channel established with {data['name']}", "system")
                
                # Start the status check loop
                self.start_status_refresh_loop()

    def add_contact_ui(self):
        name = simpledialog.askstring("Add", "Contact Name:")
        if name:
            onion = simpledialog.askstring("Add", "Onion Address:")
            if onion and onion.endswith(".onion") and len(onion) in [22, 62]:
                self.backend.add_contact(name, onion)
                self.update_contact_list()
            else:
                messagebox.showerror("Error", "Invalid Onion Address (Must end in .onion and be correct length)")

    def edit_contact_ui(self):
        selection = self.contact_list.curselection()
        if not selection: return
        idx = selection[0]
        text = self.contact_list.get(idx)
        cid = text.split(']')[0].replace('[', '')
        data = self.backend.contacts.get(cid)
        
        new_name = simpledialog.askstring("Edit", "Name:", initialvalue=data['name'])
        if new_name:
            new_onion = simpledialog.askstring("Edit", "Onion:", initialvalue=data['onion'])
            if new_onion:
                self.backend.edit_contact(cid, new_name, new_onion)
                self.update_contact_list()

    def remove_contact_ui(self):
        selection = self.contact_list.curselection()
        if not selection: return
        idx = selection[0]
        text = self.contact_list.get(idx)
        cid = text.split(']')[0].replace('[', '')
        
        if messagebox.askyesno("Delete", "Remove this contact?"):
            self.backend.delete_contact(cid)
            self.update_contact_list()

    def copy_onion(self, event):
        if self.backend.my_onion:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.backend.my_onion)
            self.root.update()
            original_text = self.lbl_onion.cget("text")
            self.lbl_onion.config(text="COPIED TO CLIPBOARD!", fg="white")
            self.root.after(1500, lambda: self.lbl_onion.config(text=original_text, fg=self.colors["fg_primary"]))

    def refresh_tor(self):
        threading.Thread(target=self.backend.load_onion_address, daemon=True).start()
        
        if self.tor_status != "Ready" and os.path.exists("2_start_daemon.bat"):
            subprocess.Popen("2_start_daemon.bat", creationflags=CREATE_NEW_CONSOLE)

    def on_closing(self):
        self.backend.stop_event.set()
        if self.status_refresh_id is not None:
            self.root.after_cancel(self.status_refresh_id)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CarbonItApp(root)
    root.mainloop()
