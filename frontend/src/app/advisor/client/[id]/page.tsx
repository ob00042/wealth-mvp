'use client';

import { use } from 'react';
import ClientDetails from '@/components/ClientDetails';

export default function AdvisorClientPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ClientDetails clientId={Number(id)} />;
}
