<template>
  <scaffold-alert
    @back="back_callback()"
    @next="next_callback()"
    :can-advance="can_advance"   
  >
    <template #before-next>
      Choose a response.
    </template>
    <div
      class="mb-4"
    >
    <p>Is your age estimate higher than or lower than Hubble's age estimate?</p>
      <v-container
        class="px-0"
        fluid
      >
        <mc-radiogroup
          :radio-options="[
            'Our class got a higher age estimate than Hubble',
            'Our class got a lower age estimate than Hubble.'
          ]"
          :feedbacks="[
            'Correct! Because the slope of the trend in our data is shallower than the trend in Hubble\'s data, our age estimate must be higher ',
            'Remember, the slope of the trend in our data is shallower than the trend in Hubble\'s data, so our age estimate must be higher.'
          ]"
          :correct-answers="[0]"
          :score-tag="state_view.score_tag"
          @mc-emit="mc_callback($event)"
          :initialization="state_view.mc_score"
        >
        </mc-radiogroup>
      </v-container>
    </div>
  </scaffold-alert>
</template>

<script>
module.exports = {
  data() {
    return {
    };
  },
};
</script>



