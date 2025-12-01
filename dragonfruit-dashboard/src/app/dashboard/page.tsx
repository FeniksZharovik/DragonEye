// src/app/dashboard/page.tsx
"use client";

import { useState, useEffect } from 'react';
import { fetchFromAPI } from '@/lib/api';

interface GradingResult {
  id: string;
  length_cm: number;
  diameter_cm: number;
  weight_est_g: number;
  weight_actual_g: number;
  ratio: number;
  fuzzy_score: number;
  final_grade: "A" | "B" | "C";
  tanggal: string;
}

interface ApiResponse {
  data: GradingResult[];
  total: number;
  message: string;
}

export default function DashboardPage() {
  const [allData, setAllData] = useState<GradingResult[]>([]);
  const [filteredData, setFilteredData] = useState<GradingResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedFilter, setSelectedFilter] = useState('Semua');
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const itemsPerPage = 20;

  // Calculate pagination values
  const totalPages = Math.ceil(filteredData.length / itemsPerPage);
  const startIdx = (currentPage - 1) * itemsPerPage;
  const endIdx = startIdx + itemsPerPage;
  const paginatedData = filteredData.slice(startIdx, endIdx);

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result: ApiResponse = await fetchFromAPI<ApiResponse>('/api/gradingresult/all', {
          method: 'GET',
          credentials: 'include',
        });
        
        // Sort by newest first (descending order)
        const sortedData = result.data.sort((a, b) => {
          const dateA = new Date(a.tanggal).getTime();
          const dateB = new Date(b.tanggal).getTime();
          return dateB - dateA;
        });

        setAllData(sortedData);
        setFilteredData(sortedData);
        setCurrentPage(1);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
        console.error('Error fetching data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Handle filtering
  useEffect(() => {
    if (selectedFilter === "Semua") {
      setFilteredData(allData);
    } else {
      const grade = selectedFilter.split(" ")[1];
      setFilteredData(allData.filter(item => item.final_grade === grade));
    }
    setCurrentPage(1);
  }, [selectedFilter, allData]);

  // Calculate statistics for today
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const todayData = allData.filter(item => {
    const itemDate = new Date(item.tanggal);
    itemDate.setHours(0, 0, 0, 0);
    return itemDate.getTime() === today.getTime();
  });

  const todayGradeA = todayData.filter(item => item.final_grade === "A").length;
  const gradeARate = todayData.length > 0 ? Math.round((todayGradeA / todayData.length) * 100) : 0;

  const stats = {
    totalGraded: allData.length,
    gradeA: allData.filter(item => item.final_grade === "A").length,
    gradeB: allData.filter(item => item.final_grade === "B").length,
    gradeC: allData.filter(item => item.final_grade === "C").length,
    machineStatus: 'online',
    lastScan: 'Real-time',
    todayRecords: todayData.length,
    todayGradeARate: gradeARate,
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-50 via-blue-50 to-indigo-50 p-6 space-y-8">
      {/* Header Section */}
      <div className="relative z-10">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-5xl font-bold bg-linear-to-r from-blue-600 via-cyan-600 to-emerald-600 bg-clip-text text-transparent mb-2">
              Dashboard
            </h1>
            <p className="text-lg text-slate-600">
              Sistem Grading Buah Naga Super Merah – Pantau proses grading real-time dari mesin IoT.
            </p>
          </div>
          <div className="hidden lg:flex items-center gap-2 px-4 py-2 bg-white rounded-full shadow-md border border-slate-200">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            <span className="text-sm font-semibold text-emerald-600">System Live</span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Graded Card */}
        <div className="group relative overflow-hidden rounded-2xl bg-white p-6 shadow-lg hover:shadow-2xl transition-all duration-300 hover:scale-105 border border-slate-100">
          <div className="absolute inset-0 bg-linear-to-br from-blue-50 to-cyan-50 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <span className="text-blue-600 text-sm font-semibold uppercase tracking-wider">Total Graded</span>
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <p className="text-4xl font-bold text-slate-900 mb-2">{stats.totalGraded}</p>
            <p className="text-slate-600 text-sm">buah graded keseluruhan</p>
            <div className="mt-4 h-1 bg-linear-to-r from-blue-400 to-cyan-400 rounded-full"></div>
          </div>
        </div>

        {/* Grade A Card */}
        <div className="group relative overflow-hidden rounded-2xl bg-white p-6 shadow-lg hover:shadow-2xl transition-all duration-300 hover:scale-105 border border-slate-100">
          <div className="absolute inset-0 bg-linear-to-br from-emerald-50 to-teal-50 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <span className="text-emerald-600 text-sm font-semibold uppercase tracking-wider">Grade A</span>
              <div className="p-2 bg-emerald-100 rounded-lg">
                <svg className="w-6 h-6 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <p className="text-4xl font-bold text-slate-900 mb-2">{stats.gradeA}</p>
            <p className="text-slate-600 text-sm">Excellent quality</p>
            <div className="mt-4 h-1 bg-linear-to-r from-emerald-400 to-teal-400 rounded-full"></div>
          </div>
        </div>

        {/* Grade B Card */}
        <div className="group relative overflow-hidden rounded-2xl bg-white p-6 shadow-lg hover:shadow-2xl transition-all duration-300 hover:scale-105 border border-slate-100">
          <div className="absolute inset-0 bg-linear-to-br from-amber-50 to-orange-50 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <span className="text-amber-600 text-sm font-semibold uppercase tracking-wider">Grade B</span>
              <div className="p-2 bg-amber-100 rounded-lg">
                <svg className="w-6 h-6 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <p className="text-4xl font-bold text-slate-900 mb-2">{stats.gradeB}</p>
            <p className="text-slate-600 text-sm">Good quality</p>
            <div className="mt-4 h-1 bg-linear-to-r from-amber-400 to-orange-400 rounded-full"></div>
          </div>
        </div>

        {/* Grade C Card */}
        <div className="group relative overflow-hidden rounded-2xl bg-white p-6 shadow-lg hover:shadow-2xl transition-all duration-300 hover:scale-105 border border-slate-100">
          <div className="absolute inset-0 bg-linear-to-br from-rose-50 to-red-50 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <span className="text-rose-600 text-sm font-semibold uppercase tracking-wider">Grade C</span>
              <div className="p-2 bg-rose-100 rounded-lg">
                <svg className="w-6 h-6 text-rose-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <p className="text-4xl font-bold text-slate-900 mb-2">{stats.gradeC}</p>
            <p className="text-slate-600 text-sm">Fair quality</p>
            <div className="mt-4 h-1 bg-linear-to-r from-rose-400 to-red-400 rounded-full"></div>
          </div>
        </div>
      </div>

      {/* Machine Status Card */}
      <div className="relative overflow-hidden rounded-2xl bg-white p-8 shadow-lg border border-slate-200">
        <div className="absolute top-0 right-0 w-40 h-40 bg-linear-to-br from-emerald-100 to-cyan-100 rounded-full blur-3xl opacity-20"></div>
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-slate-900">Status Koneksi API</h3>
            <div className="px-4 py-2 bg-emerald-100 rounded-full border border-emerald-200">
              <div className="flex items-center gap-2">
                <span className="flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
                <span className="text-sm font-semibold text-emerald-700">
                  {stats.machineStatus === 'online' ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>
          </div>
          <p className="text-slate-500 text-sm mb-4">{stats.lastScan}</p>
          <div className="p-4 bg-linear-to-r from-blue-50 to-cyan-50 rounded-lg border border-blue-200">
            <p className="text-slate-700 text-sm">
              <span className="font-semibold text-emerald-600">✓</span> API terhubung dan siap melayani {allData.length} data grading
            </p>
          </div>
        </div>
      </div>

      {/* Riwayat Penilaian Section */}
      <div className="relative overflow-hidden rounded-2xl bg-white shadow-lg border border-slate-200">
        <div className="absolute top-0 left-0 w-40 h-40 bg-linear-to-br from-blue-100 to-cyan-100 rounded-full blur-3xl opacity-10"></div>
        <div className="relative z-10 p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h2 className="text-3xl font-bold text-slate-900 mb-2">Riwayat Penilaian Buah</h2>
              <p className="text-slate-500 text-sm">Pantau hasil grading terbaru dari sistem (Newest First)</p>
            </div>

            {/* Filter Dropdown */}
            <div className="relative">
              <button
                className="inline-flex items-center px-4 py-2 text-sm font-semibold text-slate-700 bg-slate-100 border border-slate-300 rounded-lg hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200"
                type="button"
                onClick={() => setIsFilterOpen(!isFilterOpen)}
              >
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12.414 11.414a1 1 0 00-.293.707v5.172a1 1 0 01-.578.894l-2 1A1 1 0 018 17.69V12.414a1 1 0 00-.293-.707L3.293 6.707A1 1 0 013 6V3z" clipRule="evenodd" />
                </svg>
                {selectedFilter}
                <svg
                  className={`ml-2 h-4 w-4 transition-transform duration-200 ${isFilterOpen ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>

              {/* Dropdown Menu */}
              {isFilterOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white border border-slate-300 rounded-lg shadow-xl z-10 overflow-hidden">
                  <ul className="py-2">
                    {['Semua', 'Grade A', 'Grade B', 'Grade C'].map((filter) => (
                      <li key={filter}>
                        <button
                          className={`block w-full px-4 py-3 text-sm text-left transition-colors duration-150 border-l-4 ${
                            selectedFilter === filter
                              ? 'border-blue-500 bg-blue-50 text-blue-700 font-semibold'
                              : 'border-transparent text-slate-700 hover:bg-blue-50 hover:border-blue-500'
                          }`}
                          onClick={() => {
                            setSelectedFilter(filter);
                            setIsFilterOpen(false);
                          }}
                        >
                          {filter}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
              <p className="text-red-700 text-sm">Error: {error}</p>
            </div>
          )}

          {/* Table */}
          {!loading && !error && (
            <>
              <div className="overflow-x-auto rounded-xl border border-slate-200 bg-slate-50">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b-2 border-slate-300 bg-linear-to-r from-slate-100 via-blue-50 to-cyan-50">
                      <th className="px-6 py-4 text-left text-xs font-bold text-slate-800 uppercase tracking-widest">Timestamp</th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-slate-800 uppercase tracking-widest">Berat (g)</th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-slate-800 uppercase tracking-widest">Length (cm)</th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-slate-800 uppercase tracking-widest">Diameter (cm)</th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-slate-800 uppercase tracking-widest">Ratio</th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-slate-800 uppercase tracking-widest">Fuzzy Score</th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-slate-800 uppercase tracking-widest">Final Grade</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {paginatedData.length > 0 ? (
                      paginatedData.map((row, idx) => (
                        <tr key={idx} className="hover:bg-blue-50 transition-colors duration-150 group">
                          <td className="px-6 py-4 text-slate-600 text-sm whitespace-nowrap">
                            {new Date(row.tanggal).toLocaleString('id-ID')}
                          </td>
                          <td className="px-6 py-4 text-slate-600">{row.weight_actual_g?.toFixed(1) || 'N/A'}</td>
                          <td className="px-6 py-4 text-slate-600">{row.length_cm?.toFixed(2) || 'N/A'}</td>
                          <td className="px-6 py-4 text-slate-600">{row.diameter_cm?.toFixed(2) || 'N/A'}</td>
                          <td className="px-6 py-4">
                            <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-bold bg-blue-100 text-blue-700">
                              {row.ratio?.toFixed(3) || 'N/A'}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-bold bg-cyan-100 text-cyan-700">
                              {row.fuzzy_score?.toFixed(1) || 'N/A'}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold border-2 ${
                              row.final_grade === 'A' ? 'bg-emerald-50 text-emerald-700 border-emerald-400' :
                              row.final_grade === 'B' ? 'bg-amber-50 text-amber-700 border-amber-400' :
                              'bg-rose-50 text-rose-700 border-rose-400'
                            }`}>
                              {row.final_grade}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                          No data available
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination Controls */}
              {filteredData.length > 0 && (
                <div className="mt-6 flex items-center justify-between">
                  <div className="text-sm text-slate-600">
                    Showing {startIdx + 1} to {Math.min(endIdx, filteredData.length)} of {filteredData.length} results
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className="px-4 py-2 text-sm font-semibold text-slate-700 bg-slate-100 border border-slate-300 rounded-lg hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                    >
                      Previous
                    </button>

                    <div className="flex items-center gap-1">
                      {Array.from({ length: Math.min(5, totalPages) }).map((_, idx) => {
                        let pageNum;
                        if (totalPages <= 5) {
                          pageNum = idx + 1;
                        } else if (currentPage <= 3) {
                          pageNum = idx + 1;
                        } else if (currentPage >= totalPages - 2) {
                          pageNum = totalPages - 4 + idx;
                        } else {
                          pageNum = currentPage - 2 + idx;
                        }

                        return (
                          <button
                            key={pageNum}
                            onClick={() => setCurrentPage(pageNum)}
                            className={`px-3 py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${
                              currentPage === pageNum
                                ? 'bg-blue-600 text-white'
                                : 'text-slate-700 bg-slate-100 border border-slate-300 hover:bg-slate-200'
                            }`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                    </div>

                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                      className="px-4 py-2 text-sm font-semibold text-slate-700 bg-slate-100 border border-slate-300 rounded-lg hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}

              {/* Footer Stats */}
              <div className="mt-6 grid grid-cols-3 gap-4 p-4 bg-linear-to-r from-blue-50 to-cyan-50 rounded-xl border border-blue-200">
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">{stats.todayRecords}</p>
                  <p className="text-xs text-slate-600 mt-1">Records Today</p>
                </div>
                <div className="text-center border-l border-r border-slate-300">
                  <p className="text-2xl font-bold text-emerald-600">{stats.todayGradeARate}%</p>
                  <p className="text-xs text-slate-600 mt-1">Grade A Rate Today</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-cyan-600">{stats.totalGraded}</p>
                  <p className="text-xs text-slate-600 mt-1">Total Graded</p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}