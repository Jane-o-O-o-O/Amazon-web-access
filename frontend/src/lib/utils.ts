import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatUSD(value: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

export function matchLevelColor(level: string): string {
  switch (level) {
    case "same":   return "text-green-600 bg-green-50 border-green-200";
    case "high":   return "text-blue-600 bg-blue-50 border-blue-200";
    case "medium": return "text-yellow-600 bg-yellow-50 border-yellow-200";
    case "low":    return "text-gray-500 bg-gray-50 border-gray-200";
    default:       return "text-gray-500 bg-gray-50 border-gray-200";
  }
}

export function matchLevelLabel(level: string): string {
  switch (level) {
    case "same":   return "Same Product";
    case "high":   return "High Match";
    case "medium": return "Medium Match";
    case "low":    return "Low Match";
    default:       return "Unknown";
  }
}

export function stageLabel(stage: string): string {
  const labels: Record<string, string> = {
    queued:     "Queued",
    crawling:   "Crawling product page...",
    parsing:    "Parsing product info...",
    searching:  "Searching Amazon...",
    matching:   "Matching products...",
    analyzing:  "Analyzing competitors...",
    pricing:    "Calculating margins...",
    generating: "Generating Listing...",
    done:       "Complete",
  };
  return labels[stage] ?? stage;
}
