"use client";
import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { getTaskStatus } from "@/lib/api";
import { stageLabel } from "@/lib/utils";
import type { TaskProgress as TTaskProgress } from "@/types";

interface Props {
  taskId: string;
}

export function TaskProgress({ taskId }: Props) {
  const router = useRouter();

  const { data } = useQuery<TTaskProgress>({
    queryKey: ["task", taskId],
    queryFn: () => getTaskStatus(taskId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "done" || status === "failed") return false;
      return 2000;
    },
  });

  useEffect(() => {
    if (data?.status === "done") {
      router.push(`/tasks/${taskId}`);
    }
  }, [data?.status, taskId, router]);

  if (!data) {
    return (
      <div className="rounded-xl border bg-white p-8 text-center text-gray-500">
        Loading task status...
      </div>
    );
  }

  const { status, progress, stage, error } = data;

  return (
    <div className="rounded-xl border bg-white p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-800">Analyzing Product</h2>
        <span className={`text-sm font-medium px-3 py-1 rounded-full ${
          status === "failed" ? "bg-red-50 text-red-600" :
          status === "done"   ? "bg-green-50 text-green-600" :
                                "bg-blue-50 text-blue-600"
        }`}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
      </div>

      {/* Progress bar */}
      <div>
        <div className="flex justify-between text-sm text-gray-500 mb-2">
          <span>{stageLabel(stage)}</span>
          <span>{progress}%</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Pipeline steps */}
      <div className="grid grid-cols-4 gap-2 text-xs text-center">
        {["crawling", "matching", "analyzing", "generating"].map((s, i) => {
          const stages = ["crawling", "parsing", "searching", "matching", "analyzing", "pricing", "generating", "done"];
          const currentIdx = stages.indexOf(stage);
          const stepIdx = stages.indexOf(s);
          const done = currentIdx > stepIdx;
          const active = currentIdx === stepIdx;
          return (
            <div key={s} className={`py-2 px-1 rounded-lg border ${
              done   ? "bg-green-50 border-green-200 text-green-700" :
              active ? "bg-blue-50 border-blue-200 text-blue-700" :
                       "bg-gray-50 border-gray-200 text-gray-400"
            }`}>
              {done ? "✓ " : active ? "● " : ""}{stageLabel(s).replace("...", "")}
            </div>
          );
        })}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
}
