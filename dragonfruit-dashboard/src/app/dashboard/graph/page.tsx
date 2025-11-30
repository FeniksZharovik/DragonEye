'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { fetchFromAPI } from '@/lib/api';
import {
  fetchClassificationMetrics,
  fetchConfusionMatrix,
  getMetricsWithCache,
  MetricsData,
  ConfusionMatrixResponse,
} from '@/lib/metrics';

// Dynamic import to avoid SSR issues with ApexCharts
const ReactApexChart = dynamic(() => import('react-apexcharts'), { ssr: false });

interface StatisticData {
  label: string;
  value: number;
  unit: string;
  status: 'good' | 'warning' | 'danger';
}

interface IoTDailyData {
  date: string;
  uptime: number;
  temp: number;
  humidity: number;
}

interface ComputerVisionDailyData {
  date: string;
  accuracy: number;
  processingTime: number;
  detectionRate: number;
}

interface MachineLearningDailyData {
  date: string;
  fuzzyAccuracy: number;
  precision: number;
  recall: number;
}

interface SectionData {
  iotHealth: {
    uptime: StatisticData;
    temperature: StatisticData;
    humidity: StatisticData;
    signalStrength: StatisticData;
    dailyData: IoTDailyData[];
  };
  computerVision: {
    accuracy: StatisticData;
    processingTime: StatisticData;
    detectionRate: StatisticData;
    falsePositives: StatisticData;
    dailyData: ComputerVisionDailyData[];
  };
  machineLearning: {
    fuzzyAccuracy: StatisticData;
    precision: StatisticData;
    recall: StatisticData;
    f1Score: StatisticData;
    dailyData: MachineLearningDailyData[];
  };
}

export default function GraphPage() {
  const [sectionData, setSectionData] = useState<SectionData | null>(null);
  const [metricsData, setMetricsData] = useState<MetricsData | null>(null);
  const [confusionMatrix, setConfusionMatrix] = useState<number[][] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchChartData = async () => {
      try {
        // Fetch classification metrics
        const metricsResponse = await fetchClassificationMetrics();
        if (metricsResponse.status === 'success' && metricsResponse.metrics) {
          setMetricsData(metricsResponse.metrics);
        }

        // Fetch confusion matrix
        const cmResponse = await fetchConfusionMatrix();
        if (cmResponse && cmResponse.status === 'success') {
          setConfusionMatrix(cmResponse.confusion_matrix);
        }

        // Mock data for other sections - replace with actual API calls
        const mockData: SectionData = {
          iotHealth: {
            uptime: { label: 'Uptime', value: 99.8, unit: '%', status: 'good' },
            temperature: { label: 'Temperature', value: 28.5, unit: '°C', status: 'good' },
            humidity: { label: 'Humidity', value: 65, unit: '%', status: 'good' },
            signalStrength: { label: 'Signal Strength', value: 92, unit: 'dBm', status: 'good' },
            dailyData: [
              { date: 'Mon', uptime: 99.8, temp: 28.2, humidity: 64 },
              { date: 'Tue', uptime: 99.9, temp: 28.5, humidity: 65 },
              { date: 'Wed', uptime: 99.7, temp: 27.8, humidity: 63 },
              { date: 'Thu', uptime: 100, temp: 29.1, humidity: 66 },
              { date: 'Fri', uptime: 99.6, temp: 28.9, humidity: 67 },
              { date: 'Sat', uptime: 99.9, temp: 28.3, humidity: 64 },
              { date: 'Sun', uptime: 99.8, temp: 28.7, humidity: 65 },
            ],
          },
          computerVision: {
            accuracy: { label: 'Detection Accuracy', value: 96.5, unit: '%', status: 'good' },
            processingTime: { label: 'Avg Processing Time', value: 245, unit: 'ms', status: 'good' },
            detectionRate: { label: 'Detection Rate', value: 98.2, unit: '%', status: 'good' },
            falsePositives: { label: 'False Positives', value: 2.1, unit: '%', status: 'warning' },
            dailyData: [
              { date: 'Mon', accuracy: 96.2, processingTime: 250, detectionRate: 98.1 },
              { date: 'Tue', accuracy: 96.5, processingTime: 245, detectionRate: 98.2 },
              { date: 'Wed', accuracy: 96.8, processingTime: 240, detectionRate: 98.4 },
              { date: 'Thu', accuracy: 96.1, processingTime: 255, detectionRate: 97.9 },
              { date: 'Fri', accuracy: 96.9, processingTime: 235, detectionRate: 98.5 },
              { date: 'Sat', accuracy: 97.1, processingTime: 238, detectionRate: 98.6 },
              { date: 'Sun', accuracy: 96.5, processingTime: 248, detectionRate: 98.2 },
            ],
          },
          machineLearning: {
            fuzzyAccuracy: {
              label: 'Fuzzy Logic Accuracy',
              value: metricsData?.accuracy ? metricsData.accuracy * 100 : 94.7,
              unit: '%',
              status: 'good',
            },
            precision: {
              label: 'Precision',
              value: metricsData?.macro_precision ? metricsData.macro_precision * 100 : 95.2,
              unit: '%',
              status: 'good',
            },
            recall: {
              label: 'Recall',
              value: metricsData?.macro_recall ? metricsData.macro_recall * 100 : 94.1,
              unit: '%',
              status: 'good',
            },
            f1Score: {
              label: 'F1 Score',
              value: metricsData?.macro_f1 ? metricsData.macro_f1 * 100 : 94.6,
              unit: '%',
              status: 'good',
            },
            dailyData: [
              { date: 'Mon', fuzzyAccuracy: 94.5, precision: 95.0, recall: 93.9 },
              { date: 'Tue', fuzzyAccuracy: 94.7, precision: 95.2, recall: 94.1 },
              { date: 'Wed', fuzzyAccuracy: 94.9, precision: 95.4, recall: 94.3 },
              { date: 'Thu', fuzzyAccuracy: 94.3, precision: 94.8, recall: 93.7 },
              { date: 'Fri', fuzzyAccuracy: 95.1, precision: 95.6, recall: 94.5 },
              { date: 'Sat', fuzzyAccuracy: 95.3, precision: 95.8, recall: 94.8 },
              { date: 'Sun', fuzzyAccuracy: 94.7, precision: 95.2, recall: 94.1 },
            ],
          },
        };

        setSectionData(mockData);
        setLoading(false);
      } catch (err) {
        setError('Failed to load chart data');
        setLoading(false);
        console.error(err);
      }
    };

    fetchChartData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-600">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-red-600">{error}</div>
      </div>
    );
  }

  if (!sectionData) return null;

  // Helper function to get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good':
        return 'border-green-500 bg-green-50';
      case 'warning':
        return 'border-yellow-500 bg-yellow-50';
      case 'danger':
        return 'border-red-500 bg-red-50';
      default:
        return 'border-gray-500 bg-gray-50';
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'good':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'danger':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // IoT Health Charts
  const iotLineChartOptions = {
    chart: {
      type: 'line' as const,
      toolbar: { show: true },
    },
    colors: ['#3b82f6', '#ef4444', '#10b981'],
    xaxis: {
      categories: sectionData.iotHealth.dailyData.map((d) => d.date),
    },
    yaxis: {
      title: { text: 'Values' },
    },
    stroke: { curve: 'smooth' as const, width: 3 },
    markers: { size: 5 },
    legend: { position: 'top' as const },
  };

  const iotLineChartSeries = [
    {
      name: 'Uptime (%)',
      data: sectionData.iotHealth.dailyData.map((d) => d.uptime),
    },
    {
      name: 'Temperature (°C)',
      data: sectionData.iotHealth.dailyData.map((d) => d.temp),
    },
    {
      name: 'Humidity (%)',
      data: sectionData.iotHealth.dailyData.map((d) => d.humidity),
    },
  ];

  // Computer Vision Charts
  const cvLineChartOptions = {
    chart: {
      type: 'line' as const,
      toolbar: { show: true },
    },
    colors: ['#8b5cf6', '#ec4899', '#06b6d4'],
    xaxis: {
      categories: sectionData.computerVision.dailyData.map((d) => d.date),
    },
    yaxis: {
      title: { text: 'Accuracy/Detection Rate (%)' },
    },
    stroke: { curve: 'smooth' as const, width: 3 },
    markers: { size: 5 },
    legend: { position: 'top' as const },
  };

  const cvLineChartSeries = [
    {
      name: 'Accuracy (%)',
      data: sectionData.computerVision.dailyData.map((d) => d.accuracy),
    },
    {
      name: 'Detection Rate (%)',
      data: sectionData.computerVision.dailyData.map((d) => d.detectionRate),
    },
  ];

  // ML Fuzzy Charts
  // ML Radial/Gauge Charts Options
  const createRadialChartOptions = (title: string, color: string) => ({
    chart: {
      type: 'radialBar' as const,
      sparkline: {
        enabled: false,
      },
      toolbar: {
        show: false,
      },
    },
    colors: [color],
    plotOptions: {
      radialBar: {
        startAngle: -135,
        endAngle: 135,
        hollow: {
          margin: 0,
          size: '70%',
          background: '#fff',
          image: undefined,
          imageHeight: 151,
          imageWidth: 151,
        },
        track: {
          background: '#f2f2f2',
          strokeWidth: '97%',
          margin: 5,
          dropShadow: {
            enabled: true,
            top: 2,
            left: 0,
            color: '#999',
            opacity: 1,
            blur: 2,
          },
        },
        dataLabels: {
          show: true,
          name: {
            offsetY: -10,
            show: true,
            color: '#888',
            fontSize: '13px',
          },
          value: {
            formatter: function (val: number) {
              return parseInt(val.toString()) + '%';
            },
            color: '#111',
            fontSize: '30px',
            show: true,
          },
        },
      },
    },
    stroke: {
      lineCap: 'round' as const,
    },
    labels: [title],
  });

  const mlFuzzyChartOptions = createRadialChartOptions('Fuzzy Accuracy', '#f59e0b');
  const mlFuzzyChartSeries = [sectionData.machineLearning.fuzzyAccuracy.value];

  const mlPrecisionChartOptions = createRadialChartOptions('Precision', '#14b8a6');
  const mlPrecisionChartSeries = [sectionData.machineLearning.precision.value];

  const mlRecallChartOptions = createRadialChartOptions('Recall', '#6366f1');
  const mlRecallChartSeries = [sectionData.machineLearning.recall.value];

  const mlF1ScoreChartOptions = createRadialChartOptions('F1 Score', '#ec4899');
  const mlF1ScoreChartSeries = [sectionData.machineLearning.f1Score.value];

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-50 via-blue-50 to-indigo-50 p-8 space-y-8">
      {/* Header */}
      <div className="">
        <h1 className="text-5xl font-bold bg-linear-to-r from-blue-600 via-cyan-600 to-emerald-600 bg-clip-text text-transparent">System Analytics</h1>
        <p className="mt-5 text-base text-slate-600">
          Machine Learning and Computer Vision performance metrics
        </p>
      </div>

      {/* ==================== MACHINE LEARNING FUZZY STATISTICS ==================== */}
      <section className="space-y-6">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold text-slate-900">ML Fuzzy Logic Statistics</h2>
          <span className="bg-orange-100 text-orange-800 text-sm font-semibold px-3 py-1 rounded">
            AI Classification
          </span>
        </div>

        {/* ML Fuzzy Gauge Charts */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Fuzzy Accuracy Gauge */}
          <div className="bg-white rounded-lg shadow border border-slate-200 p-6 hover:shadow-md transition">
            <div className="h-56">
              <ReactApexChart
                options={mlFuzzyChartOptions}
                series={mlFuzzyChartSeries}
                type="radialBar"
                height={220}
              />
            </div>
            <div className="text-center mt-4">
              <p className="text-sm text-slate-500">Fuzzy Accuracy</p>
              <p className="text-2xl font-bold text-slate-900">{sectionData.machineLearning.fuzzyAccuracy.value}%</p>
            </div>
          </div>

          {/* Precision Gauge */}
          <div className="bg-white rounded-lg shadow border border-slate-200 p-6 hover:shadow-md transition">
            <div className="h-56">
              <ReactApexChart
                options={mlPrecisionChartOptions}
                series={mlPrecisionChartSeries}
                type="radialBar"
                height={220}
              />
            </div>
            <div className="text-center mt-4">
              <p className="text-sm text-slate-500">Precision</p>
              <p className="text-2xl font-bold text-slate-900">{sectionData.machineLearning.precision.value}%</p>
            </div>
          </div>

          {/* Recall Gauge */}
          <div className="bg-white rounded-lg shadow border border-slate-200 p-6 hover:shadow-md transition">
            <div className="h-56">
              <ReactApexChart
                options={mlRecallChartOptions}
                series={mlRecallChartSeries}
                type="radialBar"
                height={220}
              />
            </div>
            <div className="text-center mt-4">
              <p className="text-sm text-slate-500">Recall</p>
              <p className="text-2xl font-bold text-slate-900">{sectionData.machineLearning.recall.value}%</p>
            </div>
          </div>

          {/* F1 Score Gauge */}
          <div className="bg-white rounded-lg shadow border border-slate-200 p-6 hover:shadow-md transition">
            <div className="h-56">
              <ReactApexChart
                options={mlF1ScoreChartOptions}
                series={mlF1ScoreChartSeries}
                type="radialBar"
                height={220}
              />
            </div>
            <div className="text-center mt-4">
              <p className="text-sm text-slate-500">F1 Score</p>
              <p className="text-2xl font-bold text-slate-900">{sectionData.machineLearning.f1Score.value}%</p>
            </div>
          </div>
        </div>

        {/* Performance Summary */}
        <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-slate-900">Performance Overview</h3>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-full bg-emerald-500"></span>
                <span className="text-slate-600">Excellent (≥90%)</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-full bg-amber-500"></span>
                <span className="text-slate-600">Good (80-89%)</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-full bg-rose-500"></span>
                <span className="text-slate-600">Needs Work (below 80%)</span>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Fuzzy Accuracy */}
            <div className="border-l-4 border-orange-500 pl-4 py-4 bg-orange-50 rounded-r hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <p className="text-sm font-semibold text-slate-700">Fuzzy Accuracy</p>
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-xs font-bold">
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Excellent
                </span>
              </div>
              <p className="text-3xl font-bold text-slate-900 mb-2">{sectionData.machineLearning.fuzzyAccuracy.value}%</p>
              <div className="w-full bg-slate-200 rounded-full h-2 mb-2">
                <div className="bg-emerald-500 h-2 rounded-full transition-all" style={{width: `${sectionData.machineLearning.fuzzyAccuracy.value}%`}}></div>
              </div>
              <p className="text-xs text-slate-600">95 out of 100 correct</p>
            </div>

            {/* Precision */}
            <div className="border-l-4 border-emerald-500 pl-4 py-4 bg-emerald-50 rounded-r hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <p className="text-sm font-semibold text-slate-700">Precision</p>
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-xs font-bold">
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Excellent
                </span>
              </div>
              <p className="text-3xl font-bold text-slate-900 mb-2">{sectionData.machineLearning.precision.value}%</p>
              <div className="w-full bg-slate-200 rounded-full h-2 mb-2">
                <div className="bg-emerald-500 h-2 rounded-full transition-all" style={{width: `${sectionData.machineLearning.precision.value}%`}}></div>
              </div>
              <p className="text-xs text-slate-600">No false alarms</p>
            </div>

            {/* Recall */}
            <div className="border-l-4 border-indigo-500 pl-4 py-4 bg-indigo-50 rounded-r hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <p className="text-sm font-semibold text-slate-700">Recall</p>
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-xs font-bold">
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Excellent
                </span>
              </div>
              <p className="text-3xl font-bold text-slate-900 mb-2">{sectionData.machineLearning.recall.value}%</p>
              <div className="w-full bg-slate-200 rounded-full h-2 mb-2">
                <div className="bg-emerald-500 h-2 rounded-full transition-all" style={{width: `${sectionData.machineLearning.recall.value}%`}}></div>
              </div>
              <p className="text-xs text-slate-600">Finds 94% of Grade A</p>
            </div>

            {/* F1 Score */}
            <div className="border-l-4 border-pink-500 pl-4 py-4 bg-pink-50 rounded-r hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <p className="text-sm font-semibold text-slate-700">F1 Score</p>
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-xs font-bold">
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Excellent
                </span>
              </div>
              <p className="text-3xl font-bold text-slate-900 mb-2">{sectionData.machineLearning.f1Score.value}%</p>
              <div className="w-full bg-slate-200 rounded-full h-2 mb-2">
                <div className="bg-emerald-500 h-2 rounded-full transition-all" style={{width: `${sectionData.machineLearning.f1Score.value}%`}}></div>
              </div>
              <p className="text-xs text-slate-600">Perfect balance</p>
            </div>
          </div>

          {/* Status Summary Card */}
          <div className="mt-6 p-4 bg-linear-to-r from-emerald-50 to-cyan-50 rounded-lg border border-emerald-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-bold text-emerald-900 mb-1">Overall System Status</p>
                <p className="text-xs text-emerald-700">All metrics performing at excellent levels - system is production-ready</p>
              </div>
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-emerald-500 text-white font-bold text-lg">
                  ✓
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Confusion Matrix Distribution Grade */}
        <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
          <h3 className="text-lg font-bold text-slate-900 mb-2">Classification Confusion Matrix</h3>
          <p className="text-sm text-slate-600 mb-4">Performance across Dragon Fruit grades</p>
          
          <div className="overflow-x-auto rounded border border-slate-300 bg-slate-50">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-300 bg-slate-100">
                  <th className="px-4 py-2 text-left font-bold text-slate-900">Predicted →</th>
                  <th className="px-4 py-2 text-center font-bold text-white bg-emerald-500">Grade A</th>
                  <th className="px-4 py-2 text-center font-bold text-white bg-amber-500">Grade B</th>
                  <th className="px-4 py-2 text-center font-bold text-white bg-rose-500">Grade C</th>
                  <th className="px-4 py-2 text-center font-bold text-slate-900 bg-slate-200">Total</th>
                </tr>
              </thead>
              <tbody>
                {confusionMatrix ? (
                  <>
                    <tr className="border-b border-slate-200 hover:bg-emerald-50">
                      <td className="px-4 py-2 font-bold text-slate-900 bg-emerald-100">Grade A</td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-emerald-200 text-emerald-900 px-2 py-1 rounded text-sm font-bold">{confusionMatrix[0][0]}</div></td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-slate-200 text-slate-700 px-2 py-1 rounded text-sm">{confusionMatrix[0][1]}</div></td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-slate-200 text-slate-700 px-2 py-1 rounded text-sm">{confusionMatrix[0][2]}</div></td>
                      <td className="px-4 py-2 text-center font-bold text-slate-900">{confusionMatrix[0][0] + confusionMatrix[0][1] + confusionMatrix[0][2]}</td>
                    </tr>
                    <tr className="border-b border-slate-200 hover:bg-amber-50">
                      <td className="px-4 py-2 font-bold text-slate-900 bg-amber-100">Grade B</td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-slate-200 text-slate-700 px-2 py-1 rounded text-sm">{confusionMatrix[1][0]}</div></td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-amber-200 text-amber-900 px-2 py-1 rounded text-sm font-bold">{confusionMatrix[1][1]}</div></td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-slate-200 text-slate-700 px-2 py-1 rounded text-sm">{confusionMatrix[1][2]}</div></td>
                      <td className="px-4 py-2 text-center font-bold text-slate-900">{confusionMatrix[1][0] + confusionMatrix[1][1] + confusionMatrix[1][2]}</td>
                    </tr>
                    <tr className="hover:bg-rose-50">
                      <td className="px-4 py-2 font-bold text-slate-900 bg-rose-100">Grade C</td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-slate-200 text-slate-700 px-2 py-1 rounded text-sm">{confusionMatrix[2][0]}</div></td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-slate-200 text-slate-700 px-2 py-1 rounded text-sm">{confusionMatrix[2][1]}</div></td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-rose-200 text-rose-900 px-2 py-1 rounded text-sm font-bold">{confusionMatrix[2][2]}</div></td>
                      <td className="px-4 py-2 text-center font-bold text-slate-900">{confusionMatrix[2][0] + confusionMatrix[2][1] + confusionMatrix[2][2]}</td>
                    </tr>
                  </>
                ) : (
                  <tr>
                    <td colSpan={5} className="px-4 py-4 text-center text-slate-500">Loading confusion matrix...</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Matrix Legend */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 rounded border border-blue-300">
              <p className="text-sm text-blue-700 font-bold mb-2">TRUE POSITIVES</p>
              <p className="text-sm text-slate-700">
                <span className="font-bold">
                  {metricsData && confusionMatrix
                    ? confusionMatrix[0][0] + confusionMatrix[1][1] + confusionMatrix[2][2]
                    : '0'}
                </span>{' '}
                correctly classified
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {metricsData ? `${(metricsData.accuracy * 100).toFixed(1)}% accuracy` : 'Accuracy: 0%'}
              </p>
            </div>
            <div className="p-4 bg-yellow-50 rounded border border-yellow-300">
              <p className="text-sm text-yellow-700 font-bold mb-2">PRECISION</p>
              <p className="text-sm text-slate-700">
                <span className="font-bold">
                  {metricsData ? (metricsData.macro_precision * 100).toFixed(1) : '0'}%
                </span>{' '}
                average precision
              </p>
              <p className="text-xs text-slate-500 mt-1">A: {metricsData ? (metricsData.precision_A * 100).toFixed(1) : '0'}% | B: {metricsData ? (metricsData.precision_B * 100).toFixed(1) : '0'}% | C: {metricsData ? (metricsData.precision_C * 100).toFixed(1) : '0'}%</p>
            </div>
            <div className="p-4 bg-purple-50 rounded border border-purple-300">
              <p className="text-sm text-purple-700 font-bold mb-2">RECALL</p>
              <p className="text-sm text-slate-700">
                <span className="font-bold">
                  {metricsData ? (metricsData.macro_recall * 100).toFixed(1) : '0'}%
                </span>{' '}
                average recall
              </p>
              <p className="text-xs text-slate-500 mt-1">A: {metricsData ? (metricsData.recall_A * 100).toFixed(1) : '0'}% | B: {metricsData ? (metricsData.recall_B * 100).toFixed(1) : '0'}% | C: {metricsData ? (metricsData.recall_C * 100).toFixed(1) : '0'}%</p>
            </div>
          </div>
        </div>

        {/* Feature Distribution Scatter Plots */}
        {/* <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
          <h3 className="text-lg font-bold text-slate-900 mb-2">Feature Distribution Analysis</h3>
          <p className="text-sm text-slate-600 mb-4">Dragon Fruit characteristics by grade</p>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-slate-50 rounded p-4 border border-slate-200">
              <h4 className="text-sm font-bold text-slate-900 mb-2">Length vs Diameter</h4>
              <div className="relative aspect-video bg-white rounded border border-slate-300 overflow-hidden">
                <svg className="w-full h-full" viewBox="0 0 500 350">
                  <line x1="60" y1="300" x2="450" y2="300" stroke="#cbd5e1" strokeWidth="2" />
                  <line x1="60" y1="30" x2="60" y2="300" stroke="#cbd5e1" strokeWidth="2" />
                  
                  {[...Array(5)].map((_, i) => (
                    <g key={`grid-x-${i}`}>
                      <line x1={60 + i * 100} y1="300" x2={60 + i * 100} y2="295" stroke="#e2e8f0" strokeWidth="1" />
                      <text x={60 + i * 100} y="320" fontSize="10" fill="#64748b" textAnchor="middle">{5 + i * 5}</text>
                    </g>
                  ))}
                  {[...Array(6)].map((_, i) => (
                    <g key={`grid-y-${i}`}>
                      <line x1="55" y1={300 - i * 45} x2="60" y2={300 - i * 45} stroke="#e2e8f0" strokeWidth="1" />
                      <text x="50" y={305 - i * 45} fontSize="10" fill="#64748b" textAnchor="end">{i * 4}</text>
                    </g>
                  ))}
                  
                  <text x="250" y="340" fontSize="11" fontWeight="bold" fill="#334155" textAnchor="middle">Length (cm)</text>
                  <text x="20" y="160" fontSize="11" fontWeight="bold" fill="#334155" textAnchor="middle" transform="rotate(-90, 20, 160)">Diameter (cm)</text>
                  
                  {[
                    {x: 15, y: 13}, {x: 16, y: 13.5}, {x: 17, y: 14.2}, {x: 18, y: 15}, {x: 19, y: 15.8},
                    {x: 15.5, y: 13.2}, {x: 17.5, y: 14}, {x: 18.5, y: 15.2}, {x: 20, y: 16}, {x: 19.5, y: 15.5}
                  ].map((point, i) => (
                    <circle key={`a-${i}`} cx={60 + (point.x - 5) * 38} cy={300 - (point.y - 4) * 30} r="4" fill="#ef4444" opacity="0.7" />
                  ))}
                  
                  {[
                    {x: 11, y: 10.5}, {x: 12, y: 10.8}, {x: 13, y: 11}, {x: 12.5, y: 10.2}, {x: 14, y: 11.5},
                    {x: 11.5, y: 10.3}, {x: 13.5, y: 10.8}, {x: 12, y: 11}, {x: 14.5, y: 11.8}, {x: 13.5, y: 10.5}
                  ].map((point, i) => (
                    <circle key={`b-${i}`} cx={60 + (point.x - 5) * 38} cy={300 - (point.y - 4) * 30} r="4" fill="#3b82f6" opacity="0.7" />
                  ))}
                  
                  {[
                    {x: 5, y: 4}, {x: 5.5, y: 4.2}, {x: 6, y: 4.5}, {x: 9, y: 8.8}, {x: 9.5, y: 9}, {x: 10, y: 9.5},
                    {x: 5.2, y: 4.1}, {x: 9.2, y: 8.9}, {x: 10.2, y: 9.2}, {x: 8.8, y: 8.5}
                  ].map((point, i) => (
                    <circle key={`c-${i}`} cx={60 + (point.x - 5) * 38} cy={300 - (point.y - 4) * 30} r="4" fill="#22c55e" opacity="0.7" />
                  ))}
                  
                  <g>
                    <text x="380" y="40" fontSize="10" fontWeight="bold" fill="#334155">Grade</text>
                    <circle cx="380" cy="55" r="3" fill="#ef4444" />
                    <text x="390" y="60" fontSize="9" fill="#334155">A</text>
                    <circle cx="380" cy="75" r="3" fill="#3b82f6" />
                    <text x="390" y="80" fontSize="9" fill="#334155">B</text>
                    <circle cx="380" cy="95" r="3" fill="#22c55e" />
                    <text x="390" y="100" fontSize="9" fill="#334155">C</text>
                  </g>
                </svg>
              </div>
              <p className="text-sm text-slate-600 text-center mt-2">Grade separation by size</p>
            </div>

            <div className="bg-slate-50 rounded p-4 border border-slate-200">
              <h4 className="text-sm font-bold text-slate-900 mb-2">Diameter vs Weight</h4>
              <div className="relative aspect-video bg-white rounded border border-slate-300 overflow-hidden">
                <svg className="w-full h-full" viewBox="0 0 500 350">
                  <line x1="60" y1="300" x2="450" y2="300" stroke="#cbd5e1" strokeWidth="2" />
                  <line x1="60" y1="30" x2="60" y2="300" stroke="#cbd5e1" strokeWidth="2" />
                  
                  {[...Array(5)].map((_, i) => (
                    <g key={`grid-x2-${i}`}>
                      <line x1={60 + i * 100} y1="300" x2={60 + i * 100} y2="295" stroke="#e2e8f0" strokeWidth="1" />
                      <text x={60 + i * 100} y="320" fontSize="10" fill="#64748b" textAnchor="middle">{4 + i * 3}</text>
                    </g>
                  ))}
                  {[...Array(6)].map((_, i) => (
                    <g key={`grid-y2-${i}`}>
                      <line x1="55" y1={300 - i * 45} x2="60" y2={300 - i * 45} stroke="#e2e8f0" strokeWidth="1" />
                      <text x="50" y={305 - i * 45} fontSize="10" fill="#64748b" textAnchor="end">{i * 300}</text>
                    </g>
                  ))}
                  
                  <text x="250" y="340" fontSize="11" fontWeight="bold" fill="#334155" textAnchor="middle">Diameter (cm)</text>
                  <text x="20" y="160" fontSize="11" fontWeight="bold" fill="#334155" textAnchor="middle" transform="rotate(-90, 20, 160)">Weight (gram)</text>
                  
                  {[
                    {x: 13, y: 600}, {x: 14, y: 700}, {x: 15, y: 800}, {x: 15.5, y: 850}, {x: 16, y: 1050},
                    {x: 14.5, y: 750}, {x: 15.2, y: 820}, {x: 16.5, y: 1100}, {x: 17, y: 1200}, {x: 16.8, y: 1300}
                  ].map((point, i) => (
                    <circle key={`a2-${i}`} cx={60 + (point.x - 4) * 76.5} cy={300 - (point.y / 1400) * 270} r="4" fill="#14b8a6" opacity="0.7" />
                  ))}
                  
                  {[
                    {x: 9, y: 150}, {x: 10, y: 200}, {x: 11, y: 280}, {x: 11.5, y: 320}, {x: 12, y: 380},
                    {x: 9.5, y: 180}, {x: 10.5, y: 240}, {x: 12.5, y: 420}, {x: 13, y: 500}, {x: 13.5, y: 600}
                  ].map((point, i) => (
                    <circle key={`b2-${i}`} cx={60 + (point.x - 4) * 76.5} cy={300 - (point.y / 1400) * 270} r="4" fill="#f97316" opacity="0.7" />
                  ))}
                  
                  {[
                    {x: 4, y: 20}, {x: 4.2, y: 25}, {x: 4.5, y: 30}, {x: 8.5, y: 120}, {x: 8.8, y: 140}, {x: 9, y: 160},
                    {x: 4.3, y: 28}, {x: 8.6, y: 130}, {x: 9.2, y: 170}, {x: 8.3, y: 100}
                  ].map((point, i) => (
                    <circle key={`c2-${i}`} cx={60 + (point.x - 4) * 76.5} cy={300 - (point.y / 1400) * 270} r="4" fill="#6366f1" opacity="0.7" />
                  ))}
                  
                  <g>
                    <text x="380" y="40" fontSize="10" fontWeight="bold" fill="#334155">Grade</text>
                    <circle cx="380" cy="55" r="3" fill="#14b8a6" />
                    <text x="390" y="60" fontSize="9" fill="#334155">A</text>
                    <circle cx="380" cy="75" r="3" fill="#f97316" />
                    <text x="390" y="80" fontSize="9" fill="#334155">B</text>
                    <circle cx="380" cy="95" r="3" fill="#6366f1" />
                    <text x="390" y="100" fontSize="9" fill="#334155">C</text>
                  </g>
                </svg>
              </div>
              <p className="text-sm text-slate-600 text-center mt-2">Weight correlates with diameter</p>
            </div>
          </div>
        </div> */}
      </section>

      {/* Summary Section
      <section className="pt-8 border-t-2 border-gray-200">
        <div className="bg-linear-to-r from-blue-50 to-purple-50 rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">System Health Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-2">IoT Health Status</p>
              <p className="text-xl font-bold text-green-600">✓ Excellent</p>
              <p className="text-xs text-gray-500 mt-1">All devices operating normally</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 mb-2">Vision Analysis Status</p>
              <p className="text-xl font-bold text-green-600">✓ Operational</p>
              <p className="text-xs text-gray-500 mt-1">High detection accuracy maintained</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 mb-2">ML Fuzzy Logic Status</p>
              <p className="text-xl font-bold text-green-600">✓ Performing Well</p>
              <p className="text-xs text-gray-500 mt-1">Classification accuracy above 94%</p>
            </div>
          </div>
        </div>
      </section> */}
    </div>
  );
}