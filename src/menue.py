
class Menue:
    def __init__(self, data):
        self.categorie = data["category"]
        self.menue = data["name"]
        self.price = f"{data['prices']['students']:.2f}"
        self.price_unit = "€/100g" if "pro 100g Preis" in data["notes"] else "€"

    def print(self):
        print(f"{self.categorie}\n\n{self.menue} - {self.price}{self.price_unit}")

    def get(self):
        return f"{self.menue}"
    