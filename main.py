import openfoodfacts
from fastapi import FastAPI

app = FastAPI()

@app.get("/search-kbzhu")
async def search_kbzhu(barcode):
    api = openfoodfacts.API(user_agent="MyNutriApp/1.0")

    fields = ["product_name", "nutriments", "quantity"]
    code_info = api.product.get(barcode, fields = fields)  #

    if code_info:
        return {
            "result": True,
            "data": {
                "product_name": code_info["product_name"],
                "proteins_in_100g": code_info['nutriments']['proteins_100g'],
                "fats_in_100g": code_info['nutriments']['fat_100g'],
                "carbohydrates_in_100g": code_info['nutriments']['carbohydrates_100g'],
                "energy_in_100g": code_info['nutriments']['energy_100g'],
                "calcium_unit": code_info['nutriments']['calcium_unit'],
                "product_quantity": code_info['product_quantity']
            }
        }

    else:
        return {
            "result": False,
            "data": "None data"
        }