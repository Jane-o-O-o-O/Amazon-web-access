import type { Product } from "@/types";
import { formatUSD } from "@/lib/utils";

interface Props {
  product: Product;
  label?: string;
}

export function ProductCard({ product, label = "Product" }: Props) {
  const price = product.price_min ?? product.price;
  const image = product.images?.[0];

  return (
    <div className="rounded-xl border bg-white p-5 space-y-3">
      <div className="flex items-start gap-4">
        {image && (
          <img
            src={image}
            alt={product.title ?? "Product image"}
            className="w-20 h-20 object-cover rounded-lg border"
            onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
          />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-gray-100 text-gray-600">
              {label}
            </span>
            {product.platform && (
              <span className="text-xs text-gray-400">{product.platform}</span>
            )}
          </div>
          <h3 className="font-medium text-gray-900 text-sm leading-snug line-clamp-2">
            {product.title ?? "Unknown product"}
          </h3>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        {price != null && (
          <div>
            <span className="text-gray-500 text-xs">Price</span>
            <p className="font-semibold text-gray-900">
              {formatUSD(price)}
              {product.price_max && product.price_max !== price && ` – ${formatUSD(product.price_max)}`}
            </p>
          </div>
        )}
        {product.rating != null && (
          <div>
            <span className="text-gray-500 text-xs">Rating</span>
            <p className="font-semibold text-gray-900">
              ★ {product.rating.toFixed(1)}
              {product.review_count != null && (
                <span className="text-gray-400 font-normal"> ({product.review_count.toLocaleString()})</span>
              )}
            </p>
          </div>
        )}
        {product.moq != null && (
          <div>
            <span className="text-gray-500 text-xs">MOQ</span>
            <p className="font-medium text-gray-800">{product.moq} pcs</p>
          </div>
        )}
        {product.material && (
          <div>
            <span className="text-gray-500 text-xs">Material</span>
            <p className="font-medium text-gray-800 truncate">{product.material}</p>
          </div>
        )}
      </div>

      {product.source_url && (
        <a
          href={product.source_url ?? product.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-blue-500 hover:underline"
        >
          View source →
        </a>
      )}
    </div>
  );
}
