import React, { useState, useEffect, useCallback } from 'react';
import './styles/App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';

// Model info component
const ModelCard = ({ model, modelKey, selected, onSelect }) => {
  const costColors = {
    low: '#10b981',
    medium: '#f59e0b',
    high: '#ef4444'
  };

  return (
    <div
      className={`model-card ${selected ? 'selected' : ''}`}
      onClick={() => onSelect(modelKey)}
    >
      <div className="model-header">
        <span className="model-name">{model.name}</span>
        <span
          className="cost-badge"
          style={{ backgroundColor: costColors[model.cost_tier] }}
        >
          {model.cost_tier}
        </span>
      </div>
      <p className="model-description">{model.description}</p>
      <div className="model-meta">
        <span className="use-case">{model.use_case}</span>
        <span className="context">{(model.context_window / 1000).toFixed(0)}K context</span>
      </div>
    </div>
  );
};

// Progress indicator
const ProgressBar = ({ progress }) => {
  const stageEmoji = {
    initializing: '🚀',
    scraping: '🕷️',
    summarizing: '📝',
    categorizing: '🗂️',
    reporting: '📊',
    complete: '✅',
    error: '❌'
  };

  return (
    <div className="progress-container">
      <div className="progress-header">
        <span className="progress-emoji">{stageEmoji[progress.stage] || '⏳'}</span>
        <span className="progress-message">{progress.message}</span>
      </div>
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${progress.percent}%` }}
        />
      </div>
      <span className="progress-percent">{progress.percent}%</span>
    </div>
  );
};

// Question input component
const QuestionInput = ({ questions, setQuestions }) => {
  const addQuestion = () => {
    setQuestions([...questions, '']);
  };

  const updateQuestion = (index, value) => {
    const updated = [...questions];
    updated[index] = value;
    setQuestions(updated);
  };

  const removeQuestion = (index) => {
    if (questions.length > 1) {
      setQuestions(questions.filter((_, i) => i !== index));
    }
  };

  return (
    <div className="questions-section">
      <label className="section-label">Research Questions</label>
      <p className="section-hint">What do you want to learn about this company?</p>

      {questions.map((q, i) => (
        <div key={i} className="question-row">
          <span className="question-number">{i + 1}</span>
          <input
            type="text"
            value={q}
            onChange={(e) => updateQuestion(i, e.target.value)}
            placeholder="e.g., What products does this company offer?"
            className="question-input"
          />
          <button
            onClick={() => removeQuestion(i)}
            className="remove-btn"
            disabled={questions.length === 1}
          >
            ×
          </button>
        </div>
      ))}

      <button onClick={addQuestion} className="add-question-btn">
        + Add Question
      </button>
    </div>
  );
};

// Report viewer component
const ReportViewer = ({ report, job }) => {
  const [activeTab, setActiveTab] = useState('report');

  const copyToClipboard = () => {
    navigator.clipboard.writeText(report);
  };

  const downloadReport = () => {
    const blob = new Blob([report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'research-report.md';
    a.click();
  };

  return (
    <div className="report-viewer">
      <div className="report-tabs">
        <button
          className={`tab ${activeTab === 'report' ? 'active' : ''}`}
          onClick={() => setActiveTab('report')}
        >
          📊 Report
        </button>
        <button
          className={`tab ${activeTab === 'pages' ? 'active' : ''}`}
          onClick={() => setActiveTab('pages')}
        >
          🌐 Pages Scraped ({job.pages_scraped?.length || 0})
        </button>
        <button
          className={`tab ${activeTab === 'summaries' ? 'active' : ''}`}
          onClick={() => setActiveTab('summaries')}
        >
          📝 Summaries
        </button>
      </div>

      <div className="report-actions">
        <button onClick={copyToClipboard} className="action-btn">
          📋 Copy
        </button>
        <button onClick={downloadReport} className="action-btn">
          ⬇️ Download
        </button>
      </div>

      <div className="report-content">
        {activeTab === 'report' && (
          <div className="markdown-content">
            <pre>{report}</pre>
          </div>
        )}

        {activeTab === 'pages' && (
          <div className="pages-list">
            {job.pages_scraped?.map((page, i) => (
              <div key={i} className="page-item">
                <a href={page.url} target="_blank" rel="noopener noreferrer">
                  {page.title || page.url}
                </a>
                <span className="page-depth">Depth: {page.depth}</span>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'summaries' && (
          <div className="summaries-list">
            {job.summaries?.map((summary, i) => (
              <div key={i} className="summary-item">
                <h4>{summary.title}</h4>
                <a href={summary.url} target="_blank" rel="noopener noreferrer">
                  {summary.url}
                </a>
                <p>{summary.summary}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Main App
function App() {
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [questions, setQuestions] = useState(['']);
  const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-20250514');
  const [models, setModels] = useState({});
  const [maxPages, setMaxPages] = useState(30);
  const [maxDepth, setMaxDepth] = useState(2);
  const [currentJob, setCurrentJob] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showSettings, setShowSettings] = useState(false);

  // Fetch available models
  useEffect(() => {
    fetch(`${API_BASE}/models`)
      .then(res => res.json())
      .then(setModels)
      .catch(err => console.error('Failed to fetch models:', err));
  }, []);

  // Poll job status
  const pollJobStatus = useCallback(async (jobId) => {
    try {
      const res = await fetch(`${API_BASE}/research/${jobId}`);
      const job = await res.json();
      setCurrentJob(job);

      if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
        setIsLoading(false);
        if (job.status === 'failed') {
          setError(job.error);
        }
      } else {
        setTimeout(() => pollJobStatus(jobId), 2000);
      }
    } catch (err) {
      setError('Failed to fetch job status');
      setIsLoading(false);
    }
  }, []);

  // Start research
  const startResearch = async () => {
    if (!websiteUrl) {
      setError('Please enter a website URL');
      return;
    }

    const validQuestions = questions.filter(q => q.trim());
    if (validQuestions.length === 0) {
      setError('Please enter at least one research question');
      return;
    }

    setError(null);
    setIsLoading(true);
    setCurrentJob(null);

    try {
      const res = await fetch(`${API_BASE}/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          website_url: websiteUrl,
          questions: validQuestions,
          model: selectedModel,
          max_pages: maxPages,
          max_depth: maxDepth
        })
      });

      if (!res.ok) {
        throw new Error('Failed to start research');
      }

      const { job_id } = await res.json();
      pollJobStatus(job_id);
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setCurrentJob(null);
    setError(null);
    setWebsiteUrl('');
    setQuestions(['']);
  };

  return (
    <div className="app">
      <div className="background-pattern" />

      <header className="header">
        <div className="logo">
          <span className="logo-icon">🔬</span>
          <h1>Deep Research Agent</h1>
        </div>
        <p className="tagline">AI-powered company intelligence at your fingertips</p>
      </header>

      <main className="main-content">
        {!currentJob?.report ? (
          <div className="research-form">
            <div className="form-section">
              <label className="section-label">Website URL</label>
              <input
                type="url"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="https://example.com"
                className="url-input"
                disabled={isLoading}
              />
            </div>

            <QuestionInput
              questions={questions}
              setQuestions={setQuestions}
            />

            <div className="form-section">
              <div className="section-header">
                <label className="section-label">AI Model</label>
                <button
                  className="settings-toggle"
                  onClick={() => setShowSettings(!showSettings)}
                >
                  ⚙️ {showSettings ? 'Hide' : 'Show'} Advanced Settings
                </button>
              </div>

              <div className="models-grid">
                {Object.entries(models).map(([key, model]) => (
                  <ModelCard
                    key={key}
                    model={model}
                    modelKey={key}
                    selected={selectedModel === key}
                    onSelect={setSelectedModel}
                  />
                ))}
              </div>
            </div>

            {showSettings && (
              <div className="advanced-settings">
                <div className="setting-row">
                  <label>Max Pages to Scrape</label>
                  <input
                    type="range"
                    min="10"
                    max="100"
                    value={maxPages}
                    onChange={(e) => setMaxPages(parseInt(e.target.value))}
                  />
                  <span>{maxPages}</span>
                </div>
                <div className="setting-row">
                  <label>Max Crawl Depth</label>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={maxDepth}
                    onChange={(e) => setMaxDepth(parseInt(e.target.value))}
                  />
                  <span>{maxDepth}</span>
                </div>
              </div>
            )}

            {error && (
              <div className="error-message">
                ⚠️ {error}
              </div>
            )}

            {currentJob && isLoading && (
              <ProgressBar progress={currentJob.progress} />
            )}

            <button
              onClick={startResearch}
              disabled={isLoading}
              className="submit-btn"
            >
              {isLoading ? 'Researching...' : '🚀 Start Research'}
            </button>
          </div>
        ) : (
          <div className="results-section">
            <div className="results-header">
              <h2>Research Complete</h2>
              <button onClick={resetForm} className="new-research-btn">
                ← New Research
              </button>
            </div>
            <ReportViewer report={currentJob.report} job={currentJob} />
          </div>
        )}
      </main>

      <footer className="footer">
        <p>Built with FastAPI & React • Powered by Claude & GPT</p>
      </footer>
    </div>
  );
}

export default App;
