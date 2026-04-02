import type { MatchResult } from "@/types";
import { matchLevelColor, matchLevelLabel, formatUSD } from "@/lib/utils";

interface Props {
  matches: MatchResult[];
}

export function MatchResults({ matches }: Props) {
  if (!matches.length) {
    return (
      <div className="rounded-xl border bg-white p-6 text-center text-gray-500 text-sm">
        No Amazon candidates found.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {matches.map((m, i) => {
        const c = m.candidate;
        return (
          <div key={i} className="rounded-xl border bg-white p-4">
            <div className="flex items-start gap-3">
              {/* Score badge */}
              <div className="flex flex-col items-center min-w-[56px]">
                <span className="text-2xl font-bold text-gray-900">{m.match_score}</span>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${matchLevelColor(m.match_level)}`}>
                  {matchLevelLabel(m.match_level)}
                </span>
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 line-clamp-2 mb-1">
                  {c.title ?? "—"}
                </p>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                  {c.price != null && <span className="font-semibold text-gray-800">{formatUSD(c.price)}</span>}
                  {c.rating != null && <span>★ {c.rating?.toFixed(1)}</span>}
                  {c.review_count != null && <span>{c.review_count?.toLocaleString()} reviews</span>}
                  {c.url && (
                    <a href={c.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                      Amazon →
                    </a>
                  )}
                </div>

                {/* Score breakdown */}
                <div className="mt-2 grid grid-cols-3 gap-1">
                  {[
                    ["Title", m.title_similarity],
                    ["Attrs", m.attribute_overlap],
                    ["Category", m.category_match],
                  ].map(([label, val]) => val != null && (
                    <div key={label as string} className="text-xs">
                      <span className="text-gray-400">{label}: </span>
                      <span className="font-medium">{val as number}</span>
                    </div>
                  ))}
                </div>

                {m.final_reason && (
                  <p className="mt-2 text-xs text-gray-500 line-clamp-2">{m.final_reason}</p>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
