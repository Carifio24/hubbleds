<template>
  <v-container>
    <v-row v-if="show_team_interface">
      <v-col>
        <v-btn
          color="error"
          class="black--text"
          @click="() => {
            console.log('stage state:', stage_state);
            console.log('story state:', story_state);
          }"
        >
          State
        </v-btn>
        Marker: {{ stage_state.marker }}
      </v-col>
    </v-row>

    <!--------------------- TABLE ROW ----------------------->
    <v-row
      class="d-flex align-stretch"
    >
      <v-col
        cols="12"
        lg="5"
      >
        <c-guideline-explore-data
          v-if="stage_state.marker == 'exp_dat1'"
          v-intersect.once="scrollIntoView" />
      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-card
          :color="stage_state.table_highlights.includes(stage_state.marker) ? 'info' : 'black'"
          :class="stage_state.table_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
          outlined
        >
          <v-lazy>
            <jupyter-widget :widget="widgets.fit_table"/>
          </v-lazy>
        </v-card>
      </v-col>
    </v-row>

    <!--------------------- OUR DATA HUBBLE VIEWER ----------------------->

    <v-row
      class="d-flex align-stretch"
      v-if="stage_state.indices[stage_state.marker] > stage_state.indices['exp_dat1'] && stage_state.indices[stage_state.marker] < stage_state.indices['cla_res1'] || stage_state.indices[stage_state.marker] > stage_state.indices['con_int2'] "
    >
      <v-col
        cols="12"
        lg="5"
      >
        <c-guideline-trends-data-mc1
          v-if="stage_state.marker == 'tre_dat1'"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.trend_response = true" />
        <c-guideline-trends-data2
          v-if="stage_state.marker == 'tre_dat2'"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.trend_response = true" />
        <c-guideline-trends-data-mc3
          v-if="stage_state.marker == 'tre_dat3'"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.trend_response = true" />
        <c-guideline-relationship-vel-dist-mc
          v-if="stage_state.marker == 'rel_vel1'"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.relvel_response = true" />
        <c-guideline-trend-lines1
          v-if="stage_state.marker == 'tre_lin1'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-trend-lines-draw2
          v-if="stage_state.marker == 'tre_lin2'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-best-fit-line
          v-if="stage_state.marker == 'bes_fit1'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-hubbles-expanding-universe1
          v-if="stage_state.marker == 'hub_exp1'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-hubbles-expanding-universe2
          v-if="stage_state.marker == 'hub_exp2'"
          v-intersect.once="scrollIntoView" />          
        <c-guideline-running-race-mc
          v-if="stage_state.marker == 'run_rac1'"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.race_response = true" />
        <c-guideline-runners-vel-dist
          v-if="stage_state.marker == 'run_vel1'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-age-universe
          v-if="stage_state.marker == 'age_uni1'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-hypothetical-galaxy
          v-if="stage_state.marker == 'hyp_gal1'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-age-race-equation
          v-if="stage_state.marker == 'age_rac1'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-age-universe-equation2
          v-if="stage_state.marker == 'age_uni2'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-age-universe-estimate3
          v-if="stage_state.marker == 'age_uni3'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-age-universe-estimate4
          v-if="stage_state.marker == 'age_uni4'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-your-age-estimate
          v-if="stage_state.marker == 'you_age1'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-shortcomings-est-reflect1
          v-if="stage_state.marker == 'sho_est1'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-shortcomings-est2
          v-if="stage_state.marker == 'sho_est2'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-random-variability
          v-if="stage_state.marker == 'ran_var1'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-age-universe-c
          v-if="stage_state.marker == 'age_uni1c'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-hypothetical-galaxy-c
          v-if="stage_state.marker == 'hyp_gal1c'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-age-universe-estimate3-c
          v-if="stage_state.marker == 'age_uni3c'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-age-universe-estimate4-c
          v-if="stage_state.marker == 'age_uni4c'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-your-age-estimate-c
          v-if="stage_state.marker == 'you_age1c'"
          v-intersect.once="scrollIntoView" />
      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-card
          :color="stage_state.my_galaxies_plot_highlights.includes(stage_state.marker) ? 'info' : 'black'"
          :class="stage_state.my_galaxies_plot_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
          outlined
        >
          <v-lazy>
            <jupyter-widget :widget="viewers.layer_viewer"/>
          </v-lazy>
        </v-card>
        <c-hubble-slideshow 
          v-if="stage_state.indices[stage_state.marker] > stage_state.indices['rel_vel1']"
        />  
      </v-col>
    </v-row>
    <!-- <v-row>
      <v-col>
        <v-card
          color="error"
        >
          <v-card-text>
            NOTE: Graphs that appear below this card are still a work in progress. When this stage is finished, students will not see the graphs below until they reach the relevant part in the sequencing.
          </v-card-text>
        </v-card>
      </v-col>
    </v-row> -->

    <!--------------------- SLIDER VERSION: OUR DATA HUBBLE VIEWER ----------------------->

    <v-row
      class="d-flex align-stretch"
      v-if="stage_state.indices[stage_state.marker] > stage_state.indices['ran_var1'] && stage_state.indices[stage_state.marker] < stage_state.indices['age_uni1c']"
    > 
      <v-col
        cols="12"
        lg="5"
      >
        <c-guideline-classmates-results
          v-if="stage_state.marker == 'cla_res1'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-relationship-age-slope-mc
          v-if="stage_state.marker == 'rel_age1'"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.relage_response = true"  />
        <c-guideline-class-age-range
          v-if="stage_state.marker == 'cla_age1'"
          v-intersect.once="scrollIntoView"/>
        <c-guideline-class-age-range2
          v-if="stage_state.marker == 'cla_age2'"
          v-intersect.once="scrollIntoView"/>
        <c-guideline-class-age-range3
          v-if="stage_state.marker == 'cla_age3'"
          v-intersect.once="scrollIntoView"/>
        <c-guideline-class-age-range4
          v-if="stage_state.marker == 'cla_age4'"
          v-intersect.once="scrollIntoView"/>
        <c-guideline-confidence-interval
          v-if="stage_state.marker == 'con_int1'"
          v-intersect.once="scrollIntoView"/>
      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-card
          :color="stage_state.all_galaxies_plot_highlights.includes(stage_state.marker) ? 'info' : 'black'"
          :class="stage_state.all_galaxies_plot_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
          outlined
        >
          <v-lazy>
            <jupyter-widget
              :widget="viewers.comparison_viewer"
              class="comparison_viewer"
              />
          </v-lazy>
          <c-student-slider 
            class="slider_card"
            />
        </v-card>
        <c-hubble-slideshow 
          v-if="stage_state.indices[stage_state.marker] > stage_state.indices['rel_vel1']"
        />  
      </v-col>
    </v-row>

    <!--------------------- ALL DATA HUBBLE VIEWER - during class sequence ----------------------->
    <v-row
      class="d-flex align-stretch"
      v-if="stage_state.indices[stage_state.marker] > stage_state.indices['you_age1c']"
    >
      <v-col
        cols="12"
        lg="5"
      >
        <c-guideline-classmates-results-c
          v-if="stage_state.marker == 'cla_res1c'"
          v-intersect.once="scrollIntoView" />
        <c-guideline-class-age-range-c
          v-if="stage_state.marker == 'cla_age1c'"
          v-intersect.once="scrollIntoView"/>
      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-card
          outlined
        >
          <v-lazy>
            <jupyter-widget :widget="viewers.all_viewer"/>
          </v-lazy>
          <c-class-slider 
            class="slider_card"
            />
        </v-card>
      </v-col>
    </v-row>


    <!--------------------- OUR CLASS HISTOGRAM VIEWER ----------------------->
    <v-row
      class="d-flex align-stretch"
      v-if="stage_state.indices[stage_state.marker] > stage_state.indices['con_int1'] && stage_state.indices[stage_state.marker] < stage_state.indices['age_uni1c']"
    >
      <v-col
        cols="12"
        lg="5"
      >
        <c-guideline-class-age-distribution
          v-if="stage_state.marker == 'age_dis1'"
          v-intersect.once="scrollIntoView"/>
      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-card
          :color="stage_state.my_class_hist_highlights.includes(stage_state.marker) ? 'info' : 'black'"
          :class="stage_state.my_class_hist_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
          outlined
        >
          <v-lazy>
            <jupyter-widget :widget="viewers.class_distr_viewer"/>
          </v-lazy>
        </v-card>
      </v-col>
    </v-row>

    <!--------------------- ALL DATA HISTOGRAM VIEWER ----------------------->
    <v-row
      class="d-flex align-stretch"
          v-if="stage_state.indices[stage_state.marker] > stage_state.indices['cla_age1c']"
    >
      <v-col
        cols="12"
        lg="5"
      >
        <c-guideline-class-age-distribution-c
          v-if="stage_state.marker == 'age_dis1c'"
          v-intersect.once="scrollIntoView"/>
      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-card
          :color="stage_state.all_classes_hist_highlights.includes(stage_state.marker) ? 'info' : 'black'"
          :class="stage_state.all_classes_hist_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
          outlined
        >
          <v-lazy>
            <jupyter-widget :widget="viewers.all_distr_viewer"/>
          </v-lazy>
        </v-card>
      </v-col>
    </v-row>

    <c-guideline-confidence-interval-reflect2
      v-if="stage_state.marker == 'con_int2'"
      v-intersect.once="scrollIntoView"/>
    <c-guideline-confidence-interval-reflect2-c
      v-if="stage_state.marker == 'con_int2c'"
      v-intersect.once="scrollIntoView"/>

    <!--------------------- SANDBOX HISTOGRAM VIEWER ----------------------->
    <!-- <v-row
      class="d-flex align-stretch"
          v-if="stage_state.indices[stage_state.marker] > stage_state.indices['con_int2']"
    >
      <v-col
        cols="12"
        lg="5"
      >
        <v-btn
          block
        >PLACEHOLDER 6 {{ stage_state.marker }}</v-btn>
      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-card
          :color="stage_state.sandbox_hist_highlights.includes(stage_state.marker) ? 'info' : 'black'"
          :class="stage_state.sandbox_hist_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
          outlined
        >
          <v-lazy>
            <jupyter-widget :widget="viewers.sandbox_distr_viewer"/>
          </v-lazy>
        </v-card>
      </v-col>
    </v-row> -->

    <!--------------------- MORPHOLOGY HUBBLE VIEWER ----------------------->
    <!-- <v-row
      class="d-flex align-stretch"
    >
          <!-- v-if="stage_state.indices[stage_state.marker] > stage_state.indices['con_int2']" -->

      <!-- <v-col
        cols="12"
        lg="5"
      >
        <v-btn
          block
        >PLACEHOLDER 7 {{ stage_state.marker }}</v-btn>
      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-card
          :color="stage_state.all_galaxies_morph_plot_highlights.includes(stage_state.marker) ? 'info' : 'black'"
          :class="stage_state.all_galaxies_morph_plot_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
          outlined
        >
          <v-lazy>
            <jupyter-widget :widget="viewers.morphology_viewer"/>
          </v-lazy>
          <c-class-slider
            class="slider_card"
          />
        </v-card>
      </v-col>
    </v-row> -->
 -->

  </v-container>
</template>


<style>

.v-dialog .v-card__text {
  font-size: 18px !important;
}

.v-radio label.theme--dark{
  color: white !important;
}
.v-radio label.theme--light{
  color: black !important;
}

.v-alert .v-input--radio-group+.v-alert, .v-dialog .v-input--radio-group+.v-alert {
  background-color: #000b !important;
.v-slider__thumb:hover, .v-slider__thumb-label-container:hover {
  cursor: grab;
}

.v-slider__thumb:active, .v-slider__thumb-label-container:active {
  cursor: grabbing;
}

.comparison_viewer.v-card {
  border-bottom-left-radius: 0px !important;
  border-bottom-right-radius: 0px !important;
  margin-bottom: 1px !important;
}

.slider_card {
  border-top-left-radius: 0px !important;
  border-top-right-radius: 0px !important;
}

.g_legend{
  fill: #F002 !important;
}

</style>


<script>

module.exports = {
  mounted() {
    const config = { childList: true, subtree: true };
    const onMutation = (mutationList, observer) => {
      for (const mutation of mutationList) {
        if (mutation.type === 'childList') {
          const target = mutation.target;
          const viewerName = this.viewerName(target);
          if (viewerName !== null) {
            const resizeObserver = new ResizeObserver((entries) => {
              for (const entry of entries) {
                const pixelSize = entry.devicePixelContentBoxSize[0];
                const width = pixelSize.inlineSize;
                const nticks = Math.floor(width / 125);
                this.set_viewer_nticks({ nticks: nticks, axis: 'x', viewer: viewerName });
              }
            });
            resizeObserver.observe(target, { box: 'device-pixel-content-box' });
          }
        }
      }
    }
    const observer = new MutationObserver(onMutation);
    observer.observe(this.$el, config);
  },
  methods: {
    scrollIntoView: function(entries, observer, isIntersecting) {
      if (isIntersecting) {
        entries[0].target.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      }
    },
    viewerName: function(node) {
      for (const key of Object.keys(this.viewers)) {
        if (node.classList.contains(key)) {
          return key;
        }
      }
      return null;
    }
  }
}

</script>
