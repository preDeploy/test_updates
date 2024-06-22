import pandas as pd
import json


def createDB():
    lawyers = pd.read_csv('lawyer-list.csv').to_dict('dict')
    col_names = ['Username', 'Point of Contact', 'Law Firm Name', 'Experience', 'Description', 'Expertise',
                 'Main Office', 'Phone Number', 'Website', 'Image link', 'Email Address', 'Education', 'Linkedin']
    lawyer_list = {}
    for i in range(len(list(lawyers[col_names[0]].keys()))):
        username = lawyers['Username'][i]
        lawyer_list[username] = {}
        for key in col_names[1:]:
            if pd.isna(lawyers[key][i]):
                lawyer_list[username][key] = ""
            else:
                lawyer_list[username][key] = lawyers[key][i]

    with open('lawyer-list.json', 'w') as lawFile:
        json.dump(lawyer_list, lawFile)


createDB()
