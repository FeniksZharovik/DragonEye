// src/app/users/page.tsx
'use client';

import { useState, useEffect, KeyboardEvent } from 'react';
import { fetchFromAPI } from '@/lib/api';

type User = {
  uid: string;
  username: string;
  email: string;
};

type UsersResponse = {
  users: User[];
  count: number;
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [appliedSearch, setAppliedSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize, setPageSize] = useState(7);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [filterOpen, setFilterOpen] = useState(false); // For dropdown

  const fetchUsers = async (page = 1, search = '', size = pageSize) => {
    setLoading(true);
    setError(null);
    try {
      const url = `/users/?page=${page}&limit=${size}${search ? `&search=${encodeURIComponent(search)}` : ''}`;
      const response: UsersResponse = await fetchFromAPI(url);
      
      if (!response || !response.users) {
        throw new Error('Invalid response format');
      }
      
      setUsers(response.users || []);
      setTotalPages(Math.ceil((response.count || 0) / size));
      setError(null);
    } catch (err) {
      console.error('Error fetching users:', err);
      setError(err instanceof Error ? err.message : 'Failed to load users');
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers(currentPage, appliedSearch);
  }, [currentPage, appliedSearch]);

  const handleDelete = async (uid: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
      await fetchFromAPI(`/users/${uid}`, {
        method: 'DELETE',
      });
      setMessage('User deleted successfully');
      setTimeout(() => setMessage(''), 3000);
      fetchUsers(currentPage, appliedSearch);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to delete user';
      setError(errorMsg);
      setTimeout(() => setError(''), 3000);
    }
  };

  // ✅ Trigger search only on Enter
  const handleSearchKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      setAppliedSearch(searchTerm);
      setCurrentPage(1);
    }
  };

  const handlePageChange = (newPage: number) => {
    if (newPage > 0 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  // Toggle dropdown
  const toggleFilter = () => {
    setFilterOpen(!filterOpen);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      if (filterOpen) setFilterOpen(false);
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [filterOpen]);

  if (loading) {
    return (
      <div className="p-6 flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-50 via-blue-50 to-indigo-50 p-5 space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold bg-linear-to-r from-blue-600 via-cyan-600 to-emerald-600 bg-clip-text text-transparent mb-1">
          User Management
        </h1>
        <p className="text-base text-slate-600">
          Manage and monitor all system users
        </p>
      </div>

      {/* Alerts */}
      {message && (
        <div className="p-3 bg-emerald-50 border-l-4 border-emerald-500 rounded-lg flex items-start gap-2">
          <div className="text-emerald-600 text-lg">✓</div>
          <div>
            <h3 className="font-semibold text-emerald-900 text-sm">{message}</h3>
          </div>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-50 border-l-4 border-red-500 rounded-lg flex items-start gap-2">
          <div className="text-red-600 text-lg">✕</div>
          <div>
            <h3 className="font-semibold text-red-900 text-sm">{error}</h3>
          </div>
        </div>
      )}

      {/* Top Bar */}
      <div className="bg-white rounded-2xl shadow-lg p-5 border border-slate-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-5">
          <div>
            <h2 className="text-xl font-bold text-slate-900">User Directory</h2>
            <p className="text-xs text-slate-500 mt-0.5">Total users: <span className="font-semibold text-slate-700">({totalPages * pageSize})</span></p>
          </div>
          <a
            href="/dashboard/users/form"
            className="px-5 py-2 bg-linear-to-r from-blue-600 to-cyan-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all duration-300 flex items-center justify-center gap-2 text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add New User
          </a>
        </div>

        {/* Search & Filter */}
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Search by username or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-slate-50 transition text-sm"
            />
            <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          {/* Filter Button */}
          <div className="relative">
            <button
              onClick={toggleFilter}
              className="px-5 py-2 border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50 transition flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              Filter
            </button>

            {/* Dropdown */}
            {filterOpen && (
              <div className="absolute right-0 z-10 mt-2 w-48 bg-white border border-slate-300 rounded-xl shadow-xl overflow-hidden">
                <button
                  onClick={() => { setFilterOpen(false); }}
                  className="w-full px-4 py-2 text-left hover:bg-blue-50 text-slate-700 font-medium text-sm transition"
                >
                  Newest First
                </button>
                <button
                  onClick={() => { setFilterOpen(false); }}
                  className="w-full px-4 py-2 text-left hover:bg-blue-50 text-slate-700 font-medium text-sm transition border-t"
                >
                  Oldest First
                </button>
                <button
                  onClick={() => { setFilterOpen(false); }}
                  className="w-full px-4 py-2 text-left hover:bg-blue-50 text-slate-700 font-medium text-sm transition border-t"
                >
                  Clear Filter
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-slate-200 bg-linear-to-r from-slate-50 to-blue-50">
                <th className="px-5 py-3 text-left text-xs font-bold text-slate-700 uppercase tracking-wider">No</th>
                <th className="px-5 py-3 text-left text-xs font-bold text-slate-700 uppercase tracking-wider">Username</th>
                <th className="px-5 py-3 text-left text-xs font-bold text-slate-700 uppercase tracking-wider">Email</th>
                <th className="px-5 py-3 text-left text-xs font-bold text-slate-700 uppercase tracking-wider">Joined</th>
                <th className="px-5 py-3 text-center text-xs font-bold text-slate-700 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {users.map((user, idx) => (
                <tr key={user.uid} className="hover:bg-blue-50 transition-colors duration-200 group">
                  <td className="px-5 py-3">
                    <span className="inline-block bg-slate-100 text-slate-700 px-2 py-0.5 rounded-lg text-xs font-semibold">
                      {(currentPage - 1) * pageSize + idx + 1}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-linear-to-br from-blue-400 to-cyan-400 flex items-center justify-center text-white font-bold text-xs">
                        {user.username[0].toUpperCase()}
                      </div>
                      <span className="font-semibold text-slate-900 text-sm">{user.username}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-slate-600 text-sm">{user.email}</td>
                  <td className="px-5 py-3 text-slate-500 text-xs">01 Jan, 2024</td>
                  <td className="px-5 py-3">
                    <div className="flex items-center justify-center gap-2">
                      <a
                        href={`/dashboard/users/form?uid=${user.uid}`}
                        className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-lg font-semibold hover:bg-blue-200 transition text-xs"
                      >
                        Edit
                      </a>
                      <button
                        onClick={() => handleDelete(user.uid)}
                        className="px-3 py-1.5 bg-red-100 text-red-700 rounded-lg font-semibold hover:bg-red-200 transition text-xs"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-5 py-3 border-t-2 border-slate-200 bg-linear-to-r from-slate-50 to-blue-50 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-xs text-slate-600">
            Showing <span className="font-bold text-slate-900">{(currentPage - 1) * pageSize + 1}</span> to{' '}
            <span className="font-bold text-slate-900">{Math.min(currentPage * pageSize, users.length)}</span> of{' '}
            <span className="font-bold text-slate-900">{totalPages * pageSize}</span>
          </div>
          <div className="flex items-center space-x-1">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className={`px-2 py-1.5 rounded-lg font-semibold transition text-xs ${
                currentPage === 1 ? 'text-slate-400 cursor-not-allowed bg-slate-100' : 'text-slate-700 hover:bg-blue-100'
              }`}
            >
              ← Prev
            </button>
            {[...Array(totalPages)].map((_, i) => (
              <button
                key={i + 1}
                onClick={() => handlePageChange(i + 1)}
                className={`px-2 py-1.5 rounded-lg font-semibold transition text-xs ${
                  currentPage === i + 1 ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-700 hover:bg-slate-200 border border-slate-300'
                }`}
              >
                {i + 1}
              </button>
            ))}
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className={`px-2 py-1.5 rounded-lg font-semibold transition text-xs ${
                currentPage === totalPages ? 'text-slate-400 cursor-not-allowed bg-slate-100' : 'text-slate-700 hover:bg-blue-100'
              }`}
            >
              Next →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}