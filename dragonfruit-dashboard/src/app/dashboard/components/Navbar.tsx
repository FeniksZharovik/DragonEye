'use client';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faDragon, faBars, faTimes } from '@fortawesome/free-solid-svg-icons';
import { useState, useEffect } from 'react';
import { getCurrentUser } from '@/lib/auth'; // ← Import auth helper

interface NavbarProps {
  onToggleSidebar?: () => void;
}

export default function Navbar({ onToggleSidebar }: NavbarProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [user, setUser] = useState<{ username: string; email: string } | null>(null);

  useEffect(() => {
    const loadUser = async () => {
      const currentUser = await getCurrentUser();
      if (currentUser) {
        setUser(currentUser);
      }
    };
    loadUser();
  }, []);

  const handleToggle = () => {
    setSidebarOpen(!sidebarOpen);
    const event = new Event('toggleSidebar');
    window.dispatchEvent(event);
    onToggleSidebar?.();
  };

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 w-full bg-gray-900 border-b border-gray-700">
        <div className="px-3 py-3 lg:px-5 lg:pl-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center justify-start gap-2">
              {/* Mobile Toggle Button */}
              <button
                onClick={handleToggle}
                aria-controls="sidebar"
                type="button"
                className="inline-flex items-center p-2 text-sm text-gray-300 rounded-lg md:hidden hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-600"
              >
                <span className="sr-only">Toggle sidebar</span>
                <FontAwesomeIcon icon={sidebarOpen ? faTimes : faBars} className="w-6 h-6" />
              </button>

              {/* Logo */}
              <a href="/dashboard" className="flex items-center ms-2 md:ms-0">
                <FontAwesomeIcon
                  icon={faDragon}
                  className="text-[22px] mr-2 text-white"
                  aria-hidden="true"
                />
                <span className="self-center text-xl font-semibold sm:text-2xl whitespace-nowrap text-white">
                  DragonFruit
                </span>
              </a>
            </div>

            {/* User Info */}
            <div className="flex flex-col items-end gap-1">
              {user ? (
                <>
                  <p className="text-sm font-medium text-gray-300">{user.username}</p>
                  <p className="text-xs text-gray-400">{user.email}</p>
                </>
              ) : (
                <p className="text-sm font-medium text-gray-300">Not logged in</p>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden mt-16"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </>
  );
}