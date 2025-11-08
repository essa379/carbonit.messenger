# Anonymous P2P Messenger Node (Tor Hidden Service)

This project creates a simple, text-based, peer-to-peer messenger that routes all traffic over the Tor network using a dedicated v3 Hidden Service (.onion address). This ensures communication remains anonymous and bypasses common network restrictions (firewalls, NAT, port forwarding) by relying entirely on Tor's global infrastructure.

---

## 📁 Project Structure

```
msgtor/
├── tor/
│   ├── tor.exe
│   └── torrc                  # Tor configuration file
├── msg/                        # Contains 'hostname' (your .onion address) after setup
├── p2p_node.py                 # Main Python messenger script
├── 1_setup_env.bat             # One-time environment setup
├── 2_start_daemon.bat          # Starts the Tor daemon
└── 3_start_messenger.bat       # Starts the Python chat interface
```

---

## 🚀 Setup Instructions (First Time Only)

### Step 1: Download

Clone or download the entire **msgtor** folder.

### Step 2: Run Initial Setup

Navigate inside the `msgtor` folder and run:

```
1_setup_env.bat
```

This script creates a virtual environment and installs the required Python packages (like PySocks).

---

## ✅ How to Run Your Node

You need **two things running simultaneously** to chat:

1. The **Tor daemon**
2. The **Python messenger script**

---

## 🌀 Step 1: Start the Tor Daemon

The Tor daemon creates your `.onion` address and listens for incoming connections.
Run:

```
2_start_daemon.bat
```

A command window will open. Wait until you see:

```
Bootstrapped 100% (done): Done
```

Leave this window open.

---

## 🆔 Step 2: Get Your Node ID

After the daemon starts, it generates your unique P2P address.

1. Open the **msgtor/msg/** folder.
2. Find the file named **hostname**.
3. Open it in any text editor.
4. Copy the `.onion` address inside.

This is your **Node ID**. Share it with your friends.

---

## 👥 Step 3: Add Contacts

Before starting the messenger, add your friend's `.onion` address.

1. Open `p2p_node.py`.
2. Find the `CONTACTS` dictionary:

```python
CONTACTS = {
    # "friend_name": "friend_onion_address.onion"
}
```

3. Add your friend's ID:

```python
CONTACTS = {
    "alice": "YOUR_FRIENDS_ONION_ADDRESS.onion"
}
```

4. Save the file.

---

## 💬 Step 4: Start the Messenger

Make sure the Tor daemon is still running.
Run:

```
3_start_messenger.bat
```

You will see your own Node ID displayed and the client will start listening for incoming messages.

---

## 🗣️ How to Chat

Use the `send` command in the messenger interface.

### Command Format

```
send <contact_name> <your message here>
```

### Example

```
send alice Hey, can you hear me?
```

### Message Status

* **Sending**: The script will display

  ```
  Connecting to [onion address] via Tor...
  [SENT] Success.
  ```
* **Receiving**: Incoming messages appear instantly as they arrive.

---

## ✅ You're Ready!

Share your `.onion` ID, add contacts, and enjoy anonymous peer-to-peer texting over Tor.
