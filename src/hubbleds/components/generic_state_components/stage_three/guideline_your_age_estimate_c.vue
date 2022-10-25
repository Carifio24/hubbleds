<template>
  <scaffold-alert
    header-text="Your Age Estimate"
    @back="
      state.marker = 'age_uni4c';
    "
    @next="
      state.marker = 'cla_res1c';
    "
  >
    <div
      class="mb-4"
    >
      <p>
        Congratulations! &#127881 You have made your very own estimate of the age of the universe.
      </p>
      <p>
        Notice your best-fit line is now labeled with your age estimate.
      </p>
      <p>
        Next, we need to think about how reliable your estimate is.
      </p>
    </div>
  </scaffold-alert>
</template>
