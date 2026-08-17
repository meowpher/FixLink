'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Footer() {
  const pathname = usePathname();
  
  return (
    <footer className="w-full bg-[#121212] border-t border-gray-800 py-6 text-sm text-gray-400 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row justify-between items-center">
        <p>© {new Date().getFullYear()} Your Company. All rights reserved.</p>
        <div className="mt-4 sm:mt-0">
          <Link 
            href={`/report-bug?origin=${encodeURIComponent(pathname || '/')}`}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m8 2 1.88 1.88"/>
              <path d="M14.12 3.88 16 2"/>
              <path d="M9 7.13v-1a3.003 3.003 0 1 1 6 0v1"/>
              <path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6"/>
              <path d="M12 20v-9"/>
              <path d="M6.53 9C4.6 8.8 3 7.1 3 5"/>
              <path d="M17.47 9c1.93-.2 3.53-1.9 3.53-4"/>
            </svg>
            Report Bug
          </Link>
        </div>
      </div>
    </footer>
  );
}
