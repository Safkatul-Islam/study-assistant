import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center">
      <div className="text-center space-y-6">
        <h1 className="text-5xl font-bold tracking-tight">StudyForge</h1>
        <p className="text-xl text-gray-600 max-w-md">
          Turn any PDF into a structured learning experience with AI-powered
          summaries, Q&amp;A, and flashcards.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/login"
            className="px-6 py-3 bg-black text-white rounded-lg font-medium hover:bg-gray-800 transition-colors"
          >
            Get Started
          </Link>
        </div>
      </div>
    </main>
  );
}
