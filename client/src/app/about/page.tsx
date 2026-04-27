import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About Us",
  description: "Learn more about us",
};

export default function AboutPage() {
  return (
    <div className="min-h-screen flex flex-col py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-black dark:text-white mb-6">
          About Us
        </h1>
        <p className="text-lg text-zinc-600 dark:text-zinc-400 mb-8">
          We are a team dedicated to building modern web applications with the latest technologies.
        </p>
        <div className="p-6 rounded-lg border border-zinc-200 dark:border-zinc-800">
          <h2 className="text-2xl font-semibold text-black dark:text-white mb-4">
            Our Mission
          </h2>
          <p className="text-zinc-600 dark:text-zinc-400">
            To create fast, responsive, and user-friendly web applications using cutting-edge technologies.
          </p>
        </div>
        <a
          href="/"
          className="inline-block mt-8 px-6 py-3 bg-black text-white dark:bg-white dark:text-black rounded-lg font-medium hover:opacity-80 transition-opacity"
        >
          Back to Home
        </a>
      </div>
    </div>
  );
}