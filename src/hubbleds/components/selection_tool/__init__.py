from typing import Callable, Optional

import astropy.units as u
import solara
from astropy.coordinates import SkyCoord
from astropy.table import Table
from ipywwt import WWTWidget
from reacton import ipyvuetify as rv

from ...state import LOCAL_STATE
from ...utils import GALAXY_FOV

SDSS = "SDSS9 color"
DSS = "Digitized Sky Survey (Color)"

UPDATE_TIME = 1  # seconds
INIT_COORDINATE = SkyCoord(170 * u.deg, 13.3 * u.deg, frame="icrs")
START_COORDINATES = SkyCoord(180 * u.deg, 25 * u.deg, frame="icrs")


@solara.component
def SelectionTool(
    show_galaxies: bool,
    galaxy_selected_callback: Callable,
    galaxy_added_callback: Callable,
    deselect_galaxy_callback: Callable,
    selected_measurement: Optional[dict] = None,
    on_wwt_ready: Optional[Callable] = None,
):
    show_wwt = solara.use_reactive(False)
    selected_galaxy = solara.use_reactive(None)
    current_layer = solara.use_reactive(None)
    reset_view = solara.use_reactive(False)
    refresh_images = solara.use_reactive(False)
    motions_left, set_motions_left = solara.use_state(2)

    with rv.Card() as main:
        with rv.Card(color="info", class_="pa-1" if show_galaxies else ""):
            with rv.Toolbar(dense=True, class_="toolbar"):
                rv.ToolbarTitle(children=["COSMIC SKY VIEWER"])
                rv.Spacer()

            with rv.Html(
                tag="div",
                style_="position: relative; height: 400px; width: 100%",
                class_="selection-content",
            ):
                wwt_container = rv.Html(tag="div")

                if not show_wwt.value:
                    with rv.Overlay(absolute=True, opacity=1):
                        rv.ProgressCircular(
                            size=100, color="primary", indeterminate=True
                        )

                if selected_galaxy.value is not None:
                    def _on_galaxy_added():
                        galaxy_added_callback(selected_galaxy.value)
                        selected_galaxy.set(None)
                        deselect_galaxy_callback()

                    # Add galaxy button
                    add_gal_btn = solara.Button(
                        v_on="tooltip.on",
                        color="var(--success-dark)",
                        classes=["selection-fab", "black--text"],
                        fab=True,
                        bottom=True,
                        left=True,
                        absolute=True,
                        style="--margin: 15px; --card-padding: 16px; bottom: 0px !important; margin-bottom: var(--margin); margin-left: calc(var(--margin) - var(--card-padding));",
                        children=[rv.Icon(children=["mdi-plus"])],
                        on_click=_on_galaxy_added,
                    )

                    rv.Tooltip(
                        top=True,
                        v_slots=[
                            {
                                "name": "activator",
                                "variable": "tooltip",
                                "children": rv.FabTransition(children=[add_gal_btn]),
                            }
                        ],
                        children=["Add Galaxy to the Dataset"],
                    )

                # Reset view button
                reset_view_btn = solara.Button(
                    v_on="tooltip.on",
                    color="var(--success-dark)",
                    classes=["selection-fab", "black--text"],
                    fab=True,
                    bottom=True,
                    right=True,
                    absolute=True,
                    style="--margin: 15px; --card-padding: 16px; bottom: 0px !important; margin-bottom: var(--margin); margin-right: calc(var(--margin) - var(--card-padding));",
                    children=[rv.Icon(children=["mdi-cached"])],
                    on_click=lambda: reset_view.set(not reset_view.value)
                )

                rv.Tooltip(
                    top=True,
                    v_slots=[
                        {
                            "name": "activator",
                            "variable": "tooltip",
                            "children": rv.FabTransition(children=[reset_view_btn]),
                        }
                    ],
                    children=["Reset View"],
                )

                # Refresh images button
                if selected_galaxy.value is not None:
                    refresh_images_btn = solara.Button(
                        v_on="tooltip.on",
                        color="#CCCCCC",
                        classes=["selection-fab", "black--text"],
                        fab=True,
                        top=True,
                        right=True,
                        absolute=True,
                        style_="--margin: 15px; --card-padding: 16px; top: 0px !important; margin-top: var(--margin); margin-right: calc(var(--margin) - var(--card-padding));",
                        children=[
                            rv.Icon(children=["mdi-refresh"])
                        ],
                        on_click=lambda: refresh_images.set(not refresh_images.value),
                    )

                    rv.Tooltip(
                        top=True,
                        v_slots=[
                            {
                                "name": "activator",
                                "variable": "tooltip",
                                "children": rv.FabTransition(
                                    children=[refresh_images_btn]
                                ),
                            }
                        ],
                        children=["Refresh Images"],
                    )

    def _add_widget():
        """
        Add the WWT widget to the container.
        """
        wwt_widget = WWTWidget(use_remote=True)
        wwt_widget.observe(lambda change: show_wwt.set(change["new"]), "_wwt_ready")

        wwt_widget_container = solara.get_widget(wwt_container)
        wwt_widget_container.children = (wwt_widget,)

        def cleanup():
            wwt_widget_container.children = ()
            wwt_widget.close()

        return cleanup

    solara.use_effect(_add_widget, dependencies=[])

    def _on_wwt_ready():
        """
        Set up the WWT widget when it is ready.
        """
        wwt_widget = solara.get_widget(wwt_container).children[0]

        # Update the displayed foreground and background
        wwt_widget.foreground = SDSS
        wwt_widget.background = SDSS

        # Center the field on the location of the table data
        _go_to_location(
            wwt_widget, coords=INIT_COORDINATE, fov=4 * u.deg, instant=False
        )

        # Set up the selection callback
        def _on_selection_changed(wwt, updated):
            if "most_recent_source" not in updated:
                return

            source = wwt.most_recent_source
            galaxy = source["layerData"]

            for k in ["ra", "decl"]:
                galaxy[k] = float(galaxy[k])

            fov = min(wwt_widget.get_fov(), GALAXY_FOV)

            _go_to_location(
                wwt_widget,
                coords=SkyCoord(galaxy["ra"], galaxy["decl"], unit=u.deg),
                fov=fov
            )
            selected_galaxy.set(galaxy)
            galaxy_selected_callback(galaxy)

        wwt_widget.set_selection_change_callback(_on_selection_changed)

        if on_wwt_ready is not None:
            on_wwt_ready()

    solara.use_effect(_on_wwt_ready, dependencies=[show_wwt.value])

    def _on_show_galaxies():
        """
        Show or hide the galaxies on the WWT widget.
        """
        wwt_widget = solara.get_widget(wwt_container).children[0]

        if current_layer.value is None:
            table = Table(
                {
                    k: [x.dict()[k] for x in LOCAL_STATE.value.galaxies.values()]
                    for k in ["id", "ra", "decl"]
                }
            )

            layer = wwt_widget.layers.add_table_layer(
                frame="Sky",
                table=table,
                lon_att="ra",
                lat_att="decl",
                marker_type="gaussian",
                size_scale=100,
                color="#00FF00",
                marker_scale="screen",
            )

            current_layer.set(layer)

        current_layer.value.opacity = int(show_galaxies)

        if show_galaxies:
            _go_to_location(
                wwt_widget, coords=START_COORDINATES, fov=60 * u.deg, instant=True
            )

    solara.use_effect(_on_show_galaxies, dependencies=[show_galaxies])

    def _go_to_location(
        wwt_widget: WWTWidget,
        coords: SkyCoord,
        fov: u.Quantity,
        instant: Optional[bool] = None,
        motion_counted: bool = True,
    ):  
        print(f"Going to location: {coords}, fov: {fov}, instant: {instant}, motion_counted: {motion_counted}")
        if instant is None:
            if motion_counted:
                instant = motions_left <= 0
                set_motions_left(motions_left - 1)
            else:
                instant = True

        wwt_widget.center_on_coordinates(
            coords, fov=fov, instant=instant,
        )

    def _on_reset_view():
        """
        Reset the view of the WWT widget.
        """
        wwt_widget = solara.get_widget(wwt_container).children[0]
        _go_to_location(
            wwt_widget, coords=START_COORDINATES, fov=60 * u.deg, instant=True
        )

    solara.use_effect(_on_reset_view, dependencies=[reset_view.value])

    def _on_refresh_images():
        """
        Refresh the images in the WWT widget.
        """
        wwt_widget = solara.get_widget(wwt_container).children[0]
        wwt_widget.refresh_tile_cache()

    solara.use_effect(_on_refresh_images, dependencies=[refresh_images.value])

    def _update_position():
        if selected_measurement is None:
            return

        galaxy = selected_measurement["galaxy"]
        coords = SkyCoord(galaxy["ra"] * u.deg, galaxy["decl"] * u.deg, frame="icrs")

        wwt_widget = solara.get_widget(wwt_container).children[0]
        _go_to_location(wwt_widget,
                        coords=coords,
                        fov=GALAXY_FOV,
                        motion_counted=True)

    solara.use_effect(_update_position, dependencies=[selected_measurement])
