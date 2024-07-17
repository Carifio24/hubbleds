from cosmicds.config import register_tool
from echo import CallbackProperty
from echo.callback_container import CallbackContainer
from glue.viewers.common.viewer import Viewer
from glue.viewers.common.tool import CheckableTool
from typing import Callable


@register_tool
class LineDrawTool(CheckableTool):

    icon = "glue_point"
    mdi_icon = "mdi-message-draw"
    tool_id = "hubble:linedraw"
    action_text = "Draw a line"
    tool_tip = "Draw a best fit line"
    active = CallbackProperty(False)
    
    def __init__(self, viewer: Viewer):
        super().__init__(viewer)
        self._on_activated = CallbackContainer()

    def activate(self):
        self.active = not self.active
        for cb in self._on_activated:
            cb(self.active)

    def on_activate(self, callback: Callable[[bool], None]):
        self._on_activated.append(callback)
