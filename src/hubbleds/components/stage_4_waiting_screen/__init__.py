from ipywwt import WWTWidget
import reacton.ipyvuetify as rv
import solara
from typing import Callable

from hubbleds.components.counter import Counter


@solara.component
def Stage4WaitingScreen(
    can_advance: bool,
    on_advance_click: Callable,
    completed_count: int,
):

    show_wwt = solara.use_reactive(False)

    with rv.Card():
        with rv.Toolbar(color="warning", dense=True, dark=True):
            rv.ToolbarTitle(class_="text-h6 text-uppercase font-weight-regular",
                                 children=["Take a quick break"])
            rv.Spacer()

        with rv.CardText():
            with rv.Container():
                with solara.Row():
                   solara.HTML(
                        unsafe_innerHTML=
                        """
                        <p>You and your classmates will be comparing your measurements in the next section, but we need to wait a few moments for more of them to catch up.</p>
                        <p>While you wait, you can explore the same sky viewer you saw in the introduction.</p>
                        <p>You will be able to advance when enough classmates are ready to proceed.</p>
                        """
                    )

                with solara.Div(style={"position": "relative", "height": "400px"}):
                    wwt_container = rv.Html(tag="div")

                    if not show_wwt.value:
                        with rv.Overlay(absolute=True, opacity=1):
                            rv.ProgressCircular(
                                size=100, color="primary", indeterminate=True
                            )

                Counter(text="Number of classmates who have completed measurements", value=completed_count)

                with solara.Row():
                    solara.Button(label="Advance",
                                  on_click=on_advance_click,
                                  disabled=not can_advance)
        
    def _add_widget():
        wwt_widget = WWTWidget(use_remote=True)
        wwt_widget.observe(lambda change: show_wwt.set(change["new"]), "_wwt_ready")

        wwt_widget_container = solara.get_widget(wwt_container)
        wwt_widget_container.children = (wwt_widget,)

        def cleanup():
            wwt_widget_container.children = ()
            wwt_widget.close()

        return cleanup

    solara.use_effect(_add_widget, dependencies=[])
