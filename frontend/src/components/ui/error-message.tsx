interface ErrorMessageProps {
  message: string;
}

export function ErrorMessage({ message }: ErrorMessageProps) {
  return (
    <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950 p-4">
      <p className="text-sm text-red-700 dark:text-red-400">{message}</p>
    </div>
  );
}
