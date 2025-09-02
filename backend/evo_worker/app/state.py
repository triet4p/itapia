from abc import abstractmethod, ABC
from typing import Any, Dict, Self

class Stateful(ABC):
    
    @property
    @abstractmethod
    def fallback_state(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        pass
    
class SingletonNameable(ABC):
    
    @property
    def singleton_name(self) -> str:
        return type(self).__name__