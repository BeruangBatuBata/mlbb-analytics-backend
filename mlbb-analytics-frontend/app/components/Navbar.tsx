// In mlbb-analytics-frontend/app/components/Navbar.tsx
import Link from 'next/link';
import Image from 'next/image';

export default function Navbar() {
  return (
    <nav className="bg-gray-800 p-4 sticky top-0 z-10 border-b border-gray-700">
      <div className="container mx-auto flex justify-between items-center">
        {/* Logo and Title Link */}
        <Link href="/" className="flex items-center gap-3 text-white text-xl font-bold hover:text-blue-400 transition-colors">
          <Image
            src="/beruangbatubata.png" // Assumes the image is in the 'public' folder
            alt="Logo"
            width={32}
            height={32}
            className="rounded-full"
          />
          <span>MLBB Analytics</span>
        </Link>
        
        {/* Navigation Links */}
        <div className="space-x-4">
          <Link href="/" className="text-gray-300 hover:text-white transition-colors">
            Home
          </Link>
          <Link href="/statistics" className="text-gray-300 hover:text-white transition-colors">
            Statistics
          </Link>
        </div>
      </div>
    </nav>
  );
}