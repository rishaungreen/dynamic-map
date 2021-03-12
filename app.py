from flask import Flask, render_template, request
import os
import sqlite3
import copy
import requests
import re
from bs4 import BeautifulSoup
import cv2
import datetime
import json
import threading
import random
import string
import time


app = Flask(__name__)

database = "static/countries.db"

legend_fields = {"Level 1": "#00FF21", "Level 2": "#FFFF00", "Level 3": "#FF8C00", "Level 4": "#FF0000", "No Information": "#000000"}

global_indicator = 0

colour_dict = {
    "#FF0000": [0, 0, 255],
    "#00FF21": [33, 255, 0],
    "#0000FF": [255, 0, 0],
    "#FFFF00": [0, 255, 255],
    "#FF8C00": [0, 140, 255],
    "#000000": [0, 0, 0],
    "#00C455": [85, 196, 0],
    "#B0C400": [0, 196, 176],
    "#B08C00": [0, 140, 176],
    "#C44100": [0, 65, 196],
    "#9B1600": [0, 22, 155],
    "#500055": [85, 0, 80],
    "#78005A": [90, 0, 120],
    "#C800AA": [170, 0, 200],
    "#E674C8": [200, 116, 230],
    "#FFBEFF": [255, 190, 255]
}


@app.route("/", methods=["GET", "POST"])
def index():
    global img

    if 'list_of_all_countries' not in globals() or 'list_of_visible_countries' not in globals():
        global list_of_all_countries
        global list_of_visible_countries
        global pixel_dict2
        global pixels

        list_of_visible_countries = []
        list_of_all_countries = []

        with open('static/outline.json', 'r') as fp:
            pixel_dict2 = json.load(fp)

        with open('static/area.json', 'r') as fp:
            pixels = json.load(fp)

        get_aliases()
        create_list_of_countries()

        threading.Thread(target=crawl_in_background).start()
        time.sleep(1)

    if request.method == "POST":
        parameter = request.form.get("name", "travel")
        execute_operation(pixels, parameter)
        time.sleep(1)
        return render_template("map.html", legend_fields=legend_fields, parameter=parameter, pixel_dict=pixel_dict2, temp_map=full_filename, country_info=dict_travel_info, aka2=alias_dictionary2, aka=alias_dictionary, true_name=realname_dictionary)
    # Automatically run travel restrictions
    execute_operation(pixels)
    time.sleep(2)
    return render_template("map.html", legend_fields=legend_fields, parameter="travel", pixel_dict=pixel_dict2, temp_map=full_filename, country_info=dict_travel_info, aka2=alias_dictionary2, aka=alias_dictionary, true_name=realname_dictionary)


# Clear existing colours
def reinitialise_map():
    global colour_var
    global clone_img
    global global_indicator

    global_indicator = 0
    original_img = cv2.imread("static/World Map 3.png")
    clone_img = copy.copy(original_img)


# Access SQLDatabase
def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)

    return conn


def get_aliases():
    global alias_dictionary2
    global realname_dictionary
    global alias_dictionary

    conn = create_connection(database)

    mycursor = conn.cursor()

    mycursor.execute("SELECT search_name, other_names, country_name FROM countries")

    data = mycursor.fetchall()

    realname_dictionary = {}
    alias_dictionary = {}
    alias_dictionary2 = {}
    for x in data:
        names = x[0] + ", " + x[1] + ", " + x[2]
        names = names.replace("[", "").replace("]", "").replace("'s", "#").replace("'", "").replace('"','').replace("#", "'s").split(", ")
        alias_dictionary[x[0]] = names
        alias_dictionary2[x[2]] = names
        realname_dictionary[x[0]] = x[2]


def load_info(parameter):
    global dict_travel_info

    if parameter == "travel":
        # Seperate into function with ifs depending on parameter
        with open('static/travel info.json', 'r') as fp:
            dict_travel_info2 = json.load(fp)
    elif parameter == "population":
        with open('static/pop info.json', 'r') as fp:
            dict_travel_info2 = json.load(fp)
    else:
        with open('static/corona info.json', 'r') as fp:
            dict_travel_info2 = json.load(fp)

    dict_travel_info = {}
    for i in dict_travel_info2:
        dict_travel_info[i] = dict_travel_info2[i].replace("\n", "<br>")


def random_imgname():
    global full_filename
    global img

    try:
        os.remove('static/' + img + '.png')
    except FileNotFoundError:
        pass
    except NameError:
        pass
    chars = string.ascii_lowercase
    img = ''.join(random.choice(chars) for i in range(15))
    full_filename = os.path.join('static', img + '.png')


# Loop through database to get a list of countries
def create_list_of_countries():
    # create a database connection
    conn = create_connection(database)

    mycursor = conn.cursor()

    mycursor.execute("SELECT search_name, pixel_coordinates FROM countries")

    data = mycursor.fetchall()

    for x in data:
        list_of_all_countries.append(x[0])
        if x[1] != "n/a":
            list_of_visible_countries.append(x[0])


# Change colour by pixel using list of pixels
def colour_pixels(new_coords, colour):
    global clone_img
    global colour_dict

    try:
        colour = colour_dict[colour]
    except KeyError:
        colour = [0, 0, 0]
    for coord in new_coords:
        clone_img[coord[1], coord[0]] = colour


def crawl_in_background():
    # crawl for all countries travel information as "Level XX - blah blah"
    travel_info_dict = {}
    US_travel_info = "https://travel.state.gov/content/travel/en/international-travel/International-Travel-Country-Information-Pages/"

    for standard_country_name in list_of_all_countries:
        if standard_country_name == "The United States of America":
            travel_information = "This is the home country"
        else:
            country_info = US_travel_info + standard_country_name.replace(" ", "") + ".html"
            response = requests.get(country_info)
            soup = BeautifulSoup(response.text, 'html.parser')
            page_title = str(soup.find_all('title'))
            if page_title == "[<title>404 - Page Not Found</title>]":
                travel_information = "Could not find country information"
            else:
                links = str(soup.find_all('a'))
                linksf = links.find("Level ")
                travel_status = links[linksf:linksf + 7]
                links2 = str(soup.find_all('div', {"class": "tsg-rwd-alert-teaser"}))
                travel_information = travel_status + "\n" + "\n" + cleanhtml(links2).replace("\n", "").replace("[", "").replace("]", "")
        travel_info_dict[standard_country_name] = travel_information

    for standard_country_name in travel_info_dict:
        if standard_country_name == "Greenland":
            travel_info_dict[standard_country_name] = travel_info_dict["Denmark"]

    # crawl for all countries population / coronavirus information"
    population_dict = {}
    coronavirus_dict = {}
    country_list = []
    population_list = []
    coronavirus_list = []
    pop_info = "https://www.worldometers.info/coronavirus/#countries"

    response = requests.get(pop_info)
    soup = BeautifulSoup(response.text, 'html.parser')
    page_title = str(soup.find_all('title'))
    if page_title == "[<title>404 - Page Not Found</title>]":
        raise Exception("An error has occured")
    else:
        table = soup.find("table")
        tbody = table.find('tbody')
        trs = tbody.find_all('tr', {"class": ""})

        for tr in trs:
            tds = tr.find_all('td')
            country_list.append(tds[1].text)
            population_list.append(tds[14].text)
            coronavirus_list.append(tds[2].text)

        for i in range (len(country_list)):
            if country_list[i] not in list_of_all_countries:
                for x in alias_dictionary:
                    if country_list[i].strip() in alias_dictionary[x]:
                        country_list[i] = x

        for z in range(len(country_list)):
            population_dict[country_list[z]] = population_list[z]
            coronavirus_dict[country_list[z]] = coronavirus_list[z]

    other_countries = {"Turkmenistan": "turkmenistan", "KoreaDemocraticPeoplesRepublicof": "north-korea"}
    for i in other_countries:
        pop_info2 = "https://www.worldometers.info/world-population/" + other_countries[i] + "-population/"

        response = requests.get(pop_info2)
        soup = BeautifulSoup(response.text, 'html.parser')
        page_title = str(soup.find_all('title'))
        if page_title == "[<title>404 - Page Not Found</title>]":
            raise Exception("An error has occured")
        else:
            div_ = soup.find('div', {"class": "col-md-8 country-pop-description"}).findChildren()
            population_dict[i] = div_[0].find_all('strong')[1].get_text()

    date_now = f"As of {datetime.datetime.now():%H:%M} " + f"on {datetime.datetime.now():%d %B %Y}"
    coronavirus_dict["accuracy date"] = date_now
    population_dict["accuracy date"] = date_now
    travel_info_dict["accuracy date"] = date_now
    coronavirus_dict["unknown"] = "Could not find country information"
    population_dict["unknown"] = "Could not find country information"
    travel_info_dict["unknown"] = "Could not find country information"

    travel_lock = threading.Lock()
    with travel_lock:
        try:
            os.remove('static/pop info2.json')
        except FileNotFoundError:
            pass
        except PermissionError:
            pass
        try:
            os.remove('static/corona info2.json')
        except FileNotFoundError:
            pass
        except PermissionError:
            pass
        try:
            os.remove('static/travel info2.json')
        except FileNotFoundError:
            pass
        except PermissionError:
            pass
        with open('static/pop info2.json', 'w') as fp:
            json.dump(population_dict, fp)
        with open('static/corona info2.json', 'w') as fp:
            json.dump(coronavirus_dict, fp)
        with open('static/travel info2.json', 'w') as fp:
            json.dump(travel_info_dict, fp)
    return


def index_dict2(dictionary, n=0):
    if n < 0:
        n += len(dictionary)
    for i, (key, value) in enumerate(dictionary.items()):
        if i == n:
            return value
    raise IndexError("dictionary index out of range")


def index_dict(dictionary, n="Level 1"):
    for i, key in enumerate(dictionary.keys()):
        if key == n:
            return i


# Based on the parameter, assign colours to countries in the database and call other functions in the appropriate order
def assign_colours(standard_country_name, parameter="travel"):
    global legend_fields
    global sorted_dict
    global sorted_split
    global global_indicator

    if parameter == "travel":
        legend_fields = {"Level 1": "#00FF21", "Level 2": "#FFFF00", "Level 3": "#FF8C00", "Level 4": "#FF0000", "No Information": "#000000"}
        if standard_country_name in list_of_visible_countries:
            if "Level 1" in info_dict[standard_country_name]:
                return "#00FF21"
            elif "Level 2" in info_dict[standard_country_name]:
                return "#FFFF00"
            elif "Level 3" in info_dict[standard_country_name]:
                return "#FF8C00"
            elif "Level 4" in info_dict[standard_country_name]:
                return "#FF0000"
            else:
                return "#000000"
    elif parameter == "population" or parameter == "coronavirus":
        if global_indicator == 0:
            global_indicator = 1
            converted_dict = info_dict
            del converted_dict["accuracy date"]
            for x in converted_dict:
                try:
                    converted_dict[x] = int(converted_dict[x].replace(",", "").strip())
                except ValueError:
                    converted_dict[x] = 0
            sorted_dict = dict(sorted(converted_dict.items(), key=lambda item: item[1]))
            sorted_split = int(len(sorted_dict) / 5)
            categories = [f"0 - {insert_commas(index_dict2(sorted_dict, sorted_split))}", f"{insert_commas(index_dict2(sorted_dict, sorted_split))} - {insert_commas(index_dict2(sorted_dict, sorted_split * 2))}", f"{insert_commas(index_dict2(sorted_dict, sorted_split * 2))} - {insert_commas(index_dict2(sorted_dict, sorted_split * 3))}", f"{insert_commas(index_dict2(sorted_dict, sorted_split * 3))} - {insert_commas(index_dict2(sorted_dict, sorted_split * 4))}", f"{insert_commas(index_dict2(sorted_dict, sorted_split * 4))} - {insert_commas(index_dict2(sorted_dict, sorted_split * 5 - 1))}"]
            if parameter == "coronavirus":
                legend_fields = {f"{categories[4]}": "#9B1600", f"{categories[3]}": "#C44100", f"{categories[2]}": "#B08C00", f"{categories[1]}": "#B0C400", f"{categories[0]}": "#00C455",
                             "No Information": "#000000"}
            else:
                legend_fields = {f"{categories[4]}": "#500055", f"{categories[3]}": "#78005A", f"{categories[2]}": "#C800AA", f"{categories[1]}": "#E674C8", f"{categories[0]}": "#FFBEFF",
                             "No Information": "#000000"}
        try:
            category_no = int(index_dict(sorted_dict, standard_country_name) / sorted_split)
            if category_no == 5 or category_no == 4:
                category_no = 0
            elif category_no == 3:
                category_no = 1
            elif category_no == 2:
                pass
            elif category_no == 1:
                category_no = 3
            else:
                category_no = 4
        except TypeError:
            return "#000000"
        return index_dict2(legend_fields, category_no)
    else:
        return "#000000"


def insert_commas(string1):
    string1 = str(string1)
    string2 = ""
    if len(string1) % 3 == 1:
        counter = 1
        for i in string1:
            string2 += i
            counter -= 1
            if counter == 0:
                string2 += ","
                counter = 3
    elif len(string1) % 3 == 2:
        counter = 2
        for i in string1:
            string2 += i
            counter -= 1
            if counter == 0:
                string2 += ","
                counter = 3
    else:
        counter = 3
        for i in string1:
            string2 += i
            counter -= 1
            if counter == 0:
                string2 += ","
                counter = 3

    return string2[:-1]


# Parsing html
def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def execute_operation(pixel_dictionary, parameter="travel"):
    load_info(parameter)
    threading.Thread(target = execute_colouring, args=(pixel_dictionary, parameter)).start()


def execute_colouring(pixel_dictionary, parameter):
    global info_dict
    global accuracy_statement
    global final_img_data

    reinitialise_map()
    if parameter == "travel":
        travel_lock = threading.Lock()
        with travel_lock:
            with open('static/travel info.json', 'r') as fp:
                info_dict = json.load(fp)
        accuracy_statement = info_dict["accuracy date"]
        for i in pixel_dictionary:
            colour_pixels(pixel_dictionary[i], assign_colours(i))
    elif parameter == "population":
        travel_lock = threading.Lock()
        with travel_lock:
            with open('static/pop info.json', 'r') as fp:
                info_dict = json.load(fp)
        accuracy_statement = info_dict["accuracy date"]
        for i in pixel_dictionary:
            colour_pixels(pixel_dictionary[i], assign_colours(i, parameter))
        try:
            del sorted_dict
        except NameError:
            pass
        try:
            del sorted_split
        except NameError:
            pass
    else:
        travel_lock = threading.Lock()
        with travel_lock:
            with open('static/corona info.json', 'r') as fp:
                info_dict = json.load(fp)
        accuracy_statement = info_dict["accuracy date"]
        for i in pixel_dictionary:
            colour_pixels(pixel_dictionary[i], assign_colours(i, parameter))
        try:
            del sorted_dict
        except NameError:
            pass
        try:
            del sorted_split
        except NameError:
            pass

    cv2.imwrite("static/tmp.png", clone_img)
    random_imgname()

    original_img2 = cv2.imread("static/tmp.png")

    clone_img2 = copy.copy(original_img2)

    cv2.imwrite(f"static/{img}.png", clone_img2)

    convert_infos()


def convert_infos():
    travel_lock = threading.Lock()
    with travel_lock:
        try:
            with open('static/pop info2.json', 'r') as fp:
                po_dict = json.load(fp)
            with open('static/corona info2.json', 'r') as fp:
                co_dict = json.load(fp)
            with open('static/travel info2.json', 'r') as fp:
                tr_dict = json.load(fp)

            os.remove('static/pop info2.json')
            os.remove('static/corona info2.json')
            os.remove('static/travel info2.json')

            with open('static/pop info.json', 'w') as fp:
                json.dump(po_dict, fp)
            with open('static/corona info.json', 'w') as fp:
                json.dump(co_dict, fp)
            with open('static/travel info.json', 'w') as fp:
                json.dump(tr_dict, fp)

        except FileNotFoundError:
            pass


if __name__ == "__main__":
    app.run()