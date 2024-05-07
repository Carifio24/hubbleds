<template>
  <v-card
    class="slider_card"
  >
    <v-slider
      v-model="selected"
      :step="step"
      :min="vmin"
      :max="vmax"
      :color="color"
      :thumb-color="color"
      ticks
      :tick-labels="tick_labels"
      thumb-label="always"
    >
      <template v-slot:thumb-label="">
        <strong>{{ thumb_value }}</strong>
      </template>
    </v-slider>
  </v-card>
</template>

<style scoped>

</style>