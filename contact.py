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
import sys
import os

# --- Configuration ---
CONTACT_FILE = r'msg\contact.txt'


def load_contacts():
    """
    Loads contacts from contact.txt.
    New Format: { '1': {'name': 'pojit', 'onion': '...'}, ... }
    """
    contacts = {}
    if not os.path.exists(CONTACT_FILE):
        return contacts  # Return empty dict if file doesn't exist
        
    try:
        with open(CONTACT_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    # New format: number=name=onion
                    number, name, onion = line.split('=', 2)
                    contacts[number.strip()] = {'name': name.strip(), 'onion': onion.strip()}
                except ValueError:
                    print(f"[WARNING] Skipping malformed line: {line}")
    except Exception as e:
        print(f"[ERROR] Could not read {CONTACT_FILE}: {e}")
    return contacts

def save_contacts(contacts):
    """
    Saves the contacts dictionary back to file.
    New Format: number=name=onion
    """
    try:
        with open(CONTACT_FILE, 'w') as f:
            for number, details in contacts.items():
                f.write(f"{number}={details['name']}={details['onion']}\n")
    except Exception as e:
        print(f"[ERROR] Could not write to {CONTACT_FILE}: {e}")

def print_usage():
    """Prints the help message."""
    print("\n--- CarbonIt Contact Manager ---")
    print("Usage: python contact.py <command> [args]")
    print("\nCommands:")
    print("  list (or fetch)         - Show all contacts")
    print("  add                     - Interactively add a new contact")
    print("  remove <number>         - Remove a contact by its number")
    print("  change <number> <new_onion> - Update a contact's onion address")

def add_contact_interactive(contacts):
    """Interactively prompts user to add a new contact."""
    print("[*] Starting new contact wizard...")
    
    # 1. Get Name
    name = ""
    while not name:
        name = input("Enter contact name: ").strip().lower()
        if not name:
            print("Name cannot be empty.")
            
    # 2. Get Onion
    onion = ""
    while not onion:
        onion = input(f"Enter {name}'s onion address: ").strip()
        if not onion:
            print("Onion address cannot be empty.")
        if not onion.endswith(".onion"):
            print("Warning: Address does not end with .onion")
            
    # Check for duplicates
    for details in contacts.values():
        if details['name'] == name:
            print(f"[ERROR] A contact with the name '{name}' already exists.")
            return
        if details['onion'] == onion:
            print(f"[ERROR] This onion address is already in your contacts.")
            return

    # Find the next available ID
    max_id = 0
    for number_str in contacts.keys():
        try:
            max_id = max(max_id, int(number_str))
        except ValueError:
            pass # Skip invalid number keys
            
    new_id = str(max_id + 1)
    
    # Add to dictionary and save
    contacts[new_id] = {'name': name, 'onion': onion}
    save_contacts(contacts)
    
    print("\n--- Contact Added! ---")
    print(f"ID     : {new_id}")
    print(f"Name   : {name}")
    print(f"Address: {onion}")
    print("------------------------")

def main():
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()
    contacts = load_contacts()

    if command == 'add':
        if len(sys.argv) != 2:
            print("Usage: python contact.py add (no other arguments needed)")
            return
        add_contact_interactive(contacts)

    elif command == 'remove':
        if len(sys.argv) != 3:
            print("Usage: python contact.py remove <number>")
            return
        number_to_remove = sys.argv[2]
        if number_to_remove in contacts:
            removed_name = contacts[number_to_remove]['name']
            del contacts[number_to_remove]
            save_contacts(contacts)
            print(f"Removed contact: [{number_to_remove}] {removed_name}")
        else:
            print(f"[ERROR] Contact ID '{number_to_remove}' not found.")

    elif command == 'change':
        if len(sys.argv) != 4:
            print("Usage: python contact.py change <number> <new_onion>")
            return
        number_to_change = sys.argv[2]
        new_onion = sys.argv[3]
        if number_to_change in contacts:
            contacts[number_to_change]['onion'] = new_onion
            save_contacts(contacts)
            print(f"Updated onion address for contact ID {number_to_change}.")
        else:
            print(f"[ERROR] Contact ID '{number_to_change}' not found.")

    elif command in ('list', 'fetch'):
        if not contacts:
            print("No contacts found. Use 'python contact.py add' to start.")
            return
        print("\n--- Contact List ---")
        # Find max length for nice formatting
        max_len_name = max(len(d['name']) for d in contacts.values()) + 2
        max_len_num = max(len(n) for n in contacts.keys()) + 2
        
        for number, details in contacts.items():
            name = details['name']
            onion = details['onion']
            print(f"[{number:<{max_len_num}}] {name:<{max_len_name}}: {onion}")

    else:
        print(f"[ERROR] Unknown command: '{command}'")
        print_usage()

if __name__ == "__main__":
    main()
