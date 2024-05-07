from ipyvuetify import VuetifyTemplate
from echo.callback_container import CallbackContainer
from numpy import where
from traitlets import observe, Float, Int, List, Unicode

from cosmicds.utils import load_template

class IDSlider(VuetifyTemplate):
    template = load_template("id_slider.vue", __file__,
                             traitlet=True).tag(sync=True)
    color = Unicode("#112E51").tag(sync=True)
    selected = Int(0).tag(sync=True)
    step = Int(1).tag(sync=True)
    thumb_value = Float().tag(sync=True)
    tick_labels = List().tag(sync=True)
    vmax = Int(1).tag(sync=True)
    vmin = Int(0).tag(sync=True)
    
    def __init__(self, data, id_component, value_component, *args, **kwargs):
        # NB: We can't call this member value data
        # since VuetifyTemplate already has a data member
        # (that represents the typical Vue data)
        self.glue_data = data
        self.id_component = id_component
        self.value_component = value_component
        self.selected_id = None

        self.default_color = kwargs.get("default_color", "#3A86FF") 
        self.highlight_ids = kwargs.get("highlight_ids", [])
        self.highlight_label = kwargs.get("highlight_label", None)
        self.highlight_color = kwargs.get("highlight_color", "#FB5607") 
        self.color = self.default_color

        self._id_change_cbs = CallbackContainer()
        self._refresh_cbs = CallbackContainer()

        self.refresh()
        self._selected_changed({"new": self.selected})

        if "step" in kwargs:
            self.step = int(kwargs["step"])
        super().__init__(*args, **kwargs)

    def update_data(self, data):
        self.glue_data = data
        self.refresh()

    def refresh(self):
        self.ids = sorted(self.glue_data[self.id_component], key=self._sort_key)
        self.values = sorted(self.glue_data[self.value_component])
        self.vmax = len(self.values) - 1
        if(self.vmax % 2 == 0): # check if even
            self.halfvmax = self.vmax/2
            self.tick_labels = ["Low"] + ["" for _ in range(int(self.halfvmax)-1)] + ["Age (Gyr)"]  + ["" for _ in range(int(self.halfvmax)-1)] + ["High"]
        else:
            self.halfvmax = (self.vmax+1)/2
            self.tick_labels = ["Low"] + ["" for _ in range(int(self.halfvmax)-1)] + ["Age (Gyr)"]  + ["" for _ in range(int(self.halfvmax)-2)] + ["High"]

        if not hasattr(self, 'selected_id') or self.selected_id not in self.ids:
            self.selected = 0
        else:
            self.selected = self.ids.index(self.selected_id)
        for cb in self._refresh_cbs:
            cb(self)

    def _sort_key(self, id):
        idx = where(self.glue_data[self.id_component] == id)[0][0]
        return self.glue_data[self.value_component][idx]

    def on_id_change(self, callback, run=True):
        self._id_change_cbs.append(callback)
        if self.selected_id is not None and run:
            callback(self.selected_id, self.highlighted)

    def remove_on_id_change(self, callback):
        self._id_change_cbs.remove(callback)

    def on_refresh(self, callback, run=True):
        self._refresh_cbs.append(callback)
        if run:
            callback(self)

    def remove_on_refresh(self, callback):
        self._refresh_cbs.remove(callback)

    @observe('selected')
    def _selected_changed(self, change):

        old_index = change.get("old", None)
        index = change["new"]
        if len(self.ids) < index + 1 or len(self.values) < index + 1:
            return
        self.selected_id = int(self.ids[index])
        self.thumb_value = round(self.values[index])
        highlighted = self.selected_id in self.highlight_ids
        old_highlighted = old_index is not None and self.ids[old_index] in self.highlight_ids
        self.highlighted = highlighted

        if (highlighted or old_highlighted) and self.highlight_label is not None:
            labels = [x for x in self.tick_labels]
            if highlighted:
                labels[index] = self.highlight_label(self.selected_id)

            # Restore the end labels if we had previously changed them
            # and remove the highlighted label
            if old_index == 0:
                labels[0] = "Lowest"
            if old_index == len(self.ids) - 1:
                labels[-1] = "Highest"
            elif old_highlighted:
                labels[old_index] = ""
            self.tick_labels = labels

        if highlighted and self.highlight_color is not None:
            self.color = self.highlight_color
        elif self.color != self.default_color:
            self.color = self.default_color

        for cb in self._id_change_cbs:
            cb(self.selected_id, self.highlighted)
    
