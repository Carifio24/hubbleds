<template>
  <scaffold-alert
    header-text="Angular Size Measurement"
    @back="
      state.marker = 'ang_siz2';
    "
    @next="state.marker = 'ang_siz3';"
  >
    <div
      class="mb-4"
    >
    <p> 
      The angular scale is measured in degrees (&#176;&thinsp;), arcminutes (&thinsp;'&thinsp;), or arcseconds (&thinsp;"&thinsp;) as you zoom in.  
    </p>
     <p> 
      There are 60 <strong>arcminutes</strong> in 1 degree, and 60 <strong>arcseconds</strong> in 1 arcminute.
    </p>
    <p> The data in your table will be measured in arcseconds.</p>
      
    </div>
  </scaffold-alert>
</template>