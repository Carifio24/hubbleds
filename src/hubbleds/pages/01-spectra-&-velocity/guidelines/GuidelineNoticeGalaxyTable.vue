<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    title-text="Table Data"
    @back="back_callback()"
    @next="next_callback()"
    :can-advance="can_advance"
    :speech="speech"
  >
    <div
      class="mb-4"
    >
      <p>
        Notice that your table now has a row for your selected galaxy.
      </p>
    </div>
  </scaffold-alert>
</template>
