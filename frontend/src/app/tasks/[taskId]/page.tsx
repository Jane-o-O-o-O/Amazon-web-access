"use client";
import { useQuery } from "@tanstack/react-query";
import { getTaskResult } from "@/lib/api";
import { getExportCsvUrl, getExportJsonUrl } from "@/lib/api";
import { ProductCard } from "@/components/ProductCard";
import { MatchResults } from "@/components/MatchResults";
import { ProfitCalculator } from "@/components/ProfitCalculator";
import { ListingEditor } from "@/components/ListingEditor";
import type { TaskResult } from "@/types";

export default function TaskResultPage({ params }: { params: { taskId: string } }) {
  const { taskId } = params;
  const { data, isLoading, error } = useQuery<TaskResult>({
    queryKey: ["taskResult", taskId],
    queryFn: () => getTaskResult(taskId),
  });

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-48" />
          <div className="h-40 bg-gray-200 rounded" />
          <div className="h-40 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-5xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
          Failed to load results. The task may still be processing.{" "}
          <a href={`/tasks/${taskId}/progress`} className="underline">Check progress →</a>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Analysis Results</h1>
          <p className="text-xs text-gray-400 mt-0.5">Task: {taskId}</p>
        </div>
        <div className="flex gap-2">
          <a
            href={getExportCsvUrl(taskId)}
            className="text-sm border rounded-lg px-3 py-2 text-gray-600 hover:bg-gray-50"
          >
            Export CSV
          </a>
          <a
            href={getExportJsonUrl(taskId)}
            className="text-sm border rounded-lg px-3 py-2 text-gray-600 hover:bg-gray-50"
          >
            Export JSON
          </a>
        </div>
      </div>

      {/* Source product */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Source Product</h2>
        <ProductCard product={data.source_product} label={data.source_product.platform ?? "Source"} />
      </section>

      {/* Competitor analysis summary */}
      {data.competitor_analysis && (
        <section>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Market Analysis</h2>
          <div className="rounded-xl border bg-white p-5 space-y-4">
            <p className="text-sm text-gray-700 leading-relaxed">{data.competitor_analysis.market_summary}</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.competitor_analysis.top_features?.length > 0 && (
                <TagGroup label="Top Features" tags={data.competitor_analysis.top_features} color="blue" />
              )}
              {data.competitor_analysis.complaint_topics?.length > 0 && (
                <TagGroup label="Common Complaints" tags={data.competitor_analysis.complaint_topics} color="red" />
              )}
              {data.competitor_analysis.keyword_themes?.length > 0 && (
                <TagGroup label="Key Keywords" tags={data.competitor_analysis.keyword_themes} color="purple" />
              )}
              {data.competitor_analysis.differentiation_suggestions?.length > 0 && (
                <TagGroup label="Differentiation Opportunities" tags={data.competitor_analysis.differentiation_suggestions} color="green" />
              )}
            </div>

            {data.competitor_analysis.market_opportunity && (
              <div className="bg-green-50 rounded-lg p-3 text-sm text-green-800">
                <span className="font-semibold">Opportunity: </span>
                {data.competitor_analysis.market_opportunity}
              </div>
            )}

            {data.competitor_analysis.risk_warnings?.length > 0 && (
              <div className="bg-yellow-50 rounded-lg p-3 text-sm text-yellow-800">
                <span className="font-semibold">Risks: </span>
                {data.competitor_analysis.risk_warnings.join(" · ")}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Two column: matches + profit */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Amazon Candidates ({data.candidates.length})
          </h2>
          <MatchResults matches={data.candidates} />
        </section>

        <section>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Profit Analysis</h2>
          <ProfitCalculator margin={data.margin} />
        </section>
      </div>

      {/* Listing editor */}
      {data.listing && (
        <section>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Generated Listing</h2>
          <ListingEditor
            listing={data.listing}
            taskId={taskId}
            productSpecs={data.source_product}
            competitorInsights={data.competitor_analysis}
          />
        </section>
      )}
    </div>
  );
}

function TagGroup({
  label,
  tags,
  color,
}: {
  label: string;
  tags: string[];
  color: "blue" | "red" | "green" | "purple";
}) {
  const cls = {
    blue:   "bg-blue-50 text-blue-700",
    red:    "bg-red-50 text-red-700",
    green:  "bg-green-50 text-green-700",
    purple: "bg-purple-50 text-purple-700",
  }[color];

  return (
    <div>
      <p className="text-xs font-medium text-gray-500 mb-1.5">{label}</p>
      <div className="flex flex-wrap gap-1.5">
        {tags.slice(0, 8).map((t) => (
          <span key={t} className={`text-xs px-2 py-0.5 rounded-full font-medium ${cls}`}>
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}
