import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Home",
  description: "Welcome to our application",
};

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero Section */}
      <section className="flex-1 flex flex-col items-center justify-center py-20 px-6 text-center bg-gradient-to-b from-white to-zinc-50 dark:from-black dark:to-zinc-900">
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-black dark:text-white mb-6">
          Welcome to Our App
        </h1>
        <p className="text-lg sm:text-xl text-zinc-600 dark:text-zinc-400 max-w-2xl mb-10">
          A modern web application built with Next.js, React, and Tailwind CSS
        </p>
        <div className="flex gap-4">
          <a
            href="/about"
            className="px-6 py-3 bg-black text-white dark:bg-white dark:text-black rounded-lg font-medium hover:opacity-80 transition-opacity"
          >
            Learn More
          </a>
          <a
            href="#features"
            className="px-6 py-3 border border-zinc-300 dark:border-zinc-700 rounded-lg font-medium hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          >
            Features
          </a>
          <a
            href="/cvdMatcher"
            className="px-6 py-3 bg-black text-white dark:bg-white dark:text-black rounded-lg font-medium hover:opacity-80 transition-opacity"
          >
            CVD Matcher
          </a>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-6 bg-white dark:bg-zinc-950">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-semibold text-center text-black dark:text-white mb-12">
            Features
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
            <div className="p-6 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <h3 className="text-lg font-semibold text-black dark:text-white mb-2">
                Fast Performance
              </h3>
              <p className="text-zinc-600 dark:text-zinc-400">
                Built with Next.js for optimal speed and performance
              </p>
            </div>
            <div className="p-6 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <h3 className="text-lg font-semibold text-black dark:text-white mb-2">
                Responsive Design
              </h3>
              <p className="text-zinc-600 dark:text-zinc-400">
                Looks great on all devices with Tailwind CSS
              </p>
            </div>
            <div className="p-6 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <h3 className="text-lg font-semibold text-black dark:text-white mb-2">
                TypeScript
              </h3>
              <p className="text-zinc-600 dark:text-zinc-400">
                Type-safe code with full TypeScript support
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
