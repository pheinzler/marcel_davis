
class Menue:
    def __init__(self, data):
        self.categorie = data["category"]
        self.menue = data["name"]
        self.price = data["prices"]["students"]
        self.price_unit = "/100g" if "€ pro 100g Preis" in data["notes"] else ""

    def print(self):
        print(f"{self.categorie}\n\n{self.menue} - {self.price}{self.price_unit}")

    def get(self):
        quantity = "€" if self.price_unit == "" else self.price_unit
        return f"{self.menue} - {self.price}{quantity}"
    