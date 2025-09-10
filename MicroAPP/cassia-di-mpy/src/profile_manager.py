try:
    from typing import Dict, Optional
except ImportError:
    pass

from cassia_log import get_logger
from profile_model import Model


class ProfileManager:

    def __init__(self):
        self.log = get_logger(self.__class__.__name__)

        self.models: Dict[str, Model] = {}

    def add_model(self, model: Model):
        self.log.info("add model:", model.get_name())
        self.models[model.get_name()] = model

    def get_model(self, model_name: str) -> Optional[Model]:
        self.log.info("get model:", model_name)
        return self.models.get(model_name)

    def get_models(self) -> Dict[str, Model]:
        return self.models
