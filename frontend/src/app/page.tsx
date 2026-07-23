import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="max-w-5xl w-full items-center justify-between text-center">
        <h1 className="text-6xl font-bold mb-8">
          Adminory
        </h1>
        <p className="text-xl text-muted-foreground mb-12">
          Universal Admin Control Plane Framework
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-16">
          <Link
            href="/internal/dashboard"
            className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100"
          >
            <h2 className="mb-3 text-2xl font-semibold">
              Internal Control Plane{' '}
              <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
                →
              </span>
            </h2>
            <p className="m-0 max-w-[30ch] text-sm opacity-50">
              For operations teams and support staff
            </p>
          </Link>

          <Link
            href="/external/dashboard"
            className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100"
          >
            <h2 className="mb-3 text-2xl font-semibold">
              External Control Plane{' '}
              <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
                →
              </span>
            </h2>
            <p className="m-0 max-w-[30ch] text-sm opacity-50">
              For end customers and tenant administrators
            </p>
          </Link>
        </div>

        <div className="mt-16">
          <Link
            href="/login"
            className="text-blue-600 hover:text-blue-800 underline"
          >
            Login →
          </Link>
        </div>
      </div>
    </main>
  )
}
