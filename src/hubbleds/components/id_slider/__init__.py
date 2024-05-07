import solara

@solara.component
def IdSlider(app, id_component, value_component, label, step=None):
    value = solara.use_reactive(0)
    vmin = solara.use_reactive(0)
    vmin = solara.use_reactive(1)

    solara.SliderInt(
        value=value,
        label=label,
        tick_labels=True,
        step=step or 1,
    )
