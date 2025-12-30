import Link from "next/link";
import Image from "next/image";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-white dark:bg-zinc-950 text-slate-900 dark:text-slate-50 font-sans">

      {/* Navigation */}
      <header className="px-8 py-6 flex justify-between items-center bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md sticky top-0 z-10 border-b border-slate-100 dark:border-zinc-800">
        <div className="font-extrabold text-2xl tracking-tighter bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">
          AI-LMS
        </div>
        <Link
          href="/login"
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-full text-sm font-semibold transition-all shadow-md hover:shadow-lg"
        >
          Login
        </Link>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center text-center px-4 sm:px-8 py-24 relative overflow-hidden">
        {/* Decorative Background Blob */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-blue-400/20 rounded-full blur-3xl -z-10 pointer-events-none" />

        <div className="max-w-4xl space-y-8 z-0">
          <h1 className="text-5xl sm:text-7xl font-black tracking-tight text-slate-900 dark:text-white pb-2">
            The Future of Learning is <span className="bg-gradient-to-r from-blue-600 via-violet-600 to-fuchsia-500 bg-clip-text text-transparent">Intelligent.</span>
          </h1>
          <p className="text-xl sm:text-2xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
            An AI-powered Learning Management System that <span className="text-blue-600 dark:text-blue-400 font-semibold">reads your slides</span> and acts as your personal tutor 24/7.
          </p>

          <div className="pt-10 flex flex-col sm:flex-row justify-center gap-5">
            <Link
              href="/login"
              className="px-10 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-lg font-bold shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300"
            >
              Get Started
            </Link>
            <Link
              href="/api/docs"
              target="_blank"
              className="px-10 py-4 bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 hover:border-blue-300 dark:hover:border-blue-700 hover:bg-blue-50 dark:hover:bg-zinc-800 rounded-xl text-lg font-semibold transition-all duration-300 shadow-sm"
            >
              API Docs
            </Link>
          </div>
        </div>
      </main>

      {/* Features Grid */}
      <section className="bg-slate-50 dark:bg-black py-24 px-8">
        <div className="max-w-6xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-10">
          <div className="p-8 rounded-2xl bg-white dark:bg-zinc-900 shadow-xl shadow-slate-200/50 dark:shadow-none hover:shadow-2xl hover:scale-105 transition-all duration-300 border border-slate-100 dark:border-zinc-800">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center mb-6 text-2xl">🤖</div>
            <h3 className="text-2xl font-bold mb-3 text-slate-900 dark:text-white">AI Tutor</h3>
            <p className="text-slate-600 dark:text-zinc-400 leading-relaxed">
              Ask questions about any lecture slide. Our RAG pipeline retrieves the exact context and explains it simply.
            </p>
          </div>
          <div className="p-8 rounded-2xl bg-white dark:bg-zinc-900 shadow-xl shadow-slate-200/50 dark:shadow-none hover:shadow-2xl hover:scale-105 transition-all duration-300 border border-slate-100 dark:border-zinc-800">
            <div className="w-12 h-12 bg-violet-100 dark:bg-violet-900/30 rounded-lg flex items-center justify-center mb-6 text-2xl">📊</div>
            <h3 className="text-2xl font-bold mb-3 text-slate-900 dark:text-white">Adaptive Quizzes</h3>
            <p className="text-slate-600 dark:text-zinc-400 leading-relaxed">
              Generate infinite practice questions tailored to your weak topics. Never run out of revision material.
            </p>
          </div>
          <div className="p-8 rounded-2xl bg-white dark:bg-zinc-900 shadow-xl shadow-slate-200/50 dark:shadow-none hover:shadow-2xl hover:scale-105 transition-all duration-300 border border-slate-100 dark:border-zinc-800">
            <div className="w-12 h-12 bg-fuchsia-100 dark:bg-fuchsia-900/30 rounded-lg flex items-center justify-center mb-6 text-2xl">📈</div>
            <h3 className="text-2xl font-bold mb-3 text-slate-900 dark:text-white">Analytics</h3>
            <p className="text-slate-600 dark:text-zinc-400 leading-relaxed">
              Track your mastery over time. Visualize your progress and identify gaps before the exam.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 text-center text-slate-500 dark:text-slate-500 text-sm border-t border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
        <p>&copy; 2025 AI-Powered LMS. Final Year Project.</p>
      </footer>
    </div>
  );
}
