<template>
  <scaffold-alert
    header-text="Classmates' Data"
    @back="
      state.marker = 'you_age1c';
    "
    @next="
      state.marker = 'cla_age1c';
    "
  >
    <div
      class="mb-4"
    >
      <p>
        Let’s look at your classmates' data, student by student. Someone in your class measured the lowest age value for the universe. Someone measured the highest age.
      </p>
      <p>
        Use the slider to scan through the age estimates that each person in your class measured. 
      </p>
    </div>
  </scaffold-alert>
</template>
