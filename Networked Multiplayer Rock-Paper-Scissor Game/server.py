# Alp Onder Yener, Ada Yilmaz, Efe Kilickaya, Efe Guclu

import socket
import threading
import tkinter as tk
import time
from collections import defaultdict
from copy import deepcopy

class ServerApp: # Server class
    def __init__(self, master):
        self.master = master # Setup GUI
        self.master.title("Server")

        tk.Label(master, text="Port:").pack()  # port entry
        self.port_entry = tk.Entry(master)
        self.port_entry.pack()

        self.start_button = tk.Button(  # start server button
            master, text="Start Server", command=self.start_server
        )
        self.start_button.pack()

        self.system_messages = tk.Text( # Where system messages will be displayed
            master, state="disabled", height=10, width=50
        )  # display messages
        self.system_messages.pack()

        tk.Label(master, text="Players:").pack()  # display player list / leaderboard
        self.players_list = tk.Text(master, state="disabled", height=10, width=50)
        self.players_list.pack()

        self.players = (
            {}
        )  # dictionary to store connected players. key = name, value = socket
        self.capacity = 4 # Number of players
        self.queue = {}  # dictionary for queue. Same structure as players dict
        self.queue_list = []

        self.choices = {} # Choices made during the game
        self.eliminated = {} # Eliminated players
        self.records = {} # Wins, losses, draws

    def broadcast(self, message): # Broadcast a message to players
        for player_socket in self.players.values():
            try:
                player_socket.send(message.encode("utf-8"))

            except Exception as e:
                self.log_system_message(
                    f"Error sending message to {player_socket}: {e}"
                )

    def broadcast_game(self, message): # Broadcast a message to players + eliminated
        for player_socket in self.players.values():
            try:
                player_socket.send(message.encode("utf-8"))

                name = self.find_name_from_socket(player_socket)
                self.records[name] = [0,0,0]

            except Exception as e:
                self.log_system_message(
                    f"Error sending message to {player_socket}: {e}"
                )

        for player_socket in self.eliminated.values():
            try:
                player_socket.send(message.encode("utf-8"))

                name = self.find_name_from_socket(player_socket)
                self.records[name] = [0,0,0]


            except Exception as e:
                self.log_system_message(
                    f"Error sending message to {player_socket}: {e}"
                )

    def log_system_message(self, message): # Server log messages
        self.system_messages.config(state="normal")
        self.system_messages.insert(tk.END, message + "\n")
        self.system_messages.yview(tk.END)
        self.system_messages.config(state="disabled")
 
    def update_players_list_after_game(self, winner_name): # Updates scoreboard by adding the win (+1) to the winner
        self.players_list.config(state="normal")
        self.players_list.delete(1.0, tk.END)

        with open("leaderboard.txt", "r+") as file:
            leaderboard_lines = file.readlines()

        entries = []

        for name in self.players.keys():
            matched_line = next(
                (line for line in leaderboard_lines if line.strip().split()[0] == name),
                None,
            )
            if (
                matched_line
            ):  # if name found in leaderboard, display the whole line in system messages
                name, score_str = matched_line.strip().split()
                score = int(score_str)  # Convert score to integer for sorting
                if winner_name == name:
                    score += 1
                entries.append((name, score))


        entries.sort(key=lambda x: x[1], reverse=True) # Sort according to their wins

        leaderboard_to_clients = f"LEADERBOARD"
        for name, score in entries:
            self.players_list.insert(tk.END, f"{name} {score}\n")
            leaderboard_to_clients += f"{name} {score}\n"

        self.broadcast(leaderboard_to_clients) # Broadcast to clients

        self.players_list.yview(tk.END)
        self.players_list.config(state="disabled")

        with open("leaderboard.txt", "w") as file:
            file.writelines(leaderboard_to_clients[11:])

    def update_players_list(self): # Regular update before the game when new players are added
        self.players_list.config(state="normal")
        self.players_list.delete(1.0, tk.END)

        with open("leaderboard.txt", "r+") as file:
            leaderboard_lines = file.readlines()

        entries = []

        updated = False
        for name in self.players.keys():
            matched_line = next(
                (line for line in leaderboard_lines if line.strip().split()[0] == name),
                None,
            )
            if (
                matched_line
            ):  # if name found in leaderboard, display the whole line in system messages
                name, score_str = matched_line.strip().split()
                score = int(score_str)  # Convert score to integer for sorting
                entries.append((name, score))

            else:  # if name not found, add name with score 0 to system messages and leaderboard
                new_entry = f"{name} 0\n"
                entries.append((name, 0))
                leaderboard_lines.append(new_entry)  # prepare new entry for file update
                updated = True

        entries.sort(key=lambda x: x[1], reverse=True) # Sort according to their wins

        leaderboard_to_clients = f"LEADERBOARD"
        for name, score in entries:
            self.players_list.insert(tk.END, f"{name} {score}\n")
            leaderboard_to_clients += f"{name} {score}\n"

        self.broadcast(leaderboard_to_clients) # Broadcast to clients

        self.players_list.yview(tk.END)
        self.players_list.config(state="disabled")

        if updated: # Update leaderboard.txt
            with open("leaderboard.txt", "w") as file:
                file.writelines(leaderboard_lines)

    def start_game(self): # Start the game with the countdown and appropriate message
        for key, value in self.eliminated:
            self.players[key] = value
        self.eliminated = {}

        time.sleep(0.2)
        self.broadcast("The game will start in 5 seconds.")
        self.log_system_message(f"The game will start in 5 seconds.")
        countdown = [5, 4, 3, 2, 1]

        for count in countdown:

            while len(self.players) < self.capacity: # if a player leaves
                self.broadcast("Insufficient amount of players. Waiting for 5 seconds...")
                if len(self.queue_list) > 0:
                    new_name = self.queue_list[0]
                    new_sock = self.queue[new_name]

                    self.players[new_name] = new_sock
                    del self.queue[new_name]
                    self.queue_list.pop(0)

                    self.update_players_list()

                time.sleep(5)

            self.broadcast(str(count))
            self.log_system_message(str(count))
            time.sleep(1)

        self.broadcast("Go!")
        time.sleep(0.1)
        self.broadcast("Pick a move, you have 10 seconds.")
        self.log_system_message(f"The game has started.")

    def find_name_from_socket(self, socket): # you give the socket, it gives you the name of the player searching through the dictionaries
        for key, val in self.players.items():
            if val == socket:
                return key
        for key, val in self.queue.items():
            if val == socket:
                return key
        for key, val in self.eliminated.items():
            if val == socket:
                return key
        return
    
    def count_keys_with_same_value(self, dictionary): # how many values are there in a dictionary
        value_to_keys = defaultdict(list)
        # Populate the value_to_keys dictionary
        for key, value in dictionary.items():
            value_to_keys[value].append(key)
        # Count the keys for each value
        counts = {value: len(keys) for value, keys in value_to_keys.items()}
        return counts

    def all_values_nonzero(self, dictionary): # Are all values nonzero or not
        return all(value != 0 for value in dictionary.values()) and len(dictionary) == 3

    def find_opponents(self, gesture): # winners, losers
        if gesture == "R":
            return "P", "S"
        if gesture == "P":
            return "S", "R"
        if gesture == "S":
            return "R", "P"

    def evaluate_results(self): # kim kazandı ona bakıyo
        actual_choices = deepcopy(self.choices)
        gesture_counts = self.count_keys_with_same_value(actual_choices)
        all_gestures_made = self.all_values_nonzero(gesture_counts)
        
        if sum(gesture_counts.values()) == 4:
            for gesture, count in gesture_counts.items(): # check for 3v1
                if count == 3:
                    win, lose = self.find_opponents(gesture)
                    for gesture2, count2 in gesture_counts.items():
                        if count2 == 1 and gesture2 != gesture:
                            if gesture2 == win:
                                return gesture2
                            elif gesture2 == lose:
                                return gesture
            
            for gesture, count in gesture_counts.items(): # check for 2v2
                if count == 2:
                    win, lose = self.find_opponents(gesture)
                    for gesture2, count2 in gesture_counts.items():
                        if count2 == 2 and gesture2 != gesture:
                            if gesture2 == win:
                                return gesture2
                            elif gesture2 == lose:
                                return gesture
                            
                    return gesture # if 2v1v1
            
            for gesture, count in gesture_counts.items(): # check for all same choice (4v0)
                if count == 4:
                    return "TIE"
                
        elif sum(gesture_counts.values()) == 3:
            for gesture, count in gesture_counts.items(): # check for 2v1
                if count == 2:
                    win, lose = self.find_opponents(gesture)
                    for gesture2, count2 in gesture_counts.items():
                        if count2 == 1 and gesture2 != gesture:
                            if gesture2 == win:
                                return gesture2
                            elif gesture2 == lose:
                                return gesture
            
            for gesture, count in gesture_counts.items(): # check for all same choice (3v0)
                if count == 3:
                    return "TIE"

        elif sum(gesture_counts.values()) == 2:
            for gesture, count in gesture_counts.items(): # check for 1v1
                if count == 1:
                    win, lose = self.find_opponents(gesture)
                    for gesture2, count2 in gesture_counts.items():
                        if count2 == 1 and gesture2 != gesture:
                            if gesture2 == win:
                                return gesture2
                            elif gesture2 == lose:
                                return gesture
            
            for gesture, count in gesture_counts.items(): # check for all same choice
                if count == 2:
                    return "TIE"
        
        elif sum(gesture_counts.values()) == 1: # automatic win
            for gesture, count in gesture_counts.items():
                if count == 1:
                    return gesture
                

    def handle_client(self, client_socket, address): # Get messages from the clients
        self.log_system_message(f"Client {address} connected.")
        name = None

        while True:
            try:
                message = client_socket.recv(1024).decode("utf-8")
                if message.startswith("NAME:"):  # if a new name message is incoming from the client
                    name = message.split(":")[1]

                    if name in self.players.keys() or name in self.queue.keys():
                        client_socket.send("Name already taken.".encode("utf-8"))
                        continue

                    elif (
                        len(self.players) < self.capacity
                    ):  # if the player count is still not sufficient
                        self.players[name] = client_socket
                        self.records[name] = [0,0,0]
                        client_socket.send(
                            f"You are in the game! {name}".encode("utf-8")
                        )
                        self.log_system_message(f"{name} is in the game.")

                        if len(self.players) == self.capacity:
                            self.update_players_list()
                            time.sleep(0.2)
                            self.start_game()

                    else:  # Add to queue
                        self.queue[name] = client_socket
                        self.queue_list.append(name)
                        self.records[name] = [0,0,0]
                        client_socket.send("The room is full.".encode("utf-8"))
                        self.log_system_message(f"{name} is in the queue.")

                    self.update_players_list()

                elif message == "LEAVE":  # client clicked leave button

                    if name in self.players.keys():
                        del self.players[name]
                        self.log_system_message(f"{name} left the game.")
                        self.broadcast(f"{name} left the game.")
                        self.update_players_list()

                    elif name in self.queue:
                        del self.queue[name]
                        self.log_system_message(f"{name} left the game.")
                        self.broadcast(f"{name} left the game.")

                    elif name in self.eliminated:
                        del self.eliminated[name]
                        self.log_system_message(f"{name} left the game.")
                        self.broadcast(f"{name} left the game.")

                    break  # exit the loop since the client is leaving

                elif message == "GAME":
                    
                    self.choices = {}
                    time.sleep(0.5)                 
                    player_name = self.find_name_from_socket(client_socket)
                    start_time = time.time()
                    if player_name not in self.eliminated:
                        player_choice = client_socket.recv(1024).decode("utf-8").split(":")[1]

                        if time.time() - start_time <= 10: # if it was picked in 10 seconds
                            self.log_system_message(player_name + " has picked choice " + player_choice)
                            self.choices[player_name] = player_choice
                        else: # if the pick was done in over 10 seconds
                            client_socket.send("10 seconds have passed. You lost automatically...".encode("utf-8"))
                            self.eliminated[player_name] = client_socket # add to eliminated, remove from players
                            del self.players[player_name]
                            self.records[player_name][1] = self.records[player_name][1] + 1 # add loss

                    while len(self.choices) != len(self.players):
                        continue

                    
                    time.sleep(0.1)
                    result = self.evaluate_results() # get the winning gesture
                    how_many_winners = sum(1 for value in self.choices.values() if value == result)

                    client_socket.send(("CHOICES:\n" + str(self.choices)).encode("utf-8")) # choices made from all players
                    time.sleep(0.1)

                    
                
                    if how_many_winners == 1: # if there is 1 winner
                        for key, value in self.choices.items():
                            if value == result:
                                winner_name = key
                        if player_name == winner_name:
                            self.broadcast_game(f"{winner_name} HAS WON THE GAME. NEW ROUND COMING UP...")
                            self.log_system_message(f"{winner_name} HAS WON THE GAME. NEW ROUND COMING UP...")
                            self.players.update(self.eliminated) # add the eliminated players back to players dict
                            self.eliminated = {} # reset eliminated players
                            time.sleep(0.1)
                            self.update_players_list_after_game(winner_name)
                            time.sleep(0.1)
                            
                            self.start_game()

                                                    

                    elif player_name in self.players:
                        if result == "TIE":
                            if player_name in self.players:
                                self.records[player_name][2] = self.records[player_name][2] + 1 # add draw
                                player_record = "Wins: " + str(self.records[player_name][0]) + " Losses: " + str(self.records[player_name][1]) + " Draws: " + str(self.records[player_name][2]) + '\n'

                                client_socket.send((player_record + "IT WAS A TIE. New Round Go!").encode("utf-8"))
                                

                        elif player_choice != result:
                            self.eliminated[player_name] = client_socket # add to eliminated remove from players
                            if player_name in self.players:
                                del self.players[player_name]

                            self.records[player_name][1] = self.records[player_name][1] + 1
                            player_record = "Wins: " + str(self.records[player_name][0]) + " Losses: " + str(self.records[player_name][1]) + " Draws: " + str(self.records[player_name][2]) + '\n'
                            client_socket.send((player_record + "YOU LOST. Spectate.").encode("utf-8"))
                            self.log_system_message(f"{player_name} Has been eliminated")


                            

                        elif player_choice == result and player_name in self.players:
                            self.records[player_name][0] = self.records[player_name][0] + 1
                            player_record = "Wins: " + str(self.records[player_name][0]) + " Losses: " + str(self.records[player_name][1]) + " Draws: " + str(self.records[player_name][2]) + '\n'
                            client_socket.send((player_record + "YOU GO TO THE NEXT ROUND. New Round Go!").encode("utf-8"))
                            self.log_system_message(f"{player_name} is going to the next round")



                    else:
                            player_record = "Wins: " + str(self.records[player_name][0]) + " Losses: " + str(self.records[player_name][1]) + " Draws: " + str(self.records[player_name][2]) + '\n'
                            client_socket.send((player_record + "YOU LOST. Spectate.").encode("utf-8"))
                            self.log_system_message(f"{player_name} Has been eliminated")

                            

            except socket.error:  # client disconnects
                if name in self.players.keys():
                    del self.players[name]
                    self.update_players_list()
                    self.log_system_message(f"{name} disconnected.")
                    self.broadcast(f"{name} disconnected.")

                elif name in self.queue.values():
                    del self.queue[client_socket]
                    self.log_system_message(f"{name} disconnected.")
                    self.log_system_message(f"{name} disconnected.")

            except Exception as e:
                if name in self.players.keys():
                    del self.players[name]
                    self.update_players_list()
                    self.log_system_message(f"{name} disconnected.")
                    self.broadcast(f"{name} disconnected.")

                elif name in self.queue.values():
                    del self.queue[client_socket]
                    self.log_system_message(f"{name} disconnected.")
                    self.broadcast(f"{name} disconnected.")

                self.log_system_message(f"An error occurred: {e}")
                break

    def start_server(self):  # start the server
        port = int(self.port_entry.get())

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IP address and port configurations
        server_socket.bind(("", port))
        server_socket.listen()
        self.log_system_message(f"Server listening on port {port}.")

        def accept_connections():
            while True:
                client_socket, address = server_socket.accept()
                threading.Thread(
                    target=self.handle_client, args=(client_socket, address)
                ).start()

        threading.Thread(target=accept_connections, daemon=True).start() # Start thread


root = tk.Tk()
app = ServerApp(root)
root.mainloop()
