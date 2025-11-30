// src/app/dashboard/layout.tsx
'use client';

import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import { useState } from 'react';
import AuthGuard from './components/AuthGuard';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleToggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <AuthGuard> {/* 👈 Wrap entire layout */}
      <div className="flex flex-col min-h-screen bg-gray-100">
        <Navbar onToggleSidebar={handleToggleSidebar} />
        <div className="flex flex-1 pt-16">
          <Sidebar />
          <main className="flex-1 md:ml-64 w-full overflow-y-auto">
            {children}
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}