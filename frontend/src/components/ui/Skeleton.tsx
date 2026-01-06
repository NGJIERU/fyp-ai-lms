"use client";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = "" }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 bg-[length:200%_100%] rounded ${className}`}
    />
  );
}

export function RecommendationCardSkeleton() {
  return (
    <div className="rounded-xl border-2 border-gray-100 p-4 bg-white">
      <div className="flex items-start gap-3">
        {/* Icon placeholder */}
        <Skeleton className="w-10 h-10 rounded-lg" />
        
        {/* Content */}
        <div className="flex-1 space-y-3">
          {/* Title and badge row */}
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <div className="flex items-center gap-2">
                <Skeleton className="h-5 w-16 rounded-full" />
                <Skeleton className="h-3 w-12" />
              </div>
            </div>
            <Skeleton className="h-8 w-16 rounded-lg" />
          </div>
          
          {/* Topic */}
          <Skeleton className="h-3 w-1/2" />
          
          {/* Reasons box */}
          <div className="p-2 rounded-lg bg-gray-50">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-2/3 mt-1" />
          </div>
          
          {/* Actions */}
          <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
            <Skeleton className="h-8 w-20 rounded-lg" />
            <Skeleton className="h-8 w-24 rounded-lg" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function BundleCardSkeleton() {
  return (
    <div className="rounded-xl border-2 border-gray-100 bg-white overflow-hidden">
      {/* Header */}
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Skeleton className="w-10 h-10 rounded-xl" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-40" />
            <div className="flex items-center gap-2">
              <Skeleton className="h-3 w-8" />
              <Skeleton className="h-3 w-8" />
              <Skeleton className="h-3 w-16" />
            </div>
          </div>
        </div>
        <Skeleton className="w-5 h-5 rounded" />
      </div>
      
      {/* Content */}
      <div className="px-4 pb-4 space-y-3">
        {/* Summary */}
        <div className="p-3 rounded-lg bg-gray-50">
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-3/4 mt-1" />
        </div>
        
        {/* Materials */}
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-3 p-3 rounded-lg border border-gray-100">
              <Skeleton className="w-8 h-8 rounded-md" />
              <div className="flex-1 space-y-1">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-16 rounded" />
              </div>
              <Skeleton className="w-4 h-4" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function SmartFeedSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      {/* Targeted Practice Section */}
      <section className="rounded-2xl bg-white p-6 shadow-sm">
        <header className="flex flex-col gap-1 mb-5">
          <Skeleton className="h-3 w-24" />
          <div className="flex items-center gap-2">
            <Skeleton className="w-6 h-6 rounded" />
            <Skeleton className="h-5 w-32" />
          </div>
          <Skeleton className="h-3 w-64 mt-1" />
        </header>
        
        <div className="space-y-4">
          <RecommendationCardSkeleton />
          <RecommendationCardSkeleton />
        </div>
      </section>
      
      {/* Weekly Review Kits Section */}
      <section className="rounded-2xl bg-white p-6 shadow-sm">
        <header className="flex flex-col gap-1 mb-5">
          <Skeleton className="h-3 w-20" />
          <div className="flex items-center gap-2">
            <Skeleton className="w-6 h-6 rounded" />
            <Skeleton className="h-5 w-36" />
          </div>
          <Skeleton className="h-3 w-72 mt-1" />
        </header>
        
        <div className="space-y-4">
          <BundleCardSkeleton />
          <BundleCardSkeleton />
        </div>
      </section>
    </div>
  );
}
