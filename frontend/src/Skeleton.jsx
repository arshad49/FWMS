export function CardSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
      <div className="flex items-center gap-4 mb-4">
        <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-3 bg-gray-100 rounded w-1/2"></div>
        </div>
      </div>
      <div className="space-y-2">
        <div className="h-3 bg-gray-100 rounded"></div>
        <div className="h-3 bg-gray-100 rounded w-5/6"></div>
      </div>
    </div>
  );
}

export function TableSkeleton({ rows = 5 }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="p-4 border-b border-gray-100 flex gap-4">
        {[1, 2, 3, 4].map(i => <div key={i} className="h-3 bg-gray-200 rounded flex-1 animate-pulse"></div>)}
      </div>
      {[...Array(rows)].map((_, i) => (
        <div key={i} className="p-4 border-b border-gray-50 flex gap-4 animate-pulse">
          <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="h-3 bg-gray-100 rounded w-1/2"></div>
          </div>
        </div>
      ))}
    </div>
  );
}