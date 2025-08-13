import React, { useState } from 'react';
import styles from './TagInput.module.css';

const TagInput = ({ tags, setTags }) => {
  const [inputValue, setInputValue] = useState('');

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const newTag = inputValue.trim();
      if (newTag && !tags.includes(newTag)) {
        setTags([...tags, newTag]);
      }
      setInputValue('');
    }
  };

  const removeTag = (tagToRemove) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  return (
    <div className={styles.tagInputContainer}>
      {tags.map((tag, index) => (
        <div key={index} className={styles.tag}>
          {tag}
          <button onClick={() => removeTag(tag)} className={styles.tagRemoveButton}>&times;</button>
        </div>
      ))}
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Add an interest and press Enter..."
        className={styles.tagInput}
      />
    </div>
  );
};

export default TagInput;