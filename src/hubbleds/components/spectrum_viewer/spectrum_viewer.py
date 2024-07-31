from typing import Callable

import plotly.express as px
import reacton.ipyvuetify as rv
import solara
from hubbleds.state import GalaxyData
from pandas import DataFrame
from hubbleds.components.spectrum_viewer.plotly_figure import FigurePlotly


@solara.component
def SpectrumViewer(
    galaxy_data: GalaxyData | None,
    obs_wave: float | None = None,
    spectrum_click_enabled: bool = False,
    on_obs_wave_measured: Callable = None,
    on_obs_wave_tool_clicked: Callable = lambda: None,
    on_zoom_tool_clicked: Callable = lambda: None,
):

    vertical_line_visible = solara.use_reactive(False)
    toggle_group_state = solara.use_reactive([])

    x_bounds = solara.use_reactive([])
    y_bounds = solara.use_reactive([])

    async def _load_spectrum():
        if galaxy_data is None:
            return False

        return galaxy_data.spectrum_as_data_frame

    spec_data_task = solara.lab.use_task(
        _load_spectrum,
        dependencies=[galaxy_data],
    )

    def _obs_wave_tool_toggled():
        on_obs_wave_tool_clicked()

    def _on_relayout(event):
        if event is None:
            return

        try:
            x_bounds.set(
                [
                    event["relayout_data"]["xaxis.range[0]"],
                    event["relayout_data"]["xaxis.range[1]"],
                ]
            )
            # y_bounds.set(
            #     [
            #         event["relayout_data"]["yaxis.range[0]"],
            #         event["relayout_data"]["yaxis.range[1]"],
            #     ]
            # )
            toggle_group_state.set([x for x in toggle_group_state.value if x != 0])
        except:
            x_bounds.set([])
            y_bounds.set([])

    def _on_reset_button_clicked(*args, **kwargs):
        x_bounds.set([])
        y_bounds.set([])

    def _spectrum_clicked(**kwargs):
        if spectrum_click_enabled:
            vertical_line_visible.set(True)
            on_obs_wave_measured(round(kwargs["points"]["xs"][0]))

    with rv.Card():
        with rv.Toolbar(class_="toolbar", dense=True):
            with rv.ToolbarTitle():
                solara.Text("SPECTRUM VIEWER")

            rv.Spacer()

            with rv.BtnToggle(
                v_model=toggle_group_state.value,
                on_v_model=toggle_group_state.set,
                flat=True,
                tile=True,
                group=True,
                multiple=True,
            ):

                solara.IconButton(
                    icon_name="mdi-select-search",
                    on_click=on_zoom_tool_clicked,
                )

                solara.IconButton(
                    icon_name="mdi-lambda",
                    on_click=_obs_wave_tool_toggled,
                )

            rv.Divider(vertical=True)

            solara.IconButton(
                flat=True,
                tile=True,
                icon_name="mdi-refresh",
                on_click=_on_reset_button_clicked,
            )

        if spec_data_task.value is None:
            with rv.Sheet(
                style_="height: 360px", class_="d-flex justify-center align-center"
            ):
                rv.ProgressCircular(size=100, indeterminate=True, color="primary")

            return
        elif not isinstance(spec_data_task.value, DataFrame):
            with rv.Sheet(
                style_="height: 360px", class_="d-flex justify-center align-center"
            ):
                solara.Text("Select a galaxy to view its spectrum")

            return

        fig = px.line(spec_data_task.value, x="wave", y="flux")

        fig.update_traces(hovertemplate="%{x:,.0f} nm<extra></extra>")

        fig.update_layout(
            margin=dict(l=0, r=10, t=10, b=0), yaxis=dict(fixedrange=True)
        )

        fig.add_vline(
            x=obs_wave,
            line_width=1,
            line_color="red",
            # annotation_text="1BASE",
            # annotation_font_size=12,
            # annotation_position="top right",
            visible=vertical_line_visible.value and obs_wave > 0.0,
        )

        fig.add_shape(
            editable=False,
            x0=galaxy_data.redshift_rest_wave_value - 5,
            x1=galaxy_data.redshift_rest_wave_value + 5,
            y0=0.85,
            y1=0.9,
            xref="x",
            line_color="red",
            fillcolor="red",
            ysizemode="scaled",
            yref="paper",
            label={
                "text": f"{galaxy_data.element} (observed)",
                "textposition": "top center",
                "yanchor": "bottom",
            }
            # visible=
        )

        fig.add_shape(
            editable=False,
            type="line",
            x0=galaxy_data.rest_wave_value,
            x1=galaxy_data.rest_wave_value,
            xref="x",
            y0=0.5,
            y1=0.75,
            line_color="black",
            ysizemode="scaled",
            yref="paper",
            line=dict(dash="dot"),
            label={
                "text": f"{galaxy_data.element} (rest)",
                "textposition": "top center",
                "yanchor": "bottom",
            },
            visible=1 in toggle_group_state.value,
        )

        fig.update_layout(
            xaxis_zeroline=False,
            yaxis_zeroline=False,
            xaxis=dict(
                showspikes=spectrum_click_enabled,
                showline=spectrum_click_enabled,
                spikecolor="black",
                spikethickness=1,
                spikedash="solid",
                spikemode="across",
                spikesnap="cursor",
            ),
            spikedistance=-1,
            hovermode="x",
        )

        if x_bounds.value:  # and y_bounds.value:
            fig.update_xaxes(range=x_bounds.value)
            # fig.update_yaxes(range=y_bounds.value)
        # else:
        fig.update_yaxes(
            range=[
                spec_data_task.value["flux"].min() * 0.95,
                spec_data_task.value["flux"].max() * 1.25,
            ]
        )

        fig.update_layout(dragmode="zoom" if 0 in toggle_group_state.value else "pan")

        FigurePlotly(
            fig,
            on_click=lambda kwargs: _spectrum_clicked(**kwargs),
            on_relayout=_on_relayout,
            dependencies=[
                obs_wave,
                spectrum_click_enabled,
                vertical_line_visible.value,
                toggle_group_state.value,
                x_bounds.value,
                y_bounds.value,
            ],
            config={
                "displayModeBar": False,
            },
        )
