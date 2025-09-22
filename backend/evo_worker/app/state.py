from abc import ABC, abstractmethod
from typing import Any, Dict


class Stateful(ABC):
    """Abstract base class for objects that can save and restore their state."""

    @property
    @abstractmethod
    def fallback_state(self) -> Dict[str, Any]:
        """Get the fallback state of the object.

        Returns:
            Dict[str, Any]: Dictionary containing the object's state
        """

    @abstractmethod
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        """Restore the object's state from fallback state.

        Args:
            fallback_state (Dict[str, Any]): Dictionary containing the object's state
        """


class SingletonNameable(ABC):
    """Abstract base class for objects that have a singleton name."""

    @property
    def singleton_name(self) -> str:
        """Get the singleton name of the object.

        Returns:
            str: The name of the class
        """
        return type(self).__name__
