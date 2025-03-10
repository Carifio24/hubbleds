<template>
  <scaffold-alert
      color="info"
      class="mb-4 mx-auto"
      max-width="800"
      elevation="6"
      title-text="Select Your Galaxies"
      @back="back_callback()"
      @next="next_callback()"
      :can-advance="can_advance"
      :speech="speech"
  >
   <template #before-next>
     <div>
       <div
           v-if="state_view.total_galaxies < 5 && state_view.total_galaxies > 0"
           style="font-size: 16px;"
       >
         <b>Select</b> {{ 5 - state_view.total_galaxies }} <span
           v-if="state_view.total_galaxies > 0">more</span> <span
           v-if="state_view.total_galaxies < 4">galaxies</span><span
           v-if="state_view.total_galaxies == 4">galaxy</span>.
       </div>
       <div
           v-if="!state_view.galaxy_is_selected"
           style="font-size: 16px;"
       >
         <b>Click</b> on any green dot.
       </div>
       <div
           v-if="state_view.galaxy_is_selected"
           style="font-size: 16px;"
       >
         <b>Click</b>
         <v-btn icon dark x-small disabled class="mx-1 black&#45;&#45;text" elevation="2" style="background-color: var(--success-dark);">
           <v-icon style="color:black!important;">mdi-plus</v-icon>
         </v-btn>
         to add galaxy or
         <v-btn icon dark x-small disabled class="mx-1 black&#45;&#45;text" elevation="2" style="background-color: var(--success-dark);">
           <v-icon style="color:black!important;">mdi-cached</v-icon>
         </v-btn>
         to choose another
       </div>
     </div>
   </template>

    <div
        v-if="!state_view.galaxy_is_selected"
        class="mb-4"
    >
      <p>
        The green dots in the Cosmic Sky Viewer mark the locations of galaxies you can collect data for.
      </p>
      <p>
        Pan around the sky and click on one of these dots to select that galaxy.
      </p>
      <p style="font-weight: 300">
        (If no green dots are visible, try clicking back and then next to refresh the view.
      </p>
      <p style="font-weight: 300">
        If the green dots still do not appear, use the gray "SELECT A RANDOM GALAXY" button to move forward.)
      </p>
    </div>
    <div
        v-if="state_view.galaxy_is_selected"
    >
      <p>
        If this galaxy looks good to you, click
        <v-btn icon dark x-small disabled class="mx-1 black--text" elevation="2" style="background-color: var(--success-dark);">
          <v-icon style="color:black!important;">mdi-plus</v-icon>
        </v-btn>
        to add it to your data set.
      </p>
      <p>
        If you’d rather look for another galaxy, click
        <v-btn icon dark x-small disabled class="mx-1 black--text" elevation="2" style="background-color: var(--success-dark);">
          <v-icon style="color:black!important;">mdi-cached</v-icon>
        </v-btn>
        to reset the view and choose a different green dot.
      </p>
      <p style="font-weight: 300">
        If the galaxy image doesn't load correctly (and it remains very blurry), click 
        <v-btn icon dark x-small disabled class="mx-1 black--text" elevation="2" style="background-color: #CCCCCC;">
          <v-icon style="color:black!important;">mdi-refresh</v-icon>
        </v-btn>
        to reload.
      </p>
    </div>
    <div v-if="state_view.total_galaxies ==5">
      <p>
        You have already selected the maximum number of galaxies ({{ state_view.total_galaxies }} / 5). Click next to proceed to the next step.
      </p>
    </div>
  </scaffold-alert>
</template>
<script setup>
</script>
