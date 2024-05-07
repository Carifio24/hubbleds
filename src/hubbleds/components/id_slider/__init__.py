from glue.core.message import NumericalDataChangeMessage
from numpy import where
import solara

@solara.component
def IdSlider(gjapp,
             data,
             id_component,
             value_component,
             label,
             on_id,
             highlight_color="#FB5607",
             step=None,
             highlight_ids=None):
    value = solara.use_reactive(0)
    selected = 0
    values = []
    ids = []
    tick_labels = []
    highlight_ids = highlight_ids or []
    glue_data = data

    def _on_data_update(msg):
        glue_data = msg.data
        _refresh()


    def _refresh():
        values = sorted(glue_data[value_component])
        ids = sorted(glue_data[id_component], key=_sort_key)
        vmax = len(values) - 1
        half_vmax = vmax / 2 if vmax % 2 == 0 else (vmax + 1) / 2
        tick_labels = ["Low"] + ["" for _ in range(int(half_vmax) - 1)] + ["High"]

    def _sort_key(id):
        idx = where(glue_data[id_component] == id)[0][0]
        return glue_data[value_component][idx]

    def _on_value_change(id):

        if on_id:
            on_id(id)

    _refresh()

    # TODO: Who should the subscriber be?
    gjapp.hub.subscribe(gjapp.data_collection, NumericalDataChangeMessage, handler=_on_data_update)

    solara.SliderValue(
        value=value,
        values=values,
        label=label,
        tick_labels=tick_labels,
        step=step or 1,
        on_value=_on_value_change,
    )
