from astropy.coordinates import SkyCoord
import astropy.units as u

import solara
from solara.toestand import Ref

from hubbleds.components import IntroSlideshowVue
from hubbleds.state import LOCAL_STATE, GLOBAL_STATE

from hubbleds.remote import LOCAL_API
from hubbleds.widgets.exploration_tool.exploration_tool import ExplorationTool
from ..utils import IMAGE_BASE_URL

from hubbleds.layout import Layout
from cosmicds.logger import setup_logger

from cosmicds.components import StateEditor
from .component_state import COMPONENT_STATE, IntroSlideshow, Marker

logger = setup_logger("STAGE INTRO")

@solara.component
def Page():
    solara.Title("HubbleDS")
    router = solara.use_router()

    exploration_tool = ExplorationTool()
    exploration_tool1 = ExplorationTool()
    exploration_tool2 = ExplorationTool()

    exploration_tools = [exploration_tool, exploration_tool1, exploration_tool2]

    def go_to_location(options):
        index = options.get("index", 0)
        tool = exploration_tools[index]
        fov_as = options.get("fov", 216000)
        fov = fov_as * u.arcsec
        ra = options.get("ra")
        dec = options.get("dec")
        instant = options.get("instant", True)
        coordinates = SkyCoord(ra * u.deg, dec * u.deg, frame='icrs')
        tool.go_to_coordinates(coordinates, fov=fov, instant=instant)

    speech = Ref(GLOBAL_STATE.fields.speech)
    step = Ref(COMPONENT_STATE.fields.intro_slideshow_state.step)
    IntroSlideshowVue(
        step = step.value,
        event_set_step=step.set,
        length = 8,
        titles = [
            "Our Place in the Universe",
            "Answering Questions with Data",
            "Astronomy in the early 1900s",
            "Explore the Cosmic Sky",
            "What are the Fuzzy Things?",
            "Spiral Nebulae and the Great Debate",
            "Henrietta Leavitt's Discovery",
            "Vesto Slipher and Spectral Data"
        ],
        image_location=f"{IMAGE_BASE_URL}/stage_intro",
        event_slideshow_finished=lambda _: router.push("01-spectra-&-velocity"),
        debug=LOCAL_STATE.value.debug_mode,
        exploration_tool=exploration_tool,
        exploration_tool1=exploration_tool1,
        exploration_tool2=exploration_tool2,
        event_go_to_location=go_to_location,
        speech=speech.value.model_dump(),
    )
