import type { ReactElement } from 'react';
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import Alert from '@mui/material/Alert';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import ManagerAssignDecision from '../features/managerAssign/ManagerAssignDecision';
import ManagerAssignQueue from '../features/managerAssign/ManagerAssignQueue';
import ReferralDecision from '../features/underwriterReferral/ReferralDecision';
import ReferralQueue from '../features/underwriterReferral/ReferralQueue';
import { useOrchestratorHealth } from './useOrchestratorHealth';

const AREAS = [
  { path: '/manager', label: 'Manager' },
  { path: '/underwriter', label: 'Underwriter' },
] as const;

function activeAreaPath(pathname: string): string {
  const match = AREAS.find((area) => pathname.startsWith(area.path));
  return match ? match.path : AREAS[0].path;
}

/**
 * App shell: a Material UI app bar with navigation between the Manager area and
 * the Underwriter area, and the routes for each gate's queue and decision screen.
 */
export default function App(): ReactElement {
  const location = useLocation();
  const navigate = useNavigate();
  const activeArea = activeAreaPath(location.pathname);
  const health = useOrchestratorHealth();

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Approval UI
          </Typography>
        </Toolbar>
        <Tabs
          value={activeArea}
          onChange={(_event, value: string) => navigate(value)}
          textColor="inherit"
          indicatorColor="secondary"
        >
          {AREAS.map((area) => (
            <Tab key={area.path} value={area.path} label={area.label} />
          ))}
        </Tabs>
      </AppBar>

      <Container sx={{ py: 3 }}>
        {health === 'unreachable' ? (
          <Alert severity="warning" sx={{ mb: 2 }}>
            The orchestrator could not be reached. Queues and decisions below may fail until it recovers.
          </Alert>
        ) : null}
        <Routes>
          <Route path="/" element={<Navigate to="/manager" replace />} />
          <Route path="/manager" element={<ManagerAssignQueue />} />
          <Route path="/manager/:leadId" element={<ManagerAssignDecision />} />
          <Route path="/underwriter" element={<ReferralQueue />} />
          <Route path="/underwriter/:riskId" element={<ReferralDecision />} />
          <Route path="*" element={<Navigate to="/manager" replace />} />
        </Routes>
      </Container>
    </Box>
  );
}
