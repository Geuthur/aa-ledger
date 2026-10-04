// Styles
import styles from "@/Components/Loader/ErrorLoader.module.css";

interface LoaderProps {
  message?: string;
  title?: string;
}

export const ErrorLoader = (props: LoaderProps = {}) => {
  return (
    <div className={`${styles["flex-container-error"]}`}>
      <span className={styles["shake"]}><i className={`fas fa-exclamation-triangle ${styles["icon-96"]}`}></i></span>
      {props.title && <h3>{props.title}</h3>}
      {props.message && <p>{props.message}</p>}
    </div>
  );
};

export default ErrorLoader;
