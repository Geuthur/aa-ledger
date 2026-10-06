
// React
import { Outlet } from "react-router";

// Third Party
import { Col } from "react-bootstrap";

import ErrorBoundary from "@/Components/Base/Loader";
import AuthLeftMenuAsync from "@/Menu/AuthLeftMenuAsync";
import AuthRightMenuAsync from "@/Menu/AuthRightMenuAsync";

/**
 * AuthBase component that provides the layout for AllianceAuth
 */
const AuthBase = () => {
  return (
    <>
      <AuthLeftMenuAsync />
      <AuthRightMenuAsync />
      <Col>
        <div className="aa-section mt-4">
          <ErrorBoundary>
            <Outlet /> {/* Render the Children here */}
          </ErrorBoundary>
        </div>
      </Col>
    </>
  );
};

export default AuthBase;
