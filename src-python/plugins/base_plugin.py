from abc import ABC, abstractmethod
from typing import Dict, Any


class BasePlugin(ABC):
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plugin action"""
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if plugin is properly configured"""
        pass

