// lib/metrics.ts

import { fetchFromAPI } from "./api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface MetricsData {
  accuracy: number;
  precision_A: number;
  precision_B: number;
  precision_C: number;
  recall_A: number;
  recall_B: number;
  recall_C: number;
  f1_A: number;
  f1_B: number;
  f1_C: number;
  macro_precision: number;
  macro_recall: number;
  macro_f1: number;
  weighted_f1: number;
  confusion_matrix: number[][];
  total_samples: number;
  valid_samples: number;
}

export interface ClassificationMetricsResponse {
  status: "success" | "warning" | "error";
  message: string;
  metrics: MetricsData | null;
  timestamp?: string;
}

export interface MetricsSummary {
  accuracy: number;
  macro_f1: number;
  weighted_f1: number;
  total_samples: number;
  grade_distribution: {
    A: { precision: number; recall: number; f1: number };
    B: { precision: number; recall: number; f1: number };
    C: { precision: number; recall: number; f1: number };
  };
  timestamp?: string;
}

export interface ConfusionMatrixResponse {
  status: "success" | "error";
  confusion_matrix: number[][];
  labels: string[];
  total_samples: number;
}

// Storage key
const METRICS_CACHE_KEY = "grading_metrics";
const METRICS_CACHE_EXPIRY = 5 * 60 * 1000; // 5 minutes

interface CachedMetrics {
  data: MetricsData;
  timestamp: number;
}

/**
 * Fetch comprehensive classification metrics
 */
export async function fetchClassificationMetrics(): Promise<ClassificationMetricsResponse> {
  try {
    const data: ClassificationMetricsResponse = await fetchFromAPI<ClassificationMetricsResponse>(
      '/api/metrics/classification',
      {
        method: "GET",
        credentials: "include",
      }
    );
    
    // Cache the metrics
    if (data.status === "success" && data.metrics) {
      cacheMetrics(data.metrics);
    }

    return data;
  } catch (error) {
    console.error("Error fetching classification metrics:", error);
    return {
      status: "error",
      message: `Error fetching metrics: ${error instanceof Error ? error.message : "Unknown error"}`,
      metrics: null,
    };
  }
}

/**
 * Fetch simplified metrics summary
 */
export async function fetchMetricsSummary() {
  try {
    const data = await fetchFromAPI<MetricsSummary>(
      '/api/metrics/summary',
      {
        method: "GET",
        credentials: "include",
      }
    );

    return data;
  } catch (error) {
    console.error("Error fetching metrics summary:", error);
    return null;
  }
}

/**
 * Fetch confusion matrix only
 */
export async function fetchConfusionMatrix(): Promise<ConfusionMatrixResponse | null> {
  try {
    const data = await fetchFromAPI<ConfusionMatrixResponse>(
      '/api/metrics/confusion-matrix',
      {
        method: "GET",
        credentials: "include",
      }
    );

    return data;
  } catch (error) {
    console.error("Error fetching confusion matrix:", error);
    return null;
  }
}

/**
 * Cache metrics to local storage
 */
export function cacheMetrics(metrics: MetricsData): void {
  try {
    const cached: CachedMetrics = {
      data: metrics,
      timestamp: Date.now(),
    };
    localStorage.setItem(METRICS_CACHE_KEY, JSON.stringify(cached));
  } catch (error) {
    console.error("Error caching metrics:", error);
  }
}

/**
 * Get cached metrics if available and not expired
 */
export function getCachedMetrics(): MetricsData | null {
  try {
    const cached = localStorage.getItem(METRICS_CACHE_KEY);
    if (!cached) return null;

    const parsed: CachedMetrics = JSON.parse(cached);
    const age = Date.now() - parsed.timestamp;

    // Return cached data if not expired
    if (age < METRICS_CACHE_EXPIRY) {
      return parsed.data;
    }

    // Clear expired cache
    localStorage.removeItem(METRICS_CACHE_KEY);
    return null;
  } catch (error) {
    console.error("Error retrieving cached metrics:", error);
    return null;
  }
}

/**
 * Clear cached metrics
 */
export function clearMetricsCache(): void {
  try {
    localStorage.removeItem(METRICS_CACHE_KEY);
  } catch (error) {
    console.error("Error clearing metrics cache:", error);
  }
}

/**
 * Get metrics with automatic caching strategy
 */
export async function getMetricsWithCache(
  forceRefresh: boolean = false
): Promise<MetricsData | null> {
  // Check cache first
  if (!forceRefresh) {
    const cached = getCachedMetrics();
    if (cached) {
      console.log("Using cached metrics");
      return cached;
    }
  }

  // Fetch fresh data
  const response = await fetchClassificationMetrics();
  
  if (response.status === "success" && response.metrics) {
    return response.metrics;
  }

  return null;
}

/**
 * Format metrics for display
 */
export function formatMetrics(metrics: MetricsData) {
  return {
    accuracy: `${(metrics.accuracy * 100).toFixed(2)}%`,
    macro_f1: metrics.macro_f1.toFixed(4),
    weighted_f1: metrics.weighted_f1.toFixed(4),
    macro_precision: metrics.macro_precision.toFixed(4),
    macro_recall: metrics.macro_recall.toFixed(4),
    grades: {
      A: {
        precision: metrics.precision_A.toFixed(4),
        recall: metrics.recall_A.toFixed(4),
        f1: metrics.f1_A.toFixed(4),
      },
      B: {
        precision: metrics.precision_B.toFixed(4),
        recall: metrics.recall_B.toFixed(4),
        f1: metrics.f1_B.toFixed(4),
      },
      C: {
        precision: metrics.precision_C.toFixed(4),
        recall: metrics.recall_C.toFixed(4),
        f1: metrics.f1_C.toFixed(4),
      },
    },
  };
}
