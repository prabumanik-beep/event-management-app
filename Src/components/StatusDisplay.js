import React from 'react';
import Spinner from './Spinner';
import styles from './StatusDisplay.module.css';

const StatusDisplay = ({ loading, error, children, loadingText = "Loading...", errorText, emptyText = "No data found." }) => {
  if (loading) {
    return (
      <div className={styles.statusContainer}>
        <Spinner />
        <p>{loadingText}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.statusContainer}>
        <p className={styles.error}>{errorText || error}</p>
      </div>
    );
  }

  // Check if children exist and are not an empty array
  if (!React.Children.count(children) || (Array.isArray(children) && children.flat().length === 0)) {
    return <div className={styles.statusContainer}><p>{emptyText}</p></div>;
  }

  return children;
};

export default StatusDisplay;