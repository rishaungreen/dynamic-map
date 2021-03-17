# Dynamic World Map
(By Rishaun Green)

## Video Demo:  <URL HERE>

## Description:
The idea behind this project was to develop a flask application that would display a map of the world with each country coloured according to certain criteria. The particular criteria I chose were US travel advisory level, total population and total coronavirus cases.
This project was coded primarily in Python, making use of the flask framework to retrieve, analyse and render information on the countries on the server-side. I made use of a SQL database and json files to store this information. Also, I have included some user-interactable features coded in JavaScript, such as the search function and the image map, to provide access to more information than can be readily displayed on the map.
The application works by declaring and generating some global variables including a list of all of the countries in the world and a separate list of all the countries visible on the world map template. At this stage, the application is designed to generate multiple dictionaries each containing static information about the listed countries to which other functions need to refer. Subsequently, the dynamic (or changeable) information on each country is read from an Amazon Simple Storage bucket and used to determine the appropriate colour for each country, the correct search response and the colour/parameters of the legend. The result is displayed on the webpage. Additionally, the application has a threaded function tasked with crawling travel.state and worldometers websites for up-to-date information which, once acquired, is stored in the Amazon Simple Storage bucket overwriting the older information.
As mentioned, the application has some added features; firstly, the buttons on the webpage allow the user to determine the parameters by which the map is colour-coded, this also dynamically adapts the legend and the information given by the search function. The search function allows users to type in a country and get the appropriate information in response, it supports an autocomplete/correct dropdown feature to capture alternative country names. The map also supports clicking on countries to perform this same search. Finally, the application has a imagemap which allows users to hover over countries to find out their names.

###File-By-File Breakdown
####static/area.json
Houses the co-ordinates for each pixel that needs to be coloured for a specific country
####static/countries.db
Houses additional information about each country such as its alternative names
####static/outline.json
Houses the co-ordinates for each pixel on the border of a country. Used to generate the imagemap.
####static/area.json
Houses the co-ordinates for each pixel that needs to be coloured for a specific country 
####static/tmp.png
An image that is overwritten with a new appropriately coloured map and is subsequently to generate the display image
####static/World Map 3.png
A blank World Map image template from which the new tmp.png can be created
####templates/layout.html
Houses CSS and JavaScript for the webpage
####templates/map.html
Houses the html code for the webpage
####(.env)
Houses the information needed to access the Amazon Simple Storage bucket
####app.py
The flask application file
####Procfile
A file used to ensure that git and Heroku can parse the flask application correctly
####requirements.txt
A list of all the python modules needed for this application to work correctly

The web application is hosted on heroku.com
The dynamic storage system uses AWS Amazon
The original world map was acquired from the following source and subsequently edited:
http://www.freeusandworldmaps.com/html/World_Projections/WorldPrint.html
Sources for country information:
-	https://travel.state.gov/
-	https://www.worldometers.info/

