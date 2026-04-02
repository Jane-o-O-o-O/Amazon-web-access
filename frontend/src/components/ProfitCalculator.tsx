import type { MarginResult } from "@/types";
import { formatUSD, formatPercent } from "@/lib/utils";

interface Props {
  margin: MarginResult;
}

export function ProfitCalculator({ margin }: Props) {
  const netMarginPct = margin.net_margin;
  const color =
    netMarginPct >= 0.25 ? "text-green-600" :
    netMarginPct >= 0.10 ? "text-yellow-600" :
                           "text-red-600";

  return (
    <div className="rounded-xl border bg-white p-5 space-y-4">
      <h3 className="font-semibold text-gray-900">Profit Calculator</h3>

      {/* Hero metrics */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-xs text-gray-500 mb-1">Sell Price</p>
          <p className="font-bold text-gray-900">{formatUSD(margin.sell_price)}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-xs text-gray-500 mb-1">Net Profit</p>
          <p className={`font-bold ${color}`}>{formatUSD(margin.net_profit)}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-xs text-gray-500 mb-1">Net Margin</p>
          <p className={`font-bold ${color}`}>{formatPercent(margin.net_margin)}</p>
        </div>
      </div>

      {/* Suggested price */}
      <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 text-sm">
        <span className="text-blue-600 font-medium">Suggested price range: </span>
        <span className="text-blue-900 font-bold">
          {formatUSD(margin.suggested_price_min)} – {formatUSD(margin.suggested_price_max)}
        </span>
        <span className="text-blue-500 text-xs ml-1">(for ~30% net margin)</span>
      </div>

      {/* Cost breakdown */}
      <div className="space-y-1.5 text-sm">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Cost Breakdown</p>
        {[
          ["Purchase cost", margin.purchase_usd],
          ["Domestic shipping", margin.domestic_shipping_usd],
          ["International freight", margin.international_shipping],
          ["FBA fee", margin.fba_fee],
          ["Amazon commission", margin.commission],
          ["Advertising", margin.ads_cost],
          ["Tax", margin.tax],
        ].map(([label, val]) => (
          <div key={label as string} className="flex justify-between text-gray-600">
            <span>{label}</span>
            <span className="font-medium">{formatUSD(val as number)}</span>
          </div>
        ))}
        <div className="border-t pt-1.5 flex justify-between font-semibold text-gray-800">
          <span>Total Cost</span>
          <span>{formatUSD(margin.total_cost)}</span>
        </div>
      </div>
    </div>
  );
}
