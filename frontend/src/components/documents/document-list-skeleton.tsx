import { Skeleton } from "@/components/ui/skeleton";

export function DocumentListSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="rounded-xl border border-gray-200 bg-white p-5">
          <div className="flex items-start justify-between">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-5 w-16" />
          </div>
          <div className="mt-3 flex gap-3">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-20" />
          </div>
        </div>
      ))}
    </div>
  );
}
