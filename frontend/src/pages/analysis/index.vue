<script setup lang="ts">
  import { ref, reactive, watch } from 'vue';
  import { useRouter } from 'vue-router';

  // --- STATE MANAGEMENT ---

  // Loại quy trình phân tích
  type ProcessType = 'quick' | 'deep' | null;
  const selectedProcess = ref<ProcessType>(null);

  // Dữ liệu chung cho form
  const ticker = ref('');

  // Các tùy chọn cho Quick Analysis
  const quickOptions = reactive({
    daily_analysis_type: 'medium',
    required_type: 'all',
    showKeyIndicators: true,
    showTopPatterns: true,
    // Dùng mảng để lưu các lựa chọn forecasting
    selectedForecasts: [0, 1, 2], // Mặc định chọn cả 3
    showTopNews: true,
    showSummary: true,
  });

  // (Tương lai) Các tùy chọn cho Deep Analysis
  // const deepOptions = reactive({ ... });

  const router = useRouter();

  // --- LOGIC & METHODS ---

  function startAnalysis() {
    if (!ticker.value) {
      alert('Vui lòng nhập mã cổ phiếu.');
      return;
    }
    if (!selectedProcess.value) {
      alert('Vui lòng chọn một quy trình phân tích.');
      return;
    }

    // Tập hợp các query params
    let query: Record<string, any> = {
      processType: selectedProcess.value,
    };

    if (selectedProcess.value === 'quick') {
      query = {
        ...query,
        daily_analysis_type: quickOptions.daily_analysis_type,
        required_type: quickOptions.required_type,
        showKeyIndicators: quickOptions.showKeyIndicators,
        showTopPatterns: quickOptions.showTopPatterns,
        // Chuyển mảng forecasting thành chuỗi để truyền qua URL
        forecasts: quickOptions.selectedForecasts.join(','),
        showTopNews: quickOptions.showTopNews,
        showSummary: quickOptions.showSummary
      };
    } else if (selectedProcess.value === 'deep') {
      // (Tương lai) Thêm logic cho Deep Dive ở đây
      // query = { ...query, ...deepOptions };
    }
    
    // Điều hướng đến trang kết quả
    router.push({
      name: '/analysis/[ticker]',
      params: { ticker: ticker.value.toUpperCase() },
      query: query,
    });
  }

  // Theo dõi sự thay đổi của quy trình để reset các tùy chọn nếu cần
  watch(selectedProcess, (newValue, oldValue) => {
    console.log(`Đã chuyển từ quy trình ${oldValue} sang ${newValue}`);
    // Có thể thêm logic reset các form ở đây trong tương lai
  });

</script>

<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <h1 class="text-h4 text-center mb-6">ITAPIA Analysis</h1>

        <v-card class="pa-4" elevation="2">
          <!-- BƯỚC 1: CÁC THÔNG TIN CƠ BẢN -->
          <v-card-title>Basic Information</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="ticker"
                  label="Mã Cổ phiếu"
                  placeholder="VD: FPT, AAPL"
                  variant="outlined"
                  clearable
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <!-- Sử dụng v-radio-group để chọn 1 trong 2 quy trình -->
                <p class="font-weight-medium mb-2">Choose process:</p>
                <v-radio-group v-model="selectedProcess" inline>
                  <v-radio label="Quick Analysis" value="quick"></v-radio>
                  <v-radio label="Deep Analysis (Further)" value="deep" disabled></v-radio>
                </v-radio-group>
              </v-col>
            </v-row>
          </v-card-text>

          <v-divider class="my-4"></v-divider>

          <!-- BƯỚC 2: CÁC TÙY CHỌN CHO QUICK ANALYSIS -->
          <!-- Dùng v-expand-transition và v-if để chỉ hiện khi đã chọn 'quick' -->
          <v-expand-transition>
            <div v-if="selectedProcess === 'quick'">
              <v-card-title>Quick Analysis Options</v-card-title>
              <v-card-text>
                <v-row>
                  <!-- Các tham số cho API -->
                  <v-col cols="12" sm="6">
                    <v-select
                      v-model="quickOptions.daily_analysis_type"
                      label="Daily time frame"
                      :items="['short', 'medium', 'long']"
                      variant="outlined"
                    ></v-select>
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-select
                      v-model="quickOptions.required_type"
                      label="Require analysis type"
                      :items="['daily', 'intraday', 'all']"
                      variant="outlined"
                    ></v-select>
                  </v-col>
                </v-row>
                
                <v-divider class="my-2"></v-divider>
                
                <!-- Các tùy chọn hiển thị trên Frontend -->
                <p class="font-weight-medium mb-2 mt-4">Components displayed in the report:</p>
                <v-row>
                  <v-col cols="12" sm="4">
                    <v-checkbox v-model="quickOptions.showKeyIndicators" label="Key Indicators"></v-checkbox>
                  </v-col>
                  <v-col cols="12" sm="4">
                    <v-checkbox v-model="quickOptions.showTopPatterns" label="Top Patterns"></v-checkbox>
                  </v-col>
                   <v-col cols="12" sm="4">
                    <v-checkbox v-model="quickOptions.showTopNews" label="Top News"></v-checkbox>
                  </v-col>
                   <v-col cols="12" sm="4">
                    <v-checkbox v-model="quickOptions.showSummary" label="Summary of News"></v-checkbox>
                  </v-col>
                </v-row>
                
                 <v-divider class="my-2"></v-divider>
                 
                <p class="font-weight-medium mb-2 mt-4">Forecasting Task to display:</p>
                 <v-checkbox v-model="quickOptions.selectedForecasts" label="Triple Barrier" :value="0"></v-checkbox>
                 <v-checkbox v-model="quickOptions.selectedForecasts" label="5-Days Distribution (Mid-term)" :value="1"></v-checkbox>
                 <v-checkbox v-model="quickOptions.selectedForecasts" label="20-Days Distribution (Long-term)" :value="2"></v-checkbox>
              </v-card-text>
            </div>
          </v-expand-transition>
          
          <!-- (Tương lai) Tùy chọn cho Deep Dive sẽ nằm ở đây -->
          <!-- <div v-if="selectedProcess === 'deep'"> ... </div> -->

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              size="large"
              @click="startAnalysis"
              :disabled="!selectedProcess || !ticker"
            >
              Run Analysis
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>