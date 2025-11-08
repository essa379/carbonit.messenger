Anonymous P2P Messenger Node (Tor Hidden Service)This project creates a simple, text-based, peer-to-peer messenger that routes all traffic over the Tor network using a dedicated v3 Hidden Service (.onion address).This ensures communication remains anonymous and bypasses common network restrictions (like firewalls and NAT/port forwarding) by relying entirely on the Tor network infrastructure.Project Structuremsgtor/
├── tor/
│   ├── tor.exe
│   └── torrc (Configuration file)
├── msg/            <-- Contains 'hostname' (your .onion address) after setup
├── p2p_node.py     <-- The main Python messenger script
├── 1_setup_env.bat <-- Initial one-time environment setup
├── 2_start_daemon.bat <-- Starts the Tor process (required to be running)
└── 3_start_messenger.bat <-- Starts the Python chat interface
Setup Instructions (First Time Only)Download: Clone or download the entire msgtor folder.Run Setup: Navigate inside the msgtor folder and run the batch file:1_setup_env.bat
This script creates a virtual environment and installs the required Python library (PySocks).How to Run Your NodeYou need two things running simultaneously to chat: the Tor daemon and the Python messenger script.Step 1: Start the Tor DaemonThe Tor daemon creates your .onion address and listens for incoming connections.Run the batch file:2_start_daemon.bat
A command prompt window will open. You must wait for the bootstrapping process to complete. Look for the line:Bootstrapped 100% (done): Done
Leave this window open.Step 2: Get Your Node IDOnce the daemon starts, it automatically generates your unique P2P address.Look inside the new msgtor/msg folder.Open the file named hostname with a text editor (like Notepad).Copy the long .onion address. This is your unique Node ID. Share this with your friends!Step 3: Add Contacts (The Python Script)Before starting the messenger, you need to add your friend's Node ID into your contact list.Open p2p_node.py in a text editor.Find the CONTACTS dictionary around line 18:CONTACTS = {
    # Add your friend's .onion address here
    # "friend_name": "friend_onion_address.onion" 
}
Add your friend's address using a simple name (e.g., "alice") as the key:CONTACTS = {
    "alice": "YOUR_FRIENDS_ONION_ADDRESS.onion" 
}
Save and close the file.Step 4: Start the Messenger ClientMake sure the Tor Daemon window (2_start_daemon.bat) is still running.Run the final batch file:3_start_messenger.bat
The messenger interface will display your own Node ID and start listening for messages.How to ChatOnce the messenger is running, use the send command at the prompt.Command Format:send <contact_name> <your message here>
Example:(Type 'send <contact> <message>' or 'quit'): send alice Hey, can you hear me?
Sending Status: The script will show Connecting to [onion address] via Tor... and finally [SENT] Success. if the message went through.Receiving Status: Incoming messages will pop up instantly on the screen when they arrive.
