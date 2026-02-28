'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

export function RevenueCounter() {
  const [revenue, setRevenue] = useState(1247);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  useEffect(() => {
    // Listen to Firestore for real-time updates
    // Implementation depends on your Firebase setup
    
    // For demo, simulate updates every 30 seconds
    const interval = setInterval(() => {
      const increment = Math.floor(Math.random() * 80) + 20; // $20-$100
      setRevenue(prev => prev + increment);
      setLastUpdate(new Date().toLocaleTimeString());
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg shadow-2xl p-8 text-white">
      <p className="text-lg mb-2">Revenue Recovered Today</p>
      <motion.div
        key={revenue}
        initial={{ scale: 1.1 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.3 }}
        className="text-6xl font-bold mb-2"
      >
        ${revenue.toLocaleString()}
      </motion.div>
      {lastUpdate && (
        <p className="text-sm opacity-90">
          Last update: {lastUpdate}
        </p>
      )}
    </div>
  );
}