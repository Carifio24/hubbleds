<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    title-text="Angular Size Measurement"
    @back="back_callback()"
    @next="next_callback()"
    :can-advance="can_advance"
  >
    <template #before-next>
      Measure angular size of galaxy
    </template>

    <div
      class="mb-4"
    >
    <p>
        Click on one edge of your galaxy to mark the ruler's starting point.
      </p>
      <p>
        Move the cursor to the other edge of your galaxy and click again.
      </p>
      <p>
        If you want to adjust your measurement, you can click on the ends of the green line and move them to a new location.
      </p>
    </div>
  </scaffold-alert>
</template>
<script>
</script>