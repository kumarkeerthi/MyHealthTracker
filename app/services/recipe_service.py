from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyLog, MetabolicProfile, Recipe


class RecipeService:
    def list_recipes(self, db: Session) -> list[Recipe]:
        return db.scalars(select(Recipe).order_by(Recipe.carbs.asc(), Recipe.name.asc())).all()

    def suggest_recipes(self, db: Session, user_id: int, profile: MetabolicProfile, consumed_at: datetime | None = None) -> tuple[float, str, list[Recipe]]:
        target_date = (consumed_at or datetime.utcnow()).date()
        today_log = db.scalar(select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date == target_date))
        current_carbs = today_log.total_carbs if today_log else 0.0
        carb_remaining = round(max(0.0, profile.carb_ceiling - current_carbs), 2)

        all_recipes = self.list_recipes(db)
        in_budget = [recipe for recipe in all_recipes if recipe.carbs <= carb_remaining]
        selected = (in_budget or all_recipes)[:3]

        if selected:
            top_recipe = selected[0].name
            suggestion = f"Based on carb load remaining, try: {top_recipe}."
        else:
            suggestion = "No recipes available right now."

        return carb_remaining, suggestion, selected


recipe_service = RecipeService()
