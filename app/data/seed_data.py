from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FoodItem, User


FOOD_ITEMS = [
    {"name": "Egg (whole)", "protein": 6.0, "carbs": 0.6, "fats": 5.0, "glycemic_load": 0.0, "hidden_oil_estimate": 0.0},
    {"name": "Whey", "protein": 24.0, "carbs": 3.0, "fats": 1.5, "glycemic_load": 1.0, "hidden_oil_estimate": 0.0},
    {"name": "Chapati", "protein": 3.0, "carbs": 18.0, "fats": 1.0, "glycemic_load": 12.0, "hidden_oil_estimate": 0.2},
    {"name": "Dal", "protein": 9.0, "carbs": 20.0, "fats": 3.0, "glycemic_load": 10.0, "hidden_oil_estimate": 0.4},
    {"name": "Paneer 100g", "protein": 18.0, "carbs": 3.0, "fats": 20.0, "glycemic_load": 1.0, "hidden_oil_estimate": 0.4},
    {"name": "Tofu 150g", "protein": 16.0, "carbs": 4.0, "fats": 9.0, "glycemic_load": 2.0, "hidden_oil_estimate": 0.3},
    {"name": "Spinach", "protein": 2.9, "carbs": 3.6, "fats": 0.4, "glycemic_load": 1.0, "hidden_oil_estimate": 0.1},
    {"name": "Cabbage", "protein": 1.3, "carbs": 5.8, "fats": 0.1, "glycemic_load": 2.0, "hidden_oil_estimate": 0.1},
    {"name": "Bhindi", "protein": 1.9, "carbs": 7.5, "fats": 0.2, "glycemic_load": 3.0, "hidden_oil_estimate": 0.2},
    {"name": "Bottle gourd", "protein": 0.6, "carbs": 3.5, "fats": 0.1, "glycemic_load": 1.0, "hidden_oil_estimate": 0.1},
    {"name": "Ridge gourd", "protein": 1.2, "carbs": 4.4, "fats": 0.2, "glycemic_load": 1.0, "hidden_oil_estimate": 0.1},
    {"name": "Broccoli", "protein": 2.8, "carbs": 6.6, "fats": 0.3, "glycemic_load": 3.0, "hidden_oil_estimate": 0.1},
    {"name": "Cauliflower", "protein": 1.9, "carbs": 5.0, "fats": 0.3, "glycemic_load": 2.0, "hidden_oil_estimate": 0.1},
    {"name": "Zucchini", "protein": 1.2, "carbs": 3.1, "fats": 0.3, "glycemic_load": 1.0, "hidden_oil_estimate": 0.1},
    {"name": "Mushroom", "protein": 3.1, "carbs": 3.3, "fats": 0.3, "glycemic_load": 1.0, "hidden_oil_estimate": 0.1},
    {"name": "Capsicum", "protein": 1.0, "carbs": 6.0, "fats": 0.3, "glycemic_load": 2.0, "hidden_oil_estimate": 0.1},
    {"name": "Carrot", "protein": 0.9, "carbs": 9.6, "fats": 0.2, "glycemic_load": 4.0, "hidden_oil_estimate": 0.1},
    {"name": "Dark chocolate", "protein": 1.0, "carbs": 6.0, "fats": 5.0, "glycemic_load": 3.0, "hidden_oil_estimate": 0.0},
    {"name": "Milk coffee", "protein": 3.0, "carbs": 4.0, "fats": 2.0, "glycemic_load": 2.0, "hidden_oil_estimate": 0.0},
]


DEFAULT_USER = {
    "age": 38,
    "sex": "Male",
    "triglycerides": 346,
    "hdl": 29,
    "hba1c": 6.0,
    "insulin_resistant": True,
    "diet_type": "Vegetarian + eggs",
    "eating_window_start": "08:00",
    "eating_window_end": "14:00",
    "max_chapati_per_day": 2,
    "no_rice_reset": True,
    "eggs_per_day": 3,
    "whey_per_day": 1,
    "dark_chocolate_max_squares": 2,
    "oil_limit_tsp": 3.0,
    "protein_target_min": 90,
    "protein_target_max": 110,
    "carb_ceiling": 90,
}


def seed_initial_data(db: Session) -> None:
    user_exists = db.scalar(select(User.id).limit(1))
    if not user_exists:
        db.add(User(**DEFAULT_USER))

    existing_food_names = set(db.scalars(select(FoodItem.name)).all())
    for food in FOOD_ITEMS:
        if food["name"] not in existing_food_names:
            db.add(FoodItem(**food))

    db.commit()
