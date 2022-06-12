import calendar
import requests
import pandas
import string
import os
import json
import mysql.connector
from bs4 import BeautifulSoup
from datetime import date, datetime
from numpy import nan
import GUI


header = {"UserAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0'}

with open("databaseconfig.json", "r") as f:
    data = json.load(f)
    sql_data = data.get("table")
    data = data.get("database-config")[0]

source = ["https://www.amazon.pl/s?k=___",
          "https://www.libristo.pl/wyszukiwanie.html?q=___",
          "https://www.bookdepository.com/search?searchTerm=___&search=Find+book",
          ]
site_name = ["Amazon", "Libristo", "BookDepository"]


def Search(item, i):
    print(item, i)
    source[i] = source[i].replace("___", item.replace(" ", "+"))
    page = requests.get(source[i], headers=header, timeout=(5, 10))
    soup = BeautifulSoup(page.content, 'html.parser')

    if i == 0:
        price = float(soup.find("span", "a-price-whole").get_text().strip(",") + "." +
                      soup.find("span", "a-price-fraction").get_text().strip())
    elif i == 1:
        price = float(soup.find(class_="LST_buy").get_text().strip().split(sep="zł")[0])
    elif i == 2:
        price = float(soup.find(class_="price").get_text().strip(" zł").replace(",", "."))

    return price


def SQL():
    conn = mysql.connector.connect(**data)
    cursor = conn.cursor()

    td = str(date.today().strftime("%d.%m.%Y"))
    cursor.execute("SELECT Item FROM Item_Name")
    item_list = list(cursor.fetchall())
    print(td)
    print(item_list)
    cursor.execute("TRUNCATE MyManga")
    for item in item_list:
        item = item[0]
        for i in range(len(source)):
            price = Search(item, i)
            print(price)
            cursor.execute(f"SELECT * FROM {sql_data} WHERE Item = '{item}' AND Site = '{site_name[i]}' AND Date = '{td}'")
            test = cursor.fetchall()
            print(test)
            if test:
                cursor.execute(f"UPDATE {sql_data} SET Value = {price} "
                               f"WHERE Item = '{item}' AND Site = '{site_name[i]}' AND Date = '{td}'")
            else:
                cursor.execute(f"INSERT INTO {sql_data} (Item, Site ,Value, Date) "
                               f"VALUES ('{item}', '{site_name[i]}' ,{price} ,'{td}')")
    conn.commit()

    GUI(item_list)


SQL()


# ----------MAIN SCRIPT----------
def run(autorun=False):
    SQL()
    name = os.getcwd() + "/Fly me to the moon.xlsx"

    # ----------POSSESSING DATA----------
    with open('JSON_URL.json') as json_file:
        j_URL = json.load(json_file)

    j_price = []

    for item in j_URL:
        try:
            page = requests.get(item['url'], headers=header, timeout=(5, 10))
            soup = BeautifulSoup(page.content, 'html.parser')

            if soup.find(id="price") is not None:
                price = float(soup.find(id="price").get_text().strip().split()[0].replace(',', '.'))
            elif soup.find("span", itemprop="price") is not None:
                price = float(soup.find("span", itemprop="price").get_text().strip().split()[0].replace(',', '.'))
            elif soup.find("span", class_="sale-price"):
                price = float(soup.find("span", class_="sale-price").get_text().strip().split()[0].replace(',', '.'))
            else:
                price = nan

            j_price.append(price)

            print(item['item_name'], price, sep=', ')
        except AttributeError as e:
            print("Error: Item not found!", e)
            j_price.append(nan)
        except requests.exceptions.ReadTimeout:
            print("Error: Server timeout!")

    td = str(date.today().strftime("%d.%m.%Y"))

    # ----------LETTERS----------
    letters = []

    def get_code(number):
        result = []
        while number > 0:
            idx = number % 26
            result.append(string.ascii_uppercase[idx - 1])
            number -= idx
            number //= 26
        return ''.join(result[::-1])

    for p in range(1, 16383, 10):
        letters.append(get_code(p))

    # ----------LENGTH OF SERIES----------
    number_items = []
    series_list = []
    website_names = []
    longest = str(j_URL[0]['item_name'])
    for s_item in j_URL:
        longest = max(longest, s_item['item_name'])
        if s_item['series'] not in series_list:
            series_list.append(s_item['series'])
            website_names.append(s_item['website_name'])
            number_items.append(1)
        else:
            for p in range(len(series_list)):
                if series_list[p] == s_item['series']:
                    number_items[p] += 1

    # ----------DATA IN MYSQL----------
    try:
        conn = mysql.connector.connect(**data)
        cursor = conn.cursor()
        df_sql = pandas.DataFrame()
        for i in range(len(j_URL)):
            j_df = pandas.read_sql(f'SELECT Value FROM {sql_data} WHERE URL = "{j_URL[i]["url"]}"', conn).transpose()
            j_df = j_df.set_index([[j_URL[i]['item_name']]])
            df_sql = df_sql.append(j_df)
        date_df = pandas.read_sql(f'SELECT Date FROM {sql_data} WHERE URL = "{j_URL[0]["url"]}"', conn).transpose()
        date_df = date_df.values.tolist()[0]
        df_sql = df_sql.set_axis(date_df, axis='columns')
        print("Successfully connected to database...")
        df_sql[td] = j_price
        for i in range(len(j_price)):
            cursor.execute(f'SELECT EXISTS (SELECT * FROM {sql_data} WHERE URL = "{j_URL[i]["url"]}" AND Date = "{td}")')
            exist = cursor.fetchall()[0][0]
            if exist == 1:
                cursor.execute(f"UPDATE {sql_data} SET Value = '{df_sql[td][i]}' "
                               f"WHERE URL = '{j_URL[i]['url']}' AND Date = '{td}'")
            elif exist == 0:
                cursor.execute(f'INSERT INTO {sql_data} (URL, Value, Date) '
                               f'VALUES ("{j_URL[i]["url"]}", "{j_price[i]}", "{td}")')
            conn.commit()
    except mysql.connector.errors.OperationalError:
        print("Error: Not synchronized with database!\n"
              "Accessing local data...")
        df_sql = pandas.read_excel(name)
        df_sql = df_sql.set_index("Item")

    print(df_sql)
    df_month = df_sql.filter(like=td[2:])
    print(df_month)

    # ----------PREPARATIONS AND FORMATTING----------
    month_list = ['AC', 'AD', 'AE', 'AF']
    month = month_list[calendar.monthrange(datetime.now().year, datetime.now().month)[1] - 28]
    writer = pandas.ExcelWriter(name, engine='xlsxwriter')
    sheet_name = ['Scraper_Monthly', 'Scraper_Yearly']

    workbook = writer.book
    red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
    green = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})

    df = [df_month, df_sql]
    for i in range(2):
        df[i].to_excel(writer, sheet_name=sheet_name[i])
        number_rows = len(df[i].index)
        worksheet = writer.sheets[sheet_name[i]]
        worksheet.set_column("A:A", len(longest) + 2)
        if i == 0:
            worksheet.set_column(f'B:{month}', len(td) + 2)
        else:
            worksheet.set_column('B:NB', len(td) + 2)
        for q in range(2, number_rows + 2):
            q = str(q)
            if i == 0:
                color_range = f"B{q}:{month}{q}".format(number_rows)
            elif i == 1:
                color_range = f"B{q}:NB{q}".format(number_rows)
            worksheet.conditional_format(color_range, {'type': 'top', 'value': '1', 'format': red})
            worksheet.conditional_format(color_range, {'type': 'bottom', 'value': '1', 'format': green})

        x = 2
        for p in range(len(series_list)):
            chart = workbook.add_chart({'type': 'line'})
            chart.set_size({'width': 800, 'height': 360})
            if sheet_name[i] == 'Scraper_Yearly':
                chart.set_x_axis({'visible': False})
            y = number_items[p] + x
            for j in range(x, y):
                s = str(j)
                if i == 0:
                    chart.add_series({'name': f"={sheet_name[i]}!A{s}",
                                      'values': f"={sheet_name[i]}!B{s}:{month}{s}"})
                else:
                    chart.add_series({'name': f"={sheet_name[i]}!A{s}",
                                      'values': f"={sheet_name[i]}!B{s}:NB{s}"})
            chart.set_title({'name': website_names[p]})
            worksheet.insert_chart(letters[p] + str(number_rows + 6), chart)
            x = y
    writer.save()
    if autorun is False:
        os.startfile(name)
    quit()
