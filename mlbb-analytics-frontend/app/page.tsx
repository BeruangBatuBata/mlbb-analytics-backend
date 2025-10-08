// In app/page.tsx

// This is an async function that fetches data from our backend API.
// Next.js runs this on the server, making it very fast.
async function getStats() {
  try {
    // We fetch from the backend's /api/stats endpoint.
    const res = await fetch('http://127.0.0.1:8000/api/stats', { 
      // 'no-store' ensures we always get the latest data on every request.
      cache: 'no-store' 
    });

    // If the response is not OK (e.g., a 404 or 500 error), we throw an error.
    if (!res.ok) {
      throw new Error('Failed to fetch data from the API');
    }

    // We parse the JSON response and return it.
    return res.json();
  } catch (error) {
    console.error("API Fetch Error:", error);
    // Return an empty array on error so the page doesn't crash.
    return [];
  }
}

// Define a TypeScript interface for the shape of our data.
// This provides type safety and autocompletion in our code.
interface HeroStat {
  "Hero": string;
  "Picks": number;
  "Bans": number;
  "Pick Rate (%)": number;
  "Ban Rate (%)": number;
  "Win Rate (%)": number;
  "Presence (%)": number;
}

// This is our main Home Page component. It's an `async` component,
// which allows us to use `await` directly inside it.
export default async function HomePage() {
  
  // We call our data fetching function and wait for the stats to arrive.
  const stats: HeroStat[] = await getStats();

  return (
    // We use Tailwind CSS for styling. This creates a dark-themed, responsive layout.
    <main className="container mx-auto p-4 md:p-8 bg-gray-900 text-white min-h-screen">
      <header className="text-center mb-8">
        <h1 className="text-3xl md:text-5xl font-bold text-blue-400 tracking-tight">
          MLBB Hero Meta Statistics
        </h1>
        <p className="text-lg text-gray-400 mt-2">
          An overview of the current professional scene meta.
        </p>
      </header>

      <div className="overflow-x-auto relative shadow-2xl rounded-lg border border-gray-700">
        <table className="w-full text-sm text-left text-gray-300">
          <thead className="text-xs text-blue-300 uppercase bg-gray-800 sticky top-0">
            <tr>
              <th scope="col" className="py-3 px-6">Hero</th>
              <th scope="col" className="py-3 px-6">Picks</th>
              <th scope="col" className="py-3 px-6">Bans</th>
              <th scope="col" className="py-3 px-6">Pick Rate</th>
              <th scope="col" className="py-3 px-6">Ban Rate</th>
              <th scope="col" className="py-3 px-6">Win Rate</th>
              <th scope="col" className="py-3 px-6">Presence</th>
            </tr>
          </thead>
          <tbody>
            {/* We map over the `stats` array to create a table row for each hero. */}
            {stats.map((hero) => (
              <tr key={hero.Hero} className="bg-gray-800/50 border-b border-gray-700 hover:bg-gray-700/50 transition-colors duration-200">
                <th scope="row" className="py-4 px-6 font-medium text-white whitespace-nowrap">
                  {hero.Hero}
                </th>
                <td className="py-4 px-6">{hero.Picks}</td>
                <td className="py-4 px-6">{hero.Bans}</td>
                <td className="py-4 px-6">{hero["Pick Rate (%)"].toFixed(2)}%</td>
                <td className="py-4 px-6">{hero["Ban Rate (%)"].toFixed(2)}%</td>
                <td className="py-4 px-6">{hero["Win Rate (%)"].toFixed(2)}%</td>
                <td className="py-4 px-6">{hero["Presence (%)"].toFixed(2)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
