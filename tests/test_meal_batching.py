#!/usr/bin/env python3
"""
Comprehensive tests for meal batching functionality.
Tests core functionality with in-memory storage before moving to database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.services.meal_batching_memory import InMemoryMealBatchingService
from app.llms.stub_nutrition import StubNutritionLLM
from app.schemas.nutrition import DayNutrition


class TestMealBatching:
    """Test suite for meal batching functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        self.service = InMemoryMealBatchingService()
        self.llm = StubNutritionLLM()
        self.user_id = "test_user"
        self.test_date = "2024-01-15"
    
    def teardown_method(self):
        """Clean up after each test."""
        self.service.clear_all()
    
    def test_golden_flow_three_meals(self):
        """
        Golden test: append 3 meal texts → finalize → expect totals within tolerance.
        This is the core batching functionality.
        """
        # Step 1: Log 3 separate meals
        meal1_id = self.service.log_quick_meal(
            self.user_id, 
            "I had breakfast: 2 eggs scrambled with butter and 2 slices of toast",
            self.test_date
        )
        meal2_id = self.service.log_quick_meal(
            self.user_id,
            "For lunch I had grilled chicken breast with brown rice and steamed broccoli",
            self.test_date
        )
        meal3_id = self.service.log_quick_meal(
            self.user_id,
            "Dinner was salmon fillet with quinoa and mixed vegetables",
            self.test_date
        )
        
        # Verify meals were logged
        assert meal1_id == 0
        assert meal2_id == 1
        assert meal3_id == 2
        
        # Step 2: Verify pending meals
        pending = self.service.get_pending_meals(self.user_id, self.test_date)
        assert len(pending) == 3
        assert "breakfast" in pending[0].lower()
        assert "lunch" in pending[1].lower()
        assert "dinner" in pending[2].lower()
        
        # Step 3: Process daily summary (single LLM call)
        day_nutrition, warnings = self.service.process_daily_summary(
            self.user_id, self.llm, self.test_date
        )
        
        # Step 4: Verify results
        assert isinstance(day_nutrition, DayNutrition)
        assert len(day_nutrition.meals) == 3  # Should have 3 meals
        
        # Check that totals are reasonable (within expected ranges)
        assert 100 <= day_nutrition.total_protein_g <= 120  # Should be around 101.5g
        assert 80 <= day_nutrition.total_carb_g <= 90      # Should be around 85.3g
        assert 25 <= day_nutrition.total_fat_g <= 35       # Should be around 29.8g
        assert 1000 <= day_nutrition.total_kcal <= 1100    # Should be around 1050 kcal
        
        # Step 5: Verify pending meals are cleared after processing
        pending_after = self.service.get_pending_meals(self.user_id, self.test_date)
        assert len(pending_after) == 0
        
        # Step 6: Verify we can retrieve the summary
        retrieved = self.service.get_daily_summary(self.user_id, self.test_date)
        assert retrieved is not None
        assert retrieved.total_protein_g == day_nutrition.total_protein_g
        
        print(f"✅ Golden test passed! Processed 3 meals with totals: {day_nutrition.total_protein_g:.1f}g protein, {day_nutrition.total_carb_g:.1f}g carbs, {day_nutrition.total_fat_g:.1f}g fat, {day_nutrition.total_kcal:.0f} kcal")
    
    def test_edit_flow_post_hoc_edit(self):
        """
        Edit flow test: one post-hoc edit allowed → re-finalize overwrites artifact.
        """
        # Step 1: Log and process initial meals
        self.service.log_quick_meal(self.user_id, "breakfast: eggs and toast", self.test_date)
        self.service.log_quick_meal(self.user_id, "lunch: chicken and rice", self.test_date)
        
        original_nutrition, _ = self.service.process_daily_summary(
            self.user_id, self.llm, self.test_date
        )
        original_protein = original_nutrition.total_protein_g
        
        # Step 2: Create edited nutrition (increase protein by 10g)
        # We need to update the actual meal items to match the new totals
        from app.schemas.nutrition import Meal, MealItem
        
        # Create new items with increased protein
        new_items = []
        for meal in original_nutrition.meals:
            for item in meal.items:
                new_item = MealItem(
                    name=item.name,
                    grams=item.grams,
                    protein_g=item.protein_g + 5.0,  # Increase protein
                    carb_g=item.carb_g,
                    fat_g=item.fat_g,
                    kcal=item.kcal + 20  # Increase calories
                )
                new_items.append(new_item)
        
        new_meals = [Meal(name="Combined", items=new_items)]
        
        edited_nutrition = DayNutrition(
            meals=new_meals,
            total_protein_g=original_protein + 10.0,
            total_carb_g=original_nutrition.total_carb_g,
            total_fat_g=original_nutrition.total_fat_g,
            total_kcal=original_nutrition.total_kcal + 40
        )
        
        # Step 3: Apply the edit
        updated_nutrition, warnings = self.service.edit_daily_summary(
            self.user_id, self.test_date, edited_nutrition
        )
        
        # Step 4: Verify edit was applied
        assert updated_nutrition.total_protein_g == original_protein + 10.0
        assert updated_nutrition.total_kcal == original_nutrition.total_kcal + 40
        
        # Step 5: Verify the stored result was overwritten
        retrieved = self.service.get_daily_summary(self.user_id, self.test_date)
        assert retrieved.total_protein_g == original_protein + 10.0
        
        # Step 6: Verify edit count was incremented
        history = self.service.get_meal_history(self.user_id, 1)
        assert len(history) == 1
        assert history[0]['edit_count'] == 1
        
        print(f"✅ Edit flow test passed! Original protein: {original_protein:.1f}g, Edited: {updated_nutrition.total_protein_g:.1f}g")
    
    def test_edit_limit_enforcement(self):
        """Test that edit limit (2 edits per day) is enforced."""
        # Process initial meals
        self.service.log_quick_meal(self.user_id, "breakfast: eggs", self.test_date)
        original_nutrition, _ = self.service.process_daily_summary(self.user_id, self.llm, self.test_date)
        
        # First edit should work - create valid nutrition with increased protein
        from app.schemas.nutrition import Meal, MealItem
        
        new_items1 = []
        for meal in original_nutrition.meals:
            for item in meal.items:
                new_item = MealItem(
                    name=item.name,
                    grams=item.grams,
                    protein_g=item.protein_g + 2.5,
                    carb_g=item.carb_g,
                    fat_g=item.fat_g,
                    kcal=item.kcal + 10
                )
                new_items1.append(new_item)
        
        edited1 = DayNutrition(
            meals=[Meal(name="Combined", items=new_items1)],
            total_protein_g=original_nutrition.total_protein_g + 5.0,
            total_carb_g=original_nutrition.total_carb_g,
            total_fat_g=original_nutrition.total_fat_g,
            total_kcal=original_nutrition.total_kcal + 20
        )
        self.service.edit_daily_summary(self.user_id, self.test_date, edited1)
        
        # Second edit should work
        new_items2 = []
        for meal in original_nutrition.meals:
            for item in meal.items:
                new_item = MealItem(
                    name=item.name,
                    grams=item.grams,
                    protein_g=item.protein_g + 5.0,
                    carb_g=item.carb_g,
                    fat_g=item.fat_g,
                    kcal=item.kcal + 20
                )
                new_items2.append(new_item)
        
        edited2 = DayNutrition(
            meals=[Meal(name="Combined", items=new_items2)],
            total_protein_g=original_nutrition.total_protein_g + 10.0,
            total_carb_g=original_nutrition.total_carb_g,
            total_fat_g=original_nutrition.total_fat_g,
            total_kcal=original_nutrition.total_kcal + 40
        )
        self.service.edit_daily_summary(self.user_id, self.test_date, edited2)
        
        # Third edit should fail
        new_items3 = []
        for meal in original_nutrition.meals:
            for item in meal.items:
                new_item = MealItem(
                    name=item.name,
                    grams=item.grams,
                    protein_g=item.protein_g + 7.5,
                    carb_g=item.carb_g,
                    fat_g=item.fat_g,
                    kcal=item.kcal + 30
                )
                new_items3.append(new_item)
        
        edited3 = DayNutrition(
            meals=[Meal(name="Combined", items=new_items3)],
            total_protein_g=original_nutrition.total_protein_g + 15.0,
            total_carb_g=original_nutrition.total_carb_g,
            total_fat_g=original_nutrition.total_fat_g,
            total_kcal=original_nutrition.total_kcal + 60
        )
        
        with pytest.raises(ValueError, match="Maximum edit limit"):
            self.service.edit_daily_summary(self.user_id, self.test_date, edited3)
        
        print("✅ Edit limit test passed! Correctly enforced 2-edit limit")
    
    def test_whole_day_processing(self):
        """Test processing a whole day's nutrition in one go."""
        # Log a whole day's worth of meals as a single input
        whole_day_text = "Today I had breakfast: 2 eggs and toast, lunch: chicken breast with brown rice and broccoli, dinner: salmon with quinoa and vegetables"
        
        # Process as whole day (should trigger immediate LLM call)
        day_nutrition, warnings = self.service._parse_with_llm(whole_day_text, self.llm)
        
        # Verify results
        assert isinstance(day_nutrition, DayNutrition)
        assert len(day_nutrition.meals) == 3  # Should have 3 meals
        
        # Check totals are reasonable
        assert day_nutrition.total_protein_g > 90
        assert day_nutrition.total_carb_g > 70
        assert day_nutrition.total_fat_g > 20
        assert day_nutrition.total_kcal > 900
        
        print(f"✅ Whole day processing test passed! Processed all meals at once: {day_nutrition.total_kcal:.0f} kcal")
    
    def test_meal_history_tracking(self):
        """Test meal history tracking across multiple days."""
        # Process meals for two different days
        self.service.log_quick_meal(self.user_id, "breakfast: eggs", "2024-01-15")
        self.service.process_daily_summary(self.user_id, self.llm, "2024-01-15")
        
        self.service.log_quick_meal(self.user_id, "breakfast: oatmeal", "2024-01-16")
        self.service.process_daily_summary(self.user_id, self.llm, "2024-01-16")
        
        # Get history
        history = self.service.get_meal_history(self.user_id, 7)
        
        # Verify history
        assert len(history) == 2
        assert history[0]['date'] == "2024-01-16"  # Most recent first
        assert history[1]['date'] == "2024-01-15"
        
        # Verify each entry has required fields
        for entry in history:
            assert 'date' in entry
            assert 'summary' in entry
            assert 'edit_count' in entry
            assert 'nutrition' in entry
            assert isinstance(entry['nutrition'], DayNutrition)
        
        print("✅ Meal history test passed! Correctly tracked meals across multiple days")
    
    def test_no_pending_meals_error(self):
        """Test error handling when trying to process with no pending meals."""
        # Try to process with no meals logged
        with pytest.raises(ValueError, match="No pending meals found"):
            self.service.process_daily_summary(self.user_id, self.llm, self.test_date)
        
        print("✅ No pending meals error test passed!")
    
    def test_edit_nonexistent_summary_error(self):
        """Test error handling when trying to edit a non-existent summary."""
        from app.schemas.nutrition import Meal, MealItem
        
        # Create a valid nutrition object with at least one meal
        items = [MealItem(name="Test", grams=100, protein_g=10, carb_g=20, fat_g=5, kcal=150)]
        meals = [Meal(name="Test Meal", items=items)]
        
        edited_nutrition = DayNutrition(
            meals=meals,
            total_protein_g=10,
            total_carb_g=20,
            total_fat_g=5,
            total_kcal=150
        )
        
        with pytest.raises(ValueError, match="No daily summary found"):
            self.service.edit_daily_summary(self.user_id, self.test_date, edited_nutrition)
        
        print("✅ Edit nonexistent summary error test passed!")
    
    def test_nutrition_validation(self):
        """Test nutrition data validation and consistency checks."""
        # Create nutrition data with mismatched totals
        from app.schemas.nutrition import Meal, MealItem
        
        # Items that sum to different totals than declared
        items = [
            MealItem(name="Test Item", grams=100, protein_g=10.0, carb_g=20.0, fat_g=5.0, kcal=150)
        ]
        meals = [Meal(name="Test Meal", items=items)]
        
        # This should fail validation due to mismatched totals
        with pytest.raises(ValueError, match="Total protein mismatch"):
            DayNutrition(
                meals=meals,
                total_protein_g=5.0,  # Wrong total
                total_carb_g=20.0,
                total_fat_g=5.0,
                total_kcal=150
            )
        
        print("✅ Nutrition validation test passed! Correctly caught total mismatch")


def run_tests():
    """Run all tests and report results."""
    print("🧪 Running Meal Batching Tests")
    print("=" * 50)
    
    test_instance = TestMealBatching()
    
    tests = [
        ("Golden Flow (3 meals → finalize → check totals)", test_instance.test_golden_flow_three_meals),
        ("Edit Flow (post-hoc edit → re-finalize)", test_instance.test_edit_flow_post_hoc_edit),
        ("Edit Limit Enforcement", test_instance.test_edit_limit_enforcement),
        ("Whole Day Processing", test_instance.test_whole_day_processing),
        ("Meal History Tracking", test_instance.test_meal_history_tracking),
        ("No Pending Meals Error", test_instance.test_no_pending_meals_error),
        ("Edit Nonexistent Summary Error", test_instance.test_edit_nonexistent_summary_error),
        ("Nutrition Validation", test_instance.test_nutrition_validation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_instance.setup_method()
            test_func()
            test_instance.teardown_method()
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            test_instance.teardown_method()
            print(f"❌ {test_name}: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Core functionality is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please fix issues before proceeding.")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
