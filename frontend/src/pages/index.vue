<script lang="ts" setup>
  import { ref, reactive } from 'vue';

  const tickerSym = ref('');
  // Dùng reactive cho các tùy chọn để nhóm chúng lại
  const analysisOptions = reactive({
    daily_analysis_type: 'medium', // Giá trị mặc định
    required_type: 'all'      // Giá trị mặc định
  });

  const router = useRouter();

  function startAnalysis() {
    if (tickerSym.value) {
      const upperTickerSym = tickerSym.value.toUpperCase();
      // Sửa đổi router.push để gửi cả query params
      router.push({
        name: '/analysis/[ticker]', // Tên route được tạo tự động
        params: { ticker: upperTickerSym },
        query: { ...analysisOptions } // Gửi các tùy chọn làm query params
      });
    } else {
      // Sau này sẽ thay bằng v-snackbar của Vuetify
      alert("Vui lòng nhập một mã cổ phiếu hợp lệ");
    }
  }
</script>

<template>
  <v-container class="fill-height">
    <v-row justify="center" align="center">
      <v-col cols="12" md="8" lg="6">
        <v-card elevation="4" class="pa-4">
          <VCardTitle class="text-center text-h5">Start your first quick check analysis</VCardTitle>

          <VCardText>
            <VTextField
              label="Input Ticker symbol (ex. AAPL)"
              variant="outlined"
              v-model="tickerSym"
              @keydown.enter="startAnalysis"
            >
            </VTextField>
            <VRow>
              <VCol cols="12" sm="6">
                <VSelect v-model="analysisOptions.daily_analysis_type"
                label="Daily Analysis Time Frame"
                :items="['short', 'medium', 'long']"
                variant="outlined"></VSelect>
              </VCol>
              <VCol cols="12" sm="6">
                <VSelect v-model="analysisOptions.required_type"
                label="Return Analysis Report Type"
                :items="['daily', 'intraday', 'all']"
                variant="outlined"></VSelect>
              </VCol>
            </VRow>

            <VBtn block color="primary" size="large" @click="startAnalysis">Analysis</VBtn>
          </VCardText>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.text-h5 {
  font-weight: bold !important;
}
</style>