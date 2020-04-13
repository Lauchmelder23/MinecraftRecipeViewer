"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""


import mysql.connector
import json
import os
from item import Item, production_names, to_json
from flask import Flask, render_template, request, session
app = Flask(__name__)

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app

with open("config.json") as file:
    data = json.loads(file.read())
    USER = data["user"]
    PASS = data["pass"]

def make_tree_view(item):
    needs_form = (len(item.possibilities) > 1)

    output = f"<ul class='tree'><li><span>"

    if needs_form:
            output += "<form method='POST' class='left'>"
            output += f"<input type='hidden' name='target' value='{item.id}' />"
            output += "<input type='hidden' name='direction' value='<' />"
            output += "<input type='submit' value='<' />"
            output += "</form>"

    output += f"{item.amount} {item.name}"

    if needs_form:
            output += "<form method='POST' class='right'>"
            output += f"<input type='hidden' name='target' value='{item.id}' />"
            output += "<input type='hidden' name='direction' value='>' />"
            output += "<input type='submit' value='>' />"
            output += "</form>"

    output += "</span>"

    if item.made_in != "natural":
        output += "<ul><li><code>"
        if production_names.get(item.made_in) != None:
            output += f"{production_names[item.made_in]}"
        else:
            output += "???"
        output += "</code>"
    else:
        output += " can be found naturally."

    output += item.get_formatted()
    if item.made_in != "natural":
        output += "</li></ul>"
    output += "</li></ul>"

    session['item'] = to_json(item)
    return output


def request_item(id, amount):
    cnx = mysql.connector.connect(user=USER, password=PASS,
                              host='85.214.66.98', database='mc_rv')

    item = Item(cnx, id, amount)

    cnx.close()

    return item

@app.after_request
def after(response):
    response.headers["Content-Security-Policy"] = "default-src *; script-src 'self' 'unsafe-inline' 'unsafe-eval' http://*; style-src 'self' 'unsafe-inline' http://*"
    return response

@app.route('/')
def main():
    item = request_item(257, 3)
    return render_template('index.html', id=257, recipe=make_tree_view(item), amount=3)

@app.route('/', methods=['POST'])
def on_submit():
    if "target" not in request.form:
        if not str(request.form["id"]).replace(' ', '').isalpha():
            id_split = request.form["id"].split(":")
            for i in range(len(id_split)):
                id_split[i] = str(int(id_split[i]))
            id = ':'.join(id_split)
        else:
            id = str(request.form["id"])

        amount = int(request.form["amount"])

        item = request_item(id, amount)
    else:
        unique_id_parts = str(request.form.get("target")).split("/")
        unique_id_parts.pop(0)
        
        item = Item.from_json(session.get('item'))

        subitem = item
        for part in unique_id_parts:
            for subsubitem in subitem.components:
                if subsubitem.id == part:
                    subitem = subsubitem

        cnx = mysql.connector.connect(user=USER, password=PASS,
                    host='85.214.66.98', database='mc_rv')

        if request.form.get("direction") == '>':
            subitem.next(cnx)
        else:
            subitem.prev(cnx)

        amount = item.amount
        id = item.id

        cnx.close()
    

    return render_template('index.html', id=id, recipe=make_tree_view(item), amount=amount)

