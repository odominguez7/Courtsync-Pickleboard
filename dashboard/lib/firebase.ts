import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  projectId: process.env.NEXT_PUBLIC_PROJECT_ID || 'courtsync-prod',
  // Add other config if needed
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);