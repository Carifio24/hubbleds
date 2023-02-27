<template>
  <scaffold-alert
    header-text="Your Age Estimate"
    @back="
      state.marker = 'bes_fit1c';
    "
    @next="
      state.marker = 'cla_res1c';
    "
  >
    <div
      class="mb-4"
    >
      <p>
        How did your drawn trend line compare with your class's best fit line? Were they closer together than the lines for your own five galaxies?
      </p>
      <p>
        The fit line is labeled with your class's age estimate. How does it compare with the "best guess" age and confidence intervals you identified earlier? Notice whether the best fit age is within the bounds you chose. ({{ state.age_calc_state.low_guess }} to {{ state.age_calc_state.high_guess }} Gyr, with a best guess of {{ state.age_calc_state.best_guess }} Gyr)
      </p>
    </div>
  </scaffold-alert>
</template>

<script>
module.exports = {
  props: ['state']
}
</script>
