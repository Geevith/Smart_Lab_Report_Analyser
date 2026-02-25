"""
Knowledge Base Loader
Loads and manages the medical insights knowledge base from JSON with version control
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from functools import lru_cache

# Fallback embedded rules (subset for safety)
FALLBACK_RULES = {
    ("Hemoglobin", "Low"): {
        "insight": "Low hemoglobin levels can be associated with anemia. Consult a healthcare provider for proper evaluation.",
        "severity": "MEDIUM"
    },
    ("Hemoglobin", "High"): {
        "insight": "Elevated hemoglobin levels can occur due to dehydration or other conditions. Medical consultation recommended.",
        "severity": "MEDIUM"
    }
}

class KnowledgeBaseLoader:
    """Manages loading and caching of the medical knowledge base"""
    
    def __init__(self, knowledge_base_path: Optional[str] = None):
        """
        Initialize the knowledge base loader
        
        Args:
            knowledge_base_path: Path to knowledge_base.json file.
                               If None, uses default location
        """
        if knowledge_base_path is None:
            # Default to backend/knowledge_base.json
            backend_dir = Path(__file__).parent
            knowledge_base_path = backend_dir / "knowledge_base.json"
        
        self.knowledge_base_path = Path(knowledge_base_path)
        self._cache = None
        self._version = None
    
    @lru_cache(maxsize=1)
    def load_knowledge_base(self) -> Dict[str, Any]:
        """
        Load knowledge base from JSON file with caching
        
        Returns:
            Dictionary containing metadata and rules
        """
        try:
            if not self.knowledge_base_path.exists():
                print(f"Warning: Knowledge base file not found at {self.knowledge_base_path}")
                return self._get_fallback_knowledge_base()
            
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
            
            # Validate schema
            if not self.validate_schema(kb_data):
                print("Warning: Knowledge base schema validation failed")
                return self._get_fallback_knowledge_base()
            
            self._cache = kb_data
            self._version = kb_data.get("metadata", {}).get("version", "unknown")
            
            print(f"✓ Loaded knowledge base v{self._version} with {len(kb_data.get('rules', []))} rules")
            return kb_data
            
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse knowledge base JSON: {e}")
            return self._get_fallback_knowledge_base()
        except Exception as e:
            print(f"Error: Failed to load knowledge base: {e}")
            return self._get_fallback_knowledge_base()
    
    def validate_schema(self, kb_data: Dict[str, Any]) -> bool:
        """
        Validate knowledge base JSON schema
        
        Args:
            kb_data: Knowledge base dictionary
            
        Returns:
            True if valid, False otherwise
        """
        # Check required top-level keys
        if "metadata" not in kb_data or "rules" not in kb_data:
            print("Schema Error: Missing 'metadata' or 'rules' key")
            return False
        
        # Validate metadata
        metadata = kb_data["metadata"]
        required_metadata = ["version", "last_updated", "description"]
        for key in required_metadata:
            if key not in metadata:
                print(f"Schema Error: Missing metadata key '{key}'")
                return False
        
        # Validate rules structure
        rules = kb_data["rules"]
        if not isinstance(rules, list):
            print("Schema Error: 'rules' must be a list")
            return False
        
        # Validate each rule has required fields
        required_rule_fields = ["parameter", "status", "insight", "severity"]
        for i, rule in enumerate(rules):
            for field in required_rule_fields:
                if field not in rule:
                    print(f"Schema Error: Rule {i} missing field '{field}'")
                    return False
        
        return True
    
    def get_insight(
        self, 
        parameter: str, 
        status: str,
        user_age: Optional[int] = None,
        user_gender: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get insight for a specific parameter and status
        
        Args:
            parameter: Parameter name (e.g., "Hemoglobin")
            status: Status (e.g., "High", "Low")
            user_age: Optional user age for personalization
            user_gender: Optional user gender for personalization
            
        Returns:
            Dictionary with insight data or None if not found
        """
        kb_data = self.load_knowledge_base()
        rules = kb_data.get("rules", [])
        
        # Find matching rule
        for rule in rules:
            if rule["parameter"] == parameter and rule["status"] == status:
                # Clone the rule to avoid modifying cache
                result = rule.copy()
                
                # Apply age-specific variant if available
                if user_age is not None and "age_variants" in rule:
                    age_category = self._categorize_age(user_age)
                    if age_category in rule["age_variants"]:
                        result["insight"] = rule["age_variants"][age_category]
                        result["personalized"] = True
                        result["personalization_type"] = f"age_{age_category}"
                
                # Apply gender-specific variant if available
                if user_gender and "gender_variants" in rule:
                    gender_key = user_gender.lower()
                    if gender_key in rule["gender_variants"]:
                        result["insight"] = rule["gender_variants"][gender_key]
                        result["personalized"] = True
                        result["personalization_type"] = f"gender_{gender_key}"
                
                return result
        
        # Fallback to embedded rules
        fallback_key = (parameter, status)
        if fallback_key in FALLBACK_RULES:
            return FALLBACK_RULES[fallback_key]
        
        return None
    
    def get_all_insights_for_parameter(self, parameter: str) -> List[Dict[str, Any]]:
        """
        Get all insights for a specific parameter (all statuses)
        
        Args:
            parameter: Parameter name
            
        Returns:
            List of insight dictionaries
        """
        kb_data = self.load_knowledge_base()
        rules = kb_data.get("rules", [])
        
        return [rule for rule in rules if rule["parameter"] == parameter]
    
    def get_version(self) -> str:
        """Get knowledge base version"""
        if self._version is None:
            kb_data = self.load_knowledge_base()
            self._version = kb_data.get("metadata", {}).get("version", "unknown")
        return self._version
    
    def _categorize_age(self, age: int) -> str:
        """
        Categorize age into groups
        
        Args:
            age: Age in years
            
        Returns:
            Age category: 'pediatric', 'adult', or 'geriatric'
        """
        if age < 18:
            return "pediatric"
        elif age >= 65:
            return "geriatric"
        else:
            return "adult"
    
    def _get_fallback_knowledge_base(self) -> Dict[str, Any]:
        """Get minimal fallback knowledge base"""
        return {
            "metadata": {
                "version": "fallback",
                "last_updated": "N/A",
                "description": "Fallback embedded knowledge base",
                "total_rules": len(FALLBACK_RULES)
            },
            "rules": [
                {
                    "parameter": param,
                    "status": status,
                    "insight": data["insight"],
                    "severity": data["severity"]
                }
                for (param, status), data in FALLBACK_RULES.items()
            ]
        }

# Singleton instance
_loader_instance = None

def get_knowledge_base_loader() -> KnowledgeBaseLoader:
    """Get singleton knowledge base loader instance"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = KnowledgeBaseLoader()
    return _loader_instance
