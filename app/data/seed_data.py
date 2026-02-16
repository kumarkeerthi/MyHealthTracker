from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import FoodItem, HabitChallengeType, HabitCheckin, HabitDefinition, MetabolicAgentState, MetabolicProfile, NotificationSettings, Recipe, User


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
    {"name": "Almond (10 pieces)", "protein": 2.6, "carbs": 2.4, "sugar": 0.5, "fiber": 1.4, "fats": 6.1, "glycemic_load": 0.2, "hdl_support_score": 8.5, "triglyceride_risk_weight": 0.2, "food_group": "nut", "hidden_oil_estimate": 0.0},
    {"name": "Walnut (2 halves)", "protein": 0.9, "carbs": 0.8, "sugar": 0.2, "fiber": 0.4, "fats": 4.5, "glycemic_load": 0.1, "hdl_support_score": 9.0, "triglyceride_risk_weight": 0.2, "food_group": "nut", "hidden_oil_estimate": 0.0},
    {"name": "Pistachio (10 pieces)", "protein": 2.2, "carbs": 2.8, "sugar": 1.0, "fiber": 1.1, "fats": 4.4, "glycemic_load": 0.6, "hdl_support_score": 7.8, "triglyceride_risk_weight": 0.3, "food_group": "nut", "hidden_oil_estimate": 0.0},
    {"name": "Cashew (5 pieces)", "protein": 1.5, "carbs": 4.3, "sugar": 1.0, "fiber": 0.3, "fats": 4.0, "glycemic_load": 1.0, "hdl_support_score": 6.5, "triglyceride_risk_weight": 0.5, "food_group": "nut", "hidden_oil_estimate": 0.0},
    {"name": "Flaxseed (1 tbsp)", "protein": 1.9, "carbs": 3.0, "sugar": 0.2, "fiber": 2.8, "fats": 4.3, "glycemic_load": 0.2, "hdl_support_score": 9.5, "triglyceride_risk_weight": 0.1, "food_group": "nut", "nut_seed_exception": True, "hidden_oil_estimate": 0.0},
    {"name": "Chia seed (1 tbsp)", "protein": 1.7, "carbs": 4.9, "sugar": 0.0, "fiber": 4.1, "fats": 3.1, "glycemic_load": 0.2, "hdl_support_score": 9.3, "triglyceride_risk_weight": 0.1, "food_group": "nut", "nut_seed_exception": True, "hidden_oil_estimate": 0.0},
    {"name": "Apple (1 medium)", "protein": 0.5, "carbs": 25.0, "sugar": 19.0, "fiber": 4.4, "fats": 0.3, "glycemic_load": 6.0, "hdl_support_score": 2.0, "triglyceride_risk_weight": 0.5, "food_group": "fruit", "hidden_oil_estimate": 0.0},
    {"name": "Guava (1 medium)", "protein": 2.6, "carbs": 14.0, "sugar": 9.0, "fiber": 5.4, "fats": 1.0, "glycemic_load": 3.0, "hdl_support_score": 4.2, "triglyceride_risk_weight": 0.3, "food_group": "fruit", "hidden_oil_estimate": 0.0},
    {"name": "Pomegranate (1/2 cup)", "protein": 1.5, "carbs": 16.0, "sugar": 12.0, "fiber": 3.5, "fats": 1.0, "glycemic_load": 5.0, "hdl_support_score": 3.6, "triglyceride_risk_weight": 0.4, "food_group": "fruit", "hidden_oil_estimate": 0.0},
    {"name": "Orange (1 medium)", "protein": 1.2, "carbs": 15.0, "sugar": 12.0, "fiber": 3.1, "fats": 0.2, "glycemic_load": 4.0, "hdl_support_score": 2.8, "triglyceride_risk_weight": 0.3, "food_group": "fruit", "hidden_oil_estimate": 0.0},
    {"name": "Berries (1/2 cup)", "protein": 0.8, "carbs": 8.0, "sugar": 5.0, "fiber": 3.6, "fats": 0.3, "glycemic_load": 2.0, "hdl_support_score": 3.2, "triglyceride_risk_weight": 0.2, "food_group": "fruit", "hidden_oil_estimate": 0.0},
    {"name": "Papaya (small portion)", "protein": 0.7, "carbs": 11.0, "sugar": 8.0, "fiber": 1.7, "fats": 0.3, "glycemic_load": 3.0, "hdl_support_score": 2.1, "triglyceride_risk_weight": 0.3, "food_group": "fruit", "hidden_oil_estimate": 0.0},
    {"name": "Banana", "protein": 1.3, "carbs": 27.0, "sugar": 14.0, "fiber": 3.1, "fats": 0.3, "glycemic_load": 13.0, "hdl_support_score": 1.0, "triglyceride_risk_weight": 0.9, "food_group": "fruit", "high_carb_flag": True, "hidden_oil_estimate": 0.0},
    {"name": "Mango", "protein": 1.0, "carbs": 25.0, "sugar": 22.0, "fiber": 2.6, "fats": 0.4, "glycemic_load": 12.0, "hdl_support_score": 1.3, "triglyceride_risk_weight": 1.0, "food_group": "fruit", "high_carb_flag": True, "hidden_oil_estimate": 0.0},
    {"name": "Grapes", "protein": 0.6, "carbs": 18.0, "sugar": 15.0, "fiber": 1.0, "fats": 0.2, "glycemic_load": 11.0, "hdl_support_score": 1.0, "triglyceride_risk_weight": 0.8, "food_group": "fruit", "high_carb_flag": True, "hidden_oil_estimate": 0.0},
]


RECIPES = [
    {
        "name": "Spinach egg scramble",
        "ingredients": "Spinach, whole eggs, onion, garlic, turmeric, chili, salt",
        "protein": 20.0,
        "carbs": 6.0,
        "fats": 14.0,
        "cooking_time_minutes": 12,
        "oil_usage_tsp": 0.5,
        "insulin_score_impact": 0.25,
        "external_link_primary": "https://www.tarladalal.com/healthy-subzis-and-vegetables-recipes",
        "external_link_secondary": "https://www.indianhealthyrecipes.com/",
    },
    {
        "name": "Bhindi stir fry",
        "ingredients": "Bhindi, onion, cumin, turmeric, coriander, salt",
        "protein": 3.0,
        "carbs": 10.0,
        "fats": 4.0,
        "cooking_time_minutes": 18,
        "oil_usage_tsp": 0.75,
        "insulin_score_impact": 0.45,
        "external_link_primary": "https://www.tarladalal.com/healthy-subzis-and-vegetables-recipes",
        "external_link_secondary": "https://www.vegrecipesofindia.com/bhindi-recipes/",
    },
    {
        "name": "Paneer sauté",
        "ingredients": "Paneer, capsicum, onion, cumin, pepper, salt",
        "protein": 22.0,
        "carbs": 7.0,
        "fats": 18.0,
        "cooking_time_minutes": 15,
        "oil_usage_tsp": 0.75,
        "insulin_score_impact": 0.35,
        "external_link_primary": "https://www.tarladalal.com/healthy-subzis-and-vegetables-recipes",
        "external_link_secondary": "https://www.indianhealthyrecipes.com/paneer-recipes/",
    },
    {
        "name": "Broccoli lemon stir fry",
        "ingredients": "Broccoli, garlic, lemon juice, pepper, salt",
        "protein": 5.0,
        "carbs": 9.0,
        "fats": 3.0,
        "cooking_time_minutes": 10,
        "oil_usage_tsp": 0.5,
        "insulin_score_impact": 0.3,
        "external_link_primary": "https://www.tarladalal.com/healthy-subzis-and-vegetables-recipes",
        "external_link_secondary": "https://www.indianhealthyrecipes.com/broccoli-recipes/",
    },
    {
        "name": "Low oil sambar",
        "ingredients": "Toor dal, mixed vegetables, tamarind, sambar powder, mustard, curry leaves",
        "protein": 9.0,
        "carbs": 16.0,
        "fats": 4.0,
        "cooking_time_minutes": 30,
        "oil_usage_tsp": 0.5,
        "insulin_score_impact": 0.55,
        "external_link_primary": "https://www.tarladalal.com/healthy-subzis-and-vegetables-recipes",
        "external_link_secondary": "https://www.indianhealthyrecipes.com/sambar-recipe-make-sambar/",
    },
]


HABIT_DEFINITIONS = [
    {
        "code": "no_carb_dinner",
        "name": "No carb dinner",
        "description": "Keep dinner carb-light to protect overnight glucose stability.",
        "challenge_type": HabitChallengeType.STRICT,
    },
    {
        "code": "protein_first",
        "name": "Protein first",
        "description": "Start meals with a protein source before carbs.",
        "challenge_type": HabitChallengeType.STRICT,
    },
    {
        "code": "post_meal_walk",
        "name": "Post-meal walk",
        "description": "Walk for at least 10 minutes after a main meal.",
        "challenge_type": HabitChallengeType.MICRO,
    },
    {
        "code": "strength_training",
        "name": "Strength training",
        "description": "Complete at least one structured strength session.",
        "challenge_type": HabitChallengeType.STRICT,
    },
    {
        "code": "oil_under_limit",
        "name": "Oil under limit",
        "description": "Keep visible + hidden oil under your daily cap.",
        "challenge_type": HabitChallengeType.STRICT,
    },
    {
        "code": "sleep_over_7h",
        "name": "Sleep > 7 hours",
        "description": "Sleep 7+ hours to improve metabolic recovery.",
        "challenge_type": HabitChallengeType.SUPPORT,
    },
]

DEFAULT_USER = {
    "email": "demo@myhealthtracker.local",
    "hashed_password": hash_password("ChangeMe123!"),
    "role": "admin",
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


DEFAULT_METABOLIC_PROFILE = {
    "protein_target_min": 90,
    "protein_target_max": 110,
    "carb_ceiling": 90,
    "oil_limit_tsp": 3,
    "fasting_start_time": "14:00",
    "fasting_end_time": "08:00",
    "max_chapati_per_day": 2,
    "allow_rice": False,
    "chocolate_limit_per_day": 2,
    "insulin_score_green_threshold": 40,
    "insulin_score_yellow_threshold": 70,
}


def seed_initial_data(db: Session) -> None:
    user = db.scalar(select(User).limit(1))
    if not user:
        user = User(**DEFAULT_USER)
        db.add(user)
        db.flush()

    profile_exists = db.scalar(select(MetabolicProfile.id).where(MetabolicProfile.user_id == user.id))
    if not profile_exists:
        db.add(MetabolicProfile(user_id=user.id, **DEFAULT_METABOLIC_PROFILE))

    notification_settings_exists = db.scalar(select(NotificationSettings.id).where(NotificationSettings.user_id == user.id))
    if not notification_settings_exists:
        db.add(NotificationSettings(user_id=user.id))

    agent_state_exists = db.scalar(select(MetabolicAgentState.user_id).where(MetabolicAgentState.user_id == user.id))
    if not agent_state_exists:
        db.add(
            MetabolicAgentState(
                user_id=user.id,
                carb_ceiling_current=user.carb_ceiling,
                protein_target_current=user.protein_target_min,
                fruit_allowance_current=1,
                fruit_allowance_weekly=7,
                notes="Initialized from seed defaults.",
            )
        )

    existing_food_names = set(db.scalars(select(FoodItem.name)).all())
    for food in FOOD_ITEMS:
        if food["name"] not in existing_food_names:
            db.add(FoodItem(**food))

    existing_recipe_names = set(db.scalars(select(Recipe.name)).all())
    for recipe in RECIPES:
        if recipe["name"] not in existing_recipe_names:
            db.add(Recipe(**recipe))

    existing_habit_codes = set(db.scalars(select(HabitDefinition.code)).all())
    for habit in HABIT_DEFINITIONS:
        if habit["code"] not in existing_habit_codes:
            db.add(HabitDefinition(**habit))

    db.flush()

    # Seed a lightweight history so behavior analytics can render immediately.
    habits = db.scalars(select(HabitDefinition).where(HabitDefinition.active.is_(True))).all()
    if habits:
        from datetime import date, timedelta

        start = date.today() - timedelta(days=29)
        for offset in range(30):
            current_day = start + timedelta(days=offset)
            is_sunday = current_day.weekday() == 6
            for habit in habits:
                exists = db.scalar(
                    select(HabitCheckin.id).where(
                        HabitCheckin.user_id == user.id,
                        HabitCheckin.habit_id == habit.id,
                        HabitCheckin.habit_date == current_day,
                    )
                )
                if exists:
                    continue

                failure_reason = None
                success = True
                if habit.code == "no_carb_dinner" and is_sunday:
                    success = False
                    failure_reason = "Social dinner carb spike"
                elif habit.code == "sleep_over_7h" and current_day.weekday() in {0, 1}:
                    success = False
                    failure_reason = "Late-night work carried into sleep"
                elif habit.code == "post_meal_walk" and current_day.weekday() == 5:
                    success = False
                    failure_reason = "Weekend schedule drift"

                db.add(
                    HabitCheckin(
                        user_id=user.id,
                        habit_id=habit.id,
                        habit_date=current_day,
                        success=success,
                        failure_reason=failure_reason,
                        challenge_type_used=habit.challenge_type,
                    )
                )


    db.commit()
