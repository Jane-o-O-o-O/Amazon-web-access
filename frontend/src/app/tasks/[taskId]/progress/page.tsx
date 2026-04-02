import { TaskProgress } from "@/components/TaskProgress";

export default function ProgressPage({ params }: { params: { taskId: string } }) {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Analyzing Product</h1>
        <p className="text-sm text-gray-500 mt-1">Task ID: {params.taskId}</p>
      </div>
      <TaskProgress taskId={params.taskId} />
    </div>
  );
}
