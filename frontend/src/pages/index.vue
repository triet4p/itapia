<script lang="ts" setup>
    import { ref } from 'vue';

    const tickerSym = ref('')

    function startAnalysis() {
        if (tickerSym.value) {
            alert("Starting analyze ....")
        } else {
            alert("Please input an valid symbol")
        }
    }
</script>

<template>
    <v-container class="fill-height">
        <v-row justify="center" align="center">
            <v-col cols="12" md="8" lg="6">
                <v-card elevation="4" class="pa-4">
                    <VCardTitle class="text-center"></VCardTitle>

                    <VCardText>
                        <VTextField
                            label="Input Ticker symbol (ex. AAPL)"
                            variant="outlined"
                            v-model="tickerSym"
                        >
                        </VTextField>

                        <VBtn block color="primary" size="large" :onclick="startAnalysis">Analysis</VBtn>
                    </VCardText>
                </v-card>
            </v-col>
        </v-row>
    </v-container>
</template>