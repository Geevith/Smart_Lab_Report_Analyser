"""
Lifestyle Recommendations Module
Provides lifestyle advice, symptom questions, and external resource links
"""

from typing import Dict, List, Any, Optional


class LifestyleRecommendations:
    """Generates lifestyle recommendations and external resources for parameters"""
    
    def get_lifestyle_advice(
        self,
        parameter: str,
        status: str,
        insight_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get lifestyle recommendations for a parameter
        
        Args:
            parameter: Parameter name
            status: Parameter status
            insight_data: Optional insight data from knowledge base
            
        Returns:
            Dict with diet, exercise, lifestyle tips
        """
        # If insight_data from knowledge base has lifestyle info, use it
        if insight_data and "lifestyle" in insight_data:
            return insight_data["lifestyle"]
        
        # Fallback generic recommendations
        return self._get_generic_lifestyle_advice(parameter, status)
    
    def get_symptom_questions(
        self,
        parameter: str,
        status: str,
        insight_data: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Get "Questions for Your Doctor" based on parameter
        
        Args:
            parameter: Parameter name
            status: Parameter status
            insight_data: Optional insight data from knowledge base
            
        Returns:
            List of questions to discuss with healthcare provider
        """
        # If insight_data has symptom questions, use them
        if insight_data and "symptom_questions" in insight_data:
            return insight_data["symptom_questions"]
        
        # Generic questions
        return [
            f"What might be causing my {status.lower()} {parameter}?",
            "Do I need additional tests or follow-up?",
            "What symptoms should I watch for?"
        ]
    
    def get_external_resources(
        self,
        parameter: str,
        status: str,
        insight_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Get external educational resource links
        
        Args:
            parameter: Parameter name
            status: Parameter status
            insight_data: Optional insight data from knowledge base
            
        Returns:
            List of dicts with 'name' and 'url' keys
        """
        # If insight_data has external resources, use them
        if insight_data and "external_resources" in insight_data:
            return insight_data["external_resources"]
        
        # Generic resources
        return [
            {
                "name": "MedlinePlus - Health Topics",
                "url": "https://medlineplus.gov/"
            },
            {
                "name": "Mayo Clinic - Diseases & Conditions",
                "url": "https://www.mayoclinic.org/diseases-conditions"
            }
        ]
    
    def _get_generic_lifestyle_advice(self, parameter: str, status: str) -> Dict[str, List[str]]:
        """Get generic lifestyle advice when specific not available"""
        
        # General healthy living advice
        general_advice = {
            "general": [
                "Maintain a balanced diet rich in fruits, vegetables, and whole grains",
                "Stay well-hydrated throughout the day",
                "Get regular physical activity as recommended by your doctor",
                "Ensure adequate sleep (7-9 hours for adults)",
                "Manage stress through relaxation techniques"
            ]
        }
        
        return general_advice


# Singleton instance
_lifestyle_recommendations = None

def get_lifestyle_recommendations() -> LifestyleRecommendations:
    """Get singleton lifestyle recommendations instance"""
    global _lifestyle_recommendations
    if _lifestyle_recommendations is None:
        _lifestyle_recommendations = LifestyleRecommendations()
    return _lifestyle_recommendations
