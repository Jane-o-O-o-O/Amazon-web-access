"use client";
import { useState } from "react";
import type { ListingDraft } from "@/types";
import { regenerateListing } from "@/lib/api";
import { toast } from "sonner";

interface Props {
  listing: ListingDraft;
  taskId: string;
  productId?: string;
  productSpecs?: object;
  competitorInsights?: object;
  onUpdate?: (listing: ListingDraft) => void;
}

export function ListingEditor({ listing: initialListing, taskId, productId, productSpecs, competitorInsights, onUpdate }: Props) {
  const [listing, setListing] = useState(initialListing);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  async function handleRegenerate() {
    setLoading(true);
    try {
      const result = await regenerateListing({
        productId: productId ?? taskId,
        productSpecs: productSpecs ?? {},
        competitorInsights: competitorInsights ?? {},
      });
      setListing(result.listing);
      onUpdate?.(result.listing);
      toast.success("Listing regenerated!");
    } catch {
      toast.error("Failed to regenerate listing.");
    } finally {
      setLoading(false);
    }
  }

  function copy(text: string, key: string) {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 1500);
  }

  return (
    <div className="rounded-xl border bg-white p-5 space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">Amazon Listing Draft</h3>
        <button
          onClick={handleRegenerate}
          disabled={loading}
          className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Regenerating..." : "Regenerate"}
        </button>
      </div>

      {/* Title */}
      <Section label="Title" onCopy={() => copy(listing.title, "title")} copied={copied === "title"}>
        <p className="text-sm text-gray-800 leading-relaxed">{listing.title}</p>
      </Section>

      {/* Bullet Points */}
      <Section label="Bullet Points (5)" onCopy={() => copy(listing.bullets.join("\n"), "bullets")} copied={copied === "bullets"}>
        <ul className="space-y-2">
          {listing.bullets.map((b, i) => (
            <li key={i} className="flex gap-2 text-sm text-gray-800">
              <span className="text-blue-400 font-bold shrink-0">{i + 1}.</span>
              <span>{b}</span>
            </li>
          ))}
        </ul>
      </Section>

      {/* Description */}
      <Section label="Description" onCopy={() => copy(listing.description, "desc")} copied={copied === "desc"}>
        <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{listing.description}</p>
      </Section>

      {/* Search Terms */}
      <Section label="Search Terms" onCopy={() => copy(listing.search_terms, "st")} copied={copied === "st"}>
        <p className="text-sm text-gray-700 font-mono break-all">{listing.search_terms}</p>
      </Section>

      {/* Image copy suggestions */}
      {listing.image_copy_suggestions && listing.image_copy_suggestions.length > 0 && (
        <Section label="Image Copy Suggestions">
          {listing.image_copy_suggestions.map((s) => (
            <div key={s.image_number} className="text-sm text-gray-700">
              <span className="font-medium text-gray-500">Image {s.image_number}: </span>
              {s.copy}
            </div>
          ))}
        </Section>
      )}
    </div>
  );
}

function Section({
  label,
  children,
  onCopy,
  copied,
}: {
  label: string;
  children: React.ReactNode;
  onCopy?: () => void;
  copied?: boolean;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{label}</p>
        {onCopy && (
          <button onClick={onCopy} className="text-xs text-gray-400 hover:text-gray-700">
            {copied ? "Copied!" : "Copy"}
          </button>
        )}
      </div>
      <div className="bg-gray-50 rounded-lg p-3">{children}</div>
    </div>
  );
}
