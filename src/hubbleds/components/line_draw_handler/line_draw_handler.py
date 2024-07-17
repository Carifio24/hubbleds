import solara
from typing import Callable, Optional


@solara.component_vue("LineDrawHandler.vue")
def LineDrawHandler(
    graph_class: str,
    active: bool=False,
    event_line_drawn: Optional[Callable]=None,
):
    pass
