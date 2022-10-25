<template>
  <scaffold-alert
    header-text="A Hypothetical Galaxy"
    @back="
      state.marker = 'age_uni1c';
    "
    @next="
      state.marker = 'age_uni3c';
    "
  >
    <div
      class="mb-4"
    >
      <p>
        This "best fit galaxy" is a hypothetical galaxy that lies on your best fit line. You can use its distance and velocity to estimate the age of the universe given by the best fit line to your galaxy data. (Any galaxy that lies on this line would give you the same age estimate.)
      </p>
      <p>
        Now let's look at the equation that can tell us the age of universe.
      </p>
    </div>
  </scaffold-alert>
</template>
