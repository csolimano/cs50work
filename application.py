"""
Connor Solimano
CS50 Final Project - PolitiTracker
December 2018
"""

import os
import requests
import re
import sys

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from io import open

from helpers import location_required

# All API keys are unique to this project (PolitiTracker). I created an account with each service in order to obtain these keys.

# Google API used to find district given address: https://developers.google.com/civic-information/
GOOGLE_API_KEY = "AIzaSyCuup6zgPTEuXFMucmyvxy4PR_5JV27lys"
# ProPublica API used to get representative and relavant info given a cong. district: https://projects.propublica.org/api-docs/congress-api/#overview
PROPUBLICA_API_KEY = "xiZ1eoAaNO5fCUpLQdtK9weQSLyIxWOIP6U5nWu2"
# OpenSecrets API for campaign finance data: https://www.opensecrets.org/open-data/api
OPENSECRETS_API_KEY = "bdb38956626a5d7831db258fa83bb3a3"

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
# From CS50 PSET 8
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
# From CS50 PSET 8


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
# From CS50 PSET 8


app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        # Clear all of the session data about the previous rep
        session.clear()
        return render_template("index.html")
    # Post Request
    else:
        # Query Google Civics API to get district given address
        # API automatically protects against potentially dangerous inputs
        print(request.form.get('address'))
        response = requests.get(
            f"https://www.googleapis.com/civicinfo/v2/representatives?address={request.form.get('address')}&levels=country&key={GOOGLE_API_KEY}").json()
        try:
            # Pull out the division ID from the long list of information (held at an index of 3 in the "offices" dictionary key)
            # District divisionID given in the form: "ocd-division/country:us/state:ma/cd:5" for Massachusetts' 5th Congressional District
            division = response["offices"][3]["divisionId"]
        except:
            # If the address is not valid or specific enough, indexing into the 4th element of the "offices" key will return an error
            print("Invalid Address")
            return render_template("error.html", error="Invalid Address")

        # Check if the state has multiple congressional districts
        # Division will not contain "/cd" if there is only one district
        # Store the state and district info in the session dictionary for further use on other pages
        if "/cd:" in division:
            # Retrieve the substring between "state:" and "/" which contains the state abbreviation
            # Inspiration from https://stackoverflow.com/questions/4666973/how-to-extract-the-substring-between-two-markers
            session["state"] = re.search('/state:(.+?)/', division).group(1).upper()
            session["district"] = int(re.search('/cd:(.+?)', division).group(1))
            # Pull the full district name from the API using the divisionID stored in the division variable
            district_name = response["divisions"][division]["name"]
            # Capitalize the first letter of each word, ignoring apostrophes
            # Inspiration from https://stackoverflow.com/questions/1549641/how-to-capitalize-the-first-letter-of-each-word-in-a-string-python
            session["district_name"] = " ".join(w.capitalize() for w in district_name.split())
            # Store the fact that there are multiple districts in the state (to be used in /home)
            session["district_size"] = "multi"
        # There is only one district in the state
        else:
            # Retrieve the state abbreviation that follows "/state:" in the string
            session["state"] = division[division.index("/state:") + len("/state:"):].upper()
            # Set the district to 1 because the state only has 1 congressional district
            session["district"] = 1
            # States with only one district don't have a district name value, so one must be created
            session["district_name"] = response["divisions"][division]["name"] + "'s At Large Congressional District"
            # Store the fact that there is just one district in the state (to be used in /home)
            session["district_size"] = "single"

        return redirect("/home")


@app.route("/home", methods=["GET"])
@location_required
def home():
    # Retrieve the ProPublica dataset for a specific representative, then index into the first (and only) element of the "results" key
    rep = requests.get(f"https://api.propublica.org/congress/v1/members/house/{session['state']}/{str(session['district'])}/current.json", headers={
                       'X-API-Key': PROPUBLICA_API_KEY}).json()["results"][0]

    # Store the dictionary of rep info for later use on other pages
    session["rep_dict"] = rep
    # Store the ID and twitter handle in session for further use on other pages
    session["congressionalId"] = rep["id"]
    session["twitter_account"] = rep["twitter_id"]
    # Store the representative's name for later use
    session["rep_name"] = rep["name"]

    # Retrieve rep image from TheUnitedStates' open-source API
    picture = "https://theunitedstates.io/images/congress/225x275/" + session["congressionalId"] + ".jpg"

    return render_template("home.html", state=session["state"], district=session["district"], img=picture, rep=rep,
                           district_name=session["district_name"], district_size=session["district_size"])


@app.route("/votes", methods=["GET"])
@location_required
def votes():
    votes = requests.get(f"https://api.propublica.org/congress/v1/members/{session['congressionalId']}/votes.json", headers={
                         'X-API-Key': PROPUBLICA_API_KEY}).json()["results"][0]["votes"]

    # Pass the entire votes list for that candidate - individual values are accessed on the page itself
    return render_template("votes.html", votes=votes)


@app.route("/media", methods=["GET"])
@location_required
def media():
    # Pass the twitter account name with Jinja - Twitter API is called on the media.html page
    return render_template("media.html", twitter=session["twitter_account"])


@app.route("/funding", methods=["GET"])
@location_required
def funding():

    # The OpenSecrets API assigns a unique cid (different than session["congressionalId"]) to each rep. This cid is needed to then search
    # the API for a candidate's finance info. The API can only be searched by state and then one must iterate through each candidate
    # in that state to find the rep one is looking for.
    state_reps = requests.get(
        f"https://www.opensecrets.org/api/?method=getLegislators&id={session['state']}&apikey={OPENSECRETS_API_KEY}&output=json").json()

    # Create a boolean value to indicate if the member was found
    found = False
    # Iterate through the candidates in the given state to find this cong. district rep's cid
    for item in state_reps["response"]["legislator"]:
        # Check if the candidate's id is the same as the one being searched for
        if item["@attributes"]["bioguide_id"] == session["congressionalId"]:
            # Store the cid for later use
            cid = item["@attributes"]["cid"]
            # End the loop after the rep cid is found
            found = True
            break
    # Return the error page to the user if the member wasn't found
    if not found:
        return render_template("error.html", error="Error finding candidate finances")

    # Retrieves top donors for most recent cycle (2018, 2016, 2014, 2012, etc.)
    top_donations = requests.get(
        f"https://www.opensecrets.org/api/?method=candContrib&cid={cid}&apikey={OPENSECRETS_API_KEY}&output=json").json()["response"]["contributors"]

    # Retrieves summary info of campaign finances of latest cycle
    summary_donations = requests.get(
        f"https://www.opensecrets.org/api/?method=candSummary&cid={cid}&apikey={OPENSECRETS_API_KEY}&output=json").json()["response"]["summary"]["@attributes"]

    return render_template("funding.html", top_donations=top_donations, summary_donations=summary_donations)


@app.route("/contact", methods=["GET"])
@location_required
def contact():
    # Retrieve a list of house members from ProPublica API. Cannot use individual member search because (for some odd reason) the list of
    # members search contains more info (including contact info) than the specific member search does. For this reason, program iterates
    # through each member until it finds the correct one with the matching congressionalId
    reps = requests.get("https://api.propublica.org/congress/v1/115/house/members.json",
                        headers={'X-API-Key': PROPUBLICA_API_KEY}).json()["results"][0]["members"]

    # Create a boolean value to indicate if the member was found
    found = False
    for member in reps:
        if member["id"] == session["congressionalId"]:
            rep = member
            found = True
            break
    # Return the error page to the user if the member isn't found
    if not found:
        return render_template("error.html", error="Error finding candidate contact info")

    return render_template("contact.html", site=rep["url"], next_election=rep["next_election"], name=session["rep_name"],
                           phone=rep["phone"], office=rep["office"], twitter=rep["twitter_account"], facebook=rep["facebook_account"])