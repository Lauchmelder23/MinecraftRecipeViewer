import mysql.connector
import json
import math

production_names = {
    "craftingtable"     : "Crafting",
    "furnace"           : "Smelting",
    "stonecutter"       : "Stonecutting"
    }

class Item(object):
    def __init__(self, cnx, id, amount, parent_id="", recursive=True):
        self.id = id
        self.components = []
        self.possibilities = []
        self.choice = 0
        self.made_in = "natural"
        self.amount = amount
        self.creates = 1
        self.unique_id = parent_id + "/" + str(self.id)
        self.name = "???"

        if recursive:
            self.__get_components(cnx)
        
    @classmethod
    def from_json(cls, data):
        j = json.loads(data)
        item = Item(None, "", 0, recursive=False)

        item.id = j["id"]
        item.possibilities = j["possibilities"]
        item.choice = j["choice"]
        item.made_in = j["made_in"]
        item.amount = j["amount"]
        item.creates = j["creates"]
        item.unique_id = j["unique_id"]
        item.components = []
        item.name = j["name"]

        for component in j["components"]:
            item.components.append(Item.from_json(component))

        return item

    def __get_components(self, cnx):
        cursor = cnx.cursor(buffered = True)
        if str(self.id).replace(' ', '').isalpha():
            query = "SELECT recipe, name FROM items WHERE name LIKE '%{0}%'"
        else:
            query = "SELECT recipe, name FROM items WHERE item_id = '{0}'"

        cursor.execute(query.format(self.id))
        response = cursor.fetchone()

        if response == None:
            self.name = "???"
        else:
            self.name = response[1]
            data = json.loads(response[0])

            if len(data) == 0:
                raise Exception("Faulty Database Entry at {0}. Empty JSON returned".format(self.id))

            for recipe in data:
                self.possibilities.append(recipe)

            self.__make_subitem(cnx)

    def next(self, cnx):
        self.choice += 1
        if self.choice >= len(self.possibilities):
            self.choice = 0

        self.__make_subitem(cnx)

    def prev(self, cnx):
        self.choice -= 1
        if self.choice < 0:
            self.choice = len(self.possibilities) - 1

        self.__make_subitem(cnx)

    def __make_subitem(self, cnx):
        recipe = self.possibilities[self.choice]
        self.made_in = recipe["via"]
        self.components = []
        if self.made_in == "natural":
            return

        self.creates = recipe["amount"]
        
        for component in recipe["recipe"]:
            self.components.append(Item(cnx, component["id"], 
                                        math.ceil(self.amount / self.creates) * component["amount"], 
                                        parent_id=self.unique_id))

    def get_formatted(self):
        if len(self.components) == 0:
            return ""

        output = "<ul>"
        for component in self.components:
            needs_form = (len(component.possibilities) > 1)
            output += f"<li><span>"

            if needs_form:
                output += "<form method='POST' class='left'>"
                output += f"<input type='hidden' name='target' value='{component.unique_id}' />"
                output += "<input type='hidden' name='direction' value='<' />"
                output += "<input type='submit' value='<' />"
                output += "</form>"

            output += f"{component.amount} {component.name}"

            if needs_form:
                output += "<form method='POST' class='right'>"
                output += f"<input type='hidden' name='target' value='{component.unique_id}' />"
                output += "<input type='hidden' name='direction' value='>' />"
                output += "<input type='submit' value='>' />"
                output += "</form>"
            output += "</span>"
       
            if component.made_in != "natural":
                output += "<ul><li><code>"
                if production_names.get(component.made_in) != None:
                    output += f"{production_names[component.made_in]}"
                else:
                    output += "???"
                output += "</code>"

            output += component.get_formatted()
            if component.made_in != "natural":
                output += "</li></ul>"
            output += "</li>"
        output += "</ul>"
        return output

def to_json(item: Item):
    data = {
        "id": item.id,
        "choice": item.choice,
        "made_in": item.made_in,
        "amount": item.amount,
        "creates": item.creates,
        "unique_id": item.unique_id,
        "name": item.name,
        "components": [],
        "possibilities": item.possibilities
        }

    for component in item.components:
        data["components"].append(to_json(component))

    return json.dumps(data)
