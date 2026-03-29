"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const FEATURES = [
  {
    title: "AI Summaries",
    description:
      "Get structured summaries with key concepts, definitions, and study questions — instantly.",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
        className="size-8"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
        />
      </svg>
    ),
  },
  {
    title: "Smart Q&A",
    description:
      "Ask anything about your documents. Get accurate answers with source citations.",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
        className="size-8"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z"
        />
      </svg>
    ),
  },
  {
    title: "Flashcards",
    description:
      "Auto-generated flashcards with spaced repetition to lock knowledge into long-term memory.",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
        className="size-8"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3"
        />
      </svg>
    ),
  },
] as const;

const STEPS = [
  {
    number: 1,
    title: "Upload",
    description: "Drop your PDF and we handle the rest",
  },
  {
    number: 2,
    title: "AI Processes",
    description: "We extract, chunk, and embed your content",
  },
  {
    number: 3,
    title: "Study",
    description: "Summaries, Q&A, and flashcards ready to go",
  },
] as const;

const STATS = [
  { value: 10000, label: "Documents", prefix: "", suffix: "+" },
  { value: 500000, label: "Questions Answered", prefix: "", suffix: "+" },
  { value: 1000000, label: "Flashcards Generated", prefix: "", suffix: "+" },
] as const;

function formatStatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(0)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0).replace(/\.0$/, "")}K`;
  return n.toLocaleString();
}

export default function Home() {
  const heroRef = useRef<HTMLElement>(null);
  const featuresRef = useRef<HTMLElement>(null);
  const howItWorksRef = useRef<HTMLElement>(null);
  const statsRef = useRef<HTMLElement>(null);
  const ctaRef = useRef<HTMLElement>(null);
  const statNumberRefs = useRef<(HTMLSpanElement | null)[]>([]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Hero: fade-in on load
      gsap.from("[data-hero-content]", {
        opacity: 0,
        y: 40,
        duration: 1,
        ease: "power3.out",
      });

      gsap.from("[data-hero-blob]", {
        opacity: 0,
        scale: 0.8,
        duration: 1.4,
        ease: "power2.out",
      });

      // Feature cards: staggered fade-up on scroll
      gsap.from("[data-feature-card]", {
        scrollTrigger: {
          trigger: featuresRef.current,
          start: "top 80%",
          toggleActions: "play none none none",
        },
        opacity: 0,
        y: 60,
        duration: 0.7,
        stagger: 0.15,
        ease: "power3.out",
      });

      // How it works steps: staggered fade-up on scroll
      gsap.from("[data-step]", {
        scrollTrigger: {
          trigger: howItWorksRef.current,
          start: "top 80%",
          toggleActions: "play none none none",
        },
        opacity: 0,
        y: 50,
        duration: 0.7,
        stagger: 0.2,
        ease: "power3.out",
      });

      // Stats: counter animation on scroll
      STATS.forEach((stat, i) => {
        const obj = { val: 0 };
        gsap.to(obj, {
          val: stat.value,
          duration: 2,
          ease: "power1.out",
          snap: { val: stat.value >= 1_000_000 ? 10000 : stat.value >= 100_000 ? 1000 : 100 },
          scrollTrigger: {
            trigger: statsRef.current,
            start: "top 80%",
            toggleActions: "play none none none",
          },
          onUpdate() {
            const el = statNumberRefs.current[i];
            if (el) {
              el.textContent = formatStatNumber(obj.val);
            }
          },
        });
      });

      // Final CTA: fade-up on scroll
      gsap.from("[data-cta-content]", {
        scrollTrigger: {
          trigger: ctaRef.current,
          start: "top 85%",
          toggleActions: "play none none none",
        },
        opacity: 0,
        y: 50,
        duration: 0.8,
        ease: "power3.out",
      });
    });

    return () => ctx.revert();
  }, []);

  return (
    <div className="min-h-screen bg-white text-gray-900 dark:bg-gray-950 dark:text-gray-100">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-gray-200/60 bg-white/80 backdrop-blur-md dark:border-gray-800/60 dark:bg-gray-950/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/" className="text-xl font-bold tracking-tight">
            StudyForge
          </Link>
          <Link
            href="/login"
            className="text-sm font-medium text-gray-600 transition-colors hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
          >
            Log in
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section
        ref={heroRef}
        className="relative flex min-h-screen items-center justify-center overflow-hidden px-6 pt-20"
      >
        <div
          data-hero-blob
          className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full bg-gradient-to-br from-purple-400/30 via-blue-400/20 to-indigo-400/30 blur-3xl dark:from-purple-600/20 dark:via-blue-600/15 dark:to-indigo-600/20"
        />
        <div
          data-hero-content
          className="relative z-10 mx-auto max-w-3xl text-center"
        >
          <h1 className="text-5xl font-bold leading-tight tracking-tight sm:text-6xl lg:text-7xl">
            Turn PDFs into Learning Superpowers
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-gray-600 dark:text-gray-400 sm:text-xl">
            Upload any document and let AI create summaries, answer questions,
            and generate flashcards — so you study smarter, not harder.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/register"
              className="rounded-lg bg-gray-900 px-8 py-3.5 text-sm font-semibold text-white shadow-lg transition-all hover:bg-gray-800 hover:shadow-xl dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100"
            >
              Get Started Free
            </Link>
            <Link
              href="#how-it-works"
              className="rounded-lg border border-gray-300 px-8 py-3.5 text-sm font-semibold transition-all hover:border-gray-400 hover:bg-gray-50 dark:border-gray-700 dark:hover:border-gray-600 dark:hover:bg-gray-900"
            >
              See How It Works
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section
        ref={featuresRef}
        id="features"
        className="mx-auto max-w-6xl px-6 py-24 lg:py-32"
      >
        <h2 className="text-center text-3xl font-bold tracking-tight sm:text-4xl">
          Everything You Need to Study Smarter
        </h2>
        <div className="mt-16 grid gap-8 md:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              data-feature-card
              className="rounded-2xl border border-gray-200 bg-white p-8 transition-shadow hover:shadow-lg dark:border-gray-800 dark:bg-gray-900"
            >
              <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-xl bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                {feature.icon}
              </div>
              <h3 className="text-lg font-semibold">{feature.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-gray-600 dark:text-gray-400">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section
        ref={howItWorksRef}
        id="how-it-works"
        className="border-y border-gray-200 bg-gray-50 px-6 py-24 dark:border-gray-800 dark:bg-gray-900/50 lg:py-32"
      >
        <div className="mx-auto max-w-6xl">
          <h2 className="text-center text-3xl font-bold tracking-tight sm:text-4xl">
            Three Steps to Better Studying
          </h2>
          <div className="relative mt-16 grid gap-12 md:grid-cols-3 md:gap-8">
            {/* Connecting line (desktop only) */}
            <div className="pointer-events-none absolute left-0 right-0 top-10 hidden h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent dark:via-gray-700 md:block" />
            {STEPS.map((step) => (
              <div
                key={step.number}
                data-step
                className="relative flex flex-col items-center text-center"
              >
                <div className="relative z-10 flex h-20 w-20 items-center justify-center rounded-full border-2 border-gray-900 bg-white text-2xl font-bold dark:border-gray-100 dark:bg-gray-950">
                  {step.number}
                </div>
                <h3 className="mt-6 text-lg font-semibold">{step.title}</h3>
                <p className="mt-2 max-w-xs text-sm text-gray-600 dark:text-gray-400">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section
        ref={statsRef}
        className="mx-auto max-w-6xl px-6 py-24 lg:py-32"
      >
        <h2 className="text-center text-3xl font-bold tracking-tight sm:text-4xl">
          Trusted by Students Worldwide
        </h2>
        <div className="mt-16 grid gap-8 text-center sm:grid-cols-3">
          {STATS.map((stat, i) => (
            <div key={stat.label}>
              <span
                ref={(el) => {
                  statNumberRefs.current[i] = el;
                }}
                className="text-4xl font-bold tracking-tight sm:text-5xl"
              >
                0
              </span>
              <span className="text-4xl font-bold tracking-tight sm:text-5xl">
                {stat.suffix}
              </span>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {stat.label}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section
        ref={ctaRef}
        className="relative overflow-hidden px-6 py-24 lg:py-32"
      >
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 dark:from-purple-950/30 dark:via-blue-950/20 dark:to-indigo-950/30" />
        <div
          data-cta-content
          className="relative z-10 mx-auto max-w-2xl text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Ready to Transform Your Study Routine?
          </h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
            Join thousands of students studying smarter with AI.
          </p>
          <Link
            href="/register"
            className="mt-8 inline-block rounded-lg bg-gray-900 px-8 py-3.5 text-sm font-semibold text-white shadow-lg transition-all hover:bg-gray-800 hover:shadow-xl dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100"
          >
            Get Started Free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 px-6 py-8 dark:border-gray-800">
        <p className="text-center text-sm text-gray-500 dark:text-gray-500">
          &copy; 2026 StudyForge. Built with AI.
        </p>
      </footer>
    </div>
  );
}
