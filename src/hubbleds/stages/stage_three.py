from functools import partial
from os.path import join
from pathlib import Path

from numpy import asarray, histogram
from cosmicds.components.generic_state_component import GenericStateComponent
from cosmicds.components.table import Table
from cosmicds.phases import CDSState
from cosmicds.registries import register_stage
from cosmicds.utils import extend_tool, load_template, update_figure_css
from echo import CallbackProperty, add_callback, remove_callback
from glue.core.message import NumericalDataChangedMessage
from glue.core.data import Data
from hubbleds.components.id_slider import IDSlider
from pygments import highlight
from hubbleds.utils import IMAGE_BASE_URL
from traitlets import default, Bool
from ..data.styles import load_style

from ..components import TrendsData, HubbleExp, AgeCalc

from ..data_management import \
    ALL_CLASS_SUMMARIES_LABEL, ALL_DATA_LABEL, ALL_STUDENT_SUMMARIES_LABEL, \
    CLASS_DATA_LABEL, CLASS_SUMMARY_LABEL, STUDENT_DATA_LABEL, HUBBLE_1929_DATA_LABEL, \
    HUBBLE_KEY_DATA_LABEL
from ..histogram_listener import HistogramListener
from ..stage import HubbleStage
from ..viewers import HubbleFitView, \
    HubbleScatterView
from ..viewers.viewers import \
    HubbleClassHistogramView, HubbleHistogramView, HubbleFitLayerView


class StageState(CDSState):
    trend_response = CallbackProperty(False)
    relvel_response = CallbackProperty(False)
    race_response = CallbackProperty(False)
    relage_response = CallbackProperty(False)
    hubble_dialog_opened = CallbackProperty(False)
    class_layer_toggled = CallbackProperty(0)

    marker = CallbackProperty("")
    indices = CallbackProperty({})
    advance_marker = CallbackProperty(True)

    image_location = CallbackProperty(f"{IMAGE_BASE_URL}/stage_three")

    hypgal_distance = CallbackProperty(100)
    hypgal_velocity = CallbackProperty(8000)

    stu_low_age = CallbackProperty(0)
    stu_high_age = CallbackProperty(0)

    cla_low_age = CallbackProperty(0)
    cla_high_age = CallbackProperty(0)

    markers = CallbackProperty([
        'exp_dat1',
        'tre_dat1',
        'tre_dat2',
        'tre_dat3',
        'rel_vel1',
        'hub_exp1',
        'tre_lin1',
        'tre_lin2',
        'bes_fit1',
        'age_uni1',
        'hyp_gal1',
        'age_rac1',
        'age_uni2',
        'age_uni3',
        'age_uni4',
        'you_age1',
        'sho_est1',
        'sho_est2',
        'ran_var1',
        'cla_res1',
        'rel_age1',
        'cla_age1',
        'cla_age2',
        'cla_age3',
        'cla_age4',
        'con_int1',
        'age_dis1',
        'con_int2',
        'age_uni1c',
        'hyp_gal1c',
        'age_uni3c',
        'age_uni4c',
        'you_age1c',
        'cla_res1c',
        'cla_age1c',
        'age_dis1c',
        'con_int2c',
    ])

    step_markers = CallbackProperty([
    ])

    table_highlights = CallbackProperty([
        'exp_dat1',
    ])

    my_galaxies_plot_highlights = CallbackProperty([
        'tre_dat1',
        'tre_dat2',
        'tre_dat3',
        'rel_vel1',
        'hub_exp1',
        'tre_lin1',
        'tre_lin2',
        'bes_fit1',
        'age_uni1',
        'hyp_gal1',
        'age_rac1',
        'age_uni2',
        'age_uni3',
        'you_age1',
        'sho_est1',
    ])

    all_galaxies_plot_highlights = CallbackProperty([
    ])

    my_class_hist_highlights = CallbackProperty([
    ])

    all_classes_hist_highlights = CallbackProperty([
    ])

    sandbox_hist_highlights = CallbackProperty([
    ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.marker_index = 0
        self.marker = self.markers[0]
        self.indices = {marker: idx for idx, marker in enumerate(self.markers)}

    def marker_before(self, marker):
        return self.indices[self.marker] < self.indices[marker]

    def marker_after(self, marker):
        return self.indices[self.marker] > self.indices[marker]

    def move_marker_forward(self, marker_text, _value=None):
        index = min(self.markers.index(marker_text) + 1, len(self.markers) - 1)
        self.marker = self.markers[index]


@register_stage(story="hubbles_law", index=4, steps=[
    "MY DATA",
    "CLASS DATA",
    "BY GALAXY TYPE",
    "PROFESSIONAL DATA"
])
class StageThree(HubbleStage):
    show_team_interface = Bool(False).tag(sync=True)

    _state_cls = StageState

    @default('stage_state')
    def _default_state(self):
        return StageState()

    @default('template')
    def _default_template(self):
        return load_template("stage_three.vue", __file__)

    @default('stage_icon')
    def _default_stage_icon(self):
        return "3"

    @default('title')
    def _default_title(self):
        return "Explore Data"

    @default('subtitle')
    def _default_subtitle(self):
        return "Perhaps a small blurb about this stage"

    viewer_ids_for_data = {
        STUDENT_DATA_LABEL: ["comparison_viewer","layer_viewer"],
        CLASS_DATA_LABEL: ["comparison_viewer","layer_viewer"],
        CLASS_SUMMARY_LABEL: ["class_distr_viewer"]
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.show_team_interface = self.app_state.show_team_interface

        student_data = self.get_data(STUDENT_DATA_LABEL)
        class_meas_data = self.get_data(CLASS_DATA_LABEL)
        all_data = self.get_data(ALL_DATA_LABEL)

        fit_table = Table(self.session,
                          data=student_data,
                          glue_components=['name',
                                           'velocity',
                                           'distance'],
                          key_component='name',
                          names=['Galaxy Name',
                                 'Velocity (km/s)',
                                 'Distance (Mpc)'],
                          title='My Galaxies',
                          subset_label="fit_table_selected"
                          )
        self.add_widget(fit_table, label="fit_table")

        # Set up links between various data sets

        dist_attr = "distance"
        vel_attr = "velocity"
        for field in [dist_attr, vel_attr]:
            self.add_link(CLASS_DATA_LABEL, field, ALL_DATA_LABEL, field)
        self.add_link(HUBBLE_1929_DATA_LABEL, 'Distance (Mpc)', HUBBLE_KEY_DATA_LABEL,
                      'Distance (Mpc)')
        self.add_link(HUBBLE_1929_DATA_LABEL, 'Tweaked Velocity (km/s)', HUBBLE_KEY_DATA_LABEL,
                      'Velocity (km/s)')
        self.add_link(HUBBLE_KEY_DATA_LABEL, 'Distance (Mpc)', STUDENT_DATA_LABEL,
                      'distance')
        self.add_link(HUBBLE_KEY_DATA_LABEL, 'Velocity (km/s)', STUDENT_DATA_LABEL,
                      'velocity')

        # Create viewers
        layer_viewer = self.add_viewer(HubbleFitLayerView, "layer_viewer", "Our Data")
        comparison_viewer = self.add_viewer(HubbleScatterView,
                                            "comparison_viewer",
                                            "Data Comparison")
        all_viewer = self.add_viewer(HubbleScatterView, "all_viewer", "All Data")
        # morphology_viewer = self.add_viewer(HubbleScatterView,
        #                                     "morphology_viewer",
        #                                     "Galaxy Morphology")
        prodata_viewer = self.add_viewer(HubbleScatterView, "prodata_viewer",
                                         "Professional Data")
        class_distr_viewer = self.add_viewer(HubbleClassHistogramView,
                                             'class_distr_viewer', "My Class")
        all_distr_viewer = self.add_viewer(HubbleHistogramView,
                                           'all_distr_viewer', "All Classes")
        sandbox_distr_viewer = self.add_viewer(HubbleHistogramView,
                                               'sandbox_distr_viewer',
                                               "Sandbox")
        hubble_race_viewer = self.add_viewer(HubbleScatterView,
                                                "hubble_race_viewer",
                                                 "Race")
        hubble_race_viewer.figure.axes[0].tick_format = ',.0f'
        hubble_race_viewer.figure.axes[1].tick_format = ',.0f'
        hubble_race_data = Data(label='hubble_race_data')
        hubble_race_data.add_component([12,24,30],'distance (km)')
        hubble_race_data.add_component([4,8,10],'velocity (km/hr)')
        self.add_data(hubble_race_data)
        hubble_race_viewer.add_data(hubble_race_data)
        hubble_race_viewer.state.x_att = hubble_race_data.id['distance (km)']
        hubble_race_viewer.state.y_att = hubble_race_data.id['velocity (km/hr)']
        hubble_race_viewer.axis_y.tick_values  = asarray([4,6,8,10])
        hubble_race_viewer._update_appearance_from_settings()
        hubble_slideshow = HubbleExp(self.stage_state, [self.viewers["hubble_race_viewer"],self.viewers["layer_viewer"]])
        
        
        self.add_component(hubble_slideshow, label='c-hubble-slideshow')

        add_callback(self.stage_state, 'marker',
                     self._on_marker_update, echo_old=True)
        self.trigger_marker_update_cb = True

        # Set up the generic state components
        state_components_dir = str(
            Path(
                __file__).parent.parent / "components" / "generic_state_components" / "stage_three")
        path = join(state_components_dir, "")
        state_components = [
            "guideline_explore_data",
            "guideline_trends_data2",
            "guideline_relationship_vel_dist_mc",
            "guideline_trend_lines1",
            "guideline_trend_lines_draw2",
            "guideline_best_fit_line",
            "guideline_hubbles_expanding_universe1",
            "guideline_age_universe",
            "guideline_hypothetical_galaxy",
            "guideline_age_race_equation",
            "guideline_your_age_estimate",
            "guideline_shortcomings_est_reflect1",
            "guideline_shortcomings_est2",
            "guideline_random_variability",
            "guideline_classmates_results",
            "guideline_relationship_age_slope_mc",
            "guideline_class_age_range2",
            "guideline_class_age_range3",
            "guideline_class_age_range4",
            "guideline_confidence_interval",
            "guideline_class_age_distribution",
            "guideline_age_universe_c",  # move these to their own block
            "guideline_hypothetical_galaxy_c",
            "guideline_your_age_estimate_c",
            "guideline_classmates_results_c",
            "guideline_class_age_distribution_c",
        ]
        ext = ".vue"
        for comp in state_components:
            label = f"c-{comp}".replace("_", "-")

            # comp + ext = filename; path = folder where they live.
            component = GenericStateComponent(comp + ext, path,
                                              self.stage_state)
            self.add_component(component, label=label)

        # Set up trends_data components
        trends_data_components_dir = str(Path(
            __file__).parent.parent / "components" / "trends_data_components")
        path = join(trends_data_components_dir, "")
        trends_data_components = [
            "guideline_trends_data_mc1",
            "guideline_trends_data_mc3"
        ]
        for comp in trends_data_components:
            label = f"c-{comp}".replace("_", "-")
            component = TrendsData(comp + ext, path, self.stage_state)
            self.add_component(component, label=label)

        # Set up age_calc components
        age_calc_components_dir = str(Path(
            __file__).parent.parent / "components" / "age_calc_components")
        path = join(age_calc_components_dir, "")
        age_calc_components = [
            "guideline_age_universe_equation2",
            "guideline_age_universe_estimate3",
            "guideline_age_universe_estimate4",
            "guideline_class_age_range",
            "guideline_confidence_interval_reflect2",
            "guideline_age_universe_estimate3_c",
            "guideline_age_universe_estimate4_c",
            "guideline_class_age_range_c",
            "guideline_confidence_interval_reflect2_c",
        ]
        for comp in age_calc_components:
            label = f"c-{comp}".replace("_", "-")
            component = AgeCalc(comp + ext, path, self.stage_state)
            self.add_component(component, label=label) 

        # Grab data
        class_summ_data = self.get_data(CLASS_SUMMARY_LABEL)
        classes_summary_data = self.get_data(ALL_CLASS_SUMMARIES_LABEL)

        # Set up the listener to sync the histogram <--> scatter viewers

        # Set up the functionality for the histogram <---> scatter sync
        # We add a listener for when a subset is modified/created on
        # the histogram viewer as well as extend the xrange tool for the
        # histogram to always affect this subset
        histogram_source_label = "histogram_source_subset"
        histogram_modify_label = "histogram_modify_subset"
        self.histogram_listener = HistogramListener(self.story_state,
                                                    None,
                                                    class_summ_data,
                                                    None,
                                                    class_meas_data,
                                                    source_subset_label=histogram_source_label,
                                                    modify_subset_label=histogram_modify_label)

        # Create the student slider
        student_slider_subset_label = "student_slider_subset"
        self.student_slider_subset = class_meas_data.new_subset(label=student_slider_subset_label)
        student_slider = IDSlider(class_summ_data, "student_id", "age", highlight_ids=[self.story_state.student_user["id"]])
        self.add_component(student_slider, "c-student-slider")
        def student_slider_change(id, highlighted):
            self.student_slider_subset.subset_state = class_meas_data['student_id'] == id
            color = student_slider.highlight_color if highlighted else student_slider.default_color
            self.student_slider_subset.style.color = color
        def student_slider_refresh(slider):
            self.stage_state.stu_low_age = round(min(slider.values))
            self.stage_state.stu_high_age = round(max(slider.values))

        student_slider.on_id_change(student_slider_change)
        student_slider.on_refresh(student_slider_refresh)

        def update_student_slider(msg):
            student_slider.update_data(self, msg.data)
        self.hub.subscribe(self, NumericalDataChangedMessage, filter=lambda d: d.label == CLASS_SUMMARY_LABEL, handler=update_student_slider)

        # Create the class slider
        class_slider_subset_label = "class_slider_subset"
        self.class_slider_subset = all_data.new_subset(label=class_slider_subset_label)
        class_slider = IDSlider(classes_summary_data, "class_id", "age")
        self.add_component(class_slider, "c-class-slider")
        def class_slider_change(id, highlighted):
            self.class_slider_subset.subset_state = all_data['class_id'] == id
            color = class_slider.highlight_color if highlighted else class_slider.default_color
            self.class_slider_subset.style.color = color
        def class_slider_refresh(slider):
            self.stage_state.cla_low_age = round(min(slider.values))
            self.stage_state.cla_high_age = round(max(slider.values))

        class_slider.on_id_change(class_slider_change)
        class_slider.on_refresh(class_slider_refresh)

        self.hub.subscribe(self, NumericalDataChangedMessage,
                           filter=lambda msg: msg.data.label == STUDENT_DATA_LABEL,
                           handler=student_slider.refresh)
        self.hub.subscribe(self, NumericalDataChangedMessage,
                           filter=lambda msg: msg.data.label == CLASS_SUMMARY_LABEL,
                           handler=class_slider.refresh)

        def update_class_slider(msg):
            class_slider.update_data(self, msg.data)
        self.hub.subscribe(self, NumericalDataChangedMessage, filter=lambda d: d.label == ALL_CLASS_SUMMARIES_LABEL, handler=update_class_slider)    

        classes_summary_data = self.get_data(ALL_CLASS_SUMMARIES_LABEL)

        not_ignore = {
            fit_table.subset_label: [layer_viewer],
            histogram_source_label: [class_distr_viewer],
            histogram_modify_label: [comparison_viewer],
            student_slider_subset_label: [comparison_viewer]
        }

        def label_ignore(x, label):
            return x.label == label

        for label, listeners in not_ignore.items():
            ignorer = partial(label_ignore, label=label)
            for viewer in self.all_viewers:
                if viewer not in listeners:
                    viewer.ignore(ignorer)
        
        # layers from the table selection have the same label, but we only want student_data selected
        layer_viewer.ignore(lambda layer: layer.label == "fit_table_selected" and layer.data != student_data)

        def comparison_ignorer(x):
            return x.label == histogram_modify_label and x.data != self.histogram_listener.modify_data

        comparison_viewer.ignore(comparison_ignorer)

        # load all the initial styles
        self._update_viewer_style(dark=self.app_state.dark_mode)

        # set reasonable offset for y-axis labels
        # it would be better if axis labels were automatically well placed
        velocity_viewers = [prodata_viewer, comparison_viewer, layer_viewer, all_viewer]
        # velocity_viewers = [prodata_viewer, comparison_viewer, morphology_viewer, layer_viewer]
        for viewer in velocity_viewers:
            viewer.figure.axes[1].label_offset = "5em"
        

        # Just for accessibility while testing
        self.data_collection.histogram_listener = self.histogram_listener

        # Whenever data is updated, the appropriate viewers should update their bounds
        self.hub.subscribe(self, NumericalDataChangedMessage,
                           handler=self._on_data_change)

        def hist_selection_activate():
            if self.histogram_listener.source_subset is None:
                self.histogram_listener.source_subset = self.data_collection.new_subset_group(
                    label=self.histogram_listener.source_subset_label)
            self.session.edit_subset_mode.edit_subset = [
                self.histogram_listener.source_subset]

        def hist_selection_deactivate():
            self.session.edit_subset_mode.edit_subset = []

        extend_tool(class_distr_viewer, 'bqplot:xrange',
                    hist_selection_activate, hist_selection_deactivate)

        # We want the hub_fit_viewer to be selecting for the same subset as the table
        def fit_selection_activate():
            table = self.get_widget('fit_table')
            table.initialize_subset_if_needed()
            self.session.edit_subset_mode.edit_subset = [table.subset]

        def fit_selection_deactivate():
            self.session.edit_subset_mode.edit_subset = []
        
        extend_tool(layer_viewer, 'bqplot:rectangle', fit_selection_activate,
                    fit_selection_deactivate)

        # If possible, we defer some of the setup for later, to make loading faster
        self._deferred_setup_complete = False
        if self.story_state.stage_index != self.index:
            add_callback(self.story_state, 'stage_index', self._on_stage_index_changed)
        else:
            self._maybe_deferred_setup()

        self.hub.subscribe(self, NumericalDataChangedMessage,
                           filter=self._deferred_setup_filter,
                           handler=self._maybe_deferred_setup)
    
    def _on_marker_update(self, old, new):
        if not self.trigger_marker_update_cb:
            return
        markers = self.stage_state.markers
        advancing = markers.index(new) > markers.index(old)
        if advancing and new == "tre_dat2":
            layer_viewer = self.get_viewer("layer_viewer")
            layer_viewer.toolbar.set_tool_enabled('hubble:togglelayer', True)
        if advancing and new == "tre_lin1":
            layer_viewer = self.get_viewer("layer_viewer")
            class_layer = layer_viewer.layers[-1]
            class_layer.state.visible = False
        if advancing and new == "you_age1":
            layer_viewer = self.get_viewer("layer_viewer")
            layer_viewer.toolbar.tools["hubble:linefit"].show_labels = True                   
    
    def _on_class_layer_toggled(self, used):
        self.stage_state.class_layer_toggled = used 
        if(self.stage_state.class_layer_toggled == 1):
           self.stage_state.move_marker_forward(self.stage_state.marker)

    def _setup_first_scatter_layers(self):
        dist_attr = "distance"
        vel_attr = "velocity"
        comparison_viewer = self.get_viewer("comparison_viewer")
        prodata_viewer = self.get_viewer("prodata_viewer")
        layer_viewer = self.get_viewer("layer_viewer")
        all_viewer = self.get_viewer("all_viewer")
        student_data = self.get_data(STUDENT_DATA_LABEL)
        class_meas_data = self.get_data(CLASS_DATA_LABEL)
        for viewer in [comparison_viewer, prodata_viewer, layer_viewer, all_viewer]:
            viewer.add_data(student_data)
            # viewer.layers[-1].state.visible = False
            viewer.state.x_att = student_data.id[dist_attr]
            viewer.state.y_att = student_data.id[vel_attr]

        print("Set up student data")
        
        # add class measurement data and hide by default
        layer_viewer.add_data(class_meas_data)
        layer_viewer.state.reset_limits()
        class_layer = layer_viewer.layers[-1]
        class_layer.state.zorder=1
        class_layer.state.color="blue"
        class_layer.state.visible = False
        toggle_tool = layer_viewer.toolbar.tools['hubble:togglelayer']
        toggle_tool.set_layer_to_toggle(class_layer)
        layer_viewer.toolbar.set_tool_enabled('hubble:togglelayer', not self.stage_state.marker_before("tre_dat2"))

        print("Set up layer viewer")

        # cosmicds PR157 - turn off fit line label for layer_viewer
        layer_viewer.toolbar.tools["hubble:linefit"].show_labels = False

        add_callback(toggle_tool, 'class_layer_toggled', self._on_class_layer_toggled)        

        student_layer = comparison_viewer.layers[-1]
        student_layer.state.color = 'orange'
        student_layer.state.zorder = 3
        student_layer.state.size = 8
        comparison_viewer.add_data(class_meas_data)
        class_layer = comparison_viewer.layers[-2]
        class_layer.state.visible = False  # Turn off layer with the whole class
        class_layer.state.zorder = 2
        class_layer.state.color = 'red'
        # comparison_viewer.add_subset(self.student_slider_subset)
        comparison_viewer.state.x_att = class_meas_data.id[dist_attr]
        comparison_viewer.state.y_att = class_meas_data.id[vel_attr]
        comparison_viewer.state.reset_limits()

        print("Set up comparison viewer")

        # all_data = self.get_data(ALL_DATA_LABEL)
        # student_layer = all_viewer.layers[-1]
        # student_layer.state.color = 'orange'
        # student_layer.state.zorder = 3
        # student_layer.state.size = 8
        # student_layer.state.visible = False
        # all_viewer.add_data(class_meas_data)
        # class_layer = all_viewer.layers[-1]
        # class_layer.state.zorder = 2
        # class_layer.state.size = 5
        # class_layer.state.color = 'red'
        # class_layer.state.visible = False
        # all_viewer.add_data(all_data)
        # all_layer = all_viewer.layers[-2]
        # all_layer.state.zorder = 1
        # all_layer.state.visible = False
        # all_viewer.state.x_att = all_data.id[dist_attr]
        # all_viewer.state.y_att = all_data.id[vel_attr]

        # print("Set up all viewer")

        # In the comparison viewer, we only want to see the line for the student slider subset
        linefit_id = "hubble:linefit"
        comparison_toolbar = comparison_viewer.toolbar
        comparison_linefit = comparison_toolbar.tools[linefit_id]
        comparison_linefit.add_ignore_condition(lambda layer: layer.layer.label != self.student_slider_subset.label)
        comparison_linefit.activate()
        comparison_toolbar.set_tool_enabled(linefit_id, False)

        print("Set up tools")

    # def _setup_second_scatter_layers(self):
    #     hubble1929 = self.get_data(HUBBLE_1929_DATA_LABEL)
    #     hstkp = self.get_data(HUBBLE_KEY_DATA_LABEL)
    #     prodata_viewer.add_data(student_data)
    #     print(student_data)
    #     prodata_viewer.state.x_att = student_data.id[dist_attr]
    #     prodata_viewer.state.y_att = student_data.id[vel_attr]
    #     prodata_viewer.add_data(hstkp)
    #     prodata_viewer.add_data(hubble1929)

    #     print("Finished block 5")

    def _setup_histogram_layers(self):
        class_distr_viewer = self.get_viewer("class_distr_viewer")
        all_distr_viewer = self.get_viewer("all_distr_viewer")
        sandbox_distr_viewer = self.get_viewer("sandbox_distr_viewer")
        class_summ_data = self.get_data(CLASS_SUMMARY_LABEL)
        students_summary_data = self.get_data(ALL_STUDENT_SUMMARIES_LABEL)
        classes_summary_data = self.get_data(ALL_CLASS_SUMMARIES_LABEL)
        histogram_viewers = [class_distr_viewer, all_distr_viewer, sandbox_distr_viewer]
        for viewer in histogram_viewers:
            label = 'Count' if viewer == class_distr_viewer else 'Proportion'
            viewer.figure.axes[1].label = label
            if viewer != all_distr_viewer:
                viewer.add_data(class_summ_data)
                layer = viewer.layers[-1]
                layer.state.color = 'red'
                layer.state.alpha = 0.5
            if viewer != class_distr_viewer:
                viewer.add_data(students_summary_data)
                layer = viewer.layers[-1]
                layer.state.color = 'blue'
                layer.state.alpha = 0.5
                viewer.add_data(classes_summary_data)
                layer = viewer.layers[-1]
                layer.state.color = '#f0c470'
                layer.state.alpha = 0.5
                viewer.state.normalize = True
                viewer.state.y_min = 0
                viewer.state.y_max = 1
                viewer.state.hist_n_bin = 20

        class_distr_viewer.state.x_att = class_summ_data.id['age']
        all_distr_viewer.state.x_att = students_summary_data.id['age']
        sandbox_distr_viewer.state.x_att = students_summary_data.id['age']

    # def _setup_morphology_subsets(self):
    #     # Do some stuff with the galaxy data
    #     type_field = 'type'
    #     morphology_viewer = self.get_viewer("morphology_viewer")
    #     all_viewer = self.get_viewer("all_viewer")
    #     all_data = self.get_data(ALL_DATA_LABEL)
    #     all_viewer.ignore(lambda layer: layer.label in ["Elliptical", "Spiral", "Irregular"])
    #     elliptical_subset = all_data.new_subset(all_data.id[type_field] == 'E',
    #                                             label='Elliptical',
    #                                             color='orange')
    #     spiral_subset = all_data.new_subset(all_data.id[type_field] == 'Sp',
    #                                         label='Spiral', color='green')
    #     irregular_subset = all_data.new_subset(all_data.id[type_field] == 'Ir',
    #                                            label='Irregular', color='red')
    #     morphology_subsets = [elliptical_subset, spiral_subset,
    #                           irregular_subset]
    #     for subset in morphology_subsets:
    #         morphology_viewer.add_subset(subset)
    #     morphology_viewer.state.x_att = all_data.id['distance']
    #     morphology_viewer.state.y_att = all_data.id['velocity']

    def _on_stage_index_changed(self, index):
        if index > 0:
            self._deferred_setup()

            # Remove this callback once we're done
            remove_callback(self.story_state, 'stage_index', self._on_stage_index_changed)

    def _maybe_deferred_setup(self, msg=None):
        print("Maybe deferred setup?")
        if self._deferred_setup_complete or \
           self.get_data(STUDENT_DATA_LABEL).size < 2 or \
           self.get_data(CLASS_DATA_LABEL).size == 0:
            return

        self._deferred_setup()

    def _deferred_setup_filter(self, msg):
        return msg.data.label in [STUDENT_DATA_LABEL, CLASS_DATA_LABEL]

    def _deferred_setup(self):
        print("Deferred setup!")
        self._setup_first_scatter_layers()
        self._setup_histogram_layers()
        self._deferred_setup_complete = True
        # self._setup_morphology_subsets()

    @property
    def all_viewers(self):
        return [layout.viewer for layout in self.viewers.values()]

    def _on_data_change(self, msg):
        viewer_id = self.viewer_ids_for_data.get(msg.data.label, [])
        for vid in viewer_id:
            try:
                self.get_viewer(vid).state.reset_limits()
            except:
                pass

    def _update_viewer_style(self, dark):
        viewers = ['layer_viewer',
                   'hubble_race_viewer',
                   'comparison_viewer',
                   'all_viewer',
                   # 'morphology_viewer',
                   'prodata_viewer',
                   'class_distr_viewer',
                   'all_distr_viewer',
                   'sandbox_distr_viewer',
                   ]

        viewer_type = ["scatter",
                       "scatter",
                       "scatter",
                       "scatter",
                       # "scatter",
                       "scatter",
                       "histogram",
                       "histogram",
                       "histogram"]

        for viewer, vtype in zip(viewers, viewer_type):
            viewer = self.get_viewer(viewer)
            theme_name = "dark" if dark else "light"
            style = load_style(f"default_{vtype}_{theme_name}")
            update_figure_css(viewer, style_dict=style)

        # spectrum_viewer = self.get_viewer("spectrum_viewer")
        # theme_name = "dark" if dark else "light"
        # style = load_style(f"default_spectrum_{theme_name}")
        # update_figure_css(spectrum_viewer, style_dict=style)

    def _on_dark_mode_change(self, dark):
        super()._on_dark_mode_change(dark)
        self._update_viewer_style(dark)

    def table_selected_color(self, dark):
        return "colors.lightBlue.darken4"

    def _update_image_location(self, using_voila):
        prepend = "voila/files/" if using_voila else ""
        self.stage_state.image_location = prepend + "data/images/stage_three"
