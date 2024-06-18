import os
import json
from tkinter import *
from tkinter import ttk
FILE = "Order_log.csv"

class Accounter():
    def __init__(self) -> None:
        file = open("precios.json","r")
        a = file.read()
        self.precios = json.loads(a)
        file.close()

    def update_costs(self):
        file = open("costs.json","r")
        a = file.read()
        costs = json.loads(a)
        file.close()
        file = open("recipes.json","r")
        a = file.read()
        recipes = json.loads(a)
        file.close()
        for i in self.precios.keys():
            price = 0
            for j in recipes[i].keys():
                price += costs[j]*recipes[i][j]
            self.precios[i]["Coste"] = price
            self.precios[i]["Beneficios"] = self.precios[i]["Precio"] - price
        file = open("precios.json","w")
        a = file.write(json.dumps(self.precios, sort_keys=True, indent=4))
        file.close()

class Accounter_Gui:
    def __init__(self, root, token_manager):
        root.title("Account Manager")
        self.accounter = accounter

        mainframe = ttk.Frame(root, padding="3 3 12 12") #create a frame widget, which will hold the contents of our user interface.
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self.tokens = StringVar()
        self.tokens.set("ww")
        self.nuts = StringVar()
        self.nuts.set("ew")
        self.free = StringVar()
        self.free.set("dd")
        self.rewards = StringVar()

        self.nut_entry = ttk.Entry(mainframe, width=7)
        self.nut_entry.grid(column=3, row=2, sticky=(W, E))
        self.free_entry = ttk.Entry(mainframe, width=7)
        self.free_entry.grid(column=3, row=3, sticky=(W, E))
        self.reward_entry = ttk.Entry(mainframe, width=7)
        self.reward_entry.grid(column=2, row=4, sticky=(W, E), columnspan=3)            

        ttk.Label(mainframe, text="Tokens").grid(column=1, row=1, sticky=W)
        ttk.Label(mainframe, textvariable=self.tokens).grid(column=2, row=1, sticky=(W, E))
        ttk.Label(mainframe, text="Nut amount").grid(column=1, row=2, sticky=E)       
        ttk.Label(mainframe, textvariable=self.nuts).grid(column=2, row=2, sticky=(W, E))
        ttk.Label(mainframe, text="Free hours").grid(column=1, row=3, sticky=W)       
        ttk.Label(mainframe, textvariable=self.free).grid(column=2, row=3, sticky=(W, E))

        ttk.Button(mainframe, text="Validate", command=self.reward).grid(column=5, row=4, sticky=W) 

        for child in mainframe.winfo_children(): 
            child.grid_configure(padx=5, pady=5)

    def reward(self):
        event = self.reward_entry.get()
        self.token_mananger.reward(event)
        self.tokens.set(self.token_mananger.tokens)

    def validate_nut(self):
        try:
            value = int(self.nut_entry.get())
            self.token_mananger.do_activity("nut",value)
            self.nuts.set(self.token_mananger.nut)
        except ValueError:
            pass

    def validate_free(self):
        try:
            value = int(self.free_entry.get())
            self.token_mananger.do_activity("free",value)
            self.free.set(self.token_mananger.free)
        except ValueError:
            pass   

    def exchange_free(self):
        try:
            value = int(self.free_entry.get())
            self.token_mananger.exchange_tokens("free",value)
            self.free.set(self.token_mananger.free)
            self.tokens.set(self.token_mananger.tokens)
        except ValueError:
            pass   

    def exchange_nut(self):
        try:
            value = int(self.nut_entry.get())
            self.token_mananger.exchange_tokens("nut",value)
            self.nuts.set(self.token_mananger.nut)
            self.tokens.set(self.token_mananger.tokens)
        except ValueError:
            pass   


if __name__ == "__main__":  
    accounter = Accounter()
    root = Tk() #sets up the main application window
    Accounter_Gui(root,accounter)
    root.mainloop()

