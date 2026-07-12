import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: LandingPage,
})

function LandingPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center px-6 text-center">
      <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
        BamiTools
      </h1>
      <p className="mt-4 text-lg text-gray-600">
        Paste text, get a dashboard.
      </p>
      <p className="mt-2 text-sm text-gray-400">
        A visual pastebin for data — shareable dashboards in seconds.
      </p>
    </main>
  )
}
