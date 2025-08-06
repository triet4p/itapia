// src/constants/api.ts

import type { components } from '@/types/api';

// Lấy ra định nghĩa kiểu SemanticType để TypeScript hỗ trợ
type SemanticType = components['schemas']['SemanticType'];
type NodeType = components['schemas']['NodeType']

/**
 * Một mảng chứa tất cả các giá trị hợp lệ của SemanticType.
 * Mảng này được tạo thủ công nhưng được "bảo vệ" bởi kiểu dữ liệu `SemanticType[]`.
 * Nếu backend thêm một giá trị mới vào Enum và bạn chạy lại `npm run sync:api-types`,
 * TypeScript sẽ báo lỗi ở đây nếu bạn quên cập nhật mảng này,
 * giúp đảm bảo sự đồng bộ.
 */
export const SEMANTIC_TYPE_OPTIONS: SemanticType[] = [
  'ANY',
  'DECISION_SIGNAL',
  'RISK_LEVEL',
  'OPPORTUNITY_RATING',
  'NUMERICAL',
  'BOOLEAN',
  'PRICE',
  'PERCENTAGE',
  'FINANCIAL_RATIO',
  'MOMENTUM',
  'TREND',
  'VOLATILITY',
  'VOLUME',
  'SENTIMENT',
  'FORECAST_PROB'
];

export const NODE_TYPE_OPTIONS: NodeType[] = [
  'constant',
  'variable',
  'operator',
  'any'
]

// Bạn cũng có thể định nghĩa các hằng số khác ở đây trong tương lai