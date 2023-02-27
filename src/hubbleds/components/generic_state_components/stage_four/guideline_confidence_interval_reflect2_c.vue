<!-- this state.marker = con_int2c -->
<template>
  <scaffold-alert
    header-text="Identify Your Confidence Interval"
    @back="
      state.marker = 'age_dis1c';
    "
    @next="
      state.marker = 'two_his1';
    "
  >
    <div
      class="mb-4"
    >
      <p>
        Earlier, your best guess for the age of the universe was: {{ state.age_calc_state.best_guess }} Gyr, with a likely range from {{ low_guess }} to {{ high_guess }} Gyr.
      </p>
      <p>
        After exploring data from all the other classes, you might consider updating your values.
      </p>
      <v-row>
        <v-col
          cols="12"
          lg="9">      
          1. My new best guess for the age of the universe based on my entire class’s data set: 
        </v-col>
        <v-col>
          <v-btn
            color="secondary lighten-1"
            @click="state.age_calc_state.hint1_dialog = true"
          >
            hint
            <v-dialog
              v-model="state.age_calc_state.hint1_dialog"
              persistent
              max-width="600px">
              <v-card
                class="mx-auto"
              >
                <v-toolbar
                  color="secondary"
                  dense
                  dark
                >
                  <v-toolbar-title
                    class="text-h6 text-uppercase font-weight-regular"
                  >
                    Hint #1
                  </v-toolbar-title>
                  <v-spacer></v-spacer>
                  <span
                    @click="
                      () => {
                        $emit('close');
                        state.age_calc_state.hint1_dialog = false;
                      }
                    "
                  >
                    <v-btn icon>
                      <v-icon> mdi-close </v-icon>
                    </v-btn>
                  </span>
                </v-toolbar>
                <div class="pa-6">
                  A gold standard in scientific practice is reproducibility. If someone else performs a procedure you did and obtains the same or very similar result, that means your result was reproducible and is therefore more plausible.
                </div>
              </v-card>
            </v-dialog>
          </v-btn>
        </v-col>
      </v-row>
      <v-row>
        <v-col
          cols="12"
          lg="3"
        >
          <free-response
            outlined
            rows="1"
            label="New Best Guess Age"
            tag="new-best-guess-age"
          ></free-response>
        </v-col>
        <v-col>
          Gyr
        </v-col>
      </v-row>

      <v-row>
        <v-col
          cols="12"
          lg="9"
        >
          2. My best guess for the likely range of ages of the universe based on my entire class’s data set: 
        </v-col>
        <v-col>
          <v-btn
            color="secondary lighten-1"
            @click="state.age_calc_state.hint2_dialog = true"
          >
            hint
            <v-dialog
              v-model="state.age_calc_state.hint2_dialog"
              persistent
              max-width="600px">
              <v-card
                class="mx-auto"
              >
                <v-toolbar
                  color="secondary"
                  dense
                  dark
                >
                  <v-toolbar-title
                    class="text-h6 text-uppercase font-weight-regular"
                  >
                    Hint #2
                  </v-toolbar-title>
                  <v-spacer></v-spacer>
                  <span
                    @click="
                      () => {
                        $emit('close');
                        state.age_calc_state.hint2_dialog = false;
                      }
                    "
                  >
                    <v-btn icon>
                      <v-icon> mdi-close </v-icon>
                    </v-btn>
                  </span>
                </v-toolbar>
                <div class="pa-6">
                  <p>
                    The range you pick will have a tradeoff between how likely it is that the “true” value actually lies within the range you choose vs. having a narrow enough range that your measurement is actually useful. A very large range is more likely to include the "true" value, but may be so nonspecific that it is not useful. A narrow range has more specificity but may not include the "true" value.
                  </p>
                  <p>
                    Different people will feel more or less comfortable with the different sides of this tradeoff, and there isn’t really a right or wrong answer as long as you justify why you
                    chose what you did.
                  </p>
                  <p>
                    If you are feeling really stuck, feel free to discuss this with a classmate or your instructor.
                  </p>
                </div>
              </v-card>
            </v-dialog>
          </v-btn>
        </v-col>
      </v-row>
      <v-row>
        <v-col
          cols="12"
          lg="3">
          <free-response
            outlined
            rows="1"
            label="New Likely Low Age"
            tag="new-likely-low-age"
          ></free-response>
        </v-col>
        <v-col
          lg="2">
          Gyr
        </v-col>
              <v-col
          cols="12"
          lg="3">
          <free-response
            outlined
            rows="1"
            label="New Likely High Age"
            tag="new-likely-high-age"
          ></free-response>
        </v-col>
        <v-col
          lg="2">
          Gyr
        </v-col>
      </v-row>

      <p class="mt-4">
        3. Explain why you chose these new values based on the all-classes data:
      </p>
      <free-response
        outlined
        rows="1"
        label="My Updated Reasoning"
        tag="my-updated-reasoning"
      ></free-response>
    </div>
  </scaffold-alert>
</template>

<script>
module.exports = {
  props: ['state'],
}
</script>
