from glue.core.message import NumericalDataChangedMessage
from numpy import where
import solara
from solara.alias import rv
solara.SliderValue

# NB: I didn't use any of the built-in Solara sliders since none of them really fit our
# use case. Since we often have duplicate values, the only slider that would really work
# is SliderValue, but that doesn't allow all of the customization options that we need.
# In particular, we really need to be able to set the thumb label, since our "duplicate"
# values can generally correspond to different IDs (which generally correspond to a student
# or class) and so we need to be able to distinguish between them.                                                


@solara.component
def IdSlider(gjapp,
             data,
             id_component,
             value_component,
             on_id,
             default_color="#3A86FF",
             highlight_color="#FB5607",
             highlight_ids=None,
):

    def _sort_key(id):
        idx = where(glue_data[id_component] == id)[0][0]
        return glue_data[value_component][idx]

    glue_data = data
    index, set_index = solara.use_state(0, key="index")
    values = solara.use_reactive(sorted(data[value_component]))
    ids = solara.use_reactive(sorted(data[id_component], key=_sort_key))
    tick_labels = solara.use_reactive([])
    color = solara.use_reactive(default_color)
    selected_value = solara.use_reactive(0)
    selected_id = 0
    highlight_ids = highlight_ids or []

    def _on_data_update(msg):
        if msg.data == glue_data:
            _refresh(msg.data)

    def _refresh(data):
        print("Slider refresh")
        values.set(sorted(data[value_component]))
        ids.set(sorted(data[id_component], key=_sort_key))
        vmax = len(values.value) - 1
        vmax_even = vmax % 2 == 0
        half_vmax = vmax / 2 if vmax_even else (vmax + 1) / 2
        upper_blanks_offset = 1 if vmax_even else 2
        tick_labels.set(["Low"] + ["" for _ in range(int(half_vmax)-1)] + ["Age (Gyr)"]  + ["" for _ in range(int(half_vmax)-upper_blanks_offset)] + ["High"])
        if selected_id in ids.value:
            selected_value.set(values.value[ids.value.index(selected_id)])

    def _on_index(index):
        print("In _on_index")
        set_index(index)
        selected_id = glue_data[id_component][index]
        selected_value.set(glue_data[value_component][index])
        highlight = selected_id in highlight_ids
        color.set(highlight_color if highlight else default_color)
        if on_id is not None:
            on_id(selected_id, highlight)

        print(selected_id)
        print(highlight_ids)

    # TODO: Who should the subscriber be?
    # Is there a reason that it shouldn't be the data collection?
    gjapp.data_collection.hub.subscribe(gjapp.data_collection, NumericalDataChangedMessage, handler=_on_data_update)
    
    _on_index(index)
    _refresh(data)
    print("TICKS")
    print(tick_labels.value)

    return rv.Slider(
        v_model=index,
        on_v_model=_on_index,
        ticks=True,
        tick_labels=tick_labels.value,
        min=0,
        max=len(values.value)-1,
        dense=False,
        hide_details=True,
        thumb_label="always",
        color=color.value,
        v_slots=[{
            "name": "thumb-label",
            "children": solara.Text(str(round(values.value[index])))
        }]
    )

