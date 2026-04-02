"use client";
import { useState } from "react";

export default function BatchPage() {
  const [tasks, setTasks] = useState<Array<{ id: string; url: string; status: string }>>([]);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Batch Analysis</h1>
        <p className="text-gray-500 text-sm mt-1">Upload a CSV/Excel file with product URLs for bulk processing.</p>
      </div>

      {/* Upload area */}
      <div className="bg-white rounded-2xl border-2 border-dashed border-gray-200 p-12 text-center hover:border-blue-300 transition-colors">
        <div className="space-y-3">
          <div className="text-4xl">📦</div>
          <h3 className="font-medium text-gray-700">Drop your file here</h3>
          <p className="text-sm text-gray-400">CSV or Excel with a &quot;url&quot; column</p>
          <label className="inline-block cursor-pointer bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700">
            Browse file
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              className="hidden"
              onChange={(e) => {
                // MVP: just show placeholder
                const file = e.target.files?.[0];
                if (file) {
                  alert(`File selected: ${file.name}\n\nBatch processing will be available in the next release.`);
                }
              }}
            />
          </label>
        </div>
      </div>

      {/* Template download */}
      <div className="bg-gray-50 rounded-xl border p-4 text-sm text-gray-600 flex items-center justify-between">
        <span>Need a template?</span>
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            const csv = "url,purchase_price_cny,notes\nhttps://detail.1688.com/offer/xxx,5.0,sample product\n";
            const blob = new Blob([csv], { type: "text/csv" });
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = "batch_template.csv";
            a.click();
          }}
          className="text-blue-600 hover:underline font-medium"
        >
          Download CSV template →
        </a>
      </div>

      {/* Task list placeholder */}
      {tasks.length === 0 ? (
        <div className="rounded-xl border bg-white p-8 text-center text-gray-400 text-sm">
          No batch tasks yet. Upload a file to get started.
        </div>
      ) : (
        <div className="rounded-xl border bg-white overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="px-4 py-3 text-left">URL</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {tasks.map((t) => (
                <tr key={t.id}>
                  <td className="px-4 py-3 truncate max-w-xs">{t.url}</td>
                  <td className="px-4 py-3">{t.status}</td>
                  <td className="px-4 py-3">
                    <a href={`/tasks/${t.id}`} className="text-blue-500 hover:underline">View →</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
