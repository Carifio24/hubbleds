<template>
  <scaffold-alert
    title-text="Class Age Range"
    @back="back_callback()"
    @next="next_callback()"
    :can-advance="can_advance"
  >
    <div
      class="mb-4"
      v-intersect="(entries, _observer, intersecting) => { if (intersecting) { MathJax.typesetPromise(entries.map(entry => entry.target)) }}"
    >
      <v-card
        class="JaxEquation pa-3"
        color="info lighten-1"
        elevation="0"
      >        
        $$ \text{Low age: } \textcolor{black}{\colorbox{#FFAB91}{ {{ (state_view.student_low_age).toFixed(0) }} } } \text{ Gyr} $$
        $$ \text{High age: } \textcolor{black}{\colorbox{#FFAB91}{ {{ (state_view.student_high_age).toFixed(0) }} } } \text{ Gyr} $$
      </v-card>
      <p class="mt-4">
        At first glance, this may seem like a large spread in possible age values for the universe. But if you think back to what astronomers knew in the 1920’s, the common scientific view was that the universe has always existed. So being able to measure any finite age for the universe was a BIG DEAL. 
      </p>
    </div>
  </scaffold-alert>
</template>

