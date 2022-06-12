import tkinter as tk
from Scraper import run
import json


def edit_row():
    j_URL[idx]['series'] = int(series_entry.get())
    j_URL[idx]['item_name'] = item_entry.get()
    j_URL[idx]['website_name'] = web_entry.get()
    j_URL[idx]['url'] = url_entry.get()
    with open('JSON_URL.json', 'w') as w_file:
        json.dump(j_URL, w_file)


def delete_row():
    j_URL.pop(idx)
    with open('JSON_URL.json', 'w') as w_file:
        json.dump(j_URL, w_file)


def quit_b():
    quit()


def get_row(event):
    global idx
    idx = listbox.curselection()[0]
    list_get = listbox.get(idx)

    series_entry.delete(0, tk.END)
    series_entry.insert(tk.END, list_get[0])

    item_entry.delete(0, tk.END)
    item_entry.insert(tk.END, list_get[1])

    web_entry.delete(0, tk.END)
    web_entry.insert(tk.END, list_get[2])

    url_entry.delete(0, tk.END)
    url_entry.insert(tk.END, list_get[3])


def general():
    global url_entry, web_entry, item_entry, series_entry, listbox, j_URL
    with open('JSON_URL.json') as json_file:
        j_URL = json.load(json_file)
    json_file.close()
    # --------------------FRONTEND--------------------
    window = tk.Tk()

    # ----------LABELS SECTION----------
    url_label = tk.Label(window, text='URL')
    url_label.grid(row=0, column=0)

    series_label = tk.Label(window, text='Series')
    series_label.grid(row=0, column=4)

    item_label = tk.Label(window, text='Item')
    item_label.grid(row=2, column=0)

    web_label = tk.Label(window, text='Website')
    web_label.grid(row=2, column=2)

    optional_label = tk.Label(window, text='Optional')
    optional_label.grid(row=1, column=0, columnspan=6)

    # ----------ENTRY SECTION----------
    url = tk.StringVar()
    url_entry = tk.Entry(window, textvariable=url, width=100)
    url_entry.grid(row=0, column=1, columnspan=3)

    series = tk.StringVar()
    series_entry = tk.Entry(window, textvariable=series, width=10)
    series_entry.grid(row=0, column=5)

    item = tk.StringVar()
    item_entry = tk.Entry(window, textvariable=item, width=30)
    item_entry.grid(row=2, column=1)

    web = tk.StringVar()
    web_entry = tk.Entry(window, textvariable=web, width=30)
    web_entry.grid(row=2, column=3)

    # ----------BUTTONS SECTION----------
    run_button = tk.Button(window, text='Run', command=run)
    run_button.grid(row=3, column=5)

    edit_button = tk.Button(window, text='Edit', command=edit_row)
    edit_button.grid(row=4, column=5)

    delete_button = tk.Button(window, text='Delete', command=delete_row)
    delete_button.grid(row=5, column=5)

    exit_button = tk.Button(window, text='Exit', command=quit_b)
    exit_button.grid(row=6, column=5)

    # ----------LIST SECTION----------
    listbox = tk.Listbox(window, height=10, width=130)
    listbox.grid(row=3, column=0, rowspan=4, columnspan=4)

    scroll = tk.Scrollbar(window)
    scroll.grid(row=3, column=4, rowspan=4)

    listbox.configure(yscrollcommand=scroll.set)
    scroll.configure(command=listbox.yview)

    for item in j_URL:
        listbox.insert(tk.END, list(item.values()))

    listbox.bind('<<ListboxSelect>>', get_row)

    window.resizable(False, False)
    window.mainloop()


if __name__ == '__main__':
    general()
