from tkinter import *
from tkinter import ttk
import random
import os

def print_hierarchy(w, depth=0):
    print('  '*depth + w.winfo_class() + ' w=' + str(w.winfo_width()) + ' h=' + str(w.winfo_height()) + ' x=' + str(w.winfo_x()) + ' y=' + str(w.winfo_y()))
    for i in w.winfo_children():
        print_hierarchy(i, depth+1)

def placeholder():
    print('placeholder')

def get_listbox_info(listbox: Listbox):
    print(listbox.curselection())

def increase_progressbar_by(i: int):
    print(f"{i} steps increased")
    progbar.step(i)

root = Tk()
root.title("Model Generator")
root.option_add('*tearOff', FALSE)

OSNAME = root.tk.call('tk', 'windowingsystem')
print(OSNAME) #win32, x11, aqua

# Initial mainframe configuration.
# 3 columns and 4 rows.
mainframe = ttk.Frame(root, padding="12 12 12 12")
mainframe.grid(column=0, row=0)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# region TOPMENU
menubar = Menu(root)

# filemenu
menu_file = Menu(menubar)
menu_file.add_command(label='New', command=placeholder)
menu_file.add_separator()
menu_file.add_command(label='Open...', command=placeholder)
menu_file.add_command(label='Close', command=placeholder)
menubar.add_cascade(menu=menu_file, label='File')

#submenu
menu_recent = Menu(menu_file)
menu_file.add_cascade(menu=menu_recent, label='Open Recent')
recent_files = ["asdasd.py", "asdasd.py", "asdasd.py", "asdasd.py"]
for f in recent_files:
    menu_recent.add_command(label=os.path.basename(f), command=lambda f=f: openFile(f))

# editmenu
menu_edit = Menu(menubar)
menu_edit.add_command(label='Modify', command=placeholder)
menu_edit.add_command(label='Alter', command=placeholder)
menu_edit.add_separator()
menu_edit.add_command(label='Change', command=placeholder)
menubar.add_cascade(menu=menu_edit, label='Edit')

root.config(menu=menubar)
#endregion TOPMENU

# region STYLES
s = ttk.Style()
# s.configure('Danger.TFrame', background='red', borderwidth=5, relief='raised')
t = ttk.Style()
# endregion STYLES


# region ELEMENTS

# text entries
namelbl = ttk.Label(mainframe, text="Name")
name = StringVar()
name_entry = ttk.Entry(mainframe, textvariable=name, text="name")

surnamelbl = ttk.Label(mainframe, text="Surname")
surname = StringVar()
surname_entry = ttk.Entry(mainframe, textvariable=surname, text="surname")

# radio buttons
genderlbl = ttk.Label(mainframe, text='Gender')
gender = StringVar()
male = ttk.Radiobutton(mainframe, text='Woman', variable=gender, value='F') #Female
female = ttk.Radiobutton(mainframe, text='Man', variable=gender, value='M') #Male
other = ttk.Radiobutton(mainframe, text='Other', variable=gender, value='O') #Other

# listbox 
embeddings = ["TransE_l2", "DistMult", "ComplEx", "TransR"]
choices_emb = StringVar(value=embeddings)

datasets = ["COUNTRIES","UMLS","KINSHIP","WN18RR","FB15K-237","NELL-995"]
choices_datasets = StringVar(value=datasets)

l_e = Listbox(mainframe, listvariable=choices_emb, height=4)
l_d = Listbox(mainframe, listvariable=choices_datasets, height=4)

# bind an onchange event to the listbox
l_e.bind("<<ListboxSelect>>", lambda e: get_listbox_info(l_e))
l_d.bind("<<ListboxSelect>>", lambda e: get_listbox_info(l_d))

# add scrollbar to listboxes
scroll1 = ttk.Scrollbar( mainframe, orient=VERTICAL, command=l_e.yview)
scroll2 = ttk.Scrollbar( mainframe, orient=VERTICAL, command=l_d.yview)

l_e.configure(yscrollcommand=scroll1.set)
l_d.configure(yscrollcommand=scroll2.set)

# text widget
textbox = Text(mainframe, width=40, height=10)

# check buttons
newscheck = BooleanVar(value=False)
check = ttk.Checkbutton(mainframe, text='get newsletter?', variable=newscheck)
test1 = BooleanVar(value=False)
check2 = ttk.Checkbutton(mainframe, text='test1', variable=test1)
test2 = BooleanVar(value=False)
check3 = ttk.Checkbutton(mainframe, text='test2', variable=test2)
test3 = BooleanVar(value=False)
check4 = ttk.Checkbutton(mainframe, text='test3', variable=test3)

# progress bar
progbar = ttk.Progressbar(mainframe, orient=HORIZONTAL, mode='determinate', length=650, maximum=100)

# buttons
config_button = ttk.Button(mainframe, text="Configuration", command=placeholder)
demobutton = ttk.Button(mainframe, text="Demo", command=lambda: increase_progressbar_by(random.randint(1,5)))

# endregion ELEMENTS

# region GRID

#row0
namelbl.grid(column=0, row=0, sticky=['E'])
name_entry.grid(column=1, row=0, columnspan=2)
surnamelbl.grid(column=3, row=0, sticky=['E'])
surname_entry.grid(column=4, row=0, columnspan=2)

#row1
genderlbl.grid(row=1, column=0, sticky=['E'])
male.grid(row=1, column=1)
female.grid(row=1, column=2)
other.grid(row=1, column=3)

config_button.grid(row=1, column=4, columnspan=2, rowspan=2)

#row2
check.grid(row=2, column=0)
check2.grid(row=2, column=1)
check3.grid(row=2, column=2)
check4.grid(row=2, column=3)

#row3
l_e.grid(row=3, column=0, sticky=['E'])
scroll1.grid(row=3, column=1, sticky=['W'])
textbox.grid(row=3, column=2, columnspan=2, rowspan=2)

#row4
l_d.grid(row=4, column=0, sticky=['E'])
scroll2.grid(row=4, column=1, sticky=['W'])

#row5
progbar.grid(row=5, column=0, columnspan=6, sticky=['W'])


# endregion GRID

# miscelaneous
# adding pixel padding to all children of mainframe.
for child in mainframe.winfo_children(): 
    try:
        child.grid_configure(padx=5, pady=5)
    except:
        print("tried to pad something u shouldn't've.")


#automatically focus on the name entry.
name_entry.focus()

# some more binding to keys.
# l = ttk.Label(mainframe, text="Starting...")
# l.grid(column=2, row=4, sticky=S)
# a complete list of bindings is avaliable at https://tkdocs.com/tutorial/concepts.html
# print_hierarchy(root)

root.mainloop()