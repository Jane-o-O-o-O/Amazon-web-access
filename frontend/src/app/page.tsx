"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { createTask } from "@/lib/api";
import type { CostParams } from "@/types";
import { toast } from "sonner";

const DEFAULT_COST: CostParams = {
  purchasePrice: 2.5,
  domesticShipping: 0.2,
  internationalShipping: 1.0,
  fbaFee: 3.2,
  commissionRate: 0.15,
  adsRate: 0.08,
  taxRate: 0.03,
  exchangeRate: 7.2,
};

export default function HomePage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [marketplace, setMarketplace] = useState("amazon-us");
  const [cost, setCost] = useState<CostParams>(DEFAULT_COST);
  const [showCost, setShowCost] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    try {
      const { taskId } = await createTask({ sourceUrl: url, targetMarketplace: marketplace, cost });
      router.push(`/tasks/${taskId}/progress`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Failed to create task");
    } finally {
      setLoading(false);
    }
  }

  function updateCost(key: keyof CostParams, value: string) {
    setCost((prev) => ({ ...prev, [key]: parseFloat(value) || 0 }));
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Hero */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">CrossBorder AI Copilot</h1>
        <p className="text-gray-500">
          Paste a 1688 / Alibaba product link. We'll find Amazon competitors, analyze the market, and generate a listing.
        </p>
      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border p-6 space-y-5">
        {/* URL */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Product URL</label>
          <input
            type="url"
            placeholder="https://detail.1688.com/offer/..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
            className="w-full border rounded-lg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-400 mt-1">Supports 1688, Alibaba, and Amazon links</p>
        </div>

        {/* Marketplace */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Target Marketplace</label>
          <select
            value={marketplace}
            onChange={(e) => setMarketplace(e.target.value)}
            className="border rounded-lg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="amazon-us">Amazon US</option>
            <option value="amazon-uk">Amazon UK</option>
            <option value="amazon-de">Amazon DE</option>
            <option value="amazon-jp">Amazon JP</option>
          </select>
        </div>

        {/* Cost params toggle */}
        <div>
          <button
            type="button"
            onClick={() => setShowCost(!showCost)}
            className="text-sm text-blue-600 hover:underline"
          >
            {showCost ? "Hide" : "Configure"} cost parameters ▾
          </button>

          {showCost && (
            <div className="mt-3 grid grid-cols-2 gap-3">
              {(
                [
                  ["purchasePrice", "Purchase Price (CNY)"],
                  ["domesticShipping", "Domestic Shipping (CNY)"],
                  ["internationalShipping", "Int'l Freight (USD)"],
                  ["fbaFee", "FBA Fee (USD)"],
                  ["commissionRate", "Commission Rate (e.g. 0.15)"],
                  ["adsRate", "Ads Rate (e.g. 0.08)"],
                  ["taxRate", "Tax Rate (e.g. 0.03)"],
                  ["exchangeRate", "Exchange Rate (CNY/USD)"],
                ] as [keyof CostParams, string][]
              ).map(([key, label]) => (
                <div key={key}>
                  <label className="block text-xs text-gray-500 mb-1">{label}</label>
                  <input
                    type="number"
                    step="0.01"
                    value={cost[key]}
                    onChange={(e) => updateCost(key, e.target.value)}
                    className="w-full border rounded-lg px-2.5 py-1.5 text-sm outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={loading || !url.trim()}
          className="w-full bg-blue-600 text-white rounded-lg py-3 font-medium text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {loading ? "Starting analysis..." : "Analyze Product →"}
        </button>
      </form>

      {/* Example links */}
      <div className="text-center text-xs text-gray-400 space-y-1">
        <p>Don't have a link? Try a demo:</p>
        <button
          onClick={() => setUrl("https://detail.1688.com/offer/demo")}
          className="text-blue-500 hover:underline"
        >
          Load example 1688 URL
        </button>
      </div>
    </div>
  );
}
