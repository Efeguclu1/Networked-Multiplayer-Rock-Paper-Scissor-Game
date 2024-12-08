# Alp Onder Yener, Ada Yilmaz, Efe Guclu

import socket
import threading
import tkinter as tk
import time

class ClientApp:
    def __init__(self, master): ### GUI SIDE. What GUI components these are for is stated in their names.
        self.master = master
        self.master.title("Client")

        tk.Label(master, text="IP Address:").pack()
        self.ip_entry = tk.Entry(master)
        self.ip_entry.pack()

        tk.Label(master, text="Port:").pack()
        self.port_entry = tk.Entry(master)
        self.port_entry.pack()

        self.connect_button = tk.Button(master, text="Connect", command=self.connect_to_server)
        self.connect_button.pack()

        tk.Label(master, text="Name:").pack()
        self.name_entry = tk.Entry(master)
        self.name_entry.pack()

        self.send_name_button = tk.Button(master, text="Enter Game", state="disabled", command=self.send_name)
        self.send_name_button.pack()

        self.messages = tk.Text(master, state="disabled", height=15, width=50) # Where messages from the server will be displayed
        self.messages.pack()

        self.leaderboard = tk.Text(master, state="disabled", height=15, width=25) # Where leaderboard will be displayed
        self.leaderboard.pack()

        game_frame = tk.Frame(master)
        game_frame.pack(pady=10)

        self.rock_button = tk.Button(game_frame, text="R", state="disabled", command=lambda: self.send_choice("R"))
        self.rock_button.pack(side=tk.LEFT, padx=5)
        self.paper_button = tk.Button(game_frame, text="P", state="disabled", command=lambda: self.send_choice("P"))
        self.paper_button.pack(side=tk.LEFT, padx=5)
        self.scissors_button = tk.Button(game_frame, text="S", state="disabled", command=lambda: self.send_choice("S"))
        self.scissors_button.pack(side=tk.LEFT, padx=5)

        self.leave_button = tk.Button(master, text="Leave", state="disabled", command=self.leave_game)
        self.leave_button.pack()

        self.client_socket = None

        self.name = ""

    def leave_game(self): #leave_game button is clicked
        try:
            self.client_socket.send("LEAVE".encode("utf-8")) #inform the server that this client wishes to leave
        
        finally:
            self.client_socket.close() #close the connection to the server
            #self.log_message("Disconnected from the server.")

            self.leaderboard.config(state="normal")
            self.leaderboard.delete(1.0, tk.END)
            self.leaderboard.yview(tk.END) #auto-scroll
            self.leaderboard.config(state="disabled")

            self.connect_button.config(state="normal") #reset the UI for a new connection
            self.send_name_button.config(state="disabled")
            self.name_entry.config(state="normal")
            self.leave_button.config(state="disabled")

    def log_message(self, message): #send message to log
        self.messages.config(state="normal")
        self.messages.insert(tk.END, message + "\n")
        self.messages.yview(tk.END) #auto-scroll
        self.messages.config(state="disabled")

    def leaderboard_update(self, message): # Update leaderboard
        self.leaderboard.config(state="normal")
        self.leaderboard.delete(1.0, tk.END)
        self.leaderboard.insert(tk.END, message[11:])
        self.leaderboard.yview(tk.END) #auto-scroll
        self.leaderboard.config(state="disabled")


    def receive_messages(self): # Recieve messages from the server
        while True:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                
                if "LEADERBOARD" not in message: # if the incoming message is not an update of the leaderboard
                    self.log_message(message)

                    if "You are in the game!" in message:
                        self.name_entry.config(state="disabled")
                        self.send_name_button.config(state="disabled")
                        self.leave_button.config(state="normal")
                        

                    elif "Name already taken" in message:
                        self.send_name_button.config(state="normal") #re-enable the send name button for another attempt
                        #do not disable name entry; allow re-entry

                    elif "The room is full" in message:
                        self.name_entry.config(state="disabled")
                        self.send_name_button.config(state="disabled")
                        self.connect_button.config(state="disabled")
                        self.leave_button.config(state="normal")

                    elif "Go!" in message:
                        self.name_entry.config(state="disabled")
                        self.leave_button.config(state="normal")

                        self.rock_button.config(state="normal")
                        self.paper_button.config(state="normal")
                        self.scissors_button.config(state="normal")

                        self.client_socket.send(f"GAME".encode("utf-8"))

                    elif "Spectate" in message:
                        self.client_socket.send(f"GAME".encode("utf-8"))

                        self.rock_button.config(state="disabled")
                        self.paper_button.config(state="disabled")
                        self.scissors_button.config(state="disabled")

                    
                else:
                    self.leaderboard_update(message)

            except:
                self.log_message("Disconnected from server.")
                break
    
    def connect_to_server(self): # Connect to server
        port = int(self.port_entry.get())
        ip = self.ip_entry.get()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.client_socket.connect((ip, port))
            self.log_message("Connected to the server.")
            self.name_entry.config(state="normal") #ensure name entry is enabled upon connection
            self.send_name_button.config(state="normal") 
            self.connect_button.config(state="disabled")

            threading.Thread(target=self.receive_messages, daemon=True).start()
        
        except Exception as e:
            self.log_message(f"Failed to connect: {e}")

    def send_name(self): # Send the name of the player
        name = self.name_entry.get()
        self.name = name
        if name:
            self.client_socket.send(f"NAME:{name}".encode("utf-8"))
            self.send_name_button.config(state="disabled") #disable to prevent multiple sends before response
    
    def send_choice(self, choice): # Send the gesture of choice
        self.client_socket.send(f"CHOICE:{choice}".encode("utf-8"))
            
        self.rock_button.config(state="disabled")
        self.paper_button.config(state="disabled")
        self.scissors_button.config(state="disabled")

root = tk.Tk()
root.title("Rock Paper Scissors")
app = ClientApp(root)
root.mainloop()
