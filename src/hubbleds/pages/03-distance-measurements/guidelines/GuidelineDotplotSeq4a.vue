<template>
  <scaffold-alert
    title-text="Measurement Comparison"
    @back="back_callback()"
    @next="next_callback()"
    :can-advance="can_advance"
  >
    <template #before-next>
        Choose a response
      </template>
    <div
      class="mb-4"
    >
      <p>
        It might be helpful to explore how the angular size and distance measurements relate to each other. Click on different locations in the graph of angular sizes to see what values they correspond to in the distance dot plot above. 
      </p>
      <p>
        What relationship do you see between the angular size and distance measurements?
      </p>
      <mc-radiogroup 
          :radio-options="[
            'A large angular size corresponds to a small distance',
            'A large angular size corresponds to a large distance',
            'There is no relation between distance and the measured angular size',
            ]"
            :feedbacks="[
            'Correct! If two objects have the same size, the one at a larger distance will have a smaller angular size.',
            'Not quite. Look again at the graphs and check two different distance values. Which one has the larger angular size?',
            'Not quite. Look again at the graphs and check two different distance values. Which one has the larger angular size?',
            ]" 
          :correct-answers="[0]"
          :wrong-answers="[1,2]"
          :score-tag="state_view.score_tag"
          @mc-emit="mc_callback($event)"
          :initialization="state_view.mc_score"
          >
          </mc-radiogroup>
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
