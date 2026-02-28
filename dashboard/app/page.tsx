export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center p-8">
      <div className="max-w-4xl text-center text-white">
        <h1 className="text-6xl font-bold mb-6">
          CourtSync
        </h1>
        <p className="text-2xl mb-8">
          Autonomous AI coordination for pickleball
        </p>
        <div className="space-x-4">
          <a 
            href="/demo" 
            className="bg-white text-purple-600 px-8 py-4 rounded-lg font-bold text-xl hover:bg-gray-100 transition inline-block"
          >
            View Live Demo
          </a>
          <a 
            href="https://wa.me/YOUR_TWILIO_NUMBER" 
            className="bg-transparent border-2 border-white text-white px-8 py-4 rounded-lg font-bold text-xl hover:bg-white hover:text-purple-600 transition inline-block"
          >
            Try on WhatsApp
          </a>
        </div>
      </div>
    </main>
  );
}