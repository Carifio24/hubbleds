<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    title-text="Trend Lines"
    @back="back_callback()"
    @next="next_callback()"
  >
    <div
      class="mb-4"
    >
      <p>
        Now that you've drawn what conclusions you can from individual students' age measurements, let's turn back to your whole class's dataset, graphed here.
      </p>
      <p>
        The same way you and your classmates each estimated an age for the universe using your 5 galaxies, you can fit a line to your whole class's dataset and estimate a new age using the {{ 5 * state_view.class_data_size }} galaxies you have measured all together.
      </p>  
    </div>
  </scaffold-alert>
</template>

