<template>
  <v-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
  >
    <h3
      class="mb-4"
    >
      Estimate Distance
    </h3>
    <div
      class="mb-4"
    >
      <p>
        The distance estimate for your galaxy has been entered into the table.
      </p>
      <p>
        Click the <v-icon>mdi-tape-measure</v-icon> icon in the table toolbar to calculate distances for the remaining galaxies.
      </p>
    </div>
    
    <v-divider
      class="my-4"
    >
    </v-divider>

    <v-row
      align="center"
      no-gutters
    >
        <v-btn
          class="black--text"
          color="accent"
          elevation="2"
          @click="
            state.marker = 'est_dis4'
          "
        >
          back
        </v-btn>
      <v-spacer></v-spacer>
      <v-col
        cols="4"
        class="shrink"
        v-if="state.distances_total < 5"
      >
        <div
          style="font-size: 16px;"
        >
          Click <v-icon>mdi-tape-measure</v-icon> in toolbar
        </div>
      </v-col>
      <v-col
        class="shrink"
        v-if="state.distances_total == 5"
      >
        <v-btn
          class="black--text"
          color="accent"
          elevation="2"
          @click="
            state.marker = 'two_com1'
          "
        >
          next
        </v-btn>
      </v-col>
    </v-row>
  </v-alert>
</template>
