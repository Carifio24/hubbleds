from ipywwt import WWTWidget
import reacton.ipyvuetify as rv
import solara
from typing import Callable

from hubbleds.components.counter import Counter
from hubbleds.utils import SURVEYS_URL


@solara.component
def Stage4WaitingScreen(
    can_advance: bool,
    on_advance_click: Callable,
    completed_count: int,
):

    show_wwt = solara.use_reactive(False)

    with rv.Card(class_="outline-warning"):
        with rv.Toolbar(color="warning", dense=True, dark=True):
            rv.ToolbarTitle(class_="text-h6 toolbar-title font-weight-regular",
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

                with solara.Div(style={"position": "relative", "height": "100%", "border": "2px solid var(--primary)", "margin-bottom": "5px"}):
                    wwt_container = rv.Html(tag="div")

                    if not show_wwt.value:
                        with rv.Overlay(absolute=True, opacity=1):
                            rv.ProgressCircular(
                                size=100, color="primary", indeterminate=True
                            )
            with rv.Row(align="center", class_="no-padding"):
                with rv.Col(cols=10, class_="no-padding"):
                    Counter(text="Number of classmates who have completed measurements", value=completed_count)

                with rv.Col(cols=2, class_="no-padding"):
                    solara.Button(label="Advance",
                                  color="accent",
                                  class_="black--text", 
                                  on_click=on_advance_click,
                                  disabled=not can_advance)
        
    def _add_widget():
        wwt_widget = WWTWidget(use_remote=True, surveys_url=SURVEYS_URL)
        wwt_widget.observe(lambda change: show_wwt.set(change["new"]), "_wwt_ready")

        wwt_widget_container = solara.get_widget(wwt_container)
        wwt_widget_container.children = (wwt_widget,)

        def cleanup():
            wwt_widget_container.children = ()
            wwt_widget.close()

        return cleanup

    solara.use_effect(_add_widget, dependencies=[])
