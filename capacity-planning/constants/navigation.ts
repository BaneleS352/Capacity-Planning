/** Navigation items and routes */

export interface NavItem {
  label: string;
  href: string;
  icon: string;
  description?: string;
}

export const MAIN_NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: 'grid', description: 'Sprint capacity overview' },
  { label: 'Planning', href: '/planning', icon: 'sliders', description: 'What-if scenarios' },
  { label: 'Teams', href: '/teams', icon: 'layers', description: 'Team capacity groups' },
  { label: 'Employees', href: '/employees', icon: 'users', description: 'Team member profiles' },
  { label: 'Reports', href: '/reports', icon: 'bar-chart', description: 'Historical reports' },
  { label: 'Admin', href: '/admin', icon: 'settings', description: 'System configuration' },
];

export const SECONDARY_NAV_ITEMS: NavItem[] = [
  { label: 'Integrations', href: '/admin', icon: 'link', description: 'Jira & PaySpace' },
];

export const PRODUCT_NAME = 'Capacity Planning';
export const PRODUCT_SUBTITLE = 'HollywoodBets Engineering';
