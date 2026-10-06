// React
import React, { Component } from "react";
import type { ErrorInfo } from "react";

// Third Party
import {withTranslation } from "react-i18next";
import type { WithTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/ErrorBoundary.module.css";

import { ErrorLoader } from "@/Components/Base/Loader/ErrorLoader";

interface Props extends WithTranslation {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  title?: string;
  message?: string;
  trace?: string;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      message: "",
      trace: "",
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error: ", error, errorInfo);
    this.setState({
      hasError: true,
      title: error.name,
      message: error.message,
      trace: String(errorInfo.componentStack),
    });
  }

  render() {
    if (this.state.hasError) {
      const { t } = this.props;
      return (
        <>
          <ErrorLoader title={this.state.title} message={this.state.message} />
          <h1>{t("Something went wrong.")}</h1>
          <div className={`d-flex ${styles["centered"]}`}>
            <pre className={`border ${styles["trace"]}`}>
              {this.state.trace}
            </pre>
          </div>
        </>
      );
    }

    return this.props.children;
  }
}

export default withTranslation()(ErrorBoundary);
