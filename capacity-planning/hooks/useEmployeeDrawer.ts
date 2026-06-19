'use client';

import { useCallback, useState } from 'react';
import type { TeamMember } from '@/types/employee';

export function useEmployeeDrawer() {
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null);

  const openDrawer = useCallback((member: TeamMember) => {
    setSelectedMember(member);
  }, []);

  const closeDrawer = useCallback(() => {
    setSelectedMember(null);
  }, []);

  return {
    selectedMember,
    isOpen: selectedMember !== null,
    openDrawer,
    closeDrawer,
  };
}
