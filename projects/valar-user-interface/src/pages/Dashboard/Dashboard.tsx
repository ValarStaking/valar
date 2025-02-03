import { Container } from "@/components/Container/Container";
import { ROLE_DEL_STR, ROLE_VAL_STR } from "@/constants/smart-contracts";
import { DashboardContextProvider } from "@/contexts/DashboardContext";
import RoleSelector from "@/pages/Dashboard/_components/RoleSelector";
import useUserStore from "@/store/userStore";
import { bytesToStr } from "@/utils/convert";
import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

import DelegatorDashboard from "./_components/DelegatorDashboard/DelegatorDashboard";
import ValidatorDashboard from "./_components/ValidatorDashboard/ValidatorDashboard";

interface DashboardState {
  role?: string;
}

const Dashboard = () => {
  const { user } = useUserStore();
  const location = useLocation();
  const [_role, _setRole] = useState<string | undefined>(undefined);

  //Get User Role
  useEffect(() => {
    const state = location.state as DashboardState | undefined;
    const role = state?.role;

    if (!role) {
      if (user) {
        if (user.userInfo) {
          const role_fetched = bytesToStr(user.userInfo.role);
          if (role_fetched === ROLE_VAL_STR) {
            _setRole(ROLE_VAL_STR);
          } else if (role_fetched === ROLE_DEL_STR) {
            _setRole(ROLE_DEL_STR);
          } else {
            console.error("Unexpected user role: " + role_fetched);
            _setRole(undefined);
          }
        } else {
          console.log("User not yet registered at the platform.");
          //Keep the last selected role
        }
      } else {
        // Set to role that is passed during navigation
        _setRole(role);
      }
    } else {
      // Set to role that is passed during navigation
      _setRole(role);
    }
  }, [user, location]);

  // Display correct dashboard depending on user role

  if (!_role) {
    return (
      <Container>
        <RoleSelector setRole={_setRole} />
      </Container>
    );
  }

  return (
    <>
      <DashboardContextProvider>
        {_role === ROLE_VAL_STR && <ValidatorDashboard />}
        {_role === ROLE_DEL_STR && <DelegatorDashboard />}
      </DashboardContextProvider>
    </>
  );
};

export default Dashboard;
