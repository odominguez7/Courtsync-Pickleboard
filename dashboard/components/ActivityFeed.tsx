'use client';

import { useEffect, useState } from 'react';

interface Activity {
  type: string;
  description: string;
  timestamp: Date;
}

export function ActivityFeed() {
  const [activities, setActivities] = useState<Activity[]>([]);

  useEffect(() => {
    // Listen to Firestore activity_log collection
    // For demo, use static data
    const mockActivities: Activity[] = [
      {
        type: 'MATCH_CREATED',
        description: 'Match created, 3 players invited',
        timestamp: new Date()
      },
      {
        type: 'MATCH_CONFIRMED',
        description: 'Match confirmed with 4 players',
        timestamp: new Date(Date.now() - 60000)
      },
      {
        type: 'SPOT_DETECTED',
        description: 'Cancellation detected at Riverside Park',
        timestamp: new Date(Date.now() - 120000)
      }
    ];
    
    setActivities(mockActivities);
  }, []);

  return (
    <div className="space-y-4">
      {activities.map((activity, idx) => (
        <div 
          key={idx} 
          className="border-l-4 border-purple-500 pl-4 py-2 hover:bg-gray-50 transition"
        >
          <p className="font-semibold text-gray-900">{activity.description}</p>
          <p className="text-sm text-gray-600">
            {activity.timestamp.toLocaleTimeString()}
          </p>
        </div>
      ))}
    </div>
  );
}