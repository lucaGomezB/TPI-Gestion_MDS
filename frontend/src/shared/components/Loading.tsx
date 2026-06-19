import type { ReactNode } from 'react';

interface LoadingProps {
  message?: string;
  fullPage?: boolean;
  skeleton?: boolean;
}

function SkeletonInner() {
  return (
    <div className="space-y-4 animate-pulse" data-testid="skeleton-rows">
      <div className="h-4 bg-[#64748B]/10 rounded w-3/4" />
      <div className="h-4 bg-[#64748B]/10 rounded w-1/2" />
      <div className="h-4 bg-[#64748B]/10 rounded w-5/6" />
      <div className="h-4 bg-[#64748B]/10 rounded w-2/3" />
    </div>
  );
}

function LoadingIndicator({ message }: { message?: string }) {
  return (
    <>
      <div className="w-10 h-10 border-4 border-[#64748B]/20 border-t-[#0F172A] rounded-full animate-spin" />
      {message && <p className="text-sm text-gray-500">{message}</p>}
    </>
  );
}

function Loading({ message, fullPage = false, skeleton = false }: LoadingProps): ReactNode {
  if (skeleton) {
    if (fullPage) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-gray-50 p-8" role="status">
          <SkeletonInner />
        </div>
      );
    }
    return (
      <div className="p-4" role="status">
        <SkeletonInner />
      </div>
    );
  }

  if (fullPage) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 space-y-4" role="status">
        <LoadingIndicator message={message} />
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center space-y-4 p-4" role="status">
      <LoadingIndicator message={message} />
    </div>
  );
}

export default Loading;
