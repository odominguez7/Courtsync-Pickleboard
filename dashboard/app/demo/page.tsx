'use client';

import { useEffect, useState } from 'react';
import { RevenueCounter } from '@/components/RevenueCounter';
import { ActivityFeed } from '@/components/ActivityFeed';

export default function DemoPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            CourtSync Live Demo
          </h1>
          <p className="text-gray-600">
            Watch AI agents coordinate pickleball matches in real-time
          </p>
        </div>

        {/* Revenue Counter */}
        <div className="mb-8">
          <RevenueCounter />
        </div>

        {/* Activity Feed */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold mb-4">Live Agent Activity</h2>
          <ActivityFeed />
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          <MetricCard 
            title="Matches Today"
            value="47"
            change="+12%"
          />
          <MetricCard 
            title="Fill Rate"
            value="87%"
            change="+5%"
          />
          <MetricCard 
            title="Avg Time to Fill"
            value="3.2 min"
            change="-15%"
          />
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, change }: { title: string; value: string; change: string }) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <p className="text-gray-600 text-sm mb-2">{title}</p>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      <p className="text-green-600 text-sm mt-2">{change}</p>
    </div>
  );
}