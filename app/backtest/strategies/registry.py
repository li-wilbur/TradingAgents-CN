import importlib
import pkgutil
import inspect
from typing import Dict, List, Type, Any
import logging
from app.backtest.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)

class StrategyRegistry:
    """
    Central registry for discovering and managing strategies.
    """
    _strategies: Dict[str, Type[BaseStrategy]] = {}

    @classmethod
    def discover_strategies(cls, package_path: str = "app.backtest.strategies.examples"):
        """
        Dynamically import strategy modules from the specified package to trigger registration.
        """
        try:
            # Import the package
            package = importlib.import_module(package_path)
            
            # Walk through modules in the package
            if hasattr(package, "__path__"):
                for _, name, _ in pkgutil.iter_modules(package.__path__):
                    full_name = f"{package_path}.{name}"
                    importlib.import_module(full_name)
                    
            # After import, scan subclasses of BaseStrategy
            cls._scan_subclasses()
            
        except ImportError as e:
            logger.error(f"Failed to discover strategies in {package_path}: {e}")

    @classmethod
    def _scan_subclasses(cls):
        """
        Scan all subclasses of BaseStrategy and register them.
        """
        for subclass in BaseStrategy.__subclasses__():
            # Skip intermediate base classes if any (optional check)
            if subclass.__module__.startswith("app.backtest.strategies.base"):
                continue
                
            strategy_id = subclass.__name__
            cls._strategies[strategy_id] = subclass
            logger.info(f"Registered strategy: {strategy_id} ({subclass.metadata.get('name')})")

    @classmethod
    def get_strategy(cls, strategy_id: str) -> Type[BaseStrategy]:
        """Get a strategy class by its ID"""
        return cls._strategies.get(strategy_id)

    @classmethod
    def get_all_strategies(cls) -> List[Dict[str, Any]]:
        """Get schema for all registered strategies"""
        return [s.get_schema() for s in cls._strategies.values()]

# Global registry instance (optional, as class methods are used)
registry = StrategyRegistry
