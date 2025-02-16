<template>
  <v-card
    id="selection-root"
    color="info"
    :class="highlighted ? 'pa-1' : ''"
  >
    <v-toolbar
      dense
      dark
      class="toolbar"
    >
      <v-toolbar-title
        class="text-h6 text-uppercase font-weight-regular"
      >
        Cosmic Sky Viewer
      </v-toolbar-title>

      <v-spacer></v-spacer>

      <v-tooltip
        top
      >
        <template v-slot:activator="{ on, attrs }">
          <v-btn
            icon
            v-bind="attrs"
            v-on="on"
            @click.stop="dialog = true"
          >
            <v-icon>mdi-information-outline</v-icon>
          </v-btn>
        </template>
        Info for using this tool
      </v-tooltip>

      <v-dialog
          v-model="dialog"
          max-width="1000px"
      >
        <v-card
          class="mx-auto"
        >
          <v-toolbar
            color="secondary"
            dense
            dark
          >
            <v-toolbar-title
              class="text-h6 text-uppercase font-weight-regular"
            >
              How to Use the Cosmic Sky Viewer
            </v-toolbar-title>
            <v-spacer></v-spacer>
            <span
              @click="() => { $emit('close'); dialog = false; }"
            >
              <v-btn
                icon
              >
                <v-icon>
                  mdi-close
                </v-icon>
              </v-btn>
            </span>
          </v-toolbar>
          <v-card-text>
            <v-container>
              <v-row
              >
                <v-col>
                  <p>
                    The Cosmic Sky Viewer shows a modern data set from the Sloan Digital Sky Survey (SDSS), which has collected imaging and spectral data for millions of galaxies. The green dots mark the locations of galaxies you can collect data for.
                  </p>
                  <v-row>
                    <v-col
                      cols="12"
                      lg="4"
                    >
                      <v-chip
                        label
                        outlined
                      >
                        Pan
                      </v-chip>
                    </v-col>
                    <v-col
                      cols="12"
                      lg="8"
                      class="pt-2"
                    >
                      <b>click + drag</b><br>
                      (or use <b class="codeFont">I-J-K-L</b> keys)
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col
                      cols="12"
                      lg="4"
                    >
                      <v-chip
                        label
                        outlined
                      >
                        Zoom
                      </v-chip>
                    </v-col>
                    <v-col
                      cols="12"
                      lg="8"
                      class="pt-2"
                    >
                      <b>scroll in and out</b><br>
                      (or use <b class="codeFont">Z-X</b> keys)
                    </v-col>
                  </v-row>
                </v-col>
              </v-row>
            </v-container>
          </v-card-text>
        </v-card>
      </v-dialog>

    </v-toolbar>
    <div class="selection-content">
      <jupyter-widget
        :widget="widget"
        class="wwt-widget"
      />
      <v-tooltip top>
        <template v-slot:activator="{ on, attrs }">
        <v-fab-transition>
          <v-btn
            fab
            dark
            bottom
            left
            absolute
            color="var(--success-dark)"
            class="selection-fab black--text"
            v-bind="attrs"
            v-on="on"
            v-show="Object.keys(candidate_galaxy).length !== 0"
            @click="select_current_galaxy()">
            <v-icon>mdi-plus</v-icon>
          </v-btn>
        </v-fab-transition>
        </template>
        Add galaxy to my dataset
      </v-tooltip>
      <v-tooltip top>
        <template v-slot:activator="{ on, attrs }">
          <v-btn
            fab
            dark
            bottom
            right
            absolute
            color="var(--success-dark)"
            class="selection-fab black--text"
            v-bind="attrs"
            v-on="on"
            @click="reset()">
            <v-icon>mdi-cached</v-icon>
          </v-btn>
        </template>
        Reset view
      </v-tooltip>
      <v-tooltip top>
        <template v-slot:activator="{ on, attrs }">
          <v-btn
            fab
            dark
            top 
            right
            absolute
            style="margin-top: 96px"
            color="#CCCCCC"
            class="selection-fab black--text"
            v-bind="attrs"
            v-on="on"
            v-show="Object.keys(candidate_galaxy).length !== 0"
            @click="clear_tile_cache()">
            <v-icon>mdi-refresh</v-icon>
          </v-btn>
        </template>
        Refresh images
      </v-tooltip>
    </div>
  </v-card>
</template>

<style scoped>
/* #selection-root {
  --toolbar-height: 48px;
  --widget-height: 400px;
  height: calc(var(--toolbar-height) + var(--widget-height));
  width: 100%;
} */

.selection-content {
  width: 100%;
  height: 400px;
}

/* .wwt-widget {
  height: 400px;
  width: 100%;
  position: absolute;
} */

.selection-fab {
  --margin: 15px;
  --card-padding: 16px;
  bottom: 0px !important;
  margin-bottom: var(--margin);
  margin-right: calc(var(--margin) - var(--card-padding));
}

.wwt-widget .p-Widget, .wwt-widget iframe {
  height: 400px !important;
  width: 100% !important;
}
</style>
<script setup>
</script>
