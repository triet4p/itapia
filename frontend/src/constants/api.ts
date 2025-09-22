// src/constants/api.ts
/**
 * API Constants
 * 
 * Contains constant values used throughout the application that are related to API interactions.
 */

import type { components } from '@/types/api';

// Extract type definitions from API schemas for TypeScript support
type SemanticType = components['schemas']['SemanticType'];
type NodeType = components['schemas']['NodeType'];

/**
 * An array containing all valid SemanticType values.
 * This array is manually created but protected by the `SemanticType[]` type.
 * If the backend adds a new enum value and you run `npm run sync:api-types`,
 * TypeScript will throw an error here if you forget to update this array,
 * ensuring synchronization.
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

/**
 * An array containing all valid NodeType values.
 */
export const NODE_TYPE_OPTIONS: NodeType[] = [
  'constant',
  'variable',
  'operator',
  'any'
];

// You can also define other constants here in the future