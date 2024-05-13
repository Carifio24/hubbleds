<template>
  <scaffold-alert
    title-text="Most Likely Value"
    @back="back_callback()"
    @next="next_callback()"
    :can-advance="can_advance"
  >
    <div
      class="mb-4"
    >
      <p>
        Listed above are 3 quantities that scientists might calculate from a distribution to determine the <strong>most likely value</strong>.
      </p>
    </div>
  </scaffold-alert>
</template>

