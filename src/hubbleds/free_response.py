
# ==== Free Response State ====
from pydantic import Field
from typing import Dict

from .generic_question_model import GenericQuestion, GenericContainer
       
class FreeResponse(GenericQuestion):
    tag: str = ""
    response: str = ""
    initialized: bool = True
    
    # not required but is useful for debugging/introspection
    def update(self, response: str=''):
        super().update(response=response)

    
    @property
    def completed(self) -> bool:
        return self.response != ""

class FreeResponses(GenericContainer[FreeResponse]):
    # https://docs.pydantic.dev/latest/concepts/models/#fields-with-non-hashable-default-values
    responses: Dict[str, FreeResponse] = Field(default_factory=dict)
    _item_attribute_name: str = "responses"
    
    def add(self, tag: str):
        self.add_item(tag, FreeResponse)
        
    def get_or_create(self, tag: str):
        return self.get_or_create_item(tag, FreeResponse)        
    
    def update(self, tag: str, response: str):
        super().update_item(tag, response=response)
