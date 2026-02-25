"""
Personalization Engine
Provides age, gender, and demographic-aware insight customization
"""

from typing import Dict, Any, Optional

class PersonalizationEngine:
    """Handles demographic-based personalization of medical insights"""
    
    def __init__(self):
        # Age range definitions
        self.age_ranges = {
            "pediatric": (0, 17),
            "young_adult": (18, 39),
            "middle_age": (40, 64),
            "geriatric": (65, 120)
        }
    
    def personalize_insight(
        self,
        base_insight: str,
        parameter: str,
        status: str,
        user_demographics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Personalize an insight based on user demographics
        
        Args:
            base_insight: The base insight text
            parameter: Parameter name
            status: Parameter status
            user_demographics: Dict with keys: age, gender, ethnicity
            
        Returns:
            Dict with personalized_insight, personalization_applied, context
        """
        if not user_demographics:
            return {
                "insight": base_insight,
                "personalization_applied": False,
                "context": None
            }
        
        age = user_demographics.get("age")
        gender = user_demographics.get("gender")
        
        personalized_insight = base_insight
        personalization_notes = []
        
        # Apply age-based adjustments
        if age is not None:
            age_adjustment = self.adjust_for_age(parameter, status, age, base_insight)
            if age_adjustment:
                personalized_insight = age_adjustment["insight"]
                personalization_notes.append(age_adjustment["context"])
        
        # Apply gender-based adjustments
        if gender:
            gender_adjustment = self.adjust_for_gender(parameter, status, gender, personalized_insight)
            if gender_adjustment:
                personalized_insight = gender_adjustment["insight"]
                personalization_notes.append(gender_adjustment["context"])
        
        return {
            "insight": personalized_insight,
            "personalization_applied": len(personalization_notes) > 0,
            "context": " ".join(personalization_notes) if personalization_notes else None
        }
    
    def adjust_for_age(
        self,
        parameter: str,
        status: str,
        age: int,
        base_insight: str
    ) -> Optional[Dict[str, Any]]:
        """
        Apply age-specific insight adjustments
        
        Args:
            parameter: Parameter name
            status: Parameter status
            age: User age in years
            base_insight: Base insight text
            
        Returns:
            Dict with adjusted insight and context, or None if no adjustment
        """
        age_category = self._get_age_category(age)
        
        # Age-specific modifications for certain parameters
        age_specific_notes = {
            ("Hemoglobin", "Low", "pediatric"): {
                "suffix": " In children, this is often related to growth spurts and dietary needs.",
                "context": "Based on pediatric age range"
            },
            ("Hemoglobin", "Low", "geriatric"): {
                "suffix": " In older adults, chronic disease and bone marrow changes should be considered.",
                "context": "Based on senior age range"
            },
            ("Total Cholesterol", "High", "young_adult"): {
                "suffix": " At your age, lifestyle modifications can be highly effective.",
                "context": "Based on your age group"
            },
            ("Total Cholesterol", "High", "geriatric"): {
                "suffix": " Consider discussing medication options with your doctor alongside lifestyle changes.",
                "context": "Based on senior age range"
            },
            ("TSH", "High", "geriatric"): {
                "suffix": " Hypothyroidism is common in older adults and may present with subtle symptoms.",
                "context": "Based on senior age range"
            },
            ("Vitamin B12", "Low", "geriatric"): {
                "suffix": " B12 absorption decreases with age; supplements or injections may be more effective than dietary changes alone.",
                "context": "Based on senior age range"
            },
            ("Creatinine", "High", "geriatric"): {
                "suffix": " Kidney function naturally declines with age, but this still warrants evaluation.",
                "context": "Based on senior age range"
            }
        }
        
        key = (parameter, status, age_category)
        if key in age_specific_notes:
            adjustment = age_specific_notes[key]
            return {
                "insight": base_insight + adjustment["suffix"],
                "context": adjustment["context"]
            }
        
        return None
    
    def adjust_for_gender(
        self,
        parameter: str,
        status: str,
        gender: str,
        base_insight: str
    ) -> Optional[Dict[str, Any]]:
        """
        Apply gender-specific insight adjustments
        
        Args:
            parameter: Parameter name
            status: Parameter status
            gender: User gender ('male', 'female', 'other')
            base_insight: Base insight text
            
        Returns:
            Dict with adjusted insight and context, or None if no adjustment
        """
        gender = gender.lower()
        
        # Gender-specific modifications
        gender_specific_notes = {
            ("Hemoglobin", "Low", "female"): {
                "suffix": " For women, heavy menstrual periods are a common cause.",
                "context": "Based on your gender"
            },
            ("Hemoglobin", "Low", "male"): {
                "suffix": " In men, this may warrant investigation for gastrointestinal bleeding.",
                "context": "Based on your gender"
            },
            ("Creatinine", "High", "male"): {
                "suffix": " Reference ranges for creatinine are typically higher in men due to greater muscle mass.",
                "context": "Based on your gender"
            },
            ("PSA", "High", "male"): {
                "suffix": " PSA levels naturally increase with age in men. Discuss prostate health screening with your doctor.",
                "context": "Based on male-specific marker"
            }
        }
        
        key = (parameter, status, gender)
        if key in gender_specific_notes:
            adjustment = gender_specific_notes[key]
            return {
                "insight": base_insight + adjustment["suffix"],
                "context": adjustment["context"]
            }
        
        return None
    
    def _get_age_category(self, age: int) -> str:
        """Get age category for a given age"""
        for category, (min_age, max_age) in self.age_ranges.items():
            if min_age <= age <= max_age:
                return category
        return "adult"  # Default
    
    def get_age_appropriate_reference_note(self, parameter: str, age: int) -> Optional[str]:
        """
        Get age-appropriate reference range note
        
        Args:
            parameter: Parameter name
            age: User age
            
        Returns:
            Note about age-specific ranges or None
        """
        age_category = self._get_age_category(age)
        
        if age_category == "pediatric":
            return "Note: Reference ranges for children differ from adults. Consult pediatric guidelines."
        elif age_category == "geriatric":
            return "Note: Some reference ranges may vary for older adults."
        
        return None


# Singleton instance
_personalization_engine = None

def get_personalization_engine() -> PersonalizationEngine:
    """Get singleton personalization engine instance"""
    global _personalization_engine
    if _personalization_engine is None:
        _personalization_engine = PersonalizationEngine()
    return _personalization_engine
