from cosmicds.utils import vertical_line_mark
import solara
import reacton.ipyvuetify as rv
from uuid import uuid4

from typing import List

from ...utils import mode


# glue doesn't implement a mode statistic, so we roll our own
# Since there can be multiple modes, mode can be a list
# and so we return a list for every statistic to make things simpler
def find_statistic(stat, viewer, data, bins):
    if stat == "mode":
        return mode(data, viewer.state.x_att, bins=bins, range=[viewer.state.hist_x_min, viewer.state.hist_x_max])
    else:
        return [data.compute_statistic(stat, viewer.state.x_att)]


@solara.component
def StatisticsSelector(viewers, glue_data, units, bins=None, statistics=["mean", "median", "mode"], **kwargs):

    transform = kwargs.get("transform", None)
    color = kwargs.get("color", None)
    line_ids = []
    bins = bins or [getattr(viewer.state, "bins", None) for viewer in viewers]

    help_text = {
        "mode": "Description of the mode",
        "mean": "Description of the mean",
        "median": "Description of the median",
    }

    def _remove_lines():
        for (viewer, viewer_line_ids) in zip(viewers, line_ids):
            lines = list(viewer.figure.select_traces(lambda t: t.meta in viewer_line_ids))
            viewer.figure.data = [t for t in viewer.figure.data if t not in lines]
            

    def _update_lines(selected) -> List[str]:
        _remove_lines()

        if selected is None:
            return []

        line_ids = []
        for viewer, d, bin, unit in zip(viewers, glue_data, bins, units):
            viewer_lines = []
            viewer_line_ids = []
            for stat in selected:
                try:
                    capitalized = stat.capitalize()
                    values = find_statistic(stat, viewer, d, bin)
                    if transform is not None:
                        values = [transform(v) for v in values]
                    for value in values:
                        label = f"{capitalized}: {value}"
                        if unit:
                            label += f" {unit}"
                        line_id = str(uuid4())
                        line = vertical_line_mark(viewer.layers[0], value, color, label=label)
                        line["meta"] = line_id
                        viewer_lines.append(line)
                        viewer_line_ids.append(line_id)
                except ValueError:
                    pass

            # The Scatter traces that get added aren't the same instances
            # as those we pass in. So we need to grab references to them
            # AFTER they've been added
            viewer.figure.add_traces(viewer_lines)
            line_ids.append(viewer_line_ids)

        return line_ids


    selected = solara.use_reactive([])
    def _update_selected(stat, value):
        if value and stat not in selected.value:
            selected.set(selected.value + [stat])
        else:
          try:
              index = selected.value.index(stat)
              selected.set(selected.value[:index] + selected.value[index+1:])
          except ValueError:
              pass

        new_ids = _update_lines(selected.value)
        line_ids.clear()
        line_ids.extend(new_ids)
        

    with rv.Card():
        with rv.Container():
            for stat in statistics:
                model = solara.use_reactive(False)
                # We need to bind the current value of `stat` to the lambda
                solara.Switch(value=model,
                              label=stat.capitalize(),
                              on_value=lambda value, stat=stat: _update_selected(stat, value))
