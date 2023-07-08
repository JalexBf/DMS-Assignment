# import required libraries
import math
import mysql.connector
import numpy as np
from mysql.connector import errorcode
from colorama import Fore, Style
import requests
import requests_cache
import json
import time
from IPython.display import clear_output
import pandas as pd
from tqdm import tqdm
from sqlalchemy import create_engine
import pymysql
import random
from matplotlib import pyplot
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.graphics.tsaplots import plot_pacf
from math import sqrt
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
import networkx as nx
from scipy import stats
import csv
import os


# declare global variables
DB_NAME = 'mydb'
USER = 'root'
PASSWORD = 'password'

# Make requests to last.fm API
api_key = '8ae13125cd35bc796c66bbab61660f87'
USER_AGENT = 'Ilias'


# Check for connection error
def check_connection():
    global cnx
    try:
        cnx = mysql.connector.connect(
            host="localhost",
            user=USER,
            passwd=PASSWORD,
            auth_plugin='mysql_native_password'
        )
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Your username or password is not valid")
        else:
            print(err)
    else:
        print("Connection established successfully!")


# ----------CREATE DATABASE----------
# Function to create database
def create_database(cursor):
    try:
        cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
    except mysql.connector.Error as err:
        print(Fore.RED + "Failed creating database: {}".format(err) + Style.RESET_ALL)
        exit(1)


# Create and use database
def create_and_use_database(cursor):
    try:
        cursor.execute("DROP DATABASE IF EXISTS {}".format(DB_NAME))
        cursor.execute("CREATE DATABASE {}".format(DB_NAME))
        cursor.execute("USE {}".format(DB_NAME))
    except mysql.connector.Error as err:
        print("Error creating and using database: {}".format(err))
        exit(1)


# ----------CREATE TABLES----------
# Create tables
def create_tables(cursor):
    # Create table Artists
    cursor.execute("CREATE TABLE IF NOT EXISTS Artists ("
                   "artistid INTEGER(13) NOT NULL AUTO_INCREMENT,"
                   "name VARCHAR(500) NOT NULL,"
                   "primary key(artistid))")

    # Create table Albums
    cursor.execute("CREATE TABLE IF NOT EXISTS Albums ("
                   "albumid INTEGER(13) NOT NULL AUTO_INCREMENT,"
                   "name VARCHAR(500) NOT NULL,"
                   "artist VARCHAR(500),"
                   "tag VARCHAR(500),"
                   "primary key(albumid))")

    # Create table Users
    cursor.execute("CREATE TABLE IF NOT EXISTS Users ("
                   "id INTEGER(13) NOT NULL AUTO_INCREMENT,"
                   "name VARCHAR(50),"
                   "surname VARCHAR(50) NOT NULL,"
                   "primary key(id))")

    # Create table Address
    cursor.execute("CREATE TABLE IF NOT EXISTS Address ("
                   "addressid INTEGER(13) NOT NULL AUTO_INCREMENT,"
                   "street VARCHAR(50),"
                   "house_number INTEGER(13),"
                   "postal_code INTEGER(13),"
                   "city VARCHAR(50) NOT NULL,"
                   "state VARCHAR(50) NOT NULL,"
                   "PRIMARY KEY (addressid))")

    # Create table UsersArtists
    cursor.execute("CREATE TABLE IF NOT EXISTS UsersArtists ("
                   "userartistid INTEGER(13) NOT NULL AUTO_INCREMENT,"
                   "user_id INTEGER(13),"
                   "artist_id INTEGER(13),"
                   "preference INTEGER(13) NOT NULL,"
                   "PRIMARY KEY (userartistid),"
                   "CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES Users(id),"
                   "CONSTRAINT fk_artist FOREIGN KEY (artist_id) REFERENCES Artists(artistid))")

    # Create table UserAlbums
    cursor.execute("CREATE TABLE IF NOT EXISTS UserAlbums ("
                   "useralbumid INTEGER(13) NOT NULL AUTO_INCREMENT,"
                   "user_id INTEGER(13),"
                   "album_id INTEGER(13),"
                   "PRIMARY KEY (useralbumid),"
                   "FOREIGN KEY (user_id) REFERENCES Users(id),"
                   "FOREIGN KEY (album_id) REFERENCES Albums(albumid))")

    # Create table ArtistsAlbums
    cursor.execute("CREATE TABLE IF NOT EXISTS ArtistAlbum ("
                   "artistalbumid INTEGER(13) NOT NULL AUTO_INCREMENT,"
                   "artist_id INTEGER(13),"
                   "album_id INTEGER(13),"
                   "PRIMARY KEY (artistalbumid),"
                   "FOREIGN KEY (artist_id) REFERENCES Artists(artistid),"
                   "FOREIGN KEY (album_id) REFERENCES Albums(albumid))")


def insert_artists(cursor):

    artists = []

    # Enable caching for Last.fm API requests
    requests_cache.install_cache("lastfm_cache", expire_after=3600)  # cache responses for 1 hour

    # use chart.getTopArtists to get 40 top artists from last.fm
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "chart.getTopArtists",
        "api_key": api_key,
        "format": "json",
        "limit": 20  # Get 20 results per page
    }
    # send request to last.fm and retrieve data
    print(Fore.YELLOW + "Calling chart.getTopArtists from last.fm ..." + Style.RESET_ALL)
    counter = 0
    num_artists = 0
    for page in range(1, 3):
        params["page"] = page  # Set the page parameter
        try:
            response = requests.get(url, params=params)
            data = response.json()
            if "artists" in data and "artist" in data["artists"]:
                artists += data["artists"]["artist"]
            else:
                print(f"Error retrieving artist data from Last.fm (page {page})")
        except requests.exceptions.RequestException as e:
            print("Error making the request:", e)

        # increment counter and print message after every 20 API calls
        counter += 20
        if counter % 20 == 0:
            print(Fore.YELLOW + "Finished calling chart.getTopArtists for {} artists".format(counter) + Style.RESET_ALL)

    print(Fore.GREEN + "Total chart.getTopArtists calls made were {}".format(counter) + Style.RESET_ALL)

    # get random 20 artists from top 40
    print(Fore.YELLOW + "Choosing 20 artists to insert into database..." + Style.RESET_ALL)
    random_artists = random.sample(artists, 20)

    # insert 20 artists data into Artists table
    insert_query = "INSERT INTO Artists (name) VALUES (%s)"

    for artist in random_artists:
        name = artist["name"]
        artist_data = (name,)
        cursor.execute(insert_query, artist_data)
        if cursor.rowcount > 0:
            num_artists += 1
    cnx.commit()

    print(Fore.GREEN + "{} Artists were inserted successfully!".format(num_artists) + Style.RESET_ALL)
    print("----------")


def insert_albums(cursor):

    # select artists from Artists table
    query = "SELECT distinct name FROM Artists"
    cursor.execute(query)
    artists = cursor.fetchall()

    # iterate over artist names and call artist.getTopAlbums method for each artist
    print(Fore.YELLOW + "Calling artist.getTopAlbums from last.fm ..." + Style.RESET_ALL)
    counter = 0
    num_updated = 0
    for artist in artists:
        # construct API request URL
        url = "http://ws.audioscrobbler.com/2.0/"
        params = {
            "method": "artist.getTopAlbums",
            "artist": artist[0],
            "api_key": api_key,
            "format": "json",
            "limit": 10  # get top 10 albums for each artist
        }

        # send API request and retrieve json response
        response = requests.get(url, params=params)
        data = json.loads(response.text)

        # if it's not a cached result, sleep
        if not getattr(response, 'from_cache', False):
            time.sleep(0.25)

        # extract top albums from json response and insert them into Albums table
        for album in data["topalbums"]["album"]:
            album_data = (album["name"], album["artist"]["name"])
            insert_query = "INSERT INTO Albums (name, artist) VALUES (%s, %s)"
            cursor.execute(insert_query, album_data)
            if cursor.rowcount > 0:
                num_updated += 1
        cnx.commit()

        # increment counters for successful updates and API calls made
        counter += 1

        # print message every 20 API calls
        if counter % 20 == 0:
            print(Fore.YELLOW + "Finished calling artist.getTopAlbums for {} artists".format(counter) + Style.RESET_ALL)

    print(Fore.GREEN + "Total artist.getTopAlbums calls made were {}".format(counter) + Style.RESET_ALL)
    print(Fore.GREEN + "{} Albums were inserted successfully!".format(num_updated) + Style.RESET_ALL)
    print("----------")


def update_albums(cursor):

    albums = []
    # select all album names and artists from Albums
    query = "SELECT name, artist FROM Albums"
    cursor.execute(query)
    albums = cursor.fetchall()

    # iterate over albums and call album.getTopTags method for each album
    print(Fore.YELLOW + "Calling album.getTopTags from last.fm ..." + Style.RESET_ALL)
    # record total time
    total_time = 0
    # record start time of entire process
    start_time = time.time()
    # record start time of first batch
    batch_start_time = time.time()
    counter = 0
    num_updated = 0

    for album in albums:
        # construct API request URL
        url = "http://ws.audioscrobbler.com/2.0/"
        params = {
            "method": "album.getTopTags",
            "artist": album[1],
            "album": album[0],
            "api_key": api_key,
            "format": "json"
        }

        # send API request and retrieve json response
        response = requests.get(url, params=params)
        data = json.loads(response.text)
        # print(f"Received response for {album[0]} by {album[1]}")

        # extract first tag from toptags json response
        try:
            tag = data["toptags"]["tag"][0]["name"]
        except (KeyError, IndexError):
            tag = None

        # if it's not a cached result, sleep
        if not getattr(response, 'from_cache', False):
            time.sleep(0.25)
        # print(tag)
        # update tag column in Albums table with this tag
        update_query = "UPDATE Albums SET tag = %s WHERE name = %s AND artist = %s"
        cursor.execute(update_query, (tag, album[0], album[1]))
        cnx.commit()

        # increment counters for successful updates and API calls made
        counter += 1
        if cursor.rowcount > 0:
            num_updated += 1

        # print message after every 20 API calls, along with time it took to make this batch of calls
        if counter % 20 == 0:
            batch_end_time = time.time()
            batch_time = batch_end_time - batch_start_time
            total_time += batch_time
            print(Fore.YELLOW + "Finished calling album.getTopTags for {} albums in {:.2f} seconds".format(counter,
                                                                                                           total_time) + Style.RESET_ALL)
            batch_start_time = batch_end_time  # record start time of next batch
            batch_time = total_time  # update batch time to be cumulative time

    # record end time of entire process
    end_time = time.time()
    print(Fore.GREEN + "Total album.getTopTags calls made were {} in {:.2f} seconds".format(counter, (
                end_time - start_time)) + Style.RESET_ALL)
    print(Fore.GREEN + "{} Albums were updated successfully!".format(num_updated) + Style.RESET_ALL)
    print("----------")


def tag_statistics(cursor):

    # execute SQL query to get tag statistics for top 20 tags
    cursor.execute(
        "SELECT tag, COUNT(*) AS count FROM Albums WHERE tag IS NOT NULL GROUP BY tag ORDER BY count DESC LIMIT 20")
    tag_stats = cursor.fetchall()

    # print tag statistics
    print(Fore.GREEN + "Top 20 Tags statistics:" + Style.RESET_ALL)
    for tag, count in tag_stats:
        print(" - {}: {}".format(tag, count))

    # extract tags and counts from tag_stats
    tags = [tag for tag, count in tag_stats]
    counts = [count for tag, count in tag_stats]

    # create a bar chart of the tag statistics
    plt.bar(tags, counts)
    plt.xticks(rotation=90)
    plt.xlabel("Tag")
    plt.ylabel("Count")
    plt.title("Top 30 Album Tag Statistics")
    plt.show()


def insert_users(cursor):
    # Load users
    usersdata = []
    with open('users.csv', 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the first row
        for row in reader:
            usersdata.append(row)

    print(Fore.YELLOW + "Inserting users from csv file ..." + Style.RESET_ALL)
    # initialize counter
    num_users = 0
    for row in usersdata:
        insert_user = "INSERT INTO Users (name, surname) VALUES (%s, %s)"
        cursor.execute(insert_user, tuple(row))
        if cursor.rowcount > 0:
            num_users += 1
    cnx.commit()

    print(Fore.GREEN + "{} Users were inserted successfully!".format(num_users) + Style.RESET_ALL)
    print("----------")


def insert_addresses(cursor):
    # Load addresses
    addressdata = []
    with open('address.csv', 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the first row
        for row in reader:
            addressdata.append(row)

    print(Fore.YELLOW + "Inserting addresses from csv file ..." + Style.RESET_ALL)
    # initialize counter
    num_addresses = 0
    for row in addressdata:
        insert_address = "INSERT INTO Address (street, house_number, postal_code, city, state) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_address, tuple(row))
        if cursor.rowcount > 0:
            num_addresses += 1
    cnx.commit()

    print(Fore.GREEN + "{} Addresses were inserted successfully!".format(num_addresses) + Style.RESET_ALL)
    print("----------")

    # Add column user into table category
    cursor.execute("ALTER TABLE Address ADD COLUMN user INTEGER(13)")
    cursor.execute("ALTER TABLE Address ADD CONSTRAINT user_key FOREIGN KEY (user) REFERENCES Users(id)")
    cursor.execute("UPDATE Address SET user = (SELECT id FROM Users WHERE Users.id = Address.addressid)")


def insert_favorite_albums(cursor):

    # select all artists from Artists table
    cursor.execute("SELECT artistid FROM Artists")
    artist_ids = [artist[0] for artist in cursor.fetchall()]

    # insert data into UsersArtists table
    insert_query = "INSERT INTO UsersArtists (user_id, artist_id, preference) VALUES (%s, %s, %s)"
    for user_id in range(1, 21):
        # shuffle artist IDs to select random favorites
        random_artists = random.sample(artist_ids, 4)
        for i, artist_id in enumerate(random_artists):
            # insert artist ID with corresponding preference
            preference = i + 1
            values = (user_id, artist_id, preference)
            # print(insert_query, values)
            cursor.execute(insert_query, values)
            cnx.commit()

            # select the artist's albums from Albums table
            cursor.execute("SELECT albumid FROM Albums WHERE artist = (SELECT name FROM Artists WHERE artistid = %s)", (artist_id,))
            albums = [album[0] for album in cursor.fetchall()]

            # shuffle albums and select a random subset based on preference
            num_albums = 5 - preference
            if num_albums < 0 or num_albums > len(albums):
                num_albums = len(albums)
            random_albums = random.sample(albums, num_albums)
            # print(random_albums)

            # insert user's selected albums into UserAlbums table
            insert_query2 = "INSERT INTO UserAlbums (user_id, album_id) VALUES (%s, %s)"
            values2 = [(user_id, album_id) for album_id in random_albums]
            cursor.executemany(insert_query2, values2)
            cnx.commit()

    # Insert values in table ArtistAlbum
    cursor.execute(
        "INSERT INTO ArtistAlbum (album_id, artist_id) SELECT al.albumid, ar.artistid FROM Albums al JOIN Artists ar ON al.artist = ar.name")
    cnx.commit()


def check_tables(cursor):

    # check Albums table contents
    print(Fore.GREEN + "\n----Albums (First 10 Rows)----" + Style.RESET_ALL)
    cursor.execute("SELECT * FROM Albums LIMIT 10")
    for c in cursor:
        print(c)
    # print total number of rows in Albums table
    cursor.execute("SELECT COUNT(*) FROM Albums")
    total_rows = cursor.fetchone()[0]
    print(Fore.GREEN + f"Total rows in Albums are {total_rows}" + Style.RESET_ALL)

    # check Artists table contents
    print(Fore.GREEN + "\n----Artists (First 10 Rows)----" + Style.RESET_ALL)
    cursor.execute("SELECT * FROM Artists LIMIT 20")
    for c in cursor:
        print(c)
    # print total number of rows in Artists table
    cursor.execute("SELECT COUNT(*) FROM Artists")
    total_rows = cursor.fetchone()[0]
    print(Fore.GREEN + f"Total rows in Artists are {total_rows}" + Style.RESET_ALL)

    # check Address table contents
    print(Fore.GREEN + "\n----Address (First 10 Rows)----" + Style.RESET_ALL)
    cursor.execute("SELECT * FROM Address LIMIT 10")
    for c in cursor:
        print(c)
    # print total number of rows in Address table
    cursor.execute("SELECT COUNT(*) FROM Address")
    total_rows = cursor.fetchone()[0]
    print(Fore.GREEN + f"Total rows in Address are {total_rows}" + Style.RESET_ALL)

    print(Fore.GREEN + "\n----Users (First 10 Rows)----" + Style.RESET_ALL)
    # check Users table contents
    cursor.execute("SELECT * FROM Users LIMIT 10")
    for c in cursor:
        print(c)
    # print total number of rows in Users table
    cursor.execute("SELECT COUNT(*) FROM Users")
    total_rows = cursor.fetchone()[0]
    print(Fore.GREEN + f"Total rows in Users are {total_rows}" + Style.RESET_ALL)

    print(Fore.GREEN + "\n----UserAlbums (First 10 Rows)----" + Style.RESET_ALL)
    # check UserAlbums table contents
    cursor.execute("SELECT * FROM UserAlbums LIMIT 10")
    for c in cursor:
        print(c)
    # print total number of rows in UserAlbums table
    cursor.execute("SELECT COUNT(*) FROM UserAlbums")
    total_rows = cursor.fetchone()[0]
    print(Fore.GREEN + f"Total rows in UserAlbums are {total_rows}" + Style.RESET_ALL)

    print(Fore.GREEN + "\n----ArtistAlbum (First 10 Rows)----" + Style.RESET_ALL)
    # check ArtistAlbum table contents
    cursor.execute("SELECT * FROM ArtistAlbum LIMIT 10")
    for c in cursor:
        print(c)
    # print total number of rows in ArtistAlbum table
    cursor.execute("SELECT COUNT(*) FROM ArtistAlbum")
    total_rows = cursor.fetchone()[0]
    print(Fore.GREEN + f"Total rows in ArtistAlbum are {total_rows}" + Style.RESET_ALL)

    print(Fore.GREEN + "\n----UsersArtists (First 10 Rows)----" + Style.RESET_ALL)
    # check UsersArtists table contents
    cursor.execute("SELECT * FROM UsersArtists LIMIT 10")
    for c in cursor:
        print(c)
    # print total number of rows in V table
    cursor.execute("SELECT COUNT(*) FROM UsersArtists")
    total_rows = cursor.fetchone()[0]
    print(Fore.GREEN + f"Total rows in UsersArtists are {total_rows}" + Style.RESET_ALL)


def delete_duplicates(cursor):
        # Find duplicate entries in Artists table
        query = """
            SELECT name, COUNT(*) as count
            FROM Artists
            GROUP BY name
            HAVING count > 1
        """
        cursor.execute(query)
        duplicate_artists = cursor.fetchall()

        # Delete additional entries and associated entries in other tables
        for artist in duplicate_artists:
            name = artist[0]
            count = artist[1]
            print(Fore.YELLOW + f"Found {count} duplicate entries for artist: {name}. Deleting additional entries..." + Style.RESET_ALL)

            # Get the additional artist IDs to be deleted
            query = """
                SELECT artistid
                FROM Artists
                WHERE name = %s
                ORDER BY artistid DESC
                LIMIT %s
            """
            cursor.execute(query, (name, count - 1))
            additional_artist_ids = [row[0] for row in cursor.fetchall()]

            # Delete associated entries in UserArtists table
            delete_query = """
                DELETE FROM UsersArtists
                WHERE artist_id IN (%s)
            """
            cursor.execute(delete_query, additional_artist_ids)

            # Delete associated entries in ArtistAlbum table
            delete_query = """
                DELETE FROM ArtistAlbum
                WHERE artist_id IN (%s)
            """
            cursor.execute(delete_query, additional_artist_ids)

            # Delete additional artist entries
            delete_query = """
                DELETE FROM Artists
                WHERE artistid IN (%s)
            """
            cursor.execute(delete_query, additional_artist_ids)

        print(Fore.GREEN + "Duplicate entries deleted successfully!" + Style.RESET_ALL)
        print("----------")


def missing_values(cursor):
        query = "SELECT artistid, name FROM Artists WHERE name IS NULL OR name = ''"
        cursor.execute(query)
        results = cursor.fetchall()

        if len(results) > 0:
            print(Fore.YELLOW + "Found {} missing values in the Artists table. Replacing with 'unknown'...".format(len(results)) + Style.RESET_ALL)

            update_query = "UPDATE Artists SET name = 'unknown' WHERE artistid = %s"

            for row in results:
                artist_id = row[0]
                cursor.execute(update_query, (artist_id,))

            print(Fore.GREEN + "Missing values replaced successfully!" + Style.RESET_ALL)
        else:
            print(Fore.GREEN + "No missing values found in the Artists table." + Style.RESET_ALL)


def outliers(cursor, outlier_artist_id):
    threshold = 40  # Define the threshold for outlier artists (e.g., 20 albums)

    # Query to get the count of albums for the outlier artist
    count_query = "SELECT COUNT(*) FROM Albums WHERE artist = %s"
    cursor.execute(count_query, (str(outlier_artist_id),))  # Convert outlier_artist_id to a string
    num_albums = cursor.fetchone()[0]

    if num_albums > threshold:
        # Delete the albums for the outlier artist
        delete_albums_query = "DELETE FROM Albums WHERE artist = %s"
        cursor.execute(delete_albums_query, (str(outlier_artist_id),))  # Convert outlier_artist_id to a string
        num_deleted_albums = cursor.rowcount

        # Delete the outlier artist
        delete_artist_query = "DELETE FROM Artists WHERE artistid = %s"
        cursor.execute(delete_artist_query, (outlier_artist_id,))
        num_deleted_artists = cursor.rowcount

        print(Fore.GREEN + "Outlier artist and {} albums deleted successfully!".format(num_deleted_albums) + Style.RESET_ALL)
    else:
        print(Fore.YELLOW + "No outlier artist found!" + Style.RESET_ALL)


# Retrieve user albums from database
def get_user_albums(cursor):
    cursor.execute("SELECT * FROM UserAlbums")
    return cursor.fetchall()



def main():

    global cnx

    check_connection()

    # Check if connection is established successfully
    if cnx is None:
        print("Failed to establish connection!")
        return

    # Create a cursor object
    cursor = cnx.cursor()

    create_and_use_database(cursor)
    create_tables(cursor)

    # Check if tables are created
    cursor.execute("SHOW TABLES")
    for table in cursor:
        print(Fore.GREEN + "Table {} created successfully!".format(table[0]) + Style.RESET_ALL)
    print("----------")

    # Call functions
    insert_artists(cursor)
    insert_albums(cursor)
    update_albums(cursor)
    tag_statistics(cursor)
    insert_users(cursor)
    insert_addresses(cursor)
    insert_favorite_albums(cursor)
    user_albums = get_user_albums(cursor)
    check_tables(cursor)
    delete_duplicates(cursor)
    missing_values(cursor)


    # Insert an outlier artist for testing purposes
    outlier_artist_query = "INSERT INTO Artists (name) VALUES (%s)"
    outlier_artist_name = "Outlier Artist"

    # Execute the insert query
    cursor.execute(outlier_artist_query, (outlier_artist_name,))

    # Get the artist ID of the outlier artist
    outlier_artist_id = cursor.lastrowid

    # Insert a high number of albums for the outlier artist
    threshold = 40
    num_outlier_albums = threshold + 5  # Specify the number of outlier albums

    for i in range(num_outlier_albums):
        album_name = f"Album {i+1}"
        album_data = (album_name, outlier_artist_id)
        insert_query = "INSERT INTO Albums (name, artist) VALUES (%s, %s)"
        cursor.execute(insert_query, album_data)

    print(Fore.GREEN + "Outlier artist and albums created for testing!" + Style.RESET_ALL)

    # Call the search_and_delete_outliers function
    outliers(cursor, outlier_artist_id)

    # define a graph mining metric to suggest a new album for a user
    cursor.execute('SELECT albumid, name, artist, tag FROM Albums')
    albums = cursor.fetchall()

    cursor.execute('SELECT useralbumid, user_id, album_id FROM UserAlbums')
    user_albums = cursor.fetchall()

    for user_album in user_albums:
        user_id = user_album[1]
        album_id = user_album[2]

        # Find the neighbors of the user who owns this album
        neighbors = [x[1] for x in user_albums if x[2] == album_id and x[1] != user_id]


    # ----------TIME SERIES DATASET----------
    # Load users
    series = []
    with open('File_series.csv', 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the first row
        for row in reader:
            series.append(row)
    df = pd.DataFrame(series, columns=['date', 'price'])

    df.squeeze("columns")

    print("----------")
    print(series.index)
    print("----------")

    result = seasonal_decompose(df['price'], model='additive', period=365)
    result.plot()
    pyplot.show()


    # ----------CREATE BARABASI-ALBERT GRAPH----------
    print(Fore.YELLOW + "Creating Barabasi-Albert graph ..." + Style.RESET_ALL)
    cursor.execute('SELECT * FROM Users')
    users = cursor.fetchall()

    # define number of nodes and edges for Barabasi-Albert graph
    n = len(users)
    m = 3
    G = nx.barabasi_albert_graph(n, m)

    # add nodes for each user in database into the graph
    for node, user in zip(G.nodes(), users):
        G.nodes[node]['id'] = user[0]
        G.nodes[node]['name'] = user[1]
        G.nodes[node]['surname'] = user[2]

    print(Fore.GREEN + "Graph's {} nodes are:".format(G.number_of_nodes()) + Style.RESET_ALL)
    print(list(G.nodes.data()))
    print("----------")
    print(Fore.GREEN + "Graph's {} edges are:".format(G.number_of_edges()) + Style.RESET_ALL)
    print(list(G.edges.data()))
    print("----------")

    print(Fore.GREEN + "Graph's nodes and neighbors:" + Style.RESET_ALL)
    for node in G.nodes():
        print("Node {} has {} neighbors: These are {}".format(G.nodes[node], G.degree[node], G.adj[node]))
    print("----------")

    # draw Barabasi-Albert model
    nx.draw(G, with_labels=True)
    plt.show()


    def suggest_album(id):
        # get the neighbors of the user
        user = list(G.nodes())[id-1]
        neighbors = list(G.neighbors(user))

        # get the albums owned by the neighbors
        neighbor_albums = []
        for neighbor in neighbors:
            neighbor_albums += [x[2] for x in user_albums if x[1] == neighbor]

        # count the occurrence of each album and sort them in descending order
        album_counts = {}
        for album in neighbor_albums:
            if album not in album_counts:
                album_counts[album] = 1
            else:
                album_counts[album] += 1

        max_count = max(album_counts.values())
        max_albums = [album for album, count in album_counts.items() if count == max_count]

        if len(max_albums) == 1:
            # If there is only one album with the highest count, return it
            album = max_albums[0]
            print(Fore.GREEN + "Found most popular album..." + Style.RESET_ALL)
            print("----------")
            return album, album_counts
        else:
            # If there are multiple albums with the highest count, use the tiebreaker code
            print(Fore.GREEN + "There are many popular albums. Searching for the most popular artist"
                               " and suggesting one of his/her albums..." + Style.RESET_ALL)
            print("----------")
            artist_counts = {}
            for album, count in album_counts.items():
                cursor.execute('SELECT artist FROM Albums WHERE name=%s', (album,))
                rows = cursor.fetchall()
                if rows is None:
                    continue
                for row in rows:
                    artist = row[0]
                    if artist not in artist_counts:
                        artist_counts[artist] = {'count': 1, 'albums': {album: count}}
                    else:
                        artist_counts[artist]['count'] += 1
                        artist_counts[artist]['albums'][album] = count

            # sort the artists by count in descending order
            sorted_artists = sorted(artist_counts.items(), key=lambda x: x[1]['count'], reverse=True)

            for artist, data in sorted_artists:
                # sort the albums for the artist by count in descending order
                sorted_albums = sorted(data['albums'].items(), key=lambda x: x[1], reverse=True)

                for album, count in sorted_albums:
                    if album not in [x[2] for x in user_albums if x[1] == user]:
                        # return the suggested album and the album counts
                        return album, album_counts

        # suggest the album with the highest count that the user doesn't already own
        for album, count in album_counts.items():
            if not any(x[2] == album for x in user_albums if x[1] == user):
                # return the suggested album and the album counts
                return album, album_counts

        # if no suggestion can be made, return None
        return None, album_counts

    # prompt user to insert a number between 1-20 (select a user from Users table) to make a suggestion for new album
    while True:
        user_input = input(
            Fore.CYAN + "In order to make a suggestion for a user, please enter a number between 1 and 20 "
                        "or type 'exit' to quit: " + Style.RESET_ALL)
        if user_input == "exit":
            print("Exiting program...")
            break
        try:
            number = int(user_input)
            if number >= 1 and number <= 21:
                cursor.execute('SELECT * FROM Users WHERE id=%s', (number,))
                users = cursor.fetchone()
                print(Fore.GREEN + "The user you selected has id '{}', name '{}' and surname '{}'".format(number,
                                                                                                          users[1],
                                                                                                          users[
                                                                               2]) + Style.RESET_ALL)

                suggested_album, album_counts = suggest_album(number)

                cursor.execute(
                    'SELECT Users.id, Users.surname, Users.name, Albums.name, Albums.artist, Albums.tag from Users '
                    'LEFT JOIN UserAlbums on Users.id = UserAlbums.user_id '
                    'LEFT JOIN Albums on UserAlbums.album_id = Albums.albumid '
                    'WHERE Users.id = %s;', (number,))
                user_albums = cursor.fetchall()
                if len(user_albums) == 0:
                    print(Fore.RED + "No albums found for user with id {}".format(number) + Style.RESET_ALL)
                else:
                    print(Fore.GREEN + "Albums for user with id {}: ".format(number) + Style.RESET_ALL)
                    for album in user_albums:
                        print(" - '{}' by '{}' [tag: {}]".format(album[3], album[4], album[5]))

                if suggested_album:
                    if len(album_counts) > 0:
                        print(Fore.GREEN + "Neighbors' top 10 albums for user with id '{}': ".format(
                            number) + Style.RESET_ALL)
                        sorted_counts = sorted(album_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                        for album_id, count in sorted_counts:
                            cursor.execute('SELECT name, artist, tag FROM Albums WHERE albumid=%s', (album_id,))
                            album_info = cursor.fetchone()
                            print(
                                " - '{}' by '{}' [tag: {}] (count: {})".format(album_info[0], album_info[1],
                                                                               album_info[2],
                                                                               count))
                    cursor.execute('SELECT name, artist, tag FROM Albums WHERE albumid=%s', (suggested_album,))
                    album_info = cursor.fetchone()
                    print(Fore.GREEN + "Suggested album for user '{}' is:".format(number) + Style.RESET_ALL)
                    print(" - '{}' by '{}' [tag: {}]".format(album_info[0], album_info[1], album_info[2]))

                else:
                    print(Fore.RED + "No album suggestion for user {}".format(number) + Style.RESET_ALL)
                break
            else:
                print(Fore.RED + "Invalid input. Please enter a number between 1 and 20." + Style.RESET_ALL)
        except ValueError:
            print(Fore.RED + "Invalid input. Please enter a valid integer between 1 and 20." + Style.RESET_ALL)


    # Commit the changes and close the cursor and connection
    cnx.commit()
    cursor.close()
    cnx.close()

if __name__ == "__main__":
    main()